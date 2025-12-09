"""
Universal runner for Stage 1 verification.
Works from any directory level.
"""
import os
import sys
import subprocess
from pathlib import Path

# Find the correct project directory
current = Path.cwd()
script_location = Path(__file__).parent

# Possible project roots
possible_roots = [
    current,
    current / "HR-Project",
    script_location,
    script_location.parent,
]

project_root = None
for root in possible_roots:
    if (root / "data" / "json" / "resumes_sample.json").exists():
        project_root = root
        break

if project_root is None:
    print("❌ ERROR: Cannot find project data files!")
    print(f"\nSearched in:")
    for root in possible_roots:
        print(f"  - {root}")
    print(f"\nCurrent directory: {current}")
    print(f"\nPlease run from the HR-Project directory or ensure data files exist.")
    sys.exit(1)

print(f"✅ Found project at: {project_root}\n")

# Run verify_stage1.py as a subprocess from the project root
verify_script = project_root / "verify_stage1.py"
result = subprocess.run(
    [sys.executable, str(verify_script)],
    cwd=str(project_root),
    capture_output=False
)

sys.exit(result.returncode)
