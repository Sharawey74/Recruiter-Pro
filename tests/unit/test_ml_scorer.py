"""
MLScorer — the boundary between scoring and a trained artifact.

Two things matter here and neither involves the model being right.

First, that a missing, broken or slow model degrades to rule-based scoring
rather than failing a request. The deployment target may have no model at all.

Second, that `score_batch` returns exactly one entry per job. Agent 3 zips its
result against the job list with `strict=True`, so a provider returning a
short list is a loud failure rather than a corpus silently scored in part --
but only if the contract holds at this boundary.
"""
import pytest

from src.agents.scoring.ml_scorer import MLScorer
from src.core.config import get_config
from src.storage.models import CVProfile, JobPosting

CV = CVProfile(
    cv_id="ml", file_name="ml.txt", name="Jane",
    skills=["Python", "Docker"], experience_years=5, education="Bachelor's",
    extracted_data={"certifications": "AWS", "projects_count": 4},
)

JOBS = [
    JobPosting(
        job_id=f"JOB-{i}", title=f"Engineer {i}", company_name="Acme",
        location_city="Cairo", location_country="Egypt", remote_type="on-site",
        employment_type="full-time", seniority_level="mid",
        required_skills=["Python"], preferred_skills=[],
        min_experience_years=2, max_experience_years=6,
        education_level="Bachelor", description="A job. " * 30,
        category="engineering", posted_date="2026-01-15",
    )
    for i in range(3)
]


class FakePredictor:
    """Stands in for ATSPredictor. Nothing here loads a file."""

    def __init__(self, behaviour="ok"):
        self.behaviour = behaviour
        self.seen = None

    def predict(self, cv_data, use_optimal_threshold=True):
        self.seen = cv_data
        if isinstance(self.behaviour, Exception):
            raise self.behaviour
        return {"ml_score": 82, "probability": 0.82}

    def predict_batch(self, rows, use_optimal_threshold=True):
        self.seen = rows
        if isinstance(self.behaviour, Exception):
            raise self.behaviour
        if self.behaviour == "short":
            return [{"ml_score": 82}]
        return [{"ml_score": 82, "probability": 0.82} for _ in rows]


class TestNoModel:
    @pytest.mark.unit
    def test_an_inert_scorer_is_not_enabled(self):
        assert MLScorer(None).enabled is False

    @pytest.mark.unit
    def test_single_scoring_returns_none(self):
        assert MLScorer(None).score(CV, JOBS[0]) is None

    @pytest.mark.unit
    def test_batch_returns_one_none_per_job(self):
        """The length contract holds even with nothing to score against."""
        assert MLScorer(None).score_batch(CV, JOBS) == [None, None, None]

    @pytest.mark.unit
    def test_an_empty_job_list_is_an_empty_result(self):
        assert MLScorer(None).score_batch(CV, []) == []

    @pytest.mark.unit
    def test_load_never_raises_when_the_model_is_absent(self, tmp_path):
        """
        A missing model must fall back to rule-based scoring, not take the
        process down at import time.
        """
        scorer = MLScorer.load(model_dir=str(tmp_path / "nothing-here"))
        assert scorer.enabled is False


class TestScoring:
    @pytest.mark.unit
    def test_converts_the_percentage_to_a_ratio(self):
        """The model reports 0-100; callers blend a 0-1 value."""
        assert MLScorer(FakePredictor()).score(CV, JOBS[0]) == pytest.approx(0.82)

    @pytest.mark.unit
    def test_batch_scores_every_job(self):
        out = MLScorer(FakePredictor()).score_batch(CV, JOBS)
        assert out == [pytest.approx(0.82)] * 3

    @pytest.mark.unit
    def test_the_features_carry_the_job_title(self):
        """
        Job Role is the only feature that varies across jobs for a fixed CV --
        which is also why the model contributes so little ranking signal.
        """
        predictor = FakePredictor()
        MLScorer(predictor).score_batch(CV, JOBS)
        assert [row["Job Role"] for row in predictor.seen] == [j.title for j in JOBS]

    @pytest.mark.unit
    def test_the_features_carry_the_candidate(self):
        predictor = FakePredictor()
        MLScorer(predictor).score(CV, JOBS[0])
        assert predictor.seen["Experience"] == 5
        assert "Python" in predictor.seen["Skills"]
        assert predictor.seen["Certifications"] == "AWS"


class TestFailureIsNotAnOutage:
    @pytest.mark.unit
    def test_a_raising_predictor_yields_none(self):
        scorer = MLScorer(FakePredictor(RuntimeError("model exploded")))
        assert scorer.score(CV, JOBS[0]) is None

    @pytest.mark.unit
    def test_a_raising_batch_yields_one_none_per_job(self):
        scorer = MLScorer(FakePredictor(RuntimeError("model exploded")))
        assert scorer.score_batch(CV, JOBS) == [None, None, None]

    @pytest.mark.unit
    def test_a_short_batch_is_rejected_wholesale(self):
        """
        A predictor returning fewer results than jobs cannot be aligned by
        position without silently attributing one job's score to another.
        Refusing the batch is the only safe reading.
        """
        scorer = MLScorer(FakePredictor("short"))
        assert scorer.score_batch(CV, JOBS) == [None, None, None]

    @pytest.mark.unit
    def test_an_empty_result_is_none(self):
        assert MLScorer._to_score(None) is None
        assert MLScorer._to_score({}) is None

    @pytest.mark.unit
    def test_a_score_already_in_ratio_form_is_left_alone(self):
        """Guards against dividing by 100 twice if the model's scale changes."""
        assert MLScorer._to_score({"ml_score": 0.9}) == pytest.approx(0.9)
