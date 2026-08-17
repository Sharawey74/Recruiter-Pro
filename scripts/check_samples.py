import json
import random

# Load cleaned jobs
with open("data/json/jobs_cleaned.json", "r", encoding="utf-8") as f:
    jobs = json.load(f)

# Sample 15 jobs
samples = random.sample(jobs, 15)

print("=" * 120)
print("SAMPLE CLEANED JOBS")
print("=" * 120)

for i, job in enumerate(samples, 1):
    print(f"\n{i}. {job['title']}")
    print(f"   Company: {job['company_name']}")
    print(f"   Location: {job['location_city']}, {job['location_country']} ({job['remote_type']})")
    print(
        f"   Seniority: {job['seniority_level']} | Experience: {job['min_experience_years']}-{job['max_experience_years']} years"
    )
    print(f"   Required Skills: {', '.join(job['required_skills'][:8])}")
    print(f"   Type: {job['employment_type']}")

print("\n" + "=" * 120)
print(f"TOTAL JOBS: {len(jobs)}")
print("=" * 120)
