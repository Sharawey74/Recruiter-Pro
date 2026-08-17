"""
Tests for scripts/validate_corpus.py.

The validator is the thing standing between a generated corpus and the app, so
"it probably works" is not good enough. Every rule gets one planted defect and
must be shown to catch it — a validator that silently passes bad data is worse
than no validator, because it converts an unknown into a false assurance.
"""

import copy
import importlib.util
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

_spec = importlib.util.spec_from_file_location(
    "validate_corpus", PROJECT_ROOT / "scripts" / "validate_corpus.py"
)
validate_corpus = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validate_corpus)

CATEGORIES = validate_corpus.CATEGORIES
PREFIX = validate_corpus.PREFIX
GEN_DATE = date(2026, 8, 9)


def _description() -> str:
    """A description satisfying the format rules: 4 headings, 900-1400 chars."""
    body = (
        "About the role\n"
        "We run a small team that owns this area from end to end and cares about "
        "doing it properly. You will own delivery and work closely with partners "
        "across the business to keep things moving forward.\n\n"
        "Responsibilities\n"
        + "\n".join(["• Own a clear area of delivery and report progress weekly"] * 5)
        + "\n\nRequirements\n"
        + "\n".join(["• Several years of relevant hands on experience in the field"] * 4)
        + "\n\nNice to have\n"
        "• Exposure to a regulated operating environment\n"
        "• Comfort working with ambiguity and shifting priorities"
    )
    return body + " " * max(0, 920 - len(body))


def _skills_payload() -> dict:
    return {
        "_meta": {"comment": "test vocabulary", "schema_version": "2.0"},
        "families": {
            c: {f"{c.title()} Skill {i}": [f"{c} skill {i}"] for i in range(1, 10)}
            for c in CATEGORIES
        },
    }


def _jobs_payload() -> dict:
    jobs = []
    for i, c in enumerate(CATEGORIES):
        skills = [f"{c.title()} Skill {n}" for n in range(1, 10)]
        jobs.append(
            {
                "job_id": f"{PREFIX[c]}-{i + 1:04d}",
                "category": c,
                "title": f"{c.title()} Specialist",
                "company_name": f"Company {i}",
                "location_city": "Cairo",
                "location_country": "Egypt",
                "remote_type": "on-site",
                "employment_type": "full-time",
                "seniority_level": "mid",
                "min_experience_years": 3,
                "max_experience_years": 6,
                "description": _description(),
                "required_skills": skills[:6],
                "preferred_skills": skills[6:9],
                "posted_date": str(GEN_DATE - timedelta(days=10)),
                "education_level": "Bachelor's",
                "salary_range": "45000-65000 USD",
                "is_active": True,
            }
        )
    return {
        "schema_version": "2.0",
        "generated_at": str(GEN_DATE),
        "record_count": len(jobs),
        "skill_vocabulary": "data/dictionaries/skills.json",
        "skill_vocabulary_version": "2.0",
        "categories": {c: 1 for c in CATEGORIES},
        "jobs": jobs,
    }


def _run(tmp_path: Path, jobs: dict, skills: dict | None = None) -> int:
    jp, sp = tmp_path / "jobs.json", tmp_path / "skills.json"
    jp.write_text(json.dumps(jobs), encoding="utf-8")
    sp.write_text(json.dumps(skills or _skills_payload()), encoding="utf-8")
    return validate_corpus.validate(jp, sp)


# --------------------------------------------------------------------------
# The clean case must pass. If this ever fails, every negative test below is
# meaningless — they would "catch" defects that were never the real cause.
# --------------------------------------------------------------------------


def test_clean_corpus_passes(tmp_path):
    assert _run(tmp_path, _jobs_payload()) == 0


# --------------------------------------------------------------------------
# One planted defect per rule. Each must be caught.
# --------------------------------------------------------------------------


def _mutate(fn):
    payload = _jobs_payload()
    fn(payload)
    return payload


@pytest.mark.parametrize(
    "label, mutate",
    [
        ("record_count disagrees with actual length", lambda p: p.update(record_count=999)),
        ("category outside the eight", lambda p: p["jobs"][0].update(category="devops")),
        ("duplicate job_id", lambda p: p["jobs"][1].update(job_id=p["jobs"][0]["job_id"])),
        ("job_id prefix does not match category", lambda p: p["jobs"][1].update(job_id="ZZZ-0002")),
        ("deprecated key present", lambda p: p["jobs"][0].update(company="Legacy Corp")),
        (
            "skill absent from the vocabulary",
            lambda p: p["jobs"][0].update(
                required_skills=[
                    "Totally Invented Skill",
                    "Engineering Skill 2",
                    "Engineering Skill 3",
                    "Engineering Skill 4",
                    "Engineering Skill 5",
                    "Engineering Skill 6",
                ]
            ),
        ),
        (
            "required and preferred skills overlap",
            lambda p: p["jobs"][0].update(preferred_skills=p["jobs"][0]["required_skills"][:2]),
        ),
        (
            "too few required skills",
            lambda p: p["jobs"][0].update(required_skills=["Engineering Skill 1"]),
        ),
        (
            "experience range outside the seniority band",
            lambda p: p["jobs"][0].update(min_experience_years=25, max_experience_years=30),
        ),
        (
            "maintenance job marked remote",
            lambda p: next(j for j in p["jobs"] if j["category"] == "maintenance").update(
                remote_type="remote"
            ),
        ),
        (
            "maintenance job marked hybrid",
            lambda p: next(j for j in p["jobs"] if j["category"] == "maintenance").update(
                remote_type="hybrid"
            ),
        ),
        (
            "duplicate (title, company_name) pair",
            lambda p: p["jobs"][1].update(
                title=p["jobs"][0]["title"], company_name=p["jobs"][0]["company_name"]
            ),
        ),
        (
            "education_level not in the allowed set",
            lambda p: p["jobs"][0].update(education_level="Postgraduate Certificate"),
        ),
        (
            "description too short",
            lambda p: p["jobs"][0].update(description="About the role\nToo short."),
        ),
        (
            "description too long",
            lambda p: p["jobs"][0].update(description=_description() + "x" * 900),
        ),
        (
            "description missing a required heading",
            lambda p: p["jobs"][0].update(
                description=_description().replace("Nice to have", "Bonus points")
            ),
        ),
        (
            "posted_date outside the 90-day window",
            lambda p: p["jobs"][0].update(posted_date=str(GEN_DATE - timedelta(days=400))),
        ),
        (
            "posted_date in the future",
            lambda p: p["jobs"][0].update(posted_date=str(GEN_DATE + timedelta(days=5))),
        ),
        ("posted_date malformed", lambda p: p["jobs"][0].update(posted_date="09-08-2026")),
        (
            "record fails JobPosting construction",
            lambda p: p["jobs"][0].update(remote_type="anywhere"),
        ),
    ],
)
def test_planted_defect_is_caught(tmp_path, label, mutate):
    assert _run(tmp_path, _mutate(mutate)) == 1, f"validator did NOT catch: {label}"


# --------------------------------------------------------------------------
# Structural failures
# --------------------------------------------------------------------------


def test_bare_array_is_rejected(tmp_path):
    """The old corpus was a bare array; the new one must be an envelope."""
    assert _run(tmp_path, _jobs_payload()["jobs"]) == 1


def test_missing_jobs_file_is_reported(tmp_path):
    skills = tmp_path / "skills.json"
    skills.write_text(json.dumps(_skills_payload()), encoding="utf-8")
    assert validate_corpus.validate(tmp_path / "absent.json", skills) == 1


def test_flat_vocabulary_layout_still_readable(tmp_path):
    """Back-compat: the pre-_meta/families layout must still be understood."""
    flat = {"comment": "legacy layout", "schema_version": "2.0"}
    flat.update(_skills_payload()["families"])
    assert _run(tmp_path, _jobs_payload(), skills=flat) == 0
