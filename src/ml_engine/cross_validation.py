"""
Cross-Validation Strategies for ATS Model Training

Implements stratified K-fold CV, learning curves, and validation curves
to detect underfitting/overfitting.
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import (
    StratifiedKFold, cross_val_score, learning_curve, validation_curve
)
from sklearn.base import BaseEstimator
from typing import Dict, List, Tuple
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sns.set_style("whitegrid")


class CrossValidationEvaluator:
    """
    Comprehensive cross-validation evaluation for ATS models.
    
    Features:
    - Stratified K-fold CV
    - Learning curves (detect underfitting/overfitting)
    - Validation curves (hyperparameter effects)
    - Train-validation gap analysis
    """
    
    def __init__(self, n_folds: int = 5, random_state: int = 42, output_dir: str = "models/experiments"):
        """
        Initialize CV evaluator.
        
        Args:
            n_folds: Number of folds for cross-validation (default 5)
            random_state: Random seed for reproducibility
            output_dir: Directory to save plots and results
        """
        self.n_folds = n_folds
        self.random_state = random_state
        self.output_dir = output_dir
        self.cv_splitter = StratifiedKFold(
            n_splits=n_folds, 
            shuffle=True, 
            random_state=random_state
        )
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
    
    def evaluate_cv_performance(
        self, 
        estimator: BaseEstimator, 
        X: np.ndarray, 
        y: np.ndarray,
        scoring: str = 'recall'
    ) -> Dict[str, float]:
        """
        Evaluate model using stratified K-fold cross-validation.
        
        Args:
            estimator: Sklearn estimator (unfitted)
            X: Feature matrix
            y: Target labels
            scoring: Metric to evaluate (default 'recall')
            
        Returns:
            CV statistics dictionary
        """
        logger.info(f"Running {self.n_folds}-fold stratified CV with scoring={scoring}...")
        
        scores = cross_val_score(
            estimator, X, y, 
            cv=self.cv_splitter, 
            scoring=scoring,
            n_jobs=-1
        )
        
        cv_stats = {
            'mean': scores.mean(),
            'std': scores.std(),
            'min': scores.min(),
            'max': scores.max(),
            'scores': scores.tolist()
        }
        
        logger.info(f"  CV {scoring}: {cv_stats['mean']:.4f} (+/- {cv_stats['std']:.4f})")
        logger.info(f"  Range: [{cv_stats['min']:.4f}, {cv_stats['max']:.4f}]")
        
        # Check for high variance (overfitting indicator)
        if cv_stats['std'] > 0.1:
            logger.warning(f"⚠️  High variance detected (std={cv_stats['std']:.4f}). Possible overfitting!")
        
        return cv_stats
    
    def plot_learning_curves(
        self, 
        estimator: BaseEstimator, 
        X: np.ndarray, 
        y: np.ndarray,
        model_name: str,
        scoring: str = 'recall',
        train_sizes: np.ndarray = None
    ) -> Dict[str, np.ndarray]:
        """
        Generate learning curves to detect underfitting/overfitting.
        
        Args:
            estimator: Sklearn estimator (unfitted)
            X: Feature matrix
            y: Target labels
            model_name: Name for plot title
            scoring: Metric to evaluate
            train_sizes: Training set sizes to evaluate
            
        Returns:
            Dictionary with train and validation scores
        """
        logger.info(f"Generating learning curves for {model_name}...")
        
        if train_sizes is None:
            train_sizes = np.linspace(0.1, 1.0, 10)
        
        train_sizes_abs, train_scores, val_scores = learning_curve(
            estimator, X, y,
            train_sizes=train_sizes,
            cv=self.cv_splitter,
            scoring=scoring,
            n_jobs=-1,
            random_state=self.random_state
        )
        
        # Calculate means and stds
        train_mean = train_scores.mean(axis=1)
        train_std = train_scores.std(axis=1)
        val_mean = val_scores.mean(axis=1)
        val_std = val_scores.std(axis=1)
        
        # Plot
        plt.figure(figsize=(10, 6))
        plt.plot(train_sizes_abs, train_mean, 'o-', color='blue', label='Training score')
        plt.fill_between(train_sizes_abs, train_mean - train_std, train_mean + train_std, alpha=0.1, color='blue')
        plt.plot(train_sizes_abs, val_mean, 'o-', color='red', label='Validation score')
        plt.fill_between(train_sizes_abs, val_mean - val_std, val_mean + val_std, alpha=0.1, color='red')
        
        plt.xlabel('Training Set Size')
        plt.ylabel(f'{scoring.capitalize()}')
        plt.title(f'Learning Curves: {model_name}')
        plt.legend(loc='best')
        plt.grid(True)
        
        # Save plot
        plot_path = os.path.join(self.output_dir, f"learning_curve_{model_name.replace(' ', '_')}.png")
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()
        logger.info(f"  Saved learning curve to {plot_path}")
        
        # Analyze for underfitting/overfitting
        final_gap = train_mean[-1] - val_mean[-1]
        logger.info(f"  Final train-val gap: {final_gap:.4f}")
        
        if final_gap > 0.15:
            logger.warning(f"  ⚠️  Large train-val gap! Likely OVERFITTING")
        elif val_mean[-1] < 0.75:
            logger.warning(f"  ⚠️  Low validation score! Likely UNDERFITTING")
        else:
            logger.info(f"  ✅ Good bias-variance tradeoff")
        
        return {
            'train_sizes': train_sizes_abs,
            'train_scores': train_scores,
            'val_scores': val_scores,
            'train_mean': train_mean,
            'val_mean': val_mean,
            'gap': final_gap
        }
    
    def plot_validation_curve(
        self, 
        estimator: BaseEstimator, 
        X: np.ndarray, 
        y: np.ndarray,
        param_name: str,
        param_range: np.ndarray,
        model_name: str,
        scoring: str = 'recall'
    ) -> Dict[str, np.ndarray]:
        """
        Generate validation curve for a hyperparameter.
        
        Args:
            estimator: Sklearn estimator (unfitted)
            X: Feature matrix
            y: Target labels
            param_name: Hyperparameter name to vary
            param_range: Range of values to test
            model_name: Name for plot title
            scoring: Metric to evaluate
            
        Returns:
            Dictionary with train and validation scores
        """
        logger.info(f"Generating validation curve for {param_name} in {model_name}...")
        
        train_scores, val_scores = validation_curve(
            estimator, X, y,
            param_name=param_name,
            param_range=param_range,
            cv=self.cv_splitter,
            scoring=scoring,
            n_jobs=-1
        )
        
        # Calculate means and stds
        train_mean = train_scores.mean(axis=1)
        train_std = train_scores.std(axis=1)
        val_mean = val_scores.mean(axis=1)
        val_std = val_scores.std(axis=1)
        
        # Plot
        plt.figure(figsize=(10, 6))
        plt.plot(param_range, train_mean, 'o-', color='blue', label='Training score')
        plt.fill_between(param_range, train_mean - train_std, train_mean + train_std, alpha=0.1, color='blue')
        plt.plot(param_range, val_mean, 'o-', color='red', label='Validation score')
        plt.fill_between(param_range, val_mean - val_std, val_mean + val_std, alpha=0.1, color='red')
        
        plt.xlabel(param_name)
        plt.ylabel(f'{scoring.capitalize()}')
        plt.title(f'Validation Curve: {model_name} - {param_name}')
        plt.legend(loc='best')
        plt.grid(True)
        
        # Use log scale if appropriate
        if param_name in ['C', 'alpha', 'gamma', 'learning_rate', 'reg_alpha', 'reg_lambda']:
            plt.xscale('log')
        
        # Save plot
        plot_path = os.path.join(self.output_dir, f"validation_curve_{model_name.replace(' ', '_')}_{param_name}.png")
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()
        logger.info(f"  Saved validation curve to {plot_path}")
        
        # Find optimal parameter value
        best_idx = np.argmax(val_mean)
        best_param = param_range[best_idx]
        logger.info(f"  Best {param_name}: {best_param} (val score: {val_mean[best_idx]:.4f})")
        
        return {
            'param_range': param_range,
            'train_scores': train_scores,
            'val_scores': val_scores,
            'train_mean': train_mean,
            'val_mean': val_mean,
            'best_param': best_param
        }
    
    def analyze_variance(self, cv_results: Dict[str, float]) -> str:
        """
        Analyze cross-validation variance for overfitting detection.
        
        Args:
            cv_results: Results from evaluate_cv_performance
            
        Returns:
            Analysis summary string
        """
        std = cv_results['std']
        mean = cv_results['mean']
        cv_coefficient = (std / mean) * 100 if mean > 0 else float('inf')
        
        logger.info(f"Variance Analysis:")
        logger.info(f"  Mean: {mean:.4f}")
        logger.info(f"  Std:  {std:.4f}")
        logger.info(f"  CV%:  {cv_coefficient:.2f}%")
        
        if cv_coefficient < 5:
            diagnosis = "✅ Very stable (low variance)"
        elif cv_coefficient < 10:
            diagnosis = "✅ Stable (acceptable variance)"
        elif cv_coefficient < 15:
            diagnosis = "⚠️  Moderate variance (monitor for overfitting)"
        else:
            diagnosis = "❌ High variance (likely overfitting)"
        
        logger.info(f"  Diagnosis: {diagnosis}")
        
        return diagnosis
