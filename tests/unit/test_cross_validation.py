"""
Unit Tests for ML Engine - Cross-Validation Module

Tests the CrossValidator class for:
- K-fold cross-validation strategies
- Learning curves
- Validation curves
- Overfitting detection
- Stratified splitting
"""

import pytest
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

from src.ml_engine.cross_validation import CrossValidationEvaluator


class TestCrossValidator:
    """Unit tests for CrossValidator"""
    
    @pytest.fixture
    def sample_data(self):
        """Sample data for cross-validation testing"""
        np.random.seed(42)
        X = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100),
            'feature3': np.random.randn(100),
            'feature4': np.random.rand(100),
            'feature5': np.random.rand(100)
        })
        # Create target with some pattern
        y = ((X['feature1'] + X['feature2']) > 0).astype(int)
        return X, y
    
    @pytest.fixture
    def simple_model(self):
        """Simple model for testing"""
        return LogisticRegression(random_state=42, max_iter=1000)
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_initialization_default(self):
        """Test CrossValidator initialization with defaults"""
        cv = CrossValidationEvaluator()
        
        assert cv.n_folds == 5
        assert cv.random_state == 42
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_initialization_custom(self):
        """Test CrossValidator initialization with custom parameters"""
        cv = CrossValidationEvaluator(n_folds=10, random_state=123)
        
        assert cv.n_folds == 10
        assert cv.random_state == 123
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_cross_validate_basic(self, sample_data, simple_model):
        """Test basic cross-validation execution"""
        X, y = sample_data
        cv = CrossValidationEvaluator(n_folds=3)
        
        scores = cv.evaluate_cv_performance(simple_model, X.values, y.values)
        
        # Should return dict with scores
        assert isinstance(scores, dict)
        assert 'mean' in scores
        assert 'std' in scores
        assert 'scores' in scores
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_cross_validate_correct_splits(self, sample_data, simple_model):
        """Test that cross-validation uses correct number of splits"""
        X, y = sample_data
        cv = CrossValidationEvaluator(n_folds=5)
        
        scores = cv.evaluate_cv_performance(simple_model, X.values, y.values)
        
        assert len(scores['scores']) == 5
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_cross_validate_stratified(self, sample_data, simple_model):
        """Test that cross-validation maintains class distribution"""
        X, y = sample_data
        cv = CrossValidationEvaluator(n_folds=3)
        
        # Should not raise error even with imbalanced classes
        scores = cv.evaluate_cv_performance(simple_model, X.values, y.values)
        
        assert scores is not None
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_cross_validate_with_scoring(self, sample_data, simple_model):
        """Test cross-validation with custom scoring"""
        X, y = sample_data
        cv = CrossValidationEvaluator(n_folds=3)
        
        scores = cv.evaluate_cv_performance(
            simple_model, X.values, y.values, 
            scoring='f1'
        )
        
        # Should have requested metric stats
        assert 'mean' in scores
        assert 'std' in scores
        assert 'scores' in scores
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_learning_curve_basic(self, sample_data, simple_model, tmp_path):
        """Test learning curve generation"""
        X, y = sample_data
        cv = CrossValidationEvaluator(n_folds=3, output_dir=str(tmp_path))

        result = cv.plot_learning_curves(
            simple_model, X.values, y.values, model_name='TestModel'
        )

        # Returns a dict, not a tuple. These tests unpacked three values and
        # had never passed against this implementation.
        train_sizes = result['train_sizes']
        assert len(train_sizes) > 0
        assert result['train_scores'].shape[0] == len(train_sizes)
        assert result['val_scores'].shape[0] == len(train_sizes)
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_learning_curve_train_sizes(self, sample_data, simple_model, tmp_path):
        """Test learning curve with custom train sizes"""
        X, y = sample_data
        cv = CrossValidationEvaluator(n_folds=3)
        
        custom_sizes = np.linspace(0.2, 1.0, 5)
        result = cv.plot_learning_curves(
            simple_model, X.values, y.values, train_sizes=custom_sizes, model_name='TestModel'
        )

        assert len(result['train_sizes']) == 5
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_learning_curve_increasing_performance(self, sample_data, simple_model, tmp_path):
        """Test that learning curve shows improving performance"""
        X, y = sample_data
        cv = CrossValidationEvaluator(n_folds=3, output_dir=str(tmp_path))

        result = cv.plot_learning_curves(
            simple_model, X.values, y.values, model_name='TestModel'
        )

        # Mean validation score should generally increase
        val_means = result['val_scores'].mean(axis=1)
        # Last score should be >= first score (with some tolerance)
        assert val_means[-1] >= val_means[0] - 0.1
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_validation_curve_basic(self, sample_data, simple_model, tmp_path):
        """Test validation curve generation"""
        X, y = sample_data
        cv = CrossValidationEvaluator(n_folds=3, output_dir=str(tmp_path))

        param_range = [0.001, 0.01, 0.1, 1.0, 10.0]
        result = cv.plot_validation_curve(
            simple_model, X.values, y.values,
            param_name='C',
            param_range=param_range,
            model_name='TestModel',
        )

        assert result['train_scores'].shape[0] == len(param_range)
        assert result['val_scores'].shape[0] == len(param_range)
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_validation_curve_scores_vary(self, sample_data, simple_model, tmp_path):
        """Test that validation curve shows varying performance"""
        X, y = sample_data
        cv = CrossValidationEvaluator(n_folds=3, output_dir=str(tmp_path))

        param_range = [0.001, 0.01, 0.1, 1.0, 10.0]
        result = cv.plot_validation_curve(
            simple_model, X.values, y.values,
            param_name='C',
            param_range=param_range,
            model_name='TestModel'
        )

        # Scores should vary across parameter range
        val_std = result['val_scores'].mean(axis=1).std()
        assert val_std > 0  # Some variation expected
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_get_cv_splits(self, sample_data):
        """Test getting cross-validation splits"""
        X, y = sample_data
        cv = CrossValidationEvaluator(n_folds=3)
        
        splits = list(cv.cv_splitter.split(X, y))
        
        assert len(splits) == 3
        for train_idx, val_idx in splits:
            assert len(train_idx) + len(val_idx) == len(X)
            assert len(set(train_idx) & set(val_idx)) == 0  # No overlap
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_stratification_maintains_distribution(self, sample_data):
        """Test that stratified splits maintain class distribution"""
        X, y = sample_data
        cv = CrossValidationEvaluator(n_folds=3)
        
        overall_pos_rate = y.mean()
        
        splits = list(cv.cv_splitter.split(X, y))
        for train_idx, val_idx in splits:
            train_pos_rate = y.iloc[train_idx].mean()
            val_pos_rate = y.iloc[val_idx].mean()
            
            # Both should be close to overall rate (within 10%)
            assert abs(train_pos_rate - overall_pos_rate) < 0.1
            assert abs(val_pos_rate - overall_pos_rate) < 0.1
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_reproducibility_with_random_state(self, sample_data, simple_model):
        """Test that random_state ensures reproducibility"""
        X, y = sample_data
        
        cv1 = CrossValidationEvaluator(n_folds=3, random_state=42)
        scores1 = cv1.evaluate_cv_performance(simple_model, X.values, y.values)
        
        cv2 = CrossValidationEvaluator(n_folds=3, random_state=42)
        scores2 = cv2.evaluate_cv_performance(simple_model, X.values, y.values)
        
        # Same random state should give same results
        np.testing.assert_array_equal(
            scores1['scores'], 
            scores2['scores']
        )
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_edge_case_small_dataset(self, simple_model):
        """Test cross-validation with very small dataset"""
        X = pd.DataFrame({'feature': [1, 2, 3, 4, 5]})
        y = pd.Series([0, 0, 1, 1, 1])
        
        cv = CrossValidationEvaluator(n_folds=2)  # Only 2 splits for small data
        
        scores = cv.evaluate_cv_performance(simple_model, X.values, y.values)
        
        assert len(scores['scores']) == 2
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_edge_case_imbalanced_classes(self, simple_model):
        """Test cross-validation with highly imbalanced classes"""
        X = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100)
        })
        y = pd.Series([0] * 90 + [1] * 10)  # 90:10 imbalance
        
        cv = CrossValidationEvaluator(n_folds=3)
        
        scores = cv.evaluate_cv_performance(simple_model, X.values, y.values)
        
        # Should complete without error
        assert scores is not None
        assert len(scores['scores']) == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

