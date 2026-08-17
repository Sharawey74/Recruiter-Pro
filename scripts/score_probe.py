"""Score-diff harness: proves a refactor moved no score.

Emits one deterministic CSV line per job for a fixed CV, so before/after runs
can be diffed byte-for-byte. A refactor that is meant to be behaviour-preserving
is verified here, not by reading the diff and hoping.

    PYTHONHASHSEED=0 python scripts/score_probe.py before.csv
    # ... make the change ...
    PYTHONHASHSEED=0 python scripts/score_probe.py after.csv
    diff before.csv after.csv          # must be empty

Two flags are mandatory, not stylistic:

* ``PYTHONHASHSEED=0`` -- agent3 builds matched/missing/extra through ``set()``,
  and Python randomizes string hashing per process. Without a pinned seed the
  lists reorder between runs and the diff fills with phantom changes that look
  exactly like real ones.
* ``include_ml=False`` (hardcoded below) -- the ML model's presence makes runs
  incomparable across machines and masks rule-based movement.

This harness carried every Phase 2 commit. It is what established that
``c27b86f`` (the weights consolidation) moved zero scores across all 800 jobs,
and it is the acceptance test for the Agent 3 extraction in 2.7.
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agents.agent3_scorer import HybridScoringAgent  # noqa: E402
from src.storage.models import CVProfile, JobPosting  # noqa: E402

# Fixed CV. Deliberately includes skills that exercise the defects Phase 2 found,
# so a regression in any of them shows up as a diff rather than as silence:
#   JavaScript -> must NOT satisfy a "Java" requirement (substring collision)
#   .NET       -> must resolve (punctuation was stripped before lookup)
#   DevOps     -> was reachable only via the deleted local synonym dict
# Do not edit this list. Its value is that it is the same CV every baseline in
# the project was measured against; changing it invalidates the comparison.
CV = CVProfile(
    cv_id="phase2-probe",
    file_name="phase2-probe.pdf",
    name="Probe Candidate",
    email="probe@example.com",
    skills=[
        "Python",
        "JavaScript",
        "Docker",
        "SQL",
        "React",
        "AWS",
        "PostgreSQL",
        "Kubernetes",
        ".NET",
        "DevOps",
        "Communication",
        "Machine Learning",
        "Git",
        "Linux",
        "REST API",
    ],
    experience_years=5,
    education="Bachelor's",
    extracted_data={"current_title": "Senior Software Engineer"},
)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2

    out_path = Path(sys.argv[1])
    agent = HybridScoringAgent()
    payload = json.loads((ROOT / "data/json/jobs.json").read_text(encoding="utf-8"))
    jobs = [JobPosting(**j) for j in payload["jobs"]]

    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "job_id",
                "skill",
                "title",
                "experience",
                "education",
                "keyword",
                "rule_based",
                "overall",
                "matched",
                "missing",
            ]
        )
        for job in sorted(jobs, key=lambda j: j.job_id):
            b = agent.score_match(CV, job, include_ml=False)
            w.writerow(
                [
                    job.job_id,
                    f"{b.skill_score:.6f}",
                    f"{getattr(b, 'title_score', 0.0):.6f}",
                    f"{b.experience_score:.6f}",
                    f"{b.education_score:.6f}",
                    f"{b.keyword_score:.6f}",
                    f"{b.rule_based_score:.6f}",
                    f"{b.hybrid_score:.6f}",
                    "|".join(sorted(b.matched_skills or [])),
                    "|".join(sorted(b.missing_skills or [])),
                ]
            )

    print(f"wrote {out_path} for {len(jobs)} jobs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
