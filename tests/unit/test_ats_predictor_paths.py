"""
ATSPredictor's loading, feature importance and failure paths.

The predictor is the only thing standing between a joblib file on disk and 40%
of every hybrid score. Its interesting behaviour is almost entirely about what
happens when the file is absent, partial, or not what was expected -- and the
answer has to be "return False and let the caller fall back", never an
exception at import time.

`get_feature_importance` is covered because it is the one place that reads the
model's internals, so it breaks whenever the model type changes -- a
coefficient-based classifier and a tree-based one expose importance
differently.
"""
import json

import numpy as np
import pandas as pd
import pytest

from src.ml_engine.ats_predictor import ATSPredictor


class TestLoading:
    @pytest.mark.unit
    @pytest.mark.ml
    def test_a_missing_directory_returns_false(self, tmp_path):
        """False, not an exception: Agent 3 turns this into rule-based scoring."""
        assert ATSPredictor(model_dir=str(tmp_path / "absent")).load_model() is False

    @pytest.mark.unit
    @pytest.mark.ml
    def test_a_missing_feature_engineer_returns_false(self, tmp_path):
        """
        Half a model is not a model. The classifier alone cannot transform a
        CV into features, so loading must fail rather than half-succeed.
        """
        import joblib
        from sklearn.linear_model import LogisticRegression

        joblib.dump(LogisticRegression(), tmp_path / "ats_model.joblib")
        assert ATSPredictor(model_dir=str(tmp_path)).load_model() is False

    @pytest.mark.unit
    @pytest.mark.ml
    def test_a_corrupt_artifact_returns_false(self, tmp_path):
        (tmp_path / "ats_model.joblib").write_bytes(b"not a joblib file")
        assert ATSPredictor(model_dir=str(tmp_path)).load_model() is False

    @pytest.mark.unit
    @pytest.mark.ml
    def test_predicting_without_loading_raises(self, tmp_path):
        """
        This one *should* raise. Silently returning a score from no model is
        the failure mode worth preventing -- a caller would blend it at 40%.
        """
        predictor = ATSPredictor(model_dir=str(tmp_path))
        with pytest.raises(RuntimeError, match="Model not loaded"):
            predictor.predict({"Skills": "Python"})

    @pytest.mark.unit
    @pytest.mark.ml
    def test_batch_predicting_without_loading_raises(self, tmp_path):
        predictor = ATSPredictor(model_dir=str(tmp_path))
        with pytest.raises(RuntimeError, match="Model not loaded"):
            predictor.predict_batch([{"Skills": "Python"}])

    @pytest.mark.unit
    @pytest.mark.ml
    def test_importance_without_loading_raises(self, tmp_path):
        predictor = ATSPredictor(model_dir=str(tmp_path))
        with pytest.raises(RuntimeError, match="Model not loaded"):
            predictor.get_feature_importance()


@pytest.fixture(scope="module")
def loaded():
    """The real shipped model, or skip. CI has one; a bare clone may not."""
    predictor = ATSPredictor(model_dir="models/production")
    if not predictor.load_model():
        pytest.skip("no production model available")
    return predictor


class TestTheShippedModel:
    @pytest.mark.unit
    @pytest.mark.ml
    def test_metadata_is_read(self, loaded):
        info = loaded.get_model_info()
        assert info.get("model_name")

    @pytest.mark.unit
    @pytest.mark.ml
    def test_the_optimal_threshold_is_applied_not_the_default(self, loaded):
        """
        The metadata carries a tuned threshold. Defaulting to 0.5 silently
        would change every Hire/Reject decision the model makes.
        """
        assert loaded.optimal_threshold != 0.5

    @pytest.mark.unit
    @pytest.mark.ml
    def test_feature_importance_is_ranked_and_bounded(self, loaded):
        importance = loaded.get_feature_importance(top_n=5)
        assert len(importance) <= 5
        values = list(importance.values())
        assert values == sorted(values, reverse=True), "not ranked"

    @pytest.mark.unit
    @pytest.mark.ml
    def test_feature_importance_names_real_features(self, loaded):
        for name in loaded.get_feature_importance(top_n=3):
            assert isinstance(name, str) and name

    @pytest.mark.unit
    @pytest.mark.ml
    def test_a_dataframe_input_is_accepted(self, loaded):
        """Both dict and DataFrame are documented inputs."""
        row = pd.DataFrame([{
            "Skills": "Python, Docker", "Experience": 5, "Education": "Bachelor",
            "Certifications": "AWS", "Job Role": "Engineer",
            "Projects Count": 3, "Salary": 90000,
        }])
        assert 0 <= loaded.predict(row)["ml_score"] <= 100

    @pytest.mark.unit
    @pytest.mark.ml
    def test_an_unsupported_input_type_is_rejected(self, loaded):
        with pytest.raises(ValueError, match="dict or DataFrame"):
            loaded.predict("a resume as a string")

    @pytest.mark.unit
    @pytest.mark.ml
    def test_an_empty_batch_is_empty_not_an_error(self, loaded):
        assert loaded.predict_batch([]) == []

    @pytest.mark.unit
    @pytest.mark.ml
    def test_the_result_carries_every_documented_field(self, loaded):
        result = loaded.predict({
            "Skills": "Python", "Experience": 5, "Education": "Bachelor",
            "Certifications": "None", "Job Role": "Engineer",
            "Projects Count": 1, "Salary": 80000,
        })
        for field in ("decision", "ml_score", "probability", "confidence",
                      "risk_level", "threshold_used", "model_name"):
            assert field in result

    @pytest.mark.unit
    @pytest.mark.ml
    @pytest.mark.parametrize("proba,expected", [
        (0.95, "Low Risk"), (0.70, "Medium Risk"), (0.20, "High Risk"),
    ])
    def test_risk_bands(self, proba, expected):
        assert ATSPredictor._build_result(proba, 0.5, "m")["risk_level"] == expected

    @pytest.mark.unit
    @pytest.mark.ml
    def test_confidence_is_distance_from_the_coin_flip(self):
        """0.5 is maximally uncertain; both extremes are maximally confident."""
        assert ATSPredictor._build_result(0.5, 0.5, "m")["confidence"] == pytest.approx(0.5)
        assert ATSPredictor._build_result(0.99, 0.5, "m")["confidence"] == pytest.approx(0.99)
        assert ATSPredictor._build_result(0.01, 0.5, "m")["confidence"] == pytest.approx(0.99)

    @pytest.mark.unit
    @pytest.mark.ml
    def test_the_threshold_decides_the_label(self):
        assert ATSPredictor._build_result(0.30, 0.229, "m")["decision"] == "Hire"
        assert ATSPredictor._build_result(0.10, 0.229, "m")["decision"] == "Reject"
