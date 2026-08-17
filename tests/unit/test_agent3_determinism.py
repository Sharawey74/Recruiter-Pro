"""
Unit tests for Agent 3 (HybridScoringAgent) — determinism and score structure.

ADR-1 requires that the same inputs produce a byte-identical ScoreBreakdown:
Agent 3 may not call an LLM, so there is no source of legitimate variation. The
scorer nonetheless built its skill lists with list(set(...)), which reorders
between processes, so matched_skills and extra_skills differed across restarts
and extra_skills[:10] returned a different ten. These tests pin that shut.

They also pin the weighted-sum identity: the five reported components must
reconstruct rule_based_score. Before title_score was surfaced they could not,
because a sixth of the score was computed and discarded.
"""

import json

import pytest

from src.agents.agent3_scorer import HybridScoringAgent
from src.core.config import PROJECT_ROOT, get_config
from src.storage.models import CVProfile, JobPosting


@pytest.fixture(scope="module")
def agent():
    return HybridScoringAgent()


@pytest.fixture(scope="module")
def jobs():
    payload = json.loads((PROJECT_ROOT / "data/json/jobs.json").read_text(encoding="utf-8"))
    return [JobPosting(**j) for j in payload["jobs"][:40]]


@pytest.fixture(scope="module")
def cv():
    return CVProfile(
        cv_id="determinism-probe",
        file_name="determinism-probe.pdf",
        name="Probe",
        email="probe@example.com",
        skills=["Python", "Docker", "PostgreSQL", "AWS", "Communication", "Machine Learning"],
        experience_years=6,
        education="Bachelor's",
        extracted_data={"current_title": "Senior Software Engineer"},
    )


class TestDeterminism:
    @pytest.mark.unit
    def test_repeated_scoring_is_identical(self, agent, cv, jobs):
        """ADR-1: same inputs, byte-identical breakdown."""
        for job in jobs[:10]:
            a = agent.score_match(cv, job, include_ml=False)
            b = agent.score_match(cv, job, include_ml=False)
            assert a.model_dump() == b.model_dump(), f"{job.job_id} scored differently on re-run"

    @pytest.mark.unit
    def test_skill_lists_are_sorted(self, agent, cv, jobs):
        """
        Unsorted lists came from list(set(...)) and reordered per process, which
        also made extra_skills[:10] return a different ten each restart.
        """
        for job in jobs[:10]:
            b = agent.score_match(cv, job, include_ml=False)
            assert b.matched_skills == sorted(b.matched_skills)
            assert b.extra_skills == sorted(b.extra_skills)

    @pytest.mark.unit
    def test_a_fresh_agent_scores_identically(self, cv, jobs):
        """Agent construction must not carry state that changes results."""
        one, two = HybridScoringAgent(), HybridScoringAgent()
        for job in jobs[:5]:
            assert (
                one.score_match(cv, job, include_ml=False).model_dump()
                == two.score_match(cv, job, include_ml=False).model_dump()
            )

    @pytest.mark.unit
    def test_scoring_does_not_mutate_its_inputs(self, agent, cv, jobs):
        before_cv = cv.model_dump()
        before_job = jobs[0].model_dump()
        agent.score_match(cv, jobs[0], include_ml=False)
        assert cv.model_dump() == before_cv
        assert jobs[0].model_dump() == before_job


class TestScoreStructure:
    @pytest.mark.unit
    def test_components_reconstruct_the_rule_based_score(self, agent, cv, jobs):
        """
        The identity that was unverifiable until title_score was surfaced.
        Weights come from config, so this also fails if the scorer stops
        reading them.
        """
        w = get_config().scoring
        for job in jobs:
            b = agent.score_match(cv, job, include_ml=False)
            expected = (
                b.skill_score * w.skill_weight
                + b.title_score * w.title_weight
                + b.experience_score * w.experience_weight
                + b.education_score * w.education_weight
                + b.keyword_score * w.keyword_weight
            )
            assert b.rule_based_score == pytest.approx(expected, abs=1e-9), job.job_id

    @pytest.mark.unit
    def test_all_components_are_within_range(self, agent, cv, jobs):
        for job in jobs:
            b = agent.score_match(cv, job, include_ml=False)
            for field in (
                "skill_score",
                "title_score",
                "experience_score",
                "education_score",
                "keyword_score",
                "rule_based_score",
            ):
                assert 0.0 <= getattr(b, field) <= 1.0, f"{job.job_id}.{field}"

    @pytest.mark.unit
    def test_matched_and_missing_do_not_overlap(self, agent, cv, jobs):
        """A skill cannot be both present and absent."""
        for job in jobs:
            b = agent.score_match(cv, job, include_ml=False)
            assert not (set(b.matched_skills) & set(b.missing_skills)), job.job_id

    @pytest.mark.unit
    def test_a_cv_with_no_skills_scores_no_skill_match(self, agent, jobs):
        empty = CVProfile(
            cv_id="empty",
            file_name="empty.pdf",
            skills=[],
            experience_years=0,
            education="High School",
            extracted_data={},
        )
        b = agent.score_match(empty, jobs[0], include_ml=False)
        assert b.skill_score == 0.0
        assert b.matched_skills == []
