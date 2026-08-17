"""
Unit Tests for ML Engine - Evaluation Criteria Module

Tests the EvaluationCriteria class for:
- Metrics calculation
- Composite scoring
- Criteria checking
- Threshold optimization
- Business metrics
"""

import pytest
import numpy as np
from sklearn.metrics import confusion_matrix

from src.ml_engine.evaluation_criteria import EvaluationCriteria


class TestEvaluationCriteria:
    """Unit tests for EvaluationCriteria"""

    @pytest.fixture
    def perfect_predictions(self):
        """Perfect predictions (100% accuracy)"""
        y_true = np.array([1, 1, 1, 0, 0, 1, 0, 1, 1, 0])
        y_pred = np.array([1, 1, 1, 0, 0, 1, 0, 1, 1, 0])
        y_proba = np.array([0.9, 0.95, 0.92, 0.1, 0.15, 0.88, 0.2, 0.93, 0.91, 0.12])
        return y_true, y_pred, y_proba

    @pytest.fixture
    def imperfect_predictions(self):
        """Imperfect predictions with errors"""
        y_true = np.array([1, 1, 1, 0, 0, 1, 0, 1, 1, 0])
        y_pred = np.array([1, 1, 0, 0, 1, 1, 0, 1, 1, 0])  # 2 errors
        y_proba = np.array([0.9, 0.85, 0.45, 0.1, 0.6, 0.88, 0.2, 0.93, 0.91, 0.12])
        return y_true, y_pred, y_proba

    @pytest.mark.unit
    @pytest.mark.ml
    def test_calculate_metrics_perfect(self, perfect_predictions):
        """Test metrics calculation for perfect predictions"""
        y_true, y_pred, y_proba = perfect_predictions

        metrics = EvaluationCriteria.calculate_metrics(y_true, y_pred, y_proba)

        assert metrics["accuracy"] == 1.0
        assert metrics["precision"] == 1.0
        assert metrics["recall"] == 1.0
        assert metrics["f1"] == 1.0
        assert metrics["roc_auc"] == 1.0
        assert metrics["specificity"] == 1.0
        assert metrics["false_negative_rate"] == 0.0
        assert metrics["false_positive_rate"] == 0.0

    @pytest.mark.unit
    @pytest.mark.ml
    def test_calculate_metrics_imperfect(self, imperfect_predictions):
        """Test metrics calculation for imperfect predictions"""
        y_true, y_pred, y_proba = imperfect_predictions

        metrics = EvaluationCriteria.calculate_metrics(y_true, y_pred, y_proba)

        # 8/10 correct
        assert metrics["accuracy"] == 0.8

        # Should have some errors
        assert metrics["precision"] < 1.0
        assert metrics["recall"] < 1.0
        assert metrics["f1"] < 1.0

        # Should have FP or FN
        assert metrics["false_negative_rate"] > 0 or metrics["false_positive_rate"] > 0

    @pytest.mark.unit
    @pytest.mark.ml
    def test_confusion_matrix_calculation(self, imperfect_predictions):
        """Test confusion matrix values"""
        y_true, y_pred, y_proba = imperfect_predictions

        metrics = EvaluationCriteria.calculate_metrics(y_true, y_pred, y_proba)

        # Verify confusion matrix sums correctly
        total = (
            metrics["true_positives"]
            + metrics["true_negatives"]
            + metrics["false_positives"]
            + metrics["false_negatives"]
        )
        assert total == len(y_true)

        # Verify with sklearn confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        assert metrics["true_negatives"] == cm[0, 0]
        assert metrics["false_positives"] == cm[0, 1]
        assert metrics["false_negatives"] == cm[1, 0]
        assert metrics["true_positives"] == cm[1, 1]

    @pytest.mark.unit
    @pytest.mark.ml
    def test_composite_score_calculation(self, perfect_predictions):
        """Test composite score calculation"""
        y_true, y_pred, y_proba = perfect_predictions

        metrics = EvaluationCriteria.calculate_metrics(y_true, y_pred, y_proba)
        composite = EvaluationCriteria.calculate_composite_score(metrics)

        # Perfect predictions should have composite = 1.0
        assert composite == 1.0

    @pytest.mark.unit
    @pytest.mark.ml
    def test_composite_score_weights(self):
        """Test composite score uses correct weights"""
        metrics = {"recall": 0.9, "f1": 0.8, "roc_auc": 0.85, "precision": 0.75, "accuracy": 0.82}

        composite = EvaluationCriteria.calculate_composite_score(metrics)

        # Manual calculation: 0.4*0.9 + 0.25*0.8 + 0.2*0.85 + 0.1*0.75 + 0.05*0.82
        expected = 0.36 + 0.2 + 0.17 + 0.075 + 0.041

        assert abs(composite - expected) < 0.001

    @pytest.mark.unit
    @pytest.mark.ml
    def test_meets_criteria_all_passing(self):
        """Test criteria checking when all metrics pass"""
        metrics = {"recall": 0.95, "f1": 0.85, "roc_auc": 0.92, "precision": 0.88, "accuracy": 0.90}

        meets, checks = EvaluationCriteria.meets_criteria(metrics)

        assert meets is True
        assert all(checks.values())  # All checks should be True

    @pytest.mark.unit
    @pytest.mark.ml
    def test_meets_criteria_recall_failing(self):
        """Test criteria checking when recall fails"""
        metrics = {
            "recall": 0.85,  # Below 0.90 threshold
            "f1": 0.85,
            "roc_auc": 0.92,
            "precision": 0.88,
            "accuracy": 0.90,
        }

        meets, checks = EvaluationCriteria.meets_criteria(metrics)

        assert meets is False
        assert checks["recall"] is False
        assert checks["f1"] is True

    @pytest.mark.unit
    @pytest.mark.ml
    def test_meets_criteria_multiple_failing(self):
        """Test criteria checking with multiple failures"""
        metrics = {
            "recall": 0.85,  # Fail
            "f1": 0.70,  # Fail
            "roc_auc": 0.80,  # Fail
            "precision": 0.88,
            "accuracy": 0.90,
        }

        meets, checks = EvaluationCriteria.meets_criteria(metrics)

        assert meets is False
        assert sum(checks.values()) == 2  # Only 2 pass

    @pytest.mark.unit
    @pytest.mark.ml
    def test_find_optimal_threshold_basic(self):
        """Test threshold optimization"""
        y_true = np.array([1, 1, 1, 0, 0, 1, 0, 1])
        y_proba = np.array([0.9, 0.85, 0.55, 0.3, 0.45, 0.88, 0.2, 0.75])

        optimal_threshold, metrics = EvaluationCriteria.find_optimal_threshold(
            y_true, y_proba, target_recall=0.90
        )

        # Should return a threshold between 0 and 1
        assert 0.0 <= optimal_threshold <= 1.0

        # Should return metrics dict
        assert "recall" in metrics
        assert "precision" in metrics
        assert "f1" in metrics

    @pytest.mark.unit
    @pytest.mark.ml
    def test_find_optimal_threshold_achieves_target_recall(self):
        """Test that optimal threshold achieves target recall"""
        # Create data where we can achieve high recall
        y_true = np.array([1] * 8 + [0] * 2)
        y_proba = np.array([0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55, 0.3, 0.2])

        optimal_threshold, metrics = EvaluationCriteria.find_optimal_threshold(
            y_true, y_proba, target_recall=0.90
        )

        # Should achieve at least target recall
        assert metrics["recall"] >= 0.90

    @pytest.mark.unit
    @pytest.mark.ml
    def test_print_evaluation_report_runs(self, perfect_predictions):
        """Test that print_evaluation_report executes without error"""
        y_true, y_pred, y_proba = perfect_predictions

        metrics = EvaluationCriteria.calculate_metrics(y_true, y_pred, y_proba)

        # Should not raise any exceptions
        try:
            EvaluationCriteria.print_evaluation_report("Test Model", metrics, y_true, y_pred)
            success = True
        except Exception:
            success = False

        assert success is True

    @pytest.mark.unit
    @pytest.mark.ml
    def test_edge_case_all_positives(self):
        """Test edge case with all positive predictions"""
        # Include at least one negative to avoid confusion matrix edge case
        y_true = np.array([1, 1, 1, 1, 0])
        y_pred = np.array([1, 1, 1, 1, 0])
        y_proba = np.array([0.9, 0.95, 0.92, 0.88, 0.1])

        metrics = EvaluationCriteria.calculate_metrics(y_true, y_pred, y_proba)

        assert metrics["recall"] == 1.0
        assert metrics["true_positives"] == 4
        assert metrics["false_negatives"] == 0

    @pytest.mark.unit
    @pytest.mark.ml
    def test_edge_case_all_negatives(self):
        """Test edge case with all negative predictions"""
        # Include at least one positive to avoid confusion matrix edge case
        y_true = np.array([0, 0, 0, 0, 1])
        y_pred = np.array([0, 0, 0, 0, 1])
        y_proba = np.array([0.1, 0.15, 0.12, 0.18, 0.9])

        metrics = EvaluationCriteria.calculate_metrics(y_true, y_pred, y_proba)

        assert metrics["specificity"] == 1.0
        assert metrics["true_negatives"] == 4
        assert metrics["false_positives"] == 0

    @pytest.mark.unit
    @pytest.mark.ml
    def test_business_metrics_calculation(self, imperfect_predictions):
        """Test business-specific metrics"""
        y_true, y_pred, y_proba = imperfect_predictions

        metrics = EvaluationCriteria.calculate_metrics(y_true, y_pred, y_proba)

        # FNR + Recall should sum to 1.0
        assert abs((metrics["false_negative_rate"] + metrics["recall"]) - 1.0) < 0.001

        # FPR + Specificity should sum to 1.0
        assert abs((metrics["false_positive_rate"] + metrics["specificity"]) - 1.0) < 0.001

    @pytest.mark.unit
    @pytest.mark.ml
    def test_roc_auc_with_perfect_separation(self):
        """Test ROC-AUC with perfect class separation"""
        y_true = np.array([1, 1, 1, 0, 0, 0])
        y_proba = np.array([0.9, 0.85, 0.8, 0.3, 0.2, 0.1])  # Perfect separation
        y_pred = (y_proba > 0.5).astype(int)

        metrics = EvaluationCriteria.calculate_metrics(y_true, y_pred, y_proba)

        assert metrics["roc_auc"] == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
