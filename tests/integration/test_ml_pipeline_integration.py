"""
Integration Tests for ML Pipeline

Tests the end-to-end ML workflow:
- Data loading → Feature engineering → Training → Evaluation
- SMOTE integration
- Model persistence and reloading
- Full pipeline execution
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import joblib

from src.ml_engine.data_loader import ATSDataLoader
from src.ml_engine.feature_engineering import FeatureEngineer
from src.ml_engine.model_trainer import ATSModelTrainer
from src.ml_engine.evaluation_criteria import EvaluationCriteria
from src.ml_engine.ats_predictor import ATSPredictor


class TestMLPipelineIntegration:
    """Integration tests for complete ML pipeline"""
    
    @pytest.fixture
    def sample_dataset_file(self, tmp_path):
        """
        A temporary dataset with a fixed seed and a fixed class balance.

        This used to call np.random.* with no seed, so every run got a
        different label distribution. test_pipeline_with_smote failed whenever
        the draw came out balanced enough that SMOTE's sampling_strategy=0.7
        would have required removing minority samples -- which looked like an
        intermittent SMOTE bug and was in fact an unseeded fixture. Seeded and
        with a fixed 30/70 split now, so the outcome is the same on every run.
        """
        rng = np.random.default_rng(42)
        data = pd.DataFrame({
            'Skills': [
                'Python, Machine Learning, SQL',
                'Java, Spring Boot, AWS',
                'JavaScript, React, Node.js',
                'Python, Django, PostgreSQL',
                'C++, CUDA, Deep Learning',
                'Java, Microservices, Docker',
                'Python, Data Science, TensorFlow',
                'Go, Kubernetes, Cloud',
                'Python, FastAPI, MongoDB',
                'Java, Spring, Hibernate',
            ] * 10,  # 100 samples
            'Experience': rng.integers(1, 15, 100),
            'Education': rng.choice(['Bachelor', 'Master', 'PhD'], 100),
            'Certifications': rng.choice(['AWS', 'GCP', 'Azure', 'None'], 100),
            'Projects Count': rng.integers(1, 30, 100),
            'Job Role': rng.choice(['Engineer', 'Senior Engineer', 'Lead'], 100),
            'Salary': rng.integers(60000, 200000, 100),
            # 30/70, fixed. Deliberately imbalanced, because that is what
            # SMOTE exists to correct and what real ATS data looks like -- and
            # because the pipeline pins sampling_strategy=0.7, which raises on
            # any dataset already more balanced than that. A 50/50 fixture
            # fails deterministically; an unseeded draw failed intermittently.
            'Recruiter Decision': ['Hire'] * 30 + ['Reject'] * 70
        })
        
        filepath = tmp_path / "test_dataset.csv"
        data.to_csv(filepath, index=False)
        return filepath
    
    @pytest.mark.integration
    @pytest.mark.ml
    def test_full_pipeline_load_to_train(self, sample_dataset_file):
        """Test complete pipeline from data loading to model training"""
        # Step 1: Load data
        loader = ATSDataLoader(sample_dataset_file)
        loader.load_data()
        train_df, val_df, test_df = loader.split_data(test_size=0.2, val_size=0.1)
        
        X_train, y_train = loader.get_X_y(train_df)
        X_test, y_test = loader.get_X_y(test_df)
        
        # Step 2: Engineer features
        engineer = FeatureEngineer()
        X_train_transformed, feature_names = engineer.fit_transform(X_train)
        X_test_transformed = engineer.transform(X_test)
        
        # Step 3: Train model
        from sklearn.linear_model import LogisticRegression
        model = LogisticRegression(random_state=42, max_iter=1000)
        model.fit(X_train_transformed, y_train)
        
        # Verify pipeline completed successfully
        assert model is not None
        score = model.score(X_test_transformed, y_test)
        assert score >= 0.0
        assert X_train_transformed.shape[1] > 0  # Has features
    
    @pytest.mark.integration
    @pytest.mark.ml
    def test_pipeline_with_smote(self, sample_dataset_file):
        """Test pipeline with SMOTE integration"""
        # Load data
        loader = ATSDataLoader(sample_dataset_file)
        loader.load_data()
        train_df, val_df, test_df = loader.split_data(test_size=0.2, val_size=0.1)
        
        X_train, y_train = loader.get_X_y(train_df)
        X_test, y_test = loader.get_X_y(test_df)
        
        # Engineer features
        engineer = FeatureEngineer()
        X_train_transformed, _ = engineer.fit_transform(X_train)
        X_test_transformed = engineer.transform(X_test)
        
        # Train with SMOTE-enabled pipeline
        trainer = ATSModelTrainer()
        pipeline, _ = trainer.create_logistic_regression_pipeline()
        pipeline.fit(X_train_transformed, y_train)
        
        # SMOTE should have been applied
        assert pipeline is not None
        score = pipeline.score(X_test_transformed, y_test)
        assert score >= 0.0  # Should handle imbalance better
    
    @pytest.mark.integration
    @pytest.mark.ml
    def test_pipeline_model_persistence(self, sample_dataset_file, tmp_path):
        """Test saving and loading trained pipeline"""
        # Train a model
        loader = ATSDataLoader(sample_dataset_file)
        loader.load_data()
        train_df, val_df, test_df = loader.split_data(test_size=0.2, val_size=0.1)
        
        X_train, y_train = loader.get_X_y(train_df)
        X_test, y_test = loader.get_X_y(test_df)
        
        engineer = FeatureEngineer()
        X_train_transformed, _ = engineer.fit_transform(X_train)
        X_test_transformed = engineer.transform(X_test)
        
        from sklearn.linear_model import LogisticRegression
        model = LogisticRegression(random_state=42, max_iter=1000)
        model.fit(X_train_transformed, y_train)
        
        # Save model and engineer
        model_path = tmp_path / "model.joblib"
        engineer_path = tmp_path / "engineer.joblib"
        
        joblib.dump(model, model_path)
        joblib.dump(engineer, engineer_path)
        
        # Load and verify
        loaded_model = joblib.load(model_path)
        loaded_engineer = joblib.load(engineer_path)
        
        # Transform new data and predict
        X_new_transformed = loaded_engineer.transform(X_test)
        predictions = loaded_model.predict(X_new_transformed)
        
        assert len(predictions) == len(X_test)
        assert all(p in [0, 1] for p in predictions)
    
    @pytest.mark.integration
    @pytest.mark.ml
    def test_pipeline_with_predictor(self, sample_dataset_file, tmp_path):
        """Test complete pipeline with ATSPredictor"""
        # Train model
        loader = ATSDataLoader(sample_dataset_file)
        loader.load_data()
        train_df, val_df, test_df = loader.split_data(test_size=0.2, val_size=0.1)
        
        X_train, y_train = loader.get_X_y(train_df)
        X_test, y_test = loader.get_X_y(test_df)
        
        engineer = FeatureEngineer()
        X_train_transformed, _ = engineer.fit_transform(X_train)
        X_test_transformed = engineer.transform(X_test)
        
        from sklearn.linear_model import LogisticRegression
        model = LogisticRegression(random_state=42, max_iter=1000)
        model.fit(X_train_transformed, y_train)
        
        # Save model and engineer
        model_path = tmp_path / "ats_model.joblib"
        engineer_path = tmp_path / "feature_engineer.joblib"
        
        joblib.dump(model, model_path)
        joblib.dump(engineer, engineer_path)
        
        # Use ATSPredictor
        predictor = ATSPredictor(model_dir=str(tmp_path))
        predictor.load_model()
        result = predictor.predict(X_test.iloc[0:1])
        
        assert 'decision' in result
        assert 'probability' in result
        assert result['decision'] in ['Hire', 'Reject']
        assert 0.0 <= result['probability'] <= 1.0
    
    @pytest.mark.integration
    @pytest.mark.ml
    def test_pipeline_feature_consistency(self, sample_dataset_file):
        """Test that features are consistent across train/test"""
        loader = ATSDataLoader(sample_dataset_file)
        loader.load_data()
        train_df, val_df, test_df = loader.split_data(test_size=0.2, val_size=0.1)
        
        X_train, y_train = loader.get_X_y(train_df)
        X_test, y_test = loader.get_X_y(test_df)
        
        engineer = FeatureEngineer()
        X_train_transformed, feature_names = engineer.fit_transform(X_train)
        X_test_transformed = engineer.transform(X_test)
        
        # Feature counts should match
        assert X_train_transformed.shape[1] == X_test_transformed.shape[1]
        
        # Feature names should match
        assert len(feature_names) == X_train_transformed.shape[1]
    
    @pytest.mark.integration
    @pytest.mark.ml
    def test_pipeline_multiple_models_comparison(self, sample_dataset_file):
        """Test training and comparing multiple models"""
        loader = ATSDataLoader(sample_dataset_file)
        loader.load_data()
        train_df, val_df, test_df = loader.split_data(test_size=0.2, val_size=0.1)
        
        X_train, y_train = loader.get_X_y(train_df)
        X_test, y_test = loader.get_X_y(test_df)
        
        engineer = FeatureEngineer()
        X_train_transformed, _ = engineer.fit_transform(X_train)
        X_test_transformed = engineer.transform(X_test)
        
        # Train multiple models
        from sklearn.linear_model import LogisticRegression
        from sklearn.ensemble import RandomForestClassifier
        
        models = {
            'logistic': LogisticRegression(random_state=42, max_iter=1000),
            'rf': RandomForestClassifier(n_estimators=10, random_state=42)
        }
        
        scores = {}
        for name, model in models.items():
            model.fit(X_train_transformed, y_train)
            scores[name] = model.score(X_test_transformed, y_test)
        
        # Verify comparison
        assert len(scores) == 2
        assert 'logistic' in scores
        assert 'rf' in scores
    
    @pytest.mark.integration
    @pytest.mark.ml
    @pytest.mark.slow
    def test_pipeline_hyperparameter_tuning(self, sample_dataset_file):
        """Test pipeline with hyperparameter tuning"""
        loader = ATSDataLoader(sample_dataset_file)
        loader.load_data()
        train_df, val_df, test_df = loader.split_data(test_size=0.2, val_size=0.1)
        
        X_train, y_train = loader.get_X_y(train_df)
        
        engineer = FeatureEngineer()
        X_train_transformed, _ = engineer.fit_transform(X_train)
        
        # Hyperparameter tuning
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import GridSearchCV
        
        model = LogisticRegression(random_state=42, max_iter=1000)
        param_grid = {
            'C': [0.1, 1.0, 10.0],
            'penalty': ['l2']
        }
        
        grid_search = GridSearchCV(model, param_grid, cv=3, scoring='recall')
        grid_search.fit(X_train_transformed, y_train)
        
        assert grid_search.best_estimator_ is not None
        assert 'C' in grid_search.best_params_
        assert grid_search.best_score_ > 0.0
    
    @pytest.mark.integration
    @pytest.mark.ml
    def test_pipeline_evaluation_criteria(self, sample_dataset_file):
        """Test pipeline with evaluation criteria checking"""
        loader = ATSDataLoader(sample_dataset_file)
        loader.load_data()
        train_df, val_df, test_df = loader.split_data(test_size=0.2, val_size=0.1)
        
        X_train, y_train = loader.get_X_y(train_df)
        X_test, y_test = loader.get_X_y(test_df)
        
        engineer = FeatureEngineer()
        X_train_transformed, _ = engineer.fit_transform(X_train)
        X_test_transformed = engineer.transform(X_test)
        
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import recall_score, f1_score
        model = LogisticRegression(random_state=42, max_iter=1000)
        model.fit(X_train_transformed, y_train)
        
        # Get predictions
        y_pred = model.predict(X_test_transformed)
        
        # Calculate metrics
        metrics = {
            'recall': recall_score(y_test, y_pred),
            'f1': f1_score(y_test, y_pred)
        }
        
        # Check if meets criteria
        meets_criteria, checks = EvaluationCriteria.meets_criteria(metrics)
        
        # Should have criteria checks
        assert isinstance(meets_criteria, bool)
        assert isinstance(checks, dict)
        assert 'recall' in checks
        assert 'f1' in checks
    
    @pytest.mark.integration
    @pytest.mark.ml
    def test_pipeline_batch_prediction(self, sample_dataset_file, tmp_path):
        """Test batch prediction workflow"""
        # Train model
        loader = ATSDataLoader(sample_dataset_file)
        loader.load_data()
        train_df, val_df, test_df = loader.split_data(test_size=0.2, val_size=0.1)
        
        X_train, y_train = loader.get_X_y(train_df)
        X_test, y_test = loader.get_X_y(test_df)
        
        engineer = FeatureEngineer()
        X_train_transformed, _ = engineer.fit_transform(X_train)
        
        from sklearn.linear_model import LogisticRegression
        model = LogisticRegression(random_state=42, max_iter=1000)
        model.fit(X_train_transformed, y_train)
        
        # Save and load
        model_path = tmp_path / "ats_model.joblib"
        engineer_path = tmp_path / "feature_engineer.joblib"
        
        joblib.dump(model, model_path)
        joblib.dump(engineer, engineer_path)
        
        # Batch prediction
        predictor = ATSPredictor(model_dir=str(tmp_path))
        predictor.load_model()
        result = predictor.predict(X_test.iloc[0:1])
        
        assert 'decision' in result
        assert 'probability' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

