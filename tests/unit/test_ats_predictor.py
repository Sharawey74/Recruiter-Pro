"""
Unit Tests for ML Engine - ATS Predictor Module (Simplified)

Tests the ATSPredictor class for:
- Model initialization
- Model loading
- Basic predictions
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import joblib
from sklearn.linear_model import LogisticRegression

from src.ml_engine.ats_predictor import ATSPredictor
from src.ml_engine.feature_engineering import FeatureEngineer


class TestATSPredictor:
    """Unit tests for ATSPredictor - simplified"""

    @pytest.fixture
    def sample_resume_data(self):
        """Sample resume data for predictions"""
        return pd.DataFrame(
            {
                "Skills": ["Python, Machine Learning, SQL", "Java, Spring, AWS"],
                "Experience": [5, 3],
                "Education": ["Master", "Bachelor"],
                "Certifications": ["AWS Certified", "None"],
                "Projects Count": [10, 5],
                "Job Role": ["Senior Engineer", "Engineer"],
                "Salary": [120000, 80000],
            }
        )

    @pytest.fixture
    def trained_model_and_engineer(self, tmp_path):
        """Create and save a trained model and feature engineer"""
        # Create sample training data
        np.random.seed(42)
        X_train = pd.DataFrame(
            {
                "Skills": ["Python, SQL"] * 50,
                "Experience": np.random.randint(1, 10, 50),
                "Education": np.random.choice(["Bachelor", "Master", "PhD"], 50),
                "Certifications": np.random.choice(["AWS", "GCP", "None"], 50),
                "Projects Count": np.random.randint(1, 20, 50),
                "Job Role": np.random.choice(["Engineer", "Senior"], 50),
                "Salary": np.random.randint(60000, 150000, 50),
            }
        )
        y_train = np.random.randint(0, 2, 50)

        # Train feature engineer
        feature_engineer = FeatureEngineer()
        X_transformed, _ = feature_engineer.fit_transform(X_train)

        # Train model
        model = LogisticRegression(random_state=42, max_iter=1000)
        model.fit(X_transformed, y_train)

        # Save both
        model_path = tmp_path / "ats_model.joblib"
        engineer_path = tmp_path / "feature_engineer.joblib"

        joblib.dump(model, model_path)
        joblib.dump(feature_engineer, engineer_path)

        return str(tmp_path), feature_engineer

    @pytest.mark.unit
    @pytest.mark.ml
    def test_initialization(self):
        """Test ATSPredictor initialization"""
        predictor = ATSPredictor(model_dir="models/production")

        assert predictor.model_dir == "models/production"
        assert predictor.model is None
        assert predictor.feature_engineer is None

    @pytest.mark.unit
    @pytest.mark.ml
    def test_load_model(self, trained_model_and_engineer):
        """Test model loading"""
        model_dir, _ = trained_model_and_engineer
        predictor = ATSPredictor(model_dir=model_dir)

        success = predictor.load_model()

        assert success is True
        assert predictor.model is not None
        assert predictor.feature_engineer is not None

    @pytest.mark.unit
    @pytest.mark.ml
    def test_predict_single_resume(self, trained_model_and_engineer, sample_resume_data):
        """Test single resume prediction"""
        model_dir, _ = trained_model_and_engineer
        predictor = ATSPredictor(model_dir=model_dir)
        predictor.load_model()

        single_resume = sample_resume_data.iloc[0:1]
        result = predictor.predict(single_resume)

        assert isinstance(result, dict)
        assert "decision" in result
        assert "probability" in result
        assert result["decision"] in ["Hire", "Reject"]
        assert 0.0 <= result["probability"] <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
