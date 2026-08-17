"""
Performance guards on the paths Phase 3 optimised.

Replaces tests/system/test_load_testing.py, which was 418 lines of tests that
passed while measuring nothing. Every request in it went to /api/v1/score,
/api/v1/batch or /api/v1/health -- endpoints this repository has never served
-- and each measurement was collected inside `if response.status_code == 200:`.
Nothing was ever 200, so the timing lists stayed empty, the guarded
`if response_times:` never entered, and the assertions never ran. Ten tests
reported green, contributed to the suite's pass count, and could not fail.

These measure the real path instead, and they assert unconditionally: an empty
measurement is a failure, not a silent pass.

Thresholds are set well above the measured figures. The point is to catch a
regression of the kind Phase 3 removed -- a per-job model call, or a database
write per row -- not to police normal variance on a loaded machine.
"""

import json
import time
from pathlib import Path

import pytest

from src.agents.agent3_scorer import HybridScoringAgent
from src.storage.models import CVProfile, JobPosting

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CV = CVProfile(
    cv_id="perf",
    file_name="perf.txt",
    name="Perf Candidate",
    skills=[
        "Python",
        "JavaScript",
        "Docker",
        "SQL",
        "React",
        "AWS",
        "PostgreSQL",
        "Kubernetes",
        "Git",
        "Linux",
    ],
    experience_years=5,
    education="Bachelor's",
    raw_text="Senior Software Engineer with 5 years of experience. " * 40,
    extracted_data={"current_title": "Senior Software Engineer"},
)


@pytest.fixture(scope="module")
def jobs():
    payload = json.loads((PROJECT_ROOT / "data/json/jobs.json").read_text(encoding="utf-8"))
    return [JobPosting(**j) for j in payload["jobs"]]


@pytest.fixture(scope="module")
def agent():
    return HybridScoringAgent()


@pytest.mark.system
@pytest.mark.performance
class TestScoringPerformance:
    def test_rule_scoring_the_whole_corpus_is_fast(self, agent, jobs):
        """
        Measured at 0.30 s for 800 jobs. The threshold is 5 s: this is a guard
        against an accidental O(n^2) or a per-job file read, not a stopwatch.
        """
        start = time.perf_counter()
        breakdowns = agent.score_matches(CV, jobs, include_ml=False)
        elapsed = time.perf_counter() - start

        assert len(breakdowns) == len(jobs)
        assert elapsed < 5.0, f"scoring {len(jobs)} jobs took {elapsed:.2f}s"

    def test_batched_ml_beats_per_job_calls(self, agent, jobs):
        """
        The Phase 3 headline: one model call for the corpus instead of one per
        job, measured at 8.13 s -> 0.033 s. Skipped when no model is loaded,
        because then both paths are the same code.
        """
        if not agent.ml_scorer.enabled:
            pytest.skip("no ML model loaded; nothing to batch")

        sample = jobs[:60]

        start = time.perf_counter()
        [agent.score_match(CV, job, include_ml=True) for job in sample]
        per_job = time.perf_counter() - start

        start = time.perf_counter()
        agent.score_matches(CV, sample, include_ml=True)
        batched = time.perf_counter() - start

        assert batched < per_job, (
            f"batched scoring ({batched:.3f}s) is not faster than per-job "
            f"({per_job:.3f}s) -- the batch path may have regressed to a loop"
        )

    def test_batching_does_not_change_the_result(self, agent, jobs):
        """A faster path that scores differently is not an optimisation."""
        sample = jobs[:40]
        loop = [agent.score_match(CV, j, include_ml=True) for j in sample]
        batch = agent.score_matches(CV, sample, include_ml=True)

        for a, b in zip(loop, batch, strict=True):
            assert a.hybrid_score == b.hybrid_score
            assert a.matched_skills == b.matched_skills


@pytest.mark.system
@pytest.mark.performance
class TestPersistencePerformance:
    @staticmethod
    def _rows(count: int, prefix: str):
        from src.storage.models import (
            DecisionType,
            MatchDecision,
            MatchResult,
            ScoreBreakdown,
        )

        breakdown = ScoreBreakdown(
            skill_score=0.5,
            title_score=0.5,
            experience_score=0.5,
            education_score=0.5,
            keyword_score=0.5,
            rule_based_score=0.5,
            hybrid_score=0.5,
        )
        return [
            MatchResult(
                match_id=f"{prefix}-{i}",
                cv_id="perf",
                job_id=f"JOB-{i}",
                candidate_name="Perf",
                job_title="Engineer",
                score_breakdown=breakdown,
                decision=MatchDecision(decision=DecisionType.REVIEW, confidence=0.5, reason="perf"),
                final_score=0.5,
                processing_time_ms=1.0,
            )
            for i in range(count)
        ]

    def test_batch_write_opens_one_connection(self, tmp_path, monkeypatch):
        """
        The actual invariant: one connection for the whole batch, not one per
        row.

        This is asserted by counting `sqlite3.connect` calls rather than by
        timing, because the count is the property that matters and a count
        cannot be slow. `save_match` opens a fresh connection, commits and
        closes for every row -- 200 rows meant 200 connections and 200 commits.
        """
        import sqlite3

        from src.storage.database import Database

        db = Database(db_path=str(tmp_path / "perf.db"))
        db.initialize_schema()

        opened = 0
        real_connect = sqlite3.connect

        def counting_connect(*args, **kwargs):
            nonlocal opened
            opened += 1
            return real_connect(*args, **kwargs)

        monkeypatch.setattr(sqlite3, "connect", counting_connect)
        written = db.save_matches_batch(self._rows(200, "batch"))

        assert written == 200
        assert opened == 1, (
            f"{opened} connections opened for 200 rows -- batch persistence has "
            f"regressed towards one connection per row"
        )

    def test_batch_write_is_cheaper_per_row_than_saving_one_at_a_time(self, tmp_path):
        """
        The speed-up, measured as a ratio rather than against a fixed
        millisecond budget.

        The previous version of this test asserted `per_row_ms < 2.0` on a cold
        database, and failed in CI at 3.63 ms/row. Nothing had regressed. Two
        things were wrong with the measurement:

        1. **Schema creation was inside the timer.** `save_matches_batch`
           initialises the schema on first use, so the first call pays for
           CREATE TABLE and its indexes. Locally that is 15 ms of a 24 ms
           sample -- 63% of the number -- and on a slow CI disk it dominates
           entirely. It is a one-off cost being divided by the row count, so
           the reported "per row" figure fell as rows rose.
        2. **A fixed millisecond threshold measures the machine.** A shared CI
           runner is slower than a laptop by a factor nobody controls, so an
           absolute budget either fails on slow hardware or is set so loose it
           would not catch the regression it exists to catch.

        Comparing the two paths in the same process on the same disk removes
        both problems: slow hardware slows the baseline equally, and the ratio
        is what the optimisation actually claims.
        """
        from src.storage.database import Database

        db = Database(db_path=str(tmp_path / "perf.db"))
        db.initialize_schema()  # one-off; not what this measures

        # The shape this replaced: a connection, a commit and a close per row.
        # Twenty-five is enough to establish the per-row cost without paying
        # for two hundred round trips on a slow runner.
        individual = self._rows(25, "one-at-a-time")
        start = time.perf_counter()
        for row in individual:
            db.save_match(row)
        per_row_individual = (time.perf_counter() - start) / len(individual)

        batched = self._rows(200, "batched")
        start = time.perf_counter()
        written = db.save_matches_batch(batched)
        per_row_batched = (time.perf_counter() - start) / len(batched)

        assert written == 200

        # Measured at ~78x locally. Five is a floor that a genuine regression
        # to per-row connections cannot pass, with room for a noisy runner.
        ratio = per_row_individual / per_row_batched
        assert ratio > 5, (
            f"batched writes are only {ratio:.1f}x cheaper per row than "
            f"individual ones ({per_row_batched * 1000:.3f} ms vs "
            f"{per_row_individual * 1000:.3f} ms) -- the batch path may have "
            f"regressed to one connection per row"
        )


# A CV the size of a real one.
#
# The fixture above carries 10 skills. A genuine résumé put through Agent 2
# extracts far more -- the owner's own PDF yields 57 -- and scoring cost is
# roughly linear in that count. So every figure produced from `CV` describes a
# résumé about a fifth the density of the ones this product is for, and a guard
# calibrated on it cannot see a regression that only appears on real input.
DENSE_SKILLS = [
    "Python",
    "JavaScript",
    "Docker",
    "SQL",
    "React",
    "AWS",
    "PostgreSQL",
    "Kubernetes",
    "Git",
    "Linux",
    "FastAPI",
    "Django",
    "Redis",
    "Terraform",
    "Kafka",
    "Celery",
    "pytest",
    "Bash",
    "TypeScript",
    "Node.js",
    "GraphQL",
    "REST APIs",
    "Microservices",
    "System Design",
    "CI/CD",
    "Spring Boot",
    "Java",
    "Go",
    "C#",
    "Angular",
    "Vue.js",
    "MongoDB",
    "MySQL",
    "Elasticsearch",
    "RabbitMQ",
    "Jenkins",
    "Ansible",
    "Prometheus",
    "Grafana",
    "Nginx",
    "Machine Learning",
    "TensorFlow",
    "PyTorch",
    "Pandas",
    "NumPy",
    "scikit-learn",
    "Spark",
    "Hadoop",
    "Airflow",
    "dbt",
    "Snowflake",
    "Tableau",
    "Power BI",
    "Excel",
    "Figma",
    "Jira",
    "Confluence",
]

DENSE_CV = CVProfile(
    cv_id="perf-dense",
    file_name="dense.txt",
    name="Dense Candidate",
    skills=DENSE_SKILLS,
    experience_years=7,
    education="Bachelor's",
    raw_text="Senior Software Engineer with 7 years of experience. " * 60,
    extracted_data={"current_title": "Senior Software Engineer"},
)


@pytest.mark.system
@pytest.mark.performance
class TestRealisticCorpusScoring:
    """
    What a real résumé costs, measured rather than quoted.

    The README stated 0.74 s for scoring one CV against all 800 roles, and
    presented it as the whole user-visible operation. Three things were wrong
    with that. It came from the 10-skill fixture; it ran with `include_ml=False`
    while the deployed app runs with the model loaded; and it excluded parsing,
    extraction, persistence and serialisation. A dense CV measures around 3.5 s
    for the same call, and a real upload through `POST /match` around 4.7 s.

    These tests exist so the honest figure lives in the suite. A number in a
    README that nothing measures drifts from the code that produces it, which
    is the same failure this project removed from its ML metrics and from its
    provider annotations.
    """

    def test_the_dense_fixture_is_actually_dense(self):
        """
        Guards the guard.

        The defect was a threshold calibrated on an unrepresentative fixture,
        so the fixture's own realism has to be asserted -- otherwise a future
        edit can trim it back and every budget below silently becomes generous
        again.
        """
        assert len(DENSE_SKILLS) >= 50, (
            f"the dense fixture has shrunk to {len(DENSE_SKILLS)} skills; "
            "it exists to be the size of a real résumé"
        )

    def test_scoring_cost_grows_with_cv_density(self, agent, jobs):
        """
        The relationship the single headline number hid.

        Not a threshold -- a direction. If a dense CV ever stops costing more
        than a sparse one, either the skill matcher stopped reading skills or
        something is being cached that should not be.
        """
        sample = jobs[:400]

        start = time.perf_counter()
        agent.score_matches(CV, sample, include_ml=False)
        sparse = time.perf_counter() - start

        start = time.perf_counter()
        agent.score_matches(DENSE_CV, sample, include_ml=False)
        dense = time.perf_counter() - start

        assert dense > sparse, (
            f"a {len(DENSE_SKILLS)}-skill CV ({dense:.2f}s) did not cost more "
            f"than a {len(CV.skills)}-skill one ({sparse:.2f}s) -- scoring may "
            "no longer be reading the full skill set"
        )

    def test_a_realistic_cv_scores_the_corpus_within_budget(self, agent, jobs):
        """
        Measured at ~3.5 s for 800 roles with the model off, ~4.3 s with it on.

        The budget is 12 s: generous against a loaded CI runner, and still far
        below what a per-job model call or a per-job file read would produce.
        The point is that the number is now taken against a realistic input, so
        it can be quoted without a footnote.
        """
        start = time.perf_counter()
        breakdowns = agent.score_matches(DENSE_CV, jobs, include_ml=True)
        elapsed = time.perf_counter() - start

        assert len(breakdowns) == len(jobs)
        assert elapsed < 12.0, (
            f"scoring {len(jobs)} roles for a {len(DENSE_SKILLS)}-skill CV took " f"{elapsed:.2f}s"
        )
