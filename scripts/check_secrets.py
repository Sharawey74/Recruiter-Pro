"""
Fail if a credential is committed, or about to be.

This exists because one already was. `tests/test_agent2_5_llm_scorer.py` carried
a live OpenRouter key on two lines, was later deleted, and is still reachable
from origin/main in a public repository -- deleting a file does not remove it
from history, and scrapers watch public pushes for exactly these shapes.

The lesson is the same one the control-character scanner encodes: a human
reading a diff does not reliably catch this. A key is a plausible-looking
string in a file full of plausible-looking strings, and review misses it.

    python scripts/check_secrets.py              # tracked files (what CI runs)
    python scripts/check_secrets.py --staged     # pre-commit: only staged files
    python scripts/check_secrets.py --history    # every commit; slow, for audits

Exits 1 and prints the file, line and a masked excerpt of each match.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# Prefix-anchored where the vendor gives us a prefix, because that is what makes
# a pattern precise enough to block a commit on. A generic "long random string"
# rule would fire on hashes, minified JS and base64 assets, and a check that
# cries wolf gets disabled.
PATTERNS: list[tuple[str, re.Pattern]] = [
    ("OpenRouter",    re.compile(r"sk-or-v1-[0-9a-f]{32,}")),
    ("Anthropic",     re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("OpenAI",        re.compile(r"sk-(?:proj-)?[A-Za-z0-9]{32,}")),
    ("GitHub token",  re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}")),
    ("AWS key id",    re.compile(r"AKIA[0-9A-Z]{16}")),
    ("Google API",    re.compile(r"AIza[0-9A-Za-z_\-]{35}")),
    ("HuggingFace",   re.compile(r"hf_[A-Za-z0-9]{30,}")),
    ("Slack token",   re.compile(r"xox[baprs]-[0-9A-Za-z\-]{10,}")),
    ("Private key",   re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----")),
]

# This file names every pattern it hunts for, and .env.example documents the
# variable. Neither is a leak, and both would otherwise fail the check forever.
SELF_EXEMPT = {
    "scripts/check_secrets.py",
    ".env.example",
}

BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".joblib",
                   ".pkl", ".db", ".sqlite", ".sqlite3", ".woff", ".woff2"}


def mask(secret: str) -> str:
    """Enough to locate it in the file, never enough to use."""
    return f"{secret[:12]}...{secret[-4:]} ({len(secret)} chars)"


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else ""


def scan_text(text: str) -> list[tuple[str, int, str]]:
    findings = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for label, pattern in PATTERNS:
            for match in pattern.finditer(line):
                findings.append((label, line_number, match.group(0)))
    return findings


def tracked_files(staged: bool) -> list[str]:
    if staged:
        # Added, copied or modified; a deletion has nothing to scan.
        out = git("diff", "--cached", "--name-only", "--diff-filter=ACM")
    else:
        out = git("ls-files")
    return [line for line in out.splitlines() if line.strip()]


def check_working_tree(staged: bool) -> int:
    found = 0
    scanned = 0

    for relative in tracked_files(staged):
        if relative in SELF_EXEMPT:
            continue
        path = Path(relative)
        if path.suffix.lower() in BINARY_SUFFIXES or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        scanned += 1
        for label, line_number, secret in scan_text(text):
            found += 1
            print(f"{relative}:{line_number}: {label} credential - {mask(secret)}")

    if found:
        print(
            f"\n{found} credential(s) in {'staged' if staged else 'tracked'} files.\n"
            f"Move the value into .env (gitignored) and read it with os.getenv.\n"
            f"If it has already been pushed, revoking it is the fix -- rewriting\n"
            f"history does not un-publish what was public."
        )
        return 1

    print(f"No credentials in {scanned} {'staged' if staged else 'tracked'} files")
    return 0


def check_history() -> int:
    """
    Every commit reachable from any ref. Slow, and the only check that would
    have caught the key this repository actually leaked.
    """
    found = 0
    for label, pattern in PATTERNS:
        # -S is a content search across history; the regex then confirms and
        # locates the match, since -S alone only names the commits.
        commits = git("log", "--all", "--format=%H", "-S", pattern.pattern,
                      "--pickaxe-regex").splitlines()
        for commit in commits:
            blob = git("grep", "-nI", "-E", pattern.pattern, commit)
            for line in blob.splitlines():
                if any(exempt in line for exempt in SELF_EXEMPT):
                    continue
                match = pattern.search(line)
                if not match:
                    continue
                found += 1
                location = line.split(":", 3)[:3]
                print(f"{':'.join(location)}: {label} - {mask(match.group(0))}")

    if found:
        print(
            f"\n{found} credential occurrence(s) in history.\n"
            f"Revoke every key listed above. That is what closes the exposure;\n"
            f"a history rewrite is optional tidying and breaks existing clones."
        )
        return 1

    print("No credentials found in git history")
    return 0


def check_env_is_ignored() -> int:
    """`.env` gitignored and untracked. The premise everything else rests on."""
    problems = 0

    if ".env" in git("ls-files").splitlines():
        print(".env is TRACKED by git. Remove it: git rm --cached .env")
        problems += 1

    if not git("check-ignore", ".env").strip():
        print(".env is not covered by .gitignore.")
        problems += 1

    return problems


def main(argv: list[str]) -> int:
    if "--history" in argv:
        return check_history()

    staged = "--staged" in argv
    return max(check_env_is_ignored(), check_working_tree(staged))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
