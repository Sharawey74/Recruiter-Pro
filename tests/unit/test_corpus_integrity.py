"""
Guards on the shipped job corpus.

The old corpus failed silently: its skill strings were free text, so the
vocabulary recognised 2.3% of them and 60.9% of jobs had nothing matchable.
Nothing detected that, because nothing asserted it. These tests are that
assertion — the invariant is meant to hold by construction, so if one of them
ever fails, the corpus was regenerated without honouring the spec.
"""
import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
JOBS_PATH = PROJECT_ROOT / "data" / "json" / "jobs.json"
SKILLS_PATH = PROJECT_ROOT / "data" / "dictionaries" / "skills.json"

pytestmark = pytest.mark.skipif(
    not JOBS_PATH.exists() or not SKILLS_PATH.exists(),
    reason="corpus or vocabulary not present",
)


@pytest.fixture(scope="module")
def jobs():
    return json.loads(JOBS_PATH.read_text(encoding="utf-8"))["jobs"]


@pytest.fixture(scope="module")
def vocabulary():
    """Canonical skill names, from the _meta/families layout or the flat one."""
    raw = json.loads(SKILLS_PATH.read_text(encoding="utf-8"))
    families = raw.get("families") or {
        k: v for k, v in raw.items() if isinstance(v, dict)
    }
    return {c for fam in families.values() for c in fam}


@pytest.mark.unit
def test_every_job_skill_is_in_the_vocabulary(jobs, vocabulary):
    """
    The invariant the whole corpus design exists to guarantee.

    Coverage should be 100% by construction: the vocabulary was generated
    first, and jobs draw only from it. Anything less means generation did not
    honour the spec.
    """
    unknown = {
        s
        for job in jobs
        for s in (job.get("required_skills") or []) + (job.get("preferred_skills") or [])
        if s not in vocabulary
    }
    assert not unknown, (
        f"{len(unknown)} skill(s) absent from the vocabulary: {sorted(unknown)[:10]}"
    )


@pytest.mark.unit
def test_skill_coverage_is_total(jobs, vocabulary):
    """The measurement that replaces the old corpus's 2.3% / 60.9%."""
    mentions = [
        s for job in jobs for s in (job.get("required_skills") or [])
    ]
    recognised = [s for s in mentions if s in vocabulary]
    coverage = len(recognised) / len(mentions)

    jobs_with_nothing = sum(
        1
        for job in jobs
        if not any(s in vocabulary for s in (job.get("required_skills") or []))
    )

    assert coverage == 1.0, f"skill-mention coverage is {coverage:.1%}, expected 100%"
    assert jobs_with_nothing == 0, (
        f"{jobs_with_nothing} job(s) have no recognisable required skill "
        f"(the old corpus had 60.9%)"
    )


@pytest.mark.unit
def test_no_job_is_silently_discarded_at_load():
    """
    Every record in the file must survive load_jobs().

    api.py used to slice jobs[:4000], dropping 2,146 records (34.9%) with no
    indication anywhere. If a cap is reintroduced, this fails.
    """
    from src.api import load_jobs

    on_disk = len(json.loads(JOBS_PATH.read_text(encoding="utf-8"))["jobs"])
    loaded = len(load_jobs())
    assert loaded == on_disk, (
        f"{on_disk - loaded} job(s) did not survive loading — "
        f"a cap or a validation failure is dropping records"
    )


@pytest.mark.unit
def test_descriptions_do_not_restate_the_skill_list(jobs):
    """
    Guards against circular keyword scoring.

    The old corpus built every description from one template with
    required_skills interpolated, so _score_keywords measured the same skills
    twice. A description naming every one of its required skills is that
    pattern returning.
    """
    echoes = [
        job["job_id"]
        for job in jobs
        if job.get("required_skills")
        and all(s.lower() in job.get("description", "").lower()
                for s in job["required_skills"])
    ]
    assert not echoes, (
        f"{len(echoes)} description(s) name every required skill: {echoes[:5]}"
    )


@pytest.mark.unit
def test_descriptions_are_distinct(jobs):
    """Two jobs sharing description text would score identically against a CV."""
    descriptions = [j.get("description", "") for j in jobs]
    assert len(set(descriptions)) == len(descriptions), (
        f"{len(descriptions) - len(set(descriptions))} duplicate description(s)"
    )
