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
    skills=["Python", "JavaScript", "Docker", "SQL", "React", "AWS",
            "PostgreSQL", "Kubernetes", "Git", "Linux"],
    experience_years=5,
    education="Bachelor's",
    raw_text="Senior Software Engineer with 5 years of experience. " * 40,
    extracted_data={"current_title": "Senior Software Engineer"},
)


@pytest.fixture(scope="module")
def jobs():
    payload = json.loads(
        (PROJECT_ROOT / "data/json/jobs.json").read_text(encoding="utf-8")
    )
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
    def test_batch_write_is_one_transaction(self, tmp_path):
        """
        save_match opened a fresh connection, committed and closed per row --
        8.57 ms each, 6.86 s for 800 rows. save_matches_batch does the same
        work in one transaction, measured at 0.055 ms/row.
        """
        from src.storage.database import Database
        from src.storage.models import DecisionType, MatchDecision, MatchResult, ScoreBreakdown

        db = Database(db_path=str(tmp_path / "perf.db"))
        breakdown = ScoreBreakdown(
            skill_score=0.5, title_score=0.5, experience_score=0.5,
            education_score=0.5, keyword_score=0.5, rule_based_score=0.5,
            hybrid_score=0.5,
        )
        rows = [
            MatchResult(
                match_id=f"perf-{i}", cv_id="perf", job_id=f"JOB-{i}",
                candidate_name="Perf", job_title="Engineer",
                score_breakdown=breakdown,
                decision=MatchDecision(
                    decision=DecisionType.REVIEW, confidence=0.5, reason="perf"
                ),
                final_score=0.5, processing_time_ms=1.0,
            )
            for i in range(200)
        ]

        start = time.perf_counter()
        written = db.save_matches_batch(rows)
        elapsed = time.perf_counter() - start

        assert written == 200
        per_row_ms = elapsed / 200 * 1000
        assert per_row_ms < 2.0, (
            f"{per_row_ms:.2f}ms per row -- batch persistence may have "
            f"regressed to one connection per row"
        )
