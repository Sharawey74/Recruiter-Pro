"""
Unit Tests for ML Engine - Feature Engineering Module

Tests the FeatureEngineer class for:
- Feature extraction (skills, education, certifications)
- Numerical transformations
- Feature scaling
- Fit-transform pattern
- Edge cases
"""

import pytest
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

from src.ml_engine.feature_engineering import FeatureEngineer


class TestFeatureEngineer:
    """Unit tests for FeatureEngineer"""

    @pytest.fixture
    def sample_data(self):
        """Create sample resume data"""
        return pd.DataFrame(
            {
                "Experience": [5, 3, 8, 0, 10],
                "Salary": [80000, 65000, 120000, 45000, 150000],
                "Skills": [
                    "Python, Machine Learning, AWS",
                    "Java, SQL",
                    "Python, Deep Learning, TensorFlow, AWS, Docker",
                    "React",
                    "Python, Machine Learning, AWS, Kubernetes, PyTorch",
                ],
                "Education": ["Master's", "Bachelor's", "PhD", "High School", "Master's"],
                "Certifications": [
                    "AWS Certified",
                    "None",
                    "Google ML, Deep Learning Specialization",
                    "None",
                    "AWS Certified",
                ],
                "Job Role": [
                    "Data Scientist",
                    "Software Engineer",
                    "ML Engineer",
                    "Frontend Dev",
                    "Data Scientist",
                ],
                "Projects Count": [8, 5, 12, 2, 15],
            }
        )

    @pytest.mark.unit
    @pytest.mark.ml
    def test_initialization(self):
        """Test FeatureEngineer initialization"""
        engineer = FeatureEngineer()
        assert engineer.scaler is not None
        assert engineer.fitted is False

    @pytest.mark.unit
    @pytest.mark.ml
    def test_no_leaking_features_are_engineered(self, sample_data):
        """
        Salary must never become a feature.

        It is a consequence of the hiring decision, not an input to it, so
        training on it lets the model read the target. That is what produced
        the old model's precision 1.000 / ROC-AUC 1.000 on a 150-row test set.

        This test is the guard. The bug was invisible for as long as it was
        because nothing asserted the feature list, only its length.
        """
        engineer = FeatureEngineer()
        _, feature_names = engineer.fit_transform(sample_data)

        leaked = [f for f in feature_names if f.lower() in FeatureEngineer.LEAKING_FEATURES]
        assert not leaked, (
            f"Leaking feature(s) present in the model input: {leaked}. "
            f"See FeatureEngineer.LEAKING_FEATURES."
        )

        # Also catch a renamed variant, e.g. 'salary_normalized' or 'log_salary'.
        salaryish = [f for f in feature_names if "salary" in f.lower()]
        assert not salaryish, f"Salary-derived feature(s) present: {salaryish}"

    @pytest.mark.unit
    @pytest.mark.ml
    def test_trains_without_a_salary_column_at_all(self, sample_data):
        """A dataset with no Salary column must still train, not raise."""
        no_salary = sample_data.drop(columns=["Salary"])
        engineer = FeatureEngineer()
        X, feature_names = engineer.fit_transform(no_salary)
        assert X.shape[0] == len(no_salary)
        assert len(feature_names) > 0

    @pytest.mark.unit
    @pytest.mark.ml
    def test_fit_transform_returns_correct_shape(self, sample_data):
        """Test that fit_transform returns expected shape"""
        engineer = FeatureEngineer()
        X, feature_names = engineer.fit_transform(sample_data)

        assert X.shape[0] == len(sample_data)
        assert X.shape[1] > 0  # Has features
        assert len(feature_names) == X.shape[1]
        assert engineer.fitted is True

    @pytest.mark.unit
    @pytest.mark.ml
    def test_skill_features_extracted(self, sample_data):
        """Test skill binary features are created"""
        engineer = FeatureEngineer()
        X, feature_names = engineer.fit_transform(sample_data)

        # Check skill features exist
        skill_features = [f for f in feature_names if f.startswith("has_")]
        assert len(skill_features) > 0  # Has skill features

        # Check specific skills
        assert "has_python" in feature_names
        assert "has_machine_learning" in feature_names
        assert "has_aws" in feature_names

    @pytest.mark.unit
    @pytest.mark.ml
    def test_skill_count_feature(self, sample_data):
        """Test skill count feature is calculated correctly"""
        engineer = FeatureEngineer()
        X, feature_names = engineer.fit_transform(sample_data)

        skill_count_idx = feature_names.index("skill_count")
        skill_counts = X[:, skill_count_idx]

        # First row has 3 skills (Python, ML, AWS)
        # Values are scaled, so we check relative differences
        assert skill_counts[0] > skill_counts[1]  # 3 skills > 2 skills
        assert skill_counts[4] > skill_counts[0]  # 5 skills > 3 skills

    @pytest.mark.unit
    @pytest.mark.ml
    def test_education_ordinal_encoding(self, sample_data):
        """Test education level ordinal encoding"""
        engineer = FeatureEngineer()
        X, feature_names = engineer.fit_transform(sample_data)

        education_idx = feature_names.index("education_level")
        education_values = X[:, education_idx]

        # Education values should be numeric
        assert isinstance(education_values[0], (int, float, np.number))
        assert isinstance(education_values[1], (int, float, np.number))
        assert isinstance(education_values[2], (int, float, np.number))

    @pytest.mark.unit
    @pytest.mark.ml
    def test_numerical_transformations(self, sample_data):
        """Test numerical feature transformations"""
        engineer = FeatureEngineer()
        X, feature_names = engineer.fit_transform(sample_data)

        # Check transformed features exist
        assert "experience" in feature_names
        assert "experience_squared" in feature_names
        assert "experience_log" in feature_names
        assert "projects_count" in feature_names
        # 'salary' and 'salary_log' were asserted here until the leakage fix.
        # Their absence is now asserted by
        # test_no_leaking_features_are_engineered.

    @pytest.mark.unit
    @pytest.mark.ml
    def test_derived_features(self, sample_data):
        """Test derived ratio features"""
        engineer = FeatureEngineer()
        X, feature_names = engineer.fit_transform(sample_data)

        assert "years_per_project" in feature_names

    @pytest.mark.unit
    @pytest.mark.ml
    def test_transform_uses_fitted_scaler(self, sample_data):
        """Test that transform() uses fitted scaler statistics"""
        engineer = FeatureEngineer()

        # Fit on sample data
        X_train, feature_names = engineer.fit_transform(sample_data)

        # Transform new data (should use train statistics)
        new_data = sample_data.iloc[:2].copy()
        X_new = engineer.transform(new_data)

        assert X_new.shape[0] == 2
        assert X_new.shape[1] == X_train.shape[1]
        # Verify it's using the same scaler (fitted on full sample_data)
        assert engineer.fitted is True

    @pytest.mark.unit
    @pytest.mark.ml
    def test_transform_before_fit_raises_error(self, sample_data):
        """Test that transform() before fit() raises error"""
        engineer = FeatureEngineer()

        with pytest.raises(RuntimeError, match="must be fitted"):
            engineer.transform(sample_data)

    @pytest.mark.unit
    @pytest.mark.ml
    def test_scaling_produces_zero_mean_unit_variance(self, sample_data):
        """Test StandardScaler produces normalized features"""
        engineer = FeatureEngineer()
        X, _ = engineer.fit_transform(sample_data)

        # Check mean ≈ 0 and std ≈ 1 (within tolerance for small sample)
        X = np.asarray(X, dtype=float)
        means = np.mean(X, axis=0)
        stds = np.std(X, axis=0)

        # Most features should be normalized
        assert np.abs(means).mean() < 0.5  # Average mean close to 0
        assert np.abs(stds - 1.0).mean() < 0.5  # Average std close to 1

    @pytest.mark.unit
    @pytest.mark.ml
    def test_handles_zero_experience(self, sample_data):
        """Test handling of zero years experience (log transform)"""
        engineer = FeatureEngineer()
        X, feature_names = engineer.fit_transform(sample_data)

        # Check no NaN or Inf values from log(0)
        X = np.asarray(X, dtype=float)
        assert not np.isnan(X).any()
        assert not np.isinf(X).any()

    @pytest.mark.unit
    @pytest.mark.ml
    def test_handles_zero_projects(self):
        """Test division by zero handling in derived features"""
        data = pd.DataFrame(
            {
                "Experience": [5, 3],
                "Salary": [80000, 65000],
                "Skills": ["Python", "Java"],
                "Education": ["Master's", "Bachelor's"],
                "Certifications": ["AWS", "None"],
                "Job Role": ["Data Scientist", "Engineer"],
                "Projects Count": [0, 5],  # Zero projects
            }
        )

        engineer = FeatureEngineer()
        X, feature_names = engineer.fit_transform(data)

        # Check no division by zero errors
        X = np.asarray(X, dtype=float)
        assert not np.isnan(X).any()
        assert not np.isinf(X).any()

    @pytest.mark.unit
    @pytest.mark.ml
    def test_one_hot_encoding_certifications(self, sample_data):
        """Test one-hot encoding of certifications"""
        engineer = FeatureEngineer()
        X, feature_names = engineer.fit_transform(sample_data)

        # Check certification features exist
        cert_features = [f for f in feature_names if f.startswith("cert_")]
        assert len(cert_features) > 0

        # Check specific certifications
        assert any("AWS" in f for f in cert_features)
        assert any("Google" in f or "ML" in f for f in cert_features)

    @pytest.mark.unit
    @pytest.mark.ml
    def test_one_hot_encoding_job_roles(self, sample_data):
        """Test one-hot encoding of job roles"""
        engineer = FeatureEngineer()
        X, feature_names = engineer.fit_transform(sample_data)

        # Check role features exist
        role_features = [f for f in feature_names if f.startswith("role_")]
        assert len(role_features) > 0

    @pytest.mark.unit
    @pytest.mark.ml
    def test_consistent_feature_names(self, sample_data):
        """Test that feature names are consistent across calls"""
        engineer = FeatureEngineer()

        _, names1 = engineer.fit_transform(sample_data)
        X2 = engineer.transform(sample_data)

        # Feature names should be stored and consistent
        assert engineer.feature_names == names1
        assert len(engineer.feature_names) == X2.shape[1]

    @pytest.mark.unit
    @pytest.mark.ml
    def test_handles_missing_skills(self):
        """Test handling of missing/empty skills"""
        data = pd.DataFrame(
            {
                "Experience": [5],
                "Salary": [80000],
                "Skills": [""],  # Empty skills
                "Education": ["Master's"],
                "Certifications": ["None"],
                "Job Role": ["Data Scientist"],
                "Projects Count": [8],
            }
        )

        engineer = FeatureEngineer()
        X, feature_names = engineer.fit_transform(data)

        # Check no division by zero errors
        X = np.asarray(X, dtype=float)
        assert not np.isnan(X).any()
        assert not np.isinf(X).any()

    @pytest.mark.unit
    @pytest.mark.ml
    def test_case_insensitive_skill_matching(self):
        """Test that skill matching is case-insensitive"""
        data = pd.DataFrame(
            {
                "Experience": [5, 5],
                "Salary": [80000, 80000],
                "Skills": ["PYTHON, machine learning", "python, MACHINE LEARNING"],
                "Education": ["Master's", "Master's"],
                "Certifications": ["None", "None"],
                "Job Role": ["Data Scientist", "Data Scientist"],
                "Projects Count": [8, 8],
            }
        )

        engineer = FeatureEngineer()
        X, feature_names = engineer.fit_transform(data)

        feature_names.index("has_python")
        feature_names.index("has_machine_learning")

        # Both rows should have same values (case-insensitive match)
        np.testing.assert_array_almost_equal(X[0], X[1])

    @pytest.mark.unit
    @pytest.mark.ml
    def test_index_alignment(self, sample_data):
        """Test that index alignment is correct (no mismatch)"""
        engineer = FeatureEngineer()
        X, _ = engineer.fit_transform(sample_data)

        # Should return numpy array with same number of rows
        assert X.shape[0] == len(sample_data)

        # Transform should also maintain alignment
        X2 = engineer.transform(sample_data)
        assert X2.shape[0] == len(sample_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
