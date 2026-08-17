"""
Fail if any tracked source file contains a stray control character.

A literal 0x08 once reached Agent 2's tokenising regex, where `\\b` should have
been a word boundary. Skill extraction dropped from 15 skills to 1. The
terminal rendered the backspace by eating the preceding character, so the line
looked correct in every diff, grep and review -- it was only found by
inspecting the compiled code object. A 0x00 got into a test file the same way
later in the same session.

A third one, 0x0D, got into README.md's launcher command: `.\\run.ps1` was
written as a bare carriage return followed by `un.ps1`, which renders as
`.un.ps1` in a terminal and as a plausible-looking command in most editors. It
was a copy-pasteable instruction that could not work.

That third one is why this checks more than it used to. It slipped through
three separate gaps:

  * only `*.py` was scanned, and the file was Markdown;
  * only src/tests/scripts were scanned, and the file was at the root;
  * 0x0D was unconditionally allowed, because CRLF line endings are normal on
    Windows -- but a CR that is *not* followed by LF is never a line ending.

All three are closed below. CRLF is still fine; a bare CR is not.

Every one of these was introduced by tooling that wrote an escape sequence as a
raw byte, and none is visible to a human reading the file, so the check has to
be at byte level. This is that check.

    python scripts/check_control_chars.py [paths...]

Exits 1 and prints every offending file, line and byte offset.
"""

import sys
from pathlib import Path

# Everything below 0x20 except tab (09) and newline (0A). Carriage return (0D)
# is handled separately: legitimate as part of CRLF, never on its own.
FORBIDDEN = set(range(0x00, 0x09)) | {0x0B, 0x0C} | set(range(0x0E, 0x20))
CARRIAGE_RETURN = 0x0D
LINE_FEED = 0x0A

# Source and prose. Not data/ -- the job corpus is a megabyte of JSON that no
# human edits by hand, and scanning it on every CI run buys nothing.
SUFFIXES = (".py", ".ts", ".tsx", ".js", ".mjs", ".css", ".ps1", ".md", ".json", ".yml", ".yaml")

SKIP_DIRS = {
    "__pycache__",
    "node_modules",
    ".next",
    ".git",
    ".venv",
    "venv",
    "htmlcov",
    ".pytest_cache",
    "Images",
}

# Directories walked recursively, plus the root files worth checking. README.md
# is here because that is where the third incident landed, and TASKS.md because
# the fourth landed there minutes later, in the very commit that widened this
# check -- the same `.\\run.ps1` string, the same raw 0x0D, written by the same
# tooling. TASKS.md is gitignored, so it will not exist in CI; a missing path is
# skipped rather than failing, and the point of listing it is the local run.
DEFAULT_PATHS = (
    "src",
    "tests",
    "scripts",
    "frontend/app",
    "frontend/components",
    "frontend/lib",
    "README.md",
    "TASKS.md",
    "run.ps1",
)


def candidates(root: Path):
    """Every file under `root` worth scanning, or `root` itself if it is one."""
    if root.is_file():
        if root.suffix in SUFFIXES:
            yield root
        return

    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in SUFFIXES:
            continue
        if SKIP_DIRS.intersection(path.parts):
            continue
        yield path


def offenders(path: Path):
    raw = path.read_bytes()
    for offset, byte in enumerate(raw):
        # A CR is a line ending only when an LF follows it.
        if byte == CARRIAGE_RETURN:
            if offset + 1 < len(raw) and raw[offset + 1] == LINE_FEED:
                continue
        elif byte not in FORBIDDEN:
            continue

        line = raw.count(b"\n", 0, offset) + 1
        context = raw[max(0, offset - 30) : offset + 10]
        yield line, offset, byte, context


def main(argv) -> int:
    roots = [Path(p) for p in (argv[1:] or DEFAULT_PATHS)]
    found = 0
    scanned = 0

    for root in roots:
        if not root.exists():
            continue
        for path in candidates(root):
            scanned += 1
            for line, offset, byte, context in offenders(path):
                found += 1
                label = (
                    "bare carriage return"
                    if byte == CARRIAGE_RETURN
                    else f"control character {hex(byte)}"
                )
                print(f"{path}:{line}: {label} at byte {offset}")
                print(f"    context: {context!r}")

    if found:
        print(
            f"\n{found} control character(s) found across {scanned} files. "
            f"See the module docstring for why this is a hard failure."
        )
        return 1

    print(f"No control characters in {scanned} files " f"({', '.join(str(r) for r in roots)})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
