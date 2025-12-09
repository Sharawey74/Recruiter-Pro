"""
Debug script to check file paths and directory structure.
"""
import os
from pathlib import Path

print("\n" + "="*70)
print("DEBUG: File Path Checker")
print("="*70)

print(f"\n1. Current Working Directory:")
print(f"   {Path.cwd()}")

print(f"\n2. Script Location:")
print(f"   {Path(__file__).parent}")

print(f"\n3. Checking for data files...")

# Check different possible paths
possible_paths = [
    Path.cwd() / "data" / "json" / "resumes_sample.json",
    Path.cwd() / "HR-Project" / "data" / "json" / "resumes_sample.json",
    Path(__file__).parent / "data" / "json" / "resumes_sample.json",
]

for i, path in enumerate(possible_paths, 1):
    exists = "✅ EXISTS" if path.exists() else "❌ NOT FOUND"
    print(f"\n   Path {i}: {exists}")
    print(f"   {path}")

print(f"\n4. Files in current directory:")
for item in sorted(Path.cwd().iterdir())[:20]:
    icon = "📁" if item.is_dir() else "📄"
    print(f"   {icon} {item.name}")

print(f"\n5. Checking HR-Project subdirectory...")
hr_project_dir = Path.cwd() / "HR-Project"
if hr_project_dir.exists():
    print(f"   ✅ HR-Project directory exists")
    print(f"\n   Contents of HR-Project:")
    for item in sorted(hr_project_dir.iterdir())[:20]:
        icon = "📁" if item.is_dir() else "📄"
        print(f"   {icon} {item.name}")
    
    # Check data directory
    data_dir = hr_project_dir / "data" / "json"
    if data_dir.exists():
        print(f"\n   ✅ data/json directory exists")
        print(f"\n   Files in data/json:")
        for item in data_dir.iterdir():
            size = item.stat().st_size if item.is_file() else 0
            icon = "📁" if item.is_dir() else "📄"
            print(f"   {icon} {item.name} ({size:,} bytes)")
else:
    print(f"   ❌ HR-Project directory not found")

print("\n" + "="*70)
print("SOLUTION:")
print("="*70)

# Determine correct command
if (Path.cwd() / "data" / "json" / "resumes_sample.json").exists():
    print("\n✅ You're in the correct directory!")
    print("   Run: python verify_stage1.py")
elif (Path.cwd() / "HR-Project" / "data" / "json" / "resumes_sample.json").exists():
    print("\n⚠️  You need to change to the HR-Project subdirectory")
    print("   Run: cd HR-Project")
    print("   Then: python verify_stage1.py")
else:
    print("\n❌ Cannot find data files!")
    print("   Please check if the data preparation script was run:")
    print("   python scripts/prepare_jobs_json.py")

print("\n" + "="*70 + "\n")
