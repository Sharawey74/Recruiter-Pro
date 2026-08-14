#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Runs Recruiter Pro — the FastAPI backend and the Next.js frontend — in one window.

.DESCRIPTION
    Starts both services, waits until each is genuinely answering, streams their
    logs side by side with a prefix, and stops both on Ctrl-C.

    This replaces Run.ps1, which opened three detached terminals and then exited.
    Three things about that were worth fixing:

      * It ran `Get-Process | Where-Object { $_.ProcessName -match "uvicorn|python" }
        | Stop-Process -Force` whenever port 8000 was busy — and the same for
        "node" on 3000. That matches on the process *name*, so it killed every
        Python and every Node process on the machine: language servers, other
        projects' dev servers, notebooks. This script only ever touches the PID
        that actually holds the port, and only when you pass -Force.

      * Its port check used BeginConnect + WaitOne, whose wait handle signals on
        a refused connection just as it does on a successful one, so a free port
        often read as busy.

      * It reported "launched" as soon as the windows opened. A backend that
        dies on startup — a missing corpus, an import error — looked identical
        to one that came up fine, because nothing checked.

    It also started Ollama. Since ADR-2, the rule-based explanation provider is
    first-class and the app runs with no LLM at all, so a launcher that insists
    on one is asking for a dependency the product does not have. Configure a
    provider in .env if you want explanations.

.PARAMETER ApiPort
    Backend port. Default 8000.

.PARAMETER WebPort
    Frontend port. Default 3000.

.PARAMETER Prod
    Build the frontend and serve the production bundle instead of running the
    dev server. Slower to start, and what you want to check a real build.

.PARAMETER Force
    If a port is already listening, kill the process holding that one port
    before starting. Without this the script reports what is in the way and
    stops.

.PARAMETER NoBrowser
    Do not open a browser once both services are up.

.EXAMPLE
    .\run.ps1

.EXAMPLE
    .\run.ps1 -Prod -NoBrowser

.EXAMPLE
    .\run.ps1 -ApiPort 8010 -WebPort 3010 -Force
#>
[CmdletBinding()]
param(
    [int]$ApiPort = 8000,
    [int]$WebPort = 3000,
    [switch]$Prod,
    [switch]$Force,
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'

$Root     = $PSScriptRoot
$Frontend = Join-Path $Root 'frontend'
$LogDir   = Join-Path $Root 'logs'
$ApiLog   = Join-Path $LogDir 'api.log'
$WebLog   = Join-Path $LogDir 'web.log'

# Filled in as services start; the finally block stops whatever is here, so a
# failure half-way through does not leave an orphan holding a port.
$script:Started = @()

# ---------------------------------------------------------------- helpers ---

function Write-Step   { param([string]$Text) Write-Host "  $Text" -ForegroundColor Gray }
function Write-Ok     { param([string]$Text) Write-Host "  [ok] $Text" -ForegroundColor Green }
function Write-Warn   { param([string]$Text) Write-Host "  [!]  $Text" -ForegroundColor Yellow }
function Write-Fail   { param([string]$Text) Write-Host "  [x]  $Text" -ForegroundColor Red }

function Write-Banner {
    param([string]$Text)
    Write-Host ""
    Write-Host $Text -ForegroundColor Cyan
    Write-Host ('-' * $Text.Length) -ForegroundColor DarkCyan
}

<#
    True only if something accepts a connection on the port.

    Connect() throws on refusal, which is the distinction the old
    BeginConnect/WaitOne check could not make.
#>
function Test-PortInUse {
    param([int]$Port)
    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $client.Connect('127.0.0.1', $Port)
        return $true
    } catch {
        return $false
    } finally {
        $client.Dispose()
    }
}

function Get-PortOwner {
    param([int]$Port)
    if (-not (Get-Command Get-NetTCPConnection -ErrorAction SilentlyContinue)) { return $null }
    try {
        $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop |
                Select-Object -First 1
        if (-not $conn) { return $null }
        $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        return [pscustomobject]@{
            Pid  = $conn.OwningProcess
            Name = if ($proc) { $proc.ProcessName } else { 'unknown' }
        }
    } catch {
        return $null
    }
}

<#
    Clears a port, or explains what is holding it.

    Only the PID listening on this exact port is touched, and only under
    -Force. Matching on a process name is what made the old script dangerous.
#>
function Clear-Port {
    param([int]$Port, [string]$Label)

    if (-not (Test-PortInUse $Port)) { return $true }

    $owner = Get-PortOwner $Port
    $who = if ($owner) { "$($owner.Name) (PID $($owner.Pid))" } else { 'an unknown process' }

    if (-not $Force) {
        Write-Fail "$Label port $Port is already in use by $who."
        Write-Step "Re-run with -Force to stop it, pick another port with -${Label}Port,"
        Write-Step "or leave it running if that is the service you wanted."
        return $false
    }

    if (-not $owner) {
        Write-Fail "$Label port $Port is in use and the owning process could not be identified."
        return $false
    }

    Write-Warn "Stopping $who to free port $Port"
    Stop-ProcessTree -ProcessId $owner.Pid

    # Give the socket a moment to leave TIME_WAIT before we bind it.
    for ($i = 0; $i -lt 20 -and (Test-PortInUse $Port); $i++) { Start-Sleep -Milliseconds 250 }

    if (Test-PortInUse $Port) {
        Write-Fail "Port $Port is still held after stopping PID $($owner.Pid)."
        return $false
    }
    return $true
}

<#
    Kills a process and everything it spawned.

    Both services fork: `uvicorn --reload` runs a supervisor plus a worker, and
    `npm` shells out to `next`. Stopping only the parent leaves the child alive
    and the port bound.
#>
function Stop-ProcessTree {
    param([int]$ProcessId)
    if (-not $ProcessId) { return }
    if ($IsWindows -or $env:OS -eq 'Windows_NT') {
        & taskkill.exe /PID $ProcessId /T /F *> $null
    } else {
        try { Stop-Process -Id $ProcessId -Force -ErrorAction Stop } catch { }
    }
}

function Start-AppService {
    param(
        [string]$Name,
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory,
        [string]$LogPath,
        [hashtable]$Environment = @{}
    )

    # Truncated per run: an appended log makes the tail below replay the
    # previous run's output as though it were happening now.
    Set-Content -Path $LogPath -Value '' -NoNewline -Encoding utf8

    $previous = @{}
    foreach ($key in $Environment.Keys) {
        $previous[$key] = [Environment]::GetEnvironmentVariable($key)
        [Environment]::SetEnvironmentVariable($key, $Environment[$key])
    }

    try {
        $process = Start-Process -FilePath $FilePath `
                                 -ArgumentList $Arguments `
                                 -WorkingDirectory $WorkingDirectory `
                                 -RedirectStandardOutput $LogPath `
                                 -RedirectStandardError "$LogPath.err" `
                                 -WindowStyle Hidden `
                                 -PassThru
    } finally {
        foreach ($key in $previous.Keys) {
            [Environment]::SetEnvironmentVariable($key, $previous[$key])
        }
    }

    $script:Started += [pscustomobject]@{ Name = $Name; Process = $process }
    return $process
}

<#
    Waits for a predicate, surfacing the service's own log if it never passes.

    "Still starting..." with no further detail is what let a backend that had
    already crashed look like one that was merely slow.
#>
function Wait-For {
    param(
        [string]$Name,
        [scriptblock]$Ready,
        [System.Diagnostics.Process]$Process,
        [int]$TimeoutSeconds = 90,
        [string]$LogPath
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if ($Process.HasExited) {
            Write-Fail "$Name exited during startup (code $($Process.ExitCode))."
            Show-LogTail -Path $LogPath
            return $false
        }
        if (& $Ready) { return $true }
        Start-Sleep -Milliseconds 400
    }

    Write-Fail "$Name did not become ready within ${TimeoutSeconds}s."
    Show-LogTail -Path $LogPath
    return $false
}

function Show-LogTail {
    param([string]$Path, [int]$Lines = 25)
    foreach ($candidate in @($Path, "$Path.err")) {
        if (-not (Test-Path $candidate)) { continue }
        $content = Get-Content $candidate -Tail $Lines -ErrorAction SilentlyContinue
        if (-not $content) { continue }
        Write-Host ""
        Write-Host "--- last $Lines lines of $(Split-Path $candidate -Leaf) ---" -ForegroundColor DarkGray
        $content | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
    }
    Write-Host ""
}

function Stop-Everything {
    if (-not $script:Started) { return }
    Write-Host ""
    Write-Banner 'Shutting down'
    foreach ($service in $script:Started) {
        if ($service.Process -and -not $service.Process.HasExited) {
            Write-Step "Stopping $($service.Name) (PID $($service.Process.Id))"
            Stop-ProcessTree -ProcessId $service.Process.Id
        }
    }
    $script:Started = @()
    Write-Ok 'Both services stopped.'
    Write-Host ""
}

# ------------------------------------------------------------- preflight ---

Write-Host ""
Write-Host 'Recruiter Pro' -ForegroundColor Magenta
Write-Host 'CV intelligence — FastAPI + Next.js' -ForegroundColor DarkGray

Write-Banner 'Checking the environment'

# A virtualenv if the project has one, otherwise whatever python is on PATH.
$python = @(
    (Join-Path $Root '.venv/Scripts/python.exe'),
    (Join-Path $Root '.venv/bin/python'),
    (Join-Path $Root 'venv/Scripts/python.exe'),
    (Join-Path $Root 'venv/bin/python')
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($python) {
    Write-Ok "Python: $python"
} else {
    $onPath = Get-Command python -ErrorAction SilentlyContinue
    if (-not $onPath) {
        Write-Fail 'Python was not found on PATH and there is no .venv here.'
        exit 1
    }
    $python = $onPath.Source
    Write-Ok "Python: $python (no virtualenv — using PATH)"
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Fail 'npm was not found on PATH. Install Node.js 20.9+ and try again.'
    exit 1
}
Write-Ok "Node: $((& node --version) 2>$null)"

# Import the app rather than grepping for packages: this catches a missing
# dependency, a syntax error and a bad .env in one check, before two services
# are running and the failure is buried in a log.
Write-Step 'Importing the API...'
$import = & $python -c "import src.api" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Fail 'The backend could not be imported.'
    $import | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
    Write-Host ""
    Write-Step 'If this names a missing package: pip install -r requirements-dev.txt'
    exit 1
}
Write-Ok 'Backend imports cleanly'

if (-not (Test-Path (Join-Path $Frontend 'node_modules'))) {
    Write-Warn 'frontend/node_modules is missing — running npm install (one time)'
    Push-Location $Frontend
    try {
        & npm install --no-audit --no-fund
        if ($LASTEXITCODE -ne 0) { Write-Fail 'npm install failed.'; exit 1 }
    } finally { Pop-Location }
}
Write-Ok 'Frontend dependencies present'

if (-not (Clear-Port -Port $ApiPort -Label 'Api'))  { exit 1 }
if (-not (Clear-Port -Port $WebPort -Label 'Web'))  { exit 1 }

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

# ---------------------------------------------------------------- backend ---

try {
    Write-Banner "Starting the backend on port $ApiPort"

    $apiProcess = Start-AppService -Name 'api' `
        -FilePath $python `
        -Arguments @('-m', 'uvicorn', 'src.api:app', '--host', '127.0.0.1', '--port', "$ApiPort", '--reload') `
        -WorkingDirectory $Root `
        -LogPath $ApiLog `
        -Environment @{
            # Unbuffered, or nothing reaches the log until the process exits.
            PYTHONUNBUFFERED = '1'
            # The API's allowed origin has to follow -WebPort. Without this a
            # non-default port starts cleanly and then fails every request in
            # the browser with a CORS error that names neither cause nor cure.
            CORS_ORIGINS     = "http://localhost:$WebPort"
        }

    $health = "http://127.0.0.1:$ApiPort/health"
    $ready = Wait-For -Name 'Backend' -Process $apiProcess -LogPath $ApiLog -Ready {
        try {
            (Invoke-WebRequest -Uri $health -TimeoutSec 2 -UseBasicParsing).StatusCode -eq 200
        } catch { $false }
    }
    if (-not $ready) { exit 1 }

    # What the health payload says is worth repeating, because both of these
    # degrade silently: no corpus means every match returns 503, and no model
    # means the advertised hybrid scoring is not running at all.
    $status = Invoke-RestMethod -Uri $health -TimeoutSec 5
    Write-Ok "Backend ready — http://localhost:$ApiPort/docs"
    Write-Step "Corpus: $($status.components.jobs_loaded) jobs"
    if ($status.components.ml_model_loaded) {
        Write-Step 'Scoring: hybrid (ML + rules)'
    } else {
        Write-Warn 'Scoring: rule-based only — the ML model did not load'
    }
    if ([int]$status.components.jobs_loaded -eq 0) {
        Write-Warn 'No jobs loaded — /match will return 503 until data/json/jobs.json is readable'
    }

    # --------------------------------------------------------------- web ---

    Write-Banner "Starting the frontend on port $WebPort"

    $webEnv = @{
        # Inlined by Next at build time and read at dev-server start, so it has
        # to be set here for -ApiPort to reach the browser.
        NEXT_PUBLIC_API_URL = "http://localhost:$ApiPort"
    }

    if ($Prod) {
        Write-Step 'Building the production bundle...'
        Push-Location $Frontend
        try {
            $env:NEXT_PUBLIC_API_URL = $webEnv.NEXT_PUBLIC_API_URL
            & npm run build
            if ($LASTEXITCODE -ne 0) { Write-Fail 'The frontend build failed.'; exit 1 }
        } finally {
            Remove-Item Env:NEXT_PUBLIC_API_URL -ErrorAction SilentlyContinue
            Pop-Location
        }
        $webArgs = @('run', 'start', '--', '--port', "$WebPort")
    } else {
        $webArgs = @('run', 'dev', '--', '--port', "$WebPort")
    }

    $webProcess = Start-AppService -Name 'web' `
        -FilePath 'npm.cmd' `
        -Arguments $webArgs `
        -WorkingDirectory $Frontend `
        -LogPath $WebLog `
        -Environment $webEnv

    $ready = Wait-For -Name 'Frontend' -Process $webProcess -LogPath $WebLog -Ready {
        Test-PortInUse $WebPort
    }
    if (-not $ready) { exit 1 }

    $appUrl = "http://localhost:$WebPort"
    Write-Ok "Frontend ready — $appUrl"

    if (-not $NoBrowser) { Start-Process $appUrl | Out-Null }

    # -------------------------------------------------------------- logs ---

    Write-Banner 'Running'
    Write-Host "  App        $appUrl" -ForegroundColor White
    Write-Host "  API docs   http://localhost:$ApiPort/docs" -ForegroundColor White
    Write-Host "  Logs       $LogDir" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host '  Ctrl-C stops both services.' -ForegroundColor DarkGray
    Write-Host ""

    # Opened with FileShare.ReadWrite so the running services can keep writing
    # while this reads. Get-Content -Wait would lock or poll one file only.
    $readers = @(
        @{ Tag = 'api'; Colour = 'Cyan';   Reader = [System.IO.StreamReader]::new([System.IO.FileStream]::new($ApiLog, 'Open', 'Read', 'ReadWrite')) },
        @{ Tag = 'api'; Colour = 'Cyan';   Reader = [System.IO.StreamReader]::new([System.IO.FileStream]::new("$ApiLog.err", 'OpenOrCreate', 'Read', 'ReadWrite')) },
        @{ Tag = 'web'; Colour = 'Green';  Reader = [System.IO.StreamReader]::new([System.IO.FileStream]::new($WebLog, 'Open', 'Read', 'ReadWrite')) },
        @{ Tag = 'web'; Colour = 'Green';  Reader = [System.IO.StreamReader]::new([System.IO.FileStream]::new("$WebLog.err", 'OpenOrCreate', 'Read', 'ReadWrite')) }
    )

    try {
        while ($true) {
            foreach ($source in $readers) {
                while ($null -ne ($line = $source.Reader.ReadLine())) {
                    if ($line.Trim()) {
                        Write-Host "[$($source.Tag)] " -ForegroundColor $source.Colour -NoNewline
                        Write-Host $line
                    }
                }
            }

            foreach ($service in @($apiProcess, $webProcess)) {
                if ($service.HasExited) {
                    Write-Host ""
                    Write-Fail "A service exited (code $($service.ExitCode)). Stopping the other."
                    return
                }
            }

            Start-Sleep -Milliseconds 200
        }
    } finally {
        foreach ($source in $readers) { $source.Reader.Dispose() }
    }
} finally {
    # Runs on Ctrl-C, on a failed exit, and on one service dying — so the other
    # never survives as an orphan holding its port.
    Stop-Everything
}
