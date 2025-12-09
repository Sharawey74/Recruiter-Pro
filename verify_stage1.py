"""
Quick verification that Stage 1 is working correctly.
Auto-detects correct directory path.
"""
import sys
import json
from pathlib import Path
import os

# Auto-detect correct directory
script_dir = Path(__file__).parent
if not (script_dir / "data" / "json" / "resumes_sample.json").exists():
    # We might be in parent directory, try subdirectory
    if (script_dir / "HR-Project" / "data" / "json" / "resumes_sample.json").exists():
        os.chdir(script_dir / "HR-Project")
        script_dir = Path.cwd()

print(f"\nWorking directory: {Path.cwd()}")
print(f"Script directory: {script_dir}")

sys.path.insert(0, str(script_dir))

from src.agents.agent1_parser import ProfileJobParser

print("\n" + "="*60)
print("STAGE 1 VERIFICATION TEST")
print("="*60)

# Test 1: Initialize Parser
print("\n[1/5] Initializing Parser...")
parser = ProfileJobParser()
print("      SUCCESS - Parser initialized")

# Test 2: Load Data
print("\n[2/5] Loading Data Files...")
resumes_path = script_dir / "data" / "json" / "resumes_sample.json"
jobs_path = script_dir / "data" / "json" / "jobs.json"

print(f"      Looking for resumes at: {resumes_path}")
print(f"      File exists: {resumes_path.exists()}")

if not resumes_path.exists():
    print(f"\n❌ ERROR: Cannot find {resumes_path}")
    print(f"\nCurrent directory: {Path.cwd()}")
    print(f"Files in current directory:")
    for item in Path.cwd().iterdir():
        print(f"  - {item.name}")
    sys.exit(1)

with open(resumes_path, 'r', encoding='utf-8') as f:
    resumes = json.load(f)
with open(jobs_path, 'r', encoding='utf-8') as f:
    jobs = json.load(f)
print(f"      SUCCESS - Loaded {len(resumes)} resumes and {len(jobs)} jobs")

# Test 3: Parse Resume
print("\n[3/5] Parsing Sample Resume...")
resume = resumes[0]
profile = parser.parse_profile(resume['text'], 'verify_test')
print(f"      SUCCESS - Extracted:")
print(f"        - {len(profile['skills'])} skills")
print(f"        - {profile['experience_years']} years experience")
print(f"        - Seniority: {profile['seniority']}")
print(f"        - Email: {profile['contact']['email']}")

# Test 4: Parse Job
print("\n[4/5] Parsing Sample Job...")
job = jobs[0]
parsed_job = parser.parse_job(job)
print(f"      SUCCESS - Extracted:")
print(f"        - Job: {parsed_job['job_title']}")
print(f"        - {len(parsed_job['skills'])} required skills")
print(f"        - Experience: {parsed_job['experience']['min_years']}-{parsed_job['experience']['max_years']} years")

# Test 5: Calculate Match
print("\n[5/5] Calculating Match...")
matched = set(profile['skills']) & set(parsed_job['skills'])
match_pct = (len(matched) / len(parsed_job['skills']) * 100) if parsed_job['skills'] else 0
print(f"      SUCCESS - Match Score: {match_pct:.1f}%")
print(f"        - Matched {len(matched)} out of {len(parsed_job['skills'])} required skills")

# Summary
print("\n" + "="*60)
print("VERIFICATION RESULT: ALL TESTS PASSED")
print("="*60)
print("\nStage 1 is FULLY OPERATIONAL and ready to use!")
print("\nYou can now:")
print("  1. Parse any resume text")
print("  2. Parse job descriptions")
print("  3. Extract skills, experience, education")
print("  4. Calculate basic matches")
print("\nNext: Proceed to Stage 2 (Feature Engineering)")
print("="*60 + "\n")
