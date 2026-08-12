"""
Fail if any tracked Python source contains a control character.

A literal 0x08 once reached Agent 2's tokenising regex, where `\\b` should have
been a word boundary. Skill extraction dropped from 15 skills to 1. The
terminal rendered the backspace by eating the preceding character, so the line
looked correct in every diff, grep and review -- it was only found by
inspecting the compiled code object. A 0x00 got into a test file the same way
later in the same session.

Both were introduced by tooling that wrote an escape sequence as a raw byte.
Neither is visible to a human reading the file, so the check has to be at byte
level. This is that check.

    python scripts/check_control_chars.py [paths...]

Exits 1 and prints every offending file, line and byte offset.
"""
import sys
from pathlib import Path

# Everything below 0x20 except tab (09), newline (0A) and carriage return (0D).
FORBIDDEN = set(range(0x00, 0x09)) | {0x0B, 0x0C} | set(range(0x0E, 0x20))

DEFAULT_PATHS = ("src", "tests", "scripts")


def offenders(root: Path):
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        raw = path.read_bytes()
        for offset, byte in enumerate(raw):
            if byte in FORBIDDEN:
                line = raw.count(b"\n", 0, offset) + 1
                context = raw[max(0, offset - 30):offset + 10]
                yield path, line, offset, byte, context


def main(argv) -> int:
    roots = [Path(p) for p in (argv[1:] or DEFAULT_PATHS)]
    found = 0
    for root in roots:
        if not root.exists():
            continue
        for path, line, offset, byte, context in offenders(root):
            found += 1
            print(f"{path}:{line}: control character {hex(byte)} at byte {offset}")
            print(f"    context: {context!r}")

    if found:
        print(f"\n{found} control character(s) found. See the module docstring "
              f"for why this is a hard failure.")
        return 1

    print(f"No control characters in {', '.join(str(r) for r in roots)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
