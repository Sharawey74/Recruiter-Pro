import json
import shutil
from pathlib import Path


def clean_jobs_dataset():
    input_path = Path("data/json/jobs.json")
    backup_path = Path("data/json/jobs.backup.json")

    # Create backup
    if input_path.exists():
        shutil.copy(input_path, backup_path)
        print(f"Created backup at {backup_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    print(f"Total jobs before cleaning: {len(jobs)}")

    cleaned_jobs = []
    seen_ids = set()

    # Advanced Quality Scoring
    ranked_jobs = []

    # Spam/Low-quality keywords to penalize
    SPAM_KEYWORDS = [
        "urgent",
        "hiring",
        "walk-in",
        "immediate",
        "opening",
        "wanted",
        "telesales",
        "telecaller",
    ]
    # High-quality role keywords
    ROLE_KEYWORDS = [
        "engineer",
        "developer",
        "analyst",
        "manager",
        "scientist",
        "consultant",
        "architect",
        "designer",
    ]

    for job in jobs:
        score = 0

        # 1. Skill Density (capped at 20 points)
        skills_str = job.get("skills", "")
        if not isinstance(skills_str, str):
            continue
        skills = [s.strip() for s in skills_str.split("|") if s.strip()]

        if len(skills) < 6:
            continue  # Hard gate
        score += min(len(skills), 20)

        # 2. Title Quality
        title = job.get("Job Title", "").strip()
        if len(title) < 5:
            continue

        title_lower = title.lower()
        # Penalty for spammy words
        if any(kw in title_lower for kw in SPAM_KEYWORDS):
            score -= 50

        # Bonus for standard professional roles
        if any(kw in title_lower for kw in ROLE_KEYWORDS):
            score += 10

        # 3. Description Richness
        desc = job.get("Qualifications", "")
        if len(desc) > 100:
            score += 5
        if len(desc) > 300:
            score += 5

        # 4. Consistency
        # Prefer jobs where title and skills align (heuristic)

        ranked_jobs.append({"job": job, "score": score})

    # Sort by quality score descending
    ranked_jobs.sort(key=lambda x: x["score"], reverse=True)

    # Select Top 500
    top_500 = [item["job"] for item in ranked_jobs[:500]]

    print(f"Filtered down to {len(top_500)} high-quality jobs.")

    # Save
    with open(input_path, "w", encoding="utf-8") as f:
        json.dump(top_500, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    clean_jobs_dataset()
