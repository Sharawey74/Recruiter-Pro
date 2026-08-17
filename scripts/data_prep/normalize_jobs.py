"""
Job Normalization Script
Converts raw jobs.json to canonical format with exactly 3 jobs
"""

import json
import re
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
SOURCE_FILE = PROJECT_ROOT / "data" / "json" / "jobs.json"
TARGET_FILE = PROJECT_ROOT / "data" / "json" / "jobs_canonical.json"
ARCHIVE_FILE = PROJECT_ROOT / "data" / "json" / "jobs_archive.json"


def parse_experience(exp_str: str) -> int:
    """Extract minimum years from experience string like '1 - 2 yrs'"""
    match = re.search(r"(\d+)", str(exp_str))
    return int(match.group(1)) if match else 0


def normalize_skills(skills_str: str) -> list:
    """Parse pipe-separated skills and normalize"""
    if not skills_str:
        return []
    skills = [s.strip().lower() for s in skills_str.split("|") if s.strip()]
    # Remove duplicates and normalize common synonyms
    normalized = []
    for skill in skills:
        skill = skill.replace(".js", "js").replace("javascript", "js")
        if skill not in normalized:
            normalized.append(skill)
    return normalized


def select_diverse_jobs(jobs: list, count: int = 3) -> list:
    """Select diverse jobs - prioritize different categories"""
    if len(jobs) <= count:
        return jobs

    # Take first job (Digital Artist), second (Analytics), fourth (Developer)
    # This ensures variety across design, analytics, and development
    selected_indices = [0, 1, 3]
    return [jobs[i] for i in selected_indices if i < len(jobs)]


def normalize_jobs():
    """Main normalization pipeline"""
    print(f"Reading from: {SOURCE_FILE}")

    if not SOURCE_FILE.exists():
        print(f"Error: {SOURCE_FILE} not found.")
        return False

    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        raw_jobs = json.load(f)

    print(f"Loaded {len(raw_jobs)} raw jobs")

    # Select 3 diverse jobs
    selected_raw = select_diverse_jobs(raw_jobs, count=3)

    # Normalize selected jobs
    canonical_jobs = []
    for job in selected_raw:
        canonical_jobs.append(
            {
                "job_id": job.get("Job Id", ""),
                "title": job.get("Job Title", ""),
                "description": job.get("Qualifications", ""),
                "required_skills": normalize_skills(job.get("skills", "")),
                "min_experience_years": parse_experience(job.get("Experience", "0")),
                "location": job.get("Location", "Remote"),
                "employment_type": "Full-time",
                "posted_date": "2023-10-27",
            }
        )

    # Save canonical jobs
    TARGET_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TARGET_FILE, "w", encoding="utf-8") as f:
        json.dump(canonical_jobs, f, indent=2, ensure_ascii=False)

    print(f"✓ Created {TARGET_FILE} with {len(canonical_jobs)} jobs")

    # Archive remaining jobs
    archive_jobs = [j for i, j in enumerate(raw_jobs) if i not in [0, 1, 3]]
    with open(ARCHIVE_FILE, "w", encoding="utf-8") as f:
        json.dump(archive_jobs, f, indent=2, ensure_ascii=False)

    print(f"✓ Archived {len(archive_jobs)} jobs to {ARCHIVE_FILE}")

    # Display canonical jobs
    print("\n=== Canonical Jobs ===")
    for i, job in enumerate(canonical_jobs, 1):
        print(f"\n{i}. {job['title']}")
        print(f"   Skills: {', '.join(job['required_skills'][:5])}...")
        print(f"   Experience: {job['min_experience_years']} years")

    return True


if __name__ == "__main__":
    success = normalize_jobs()
    if success:
        print("\n✓ Job normalization complete!")
    else:
        print("\n✗ Job normalization failed!")
