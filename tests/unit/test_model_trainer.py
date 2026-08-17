"""
Unit Tests for ML Engine - Model Trainer Module (Simplified)

Tests the ModelTrainer class for:
- Model training
- Hyperparameter tuning
- Model persistence
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

from src.ml_engine.model_trainer import ATSModelTrainer


class TestModelTrainer:
    """Unit tests for ModelTrainer - simplified"""

    @pytest.fixture
    def sample_training_data(self):
        """Sample data for model training"""
        np.random.seed(42)
        X_train = np.random.randn(80, 5)
        y_train = ((X_train[:, 0] + X_train[:, 1]) > 0).astype(int)

        X_test = np.random.randn(20, 5)
        y_test = ((X_test[:, 0] + X_test[:, 1]) > 0).astype(int)

        return X_train, y_train, X_test, y_test

    @pytest.mark.unit
    @pytest.mark.ml
    def test_initialization_default(self):
        """Test ModelTrainer initialization with defaults"""
        trainer = ATSModelTrainer()

        assert trainer.random_state == 42
        assert trainer.models == {}

    @pytest.mark.unit
    @pytest.mark.ml
    def test_initialization_custom(self):
        """Test ModelTrainer initialization with custom parameters"""
        trainer = ATSModelTrainer(random_state=123)

        assert trainer.random_state == 123

    @pytest.mark.unit
    @pytest.mark.ml
    def test_create_logistic_regression_pipeline(self):
        """Test pipeline creation for logistic regression"""
        trainer = ATSModelTrainer()

        pipeline, param_grid = trainer.create_logistic_regression_pipeline()

        assert pipeline is not None
        assert param_grid is not None
        # A list of grids, because l1_ratio is only valid under elasticnet.
        # Every one of them tunes the regularization strength.
        assert all("classifier__C" in grid for grid in param_grid)

    @pytest.mark.unit
    @pytest.mark.ml
    def test_create_random_forest_pipeline(self):
        """Test pipeline creation for random forest"""
        trainer = ATSModelTrainer()

        pipeline, param_grid = trainer.create_random_forest_pipeline()

        assert pipeline is not None
        assert param_grid is not None
        assert "classifier__n_estimators" in param_grid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
