"""
Evaluation Criteria for ATS ML Models

Comprehensive evaluation metrics and performance criteria for model selection.
Focus on minimizing false negatives (don't miss qualified candidates).
"""

import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    precision_recall_curve, roc_curve
)
from typing import Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EvaluationCriteria:
    """
    Comprehensive evaluation criteria for ATS models.
    
    Primary Metric: Recall (minimize false negatives - don't miss good candidates)
    Target Performance:
        - Recall >= 90% (catch 90%+ of qualified candidates)
        - F1 >= 75% (balanced precision-recall)
        - ROC-AUC >= 0.85 (good discrimination)
        - Precision >= 70% (acceptable false positive rate)
    """
    
    # Performance thresholds
    THRESHOLDS = {
        'recall_min': 0.90,      # Critical: Don't miss qualified candidates
        'f1_min': 0.75,          # Balanced performance
        'roc_auc_min': 0.85,     # Good discrimination ability
        'precision_min': 0.70,   # Acceptable false positive rate
        'accuracy_min': 0.80     # Overall correctness
    }
    
    # Weights for composite score (recall is most important)
    WEIGHTS = {
        'recall': 0.40,
        'f1': 0.25,
        'roc_auc': 0.20,
        'precision': 0.10,
        'accuracy': 0.05
    }
    
    @staticmethod
    def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_pred_proba: np.ndarray = None) -> Dict[str, float]:
        """
        Calculate all evaluation metrics.
        
        Args:
            y_true: Ground truth labels (0=Reject, 1=Hire)
            y_pred: Predicted labels
            y_pred_proba: Predicted probabilities for positive class (optional)
            
        Returns:
            Dictionary of metric names and values
        """
        metrics = {}
        
        # Basic metrics
        metrics['accuracy'] = accuracy_score(y_true, y_pred)
        metrics['precision'] = precision_score(y_true, y_pred, zero_division=0)
        metrics['recall'] = recall_score(y_true, y_pred, zero_division=0)
        metrics['f1'] = f1_score(y_true, y_pred, zero_division=0)
        
        # ROC-AUC (requires probabilities)
        if y_pred_proba is not None:
            try:
                metrics['roc_auc'] = roc_auc_score(y_true, y_pred_proba)
            except ValueError:
                metrics['roc_auc'] = 0.0
        else:
            metrics['roc_auc'] = 0.0
        
        # Confusion matrix components
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        metrics['true_positives'] = int(tp)
        metrics['true_negatives'] = int(tn)
        metrics['false_positives'] = int(fp)
        metrics['false_negatives'] = int(fn)
        
        # Critical business metrics
        metrics['specificity'] = tn / (tn + fp) if (tn + fp) > 0 else 0.0  # True negative rate
        metrics['false_negative_rate'] = fn / (fn + tp) if (fn + tp) > 0 else 0.0  # Miss rate
        metrics['false_positive_rate'] = fp / (fp + tn) if (fp + tn) > 0 else 0.0  # False alarm rate
        
        return metrics
    
    @classmethod
    def calculate_composite_score(cls, metrics: Dict[str, float]) -> float:
        """
        Calculate weighted composite score for model ranking.
        
        Args:
            metrics: Dictionary of metric values
            
        Returns:
            Composite score (0-1, higher is better)
        """
        composite = (
            cls.WEIGHTS['recall'] * metrics.get('recall', 0) +
            cls.WEIGHTS['f1'] * metrics.get('f1', 0) +
            cls.WEIGHTS['roc_auc'] * metrics.get('roc_auc', 0) +
            cls.WEIGHTS['precision'] * metrics.get('precision', 0) +
            cls.WEIGHTS['accuracy'] * metrics.get('accuracy', 0)
        )
        return composite
    
    @classmethod
    def meets_criteria(cls, metrics: Dict[str, float]) -> Tuple[bool, Dict[str, bool]]:
        """
        Check if model meets performance criteria.
        
        Args:
            metrics: Dictionary of metric values
            
        Returns:
            (overall_pass, individual_checks)
        """
        checks = {
            'recall': metrics.get('recall', 0) >= cls.THRESHOLDS['recall_min'],
            'f1': metrics.get('f1', 0) >= cls.THRESHOLDS['f1_min'],
            'roc_auc': metrics.get('roc_auc', 0) >= cls.THRESHOLDS['roc_auc_min'],
            'precision': metrics.get('precision', 0) >= cls.THRESHOLDS['precision_min'],
            'accuracy': metrics.get('accuracy', 0) >= cls.THRESHOLDS['accuracy_min']
        }
        
        # Model must meet recall threshold (critical) and at least 3 out of 4 other criteria
        critical_pass = checks['recall']
        other_passes = sum([checks[k] for k in ['f1', 'roc_auc', 'precision', 'accuracy']])
        
        overall_pass = critical_pass and (other_passes >= 3)
        
        return overall_pass, checks
    
    @staticmethod
    def print_evaluation_report(
        model_name: str, 
        metrics: Dict[str, float], 
        y_true: np.ndarray = None, 
        y_pred: np.ndarray = None
    ):
        """
        Print comprehensive evaluation report.
        
        Args:
            model_name: Name of the model
            metrics: Dictionary of metric values
            y_true: Ground truth labels (optional, for classification report)
            y_pred: Predicted labels (optional, for classification report)
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"EVALUATION REPORT: {model_name}")
        logger.info(f"{'='*60}")
        
        # Primary metrics
        logger.info(f"\n📊 PRIMARY METRICS:")
        logger.info(f"  Recall (Sensitivity):    {metrics.get('recall', 0):.4f} {'✅' if metrics.get('recall', 0) >= EvaluationCriteria.THRESHOLDS['recall_min'] else '❌'}")
        logger.info(f"  F1 Score:                {metrics.get('f1', 0):.4f} {'✅' if metrics.get('f1', 0) >= EvaluationCriteria.THRESHOLDS['f1_min'] else '❌'}")
        logger.info(f"  ROC-AUC:                 {metrics.get('roc_auc', 0):.4f} {'✅' if metrics.get('roc_auc', 0) >= EvaluationCriteria.THRESHOLDS['roc_auc_min'] else '❌'}")
        logger.info(f"  Precision:               {metrics.get('precision', 0):.4f} {'✅' if metrics.get('precision', 0) >= EvaluationCriteria.THRESHOLDS['precision_min'] else '❌'}")
        logger.info(f"  Accuracy:                {metrics.get('accuracy', 0):.4f} {'✅' if metrics.get('accuracy', 0) >= EvaluationCriteria.THRESHOLDS['accuracy_min'] else '❌'}")
        
        # Business metrics
        logger.info(f"\n💼 BUSINESS METRICS:")
        logger.info(f"  False Negative Rate:     {metrics.get('false_negative_rate', 0):.4f} (missed good candidates)")
        logger.info(f"  False Positive Rate:     {metrics.get('false_positive_rate', 0):.4f} (wasted interviews)")
        logger.info(f"  Specificity:             {metrics.get('specificity', 0):.4f} (true rejection rate)")
        
        # Confusion matrix
        if all(k in metrics for k in ['true_positives', 'true_negatives', 'false_positives', 'false_negatives']):
            logger.info(f"\n📋 CONFUSION MATRIX:")
            logger.info(f"  True Positives:  {metrics['true_positives']:4d} (correctly identified qualified)")
            logger.info(f"  True Negatives:  {metrics['true_negatives']:4d} (correctly rejected unqualified)")
            logger.info(f"  False Positives: {metrics['false_positives']:4d} (false alarms)")
            logger.info(f"  False Negatives: {metrics['false_negatives']:4d} (missed opportunities) ⚠️")
        
        # Composite score
        composite = EvaluationCriteria.calculate_composite_score(metrics)
        logger.info(f"\n🎯 COMPOSITE SCORE: {composite:.4f}")
        
        # Criteria check
        passes, checks = EvaluationCriteria.meets_criteria(metrics)
        logger.info(f"\n✅ MEETS CRITERIA: {'YES' if passes else 'NO'}")
        logger.info(f"  Individual checks: {sum(checks.values())}/5 passed")
        
        # Detailed classification report
        if y_true is not None and y_pred is not None:
            logger.info(f"\n📈 DETAILED CLASSIFICATION REPORT:")
            logger.info(f"\n{classification_report(y_true, y_pred, target_names=['Reject', 'Hire'])}")
        
        logger.info(f"{'='*60}\n")
    
    @staticmethod
    def find_optimal_threshold(y_true: np.ndarray, y_pred_proba: np.ndarray, target_recall: float = 0.90) -> Tuple[float, Dict[str, float]]:
        """
        Find optimal classification threshold to achieve target recall.
        
        Args:
            y_true: Ground truth labels
            y_pred_proba: Predicted probabilities for positive class
            target_recall: Desired recall level (default 0.90)
            
        Returns:
            (optimal_threshold, metrics_at_threshold)
        """
        precision, recall, thresholds = precision_recall_curve(y_true, y_pred_proba)
        
        # Find threshold where recall >= target_recall
        valid_indices = np.where(recall >= target_recall)[0]
        
        if len(valid_indices) == 0:
            logger.warning(f"⚠️  Cannot achieve target recall of {target_recall:.2f}")
            optimal_threshold = 0.5
        else:
            # Among valid thresholds, choose one with highest precision
            best_idx = valid_indices[np.argmax(precision[valid_indices])]
            optimal_threshold = thresholds[best_idx] if best_idx < len(thresholds) else 0.5
        
        # Calculate metrics at optimal threshold
        y_pred_optimal = (y_pred_proba >= optimal_threshold).astype(int)
        metrics = EvaluationCriteria.calculate_metrics(y_true, y_pred_optimal, y_pred_proba)
        
        logger.info(f"🎯 Optimal threshold: {optimal_threshold:.4f}")
        logger.info(f"   Recall: {metrics['recall']:.4f}, Precision: {metrics['precision']:.4f}, F1: {metrics['f1']:.4f}")
        
        return optimal_threshold, metrics
