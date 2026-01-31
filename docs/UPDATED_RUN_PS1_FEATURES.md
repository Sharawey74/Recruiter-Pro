# 🚀 UPDATED Run.ps1 - NEW FEATURES

## ✨ What's New in the Updated Script

### 1. **Live API Startup Logs** ✅
The script now shows you **real-time FastAPI initialization** in the terminal:

**Before:**
```
[2/3] Starting FastAPI Server...
✓ API started (you didn't see what happened)
```

**Now:**
```
[2/3] Starting FastAPI Server...
  Showing live API startup logs...
  
  🚀 Initializing 4-Agent Pipeline...
  ✅ Agent 1 (Parser) ready
  ✅ Agent 2 (Extractor) ready
  ✅ Agent 3 (Scorer) ready
  ✅ Agent 4 (Explainer) ready
  🎉 Pipeline initialization complete!
  ✅ Loaded 3000 jobs
  ✅ Model loaded: production/ats_model.joblib
  ✅ API Server Ready!
  📖 API Docs: http://localhost:8000/docs
  INFO: Uvicorn running on http://0.0.0.0:8000
```

### 2. **Live Next.js Compilation Logs** ✅
See exactly what Next.js is doing:

**Before:**
```
[3/3] Starting Next.js Frontend...
Waiting for Next.js to start... (5/30)
✓ Next.js started
```

**Now:**
```
[3/3] Starting Next.js Frontend...
  Showing live compilation logs...
  
  📦 Installing dependencies (if missing)...
  🧹 Cleaning Next.js cache...
  
  ▲ Next.js 14.2.3
  - Local:        http://localhost:3000
  - Environments: .env.local
  
  ✓ Starting...
  ✓ Ready in 3.8s
```

### 3. **Auto npm Install** 🎯
The script now checks if `node_modules` exists and installs automatically:

```powershell
if (-not (Test-Path node_modules)) {
    Write-Host "📦 Installing Next.js dependencies..."
    npm install
    # Shows progress in real-time
}
```

### 4. **Auto Clean .next Cache** 🧹
Prevents stale cache issues by cleaning before every start:

```powershell
# Automatically removes .next folder
Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue
```

### 5. **Better Next.js Detection** ⚡
No more false positives! The script now:
- Kills existing Node processes before starting
- Verifies Next.js is actually ready (not just port responding)
- Shows clear error messages if startup fails

**Before:**
```powershell
if (Test-Port 3000) {
    # Assumes Next.js is running
}
```

**Now:**
```powershell
if (Test-Port 3000) {
    Write-Host "⚠ Next.js already running on port 3000"
    Write-Host "Stopping existing instance..."
    Get-Process | Where-Object { $_.ProcessName -match "node" } | Stop-Process -Force
    Start-Sleep -Seconds 2
    # Then starts fresh
}
```

### 6. **Color-Coded Output** 🎨
Important messages are now highlighted:

- **🔴 Red:** Errors, failures, exceptions
- **🟢 Green:** Success messages, ready states, agent initialization
- **🟡 Yellow:** Warnings, skipped steps
- **🔵 Cyan:** Info messages, startup events
- **⚪ Gray:** Normal output, detailed logs

### 7. **Improved Error Handling** 🛡️
The script now:
- Checks if jobs fail to start
- Shows full error output if services crash
- Provides helpful troubleshooting hints

**Example:**
```powershell
if ($fastapiJob.State -eq 'Failed') {
    Write-Host "✗ FastAPI job failed!" -ForegroundColor Red
    Receive-Job $fastapiJob | Write-Host
    Write-Host "Check if data/json/jobs.json exists" -ForegroundColor Yellow
    Cleanup
    exit 1
}
```

### 8. **Better Cleanup** 🧽
When you press `Ctrl+C`, the script:
- Stops all background jobs gracefully
- Kills Node.js processes (no orphan processes)
- Clears the screen for next run

---

## 📊 Side-by-Side Comparison

### Starting FastAPI

#### OLD VERSION:
```powershell
[2/3] Starting FastAPI Server...
✓ API started on port 8000
```

#### NEW VERSION:
```powershell
[2/3] Starting FastAPI Server...
  Showing live API startup logs...
  
  INFO:     Will watch for changes in these directories: [...
  INFO:     Uvicorn running on http://0.0.0.0:8000
  INFO:     Started server process [12345]
  INFO:     Waiting for application startup.
  🚀 Initializing 4-Agent Pipeline...
  ✅ Agent 1 (Parser) ready
  ✅ Agent 2 (Extractor) ready  
  ✅ Agent 3 (Scorer) ready
  ✅ Agent 4 (Explainer) ready
  🎉 Pipeline initialization complete!
  ✅ Loaded 3000 jobs from data/json/jobs.json
  ✅ Model loaded: production/ats_model.joblib (99.18% recall)
  ✅ API Server Ready!
  📖 API Docs: http://localhost:8000/docs
  INFO:     Application startup complete.
  
  ✓ FastAPI Server Ready on port 8000
```

### Starting Next.js

#### OLD VERSION:
```powershell
[3/3] Starting Next.js Frontend...
Waiting for Next.js to start... (1/30)
Waiting for Next.js to start... (2/30)
Waiting for Next.js to start... (3/30)
...
✓ Next.js started successfully on port 3000
```

#### NEW VERSION:
```powershell
[3/3] Starting Next.js Frontend...
  Showing live compilation logs...
  
  ⚠ Next.js already running on port 3000
  Stopping existing instance...
  
  📦 Installing Next.js dependencies...
  (skipped - already installed)
  
  🧹 Cleaning Next.js cache...
  
  > ai-resume-matcher-frontend@2.0.0 dev
  > next dev
  
  ▲ Next.js 14.2.3
  - Local:        http://localhost:3000
  - Environments: .env.local
  
  ✓ Starting...
  ✓ Ready in 3.8s
  
  ✓ Next.js Frontend Ready on port 3000
```

---

## 🎯 Why These Changes Matter

### 1. **Transparency**
You can now see exactly what's happening at each step. No more wondering "is it stuck or still loading?"

### 2. **Debugging**
If something fails, you'll see the error immediately in the terminal, making troubleshooting much easier.

### 3. **Confidence**
You know the app is truly ready when you see "✓ Ready in 3.8s" instead of just hoping port 3000 is responding.

### 4. **Reliability**
Auto npm install and cache cleaning prevent common startup issues.

### 5. **Speed**
Killing orphan processes and cleaning cache means faster, cleaner starts.

---

## 🚀 How to Use the Updated Script

### Start All Services:
```powershell
cd C:\Users\DELL\Desktop\Recruiter-Pro-AI
.\Run.ps1
```

### What You'll See:
1. **Ollama starts** - Shows "Listening on 127.0.0.1:11500"
2. **FastAPI starts** - Shows full 4-agent pipeline initialization
3. **Next.js starts** - Shows compilation and "Ready" message
4. **Summary** - All services listed with their URLs

### Monitor Services:
The script keeps running and shows live output from all services.

### Stop All Services:
Press `Ctrl+C` once - all services will shut down gracefully.

---

## 🔧 Troubleshooting

### If FastAPI Fails to Start:
The script now shows you WHY it failed:

**Example Error:**
```
  ERROR: Could not load jobs.json
  FileNotFoundError: data/json/jobs.json not found
  
  ✗ FastAPI job failed!
  Check if data/json/jobs.json exists
```

### If Next.js Fails to Start:
You'll see the exact compilation error:

**Example Error:**
```
  Error: Cannot find module 'sonner'
  
  ✗ Next.js failed to start!
  Run manually: cd frontend && npm install && npm run dev
```

---

## 📝 Full Feature List

### Startup Sequence:
- [x] Check ports before starting
- [x] Start Ollama with status check
- [x] Start FastAPI with **live logs**
- [x] Start Next.js with **live logs**
- [x] Auto npm install if needed
- [x] Auto clean .next cache
- [x] Kill existing processes on port 3000
- [x] Verify each service is truly ready
- [x] Show all service URLs at the end

### Monitoring:
- [x] Real-time API initialization logs
- [x] Real-time Next.js compilation logs
- [x] Color-coded output (errors, success, warnings)
- [x] Job state monitoring (Failed, Running, Completed)

### Error Handling:
- [x] Detect job failures
- [x] Show full error output
- [x] Provide troubleshooting hints
- [x] Graceful cleanup on failure

### Cleanup:
- [x] Stop all background jobs on Ctrl+C
- [x] Kill orphan Node processes
- [x] Remove old .next cache
- [x] Clear terminal for next run

---

## 🎓 Technical Details

### How Live Logs Work:

```powershell
# Start job
$fastapiJob = Start-Job -ScriptBlock {
    python -m uvicorn src.api:app --reload 2>&1
}

# Receive output in real-time
$lastOutputLength = 0
while ($elapsed -lt $timeout) {
    $allOutput = Receive-Job $fastapiJob
    if ($allOutput) {
        $outputLines = @($allOutput)
        # Show only new lines
        for ($i = $lastOutputLength; $i -lt $outputLines.Count; $i++) {
            Write-Host "  $outputLines[$i]"
        }
        $lastOutputLength = $outputLines.Count
    }
    Start-Sleep -Milliseconds 500
}
```

### How Process Cleanup Works:

```powershell
# On Ctrl+C:
trap {
    # Stop all jobs
    $jobs | ForEach-Object { Stop-Job $_ -ErrorAction SilentlyContinue }
    $jobs | ForEach-Object { Remove-Job $_ -Force -ErrorAction SilentlyContinue }
    
    # Kill orphan Node processes
    Get-Process | Where-Object { $_.ProcessName -match "node" } | Stop-Process -Force
    
    # Exit gracefully
    exit 0
}
```

---

## 🌟 What This Means for You

### Before:
- ❌ Blind startup (is it working? stuck? crashed?)
- ❌ False positives (port 3000 in use = Next.js running)
- ❌ Manual npm install required
- ❌ Stale cache causing issues
- ❌ Cryptic errors with no context

### Now:
- ✅ See every step in real-time
- ✅ Know exactly when services are ready
- ✅ Auto-installation of dependencies
- ✅ Fresh start every time
- ✅ Clear error messages with hints

---

**Last Updated:** 2026-01-30  
**Version:** 2.0 (with live logs)  
**Status:** ✅ Production Ready
