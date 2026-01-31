"""
Model Trainer for ATS Resume Scoring

Trains Logistic Regression, Random Forest, and XGBoost models with:
- SMOTE for class balancing
- Extensive hyperparameter tuning (GridSearchCV/RandomizedSearchCV)
- Regularization (L1/L2, tree depth, early stopping)
- Evaluation criteria integration
"""

import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.over_sampling import SMOTE
from typing import Dict, Tuple, Any
import logging
import os
import json
from datetime import datetime

from .evaluation_criteria import EvaluationCriteria

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ATSModelTrainer:
    """
    Comprehensive trainer for ATS models with hyperparameter tuning.
    
    Models trained:
    1. Logistic Regression (L1/L2/ElasticNet regularization)
    2. Random Forest (max_depth, min_samples_split regularization)
    3. XGBoost (learning_rate, max_depth, gamma, reg_alpha/lambda regularization)
    """
    
    def __init__(self, random_state: int = 42, output_dir: str = "models/experiments"):
        """
        Initialize model trainer.
        
        Args:
            random_state: Random seed for reproducibility
            output_dir: Directory to save models and results
        """
        self.random_state = random_state
        self.output_dir = output_dir
        self.models = {}
        self.best_model = None
        self.best_model_name = None
        
        os.makedirs(output_dir, exist_ok=True)
    
    def create_logistic_regression_pipeline(self) -> Tuple[ImbPipeline, Dict]:
        """
        Create Logistic Regression pipeline with SMOTE and hyperparameter grid.
        
        Returns:
            (pipeline, param_grid)
        """
        pipeline = ImbPipeline([
            ('smote', SMOTE(sampling_strategy=0.7, random_state=self.random_state)),
            ('classifier', LogisticRegression(
                random_state=self.random_state,
                max_iter=1000,
                solver='saga',  # Supports L1, L2, and ElasticNet
                class_weight='balanced'
            ))
        ])
        
        param_grid = {
            'classifier__C': [0.001, 0.01, 0.1, 1.0, 10.0, 100.0],  # Regularization strength
            'classifier__penalty': ['l1', 'l2', 'elasticnet'],
            'classifier__l1_ratio': [0.3, 0.5, 0.7]  # For elasticnet
        }
        
        return pipeline, param_grid
    
    def create_random_forest_pipeline(self) -> Tuple[ImbPipeline, Dict]:
        """
        Create Random Forest pipeline with SMOTE and hyperparameter grid.
        
        Returns:
            (pipeline, param_grid)
        """
        pipeline = ImbPipeline([
            ('smote', SMOTE(sampling_strategy=0.7, random_state=self.random_state)),
            ('classifier', RandomForestClassifier(
                random_state=self.random_state,
                class_weight='balanced',
                n_jobs=-1
            ))
        ])
        
        param_grid = {
            'classifier__n_estimators': [100, 200, 300],
            'classifier__max_depth': [10, 15, 20, 25, None],  # Regularization via depth
            'classifier__min_samples_split': [10, 20, 30, 50],  # Regularization via min samples
            'classifier__min_samples_leaf': [5, 10, 15],
            'classifier__max_features': ['sqrt', 'log2', 0.3],
            'classifier__criterion': ['gini', 'entropy']
        }
        
        return pipeline, param_grid
    
    def create_xgboost_pipeline(self) -> Tuple[ImbPipeline, Dict]:
        """
        Create XGBoost pipeline with SMOTE and hyperparameter grid.
        
        Returns:
            (pipeline, param_grid)
        """
        # Calculate scale_pos_weight for imbalanced data
        # Will be overridden if using SMOTE, but good for initial estimate
        
        pipeline = ImbPipeline([
            ('smote', SMOTE(sampling_strategy=0.7, random_state=self.random_state)),
            ('classifier', XGBClassifier(
                random_state=self.random_state,
                eval_metric='logloss',
                use_label_encoder=False,
                n_jobs=-1
            ))
        ])
        
        param_grid = {
            'classifier__n_estimators': [100, 200, 300],
            'classifier__learning_rate': [0.01, 0.05, 0.1],  # Regularization via learning rate
            'classifier__max_depth': [3, 5, 7],  # Regularization via depth
            'classifier__min_child_weight': [1, 3, 5],  # Regularization via min weight
            'classifier__gamma': [0, 0.1, 0.3, 0.5],  # Regularization via min split loss
            'classifier__subsample': [0.7, 0.8, 1.0],  # Regularization via row sampling
            'classifier__colsample_bytree': [0.7, 0.8, 1.0],  # Regularization via column sampling
            'classifier__reg_alpha': [0, 0.1, 1.0],  # L1 regularization
            'classifier__reg_lambda': [1, 5, 10]  # L2 regularization
        }
        
        return pipeline, param_grid
    
    def train_with_grid_search(
        self,
        model_name: str,
        pipeline: ImbPipeline,
        param_grid: Dict,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        use_randomized: bool = True,
        n_iter: int = 50
    ) -> Dict[str, Any]:
        """
        Train model with GridSearchCV or RandomizedSearchCV.
        
        Args:
            model_name: Name of the model
            pipeline: Sklearn pipeline with SMOTE and classifier
            param_grid: Hyperparameter grid
            X_train: Training features
            y_train: Training labels
            X_val: Validation features
            y_val: Validation labels
            use_randomized: Use RandomizedSearchCV instead of GridSearchCV (faster)
            n_iter: Number of iterations for RandomizedSearchCV
            
        Returns:
            Dictionary with model, best params, and metrics
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"TRAINING: {model_name}")
        logger.info(f"{'='*60}")
        
        # Choose search strategy
        if use_randomized and len(param_grid) > 3:
            logger.info(f"Using RandomizedSearchCV with {n_iter} iterations...")
            search = RandomizedSearchCV(
                pipeline,
                param_distributions=param_grid,
                n_iter=n_iter,
                cv=5,
                scoring='recall',  # Optimize for recall (minimize false negatives)
                n_jobs=-1,
                random_state=self.random_state,
                verbose=1
            )
        else:
            logger.info(f"Using GridSearchCV...")
            search = GridSearchCV(
                pipeline,
                param_grid=param_grid,
                cv=5,
                scoring='recall',
                n_jobs=-1,
                verbose=1
            )
        
        # Fit
        logger.info("Starting hyperparameter search...")
        search.fit(X_train, y_train)
        
        logger.info(f"✅ Best CV recall: {search.best_score_:.4f}")
        logger.info(f"Best parameters:")
        for param, value in search.best_params_.items():
            logger.info(f"  {param}: {value}")
        
        # Evaluate on validation set
        logger.info("\nEvaluating on validation set...")
        y_val_pred = search.predict(X_val)
        y_val_proba = search.predict_proba(X_val)[:, 1]
        
        val_metrics = EvaluationCriteria.calculate_metrics(y_val, y_val_pred, y_val_proba)
        
        # Print evaluation report
        EvaluationCriteria.print_evaluation_report(model_name, val_metrics, y_val, y_val_pred)
        
        # Check if meets criteria
        meets_criteria, checks = EvaluationCriteria.meets_criteria(val_metrics)
        val_metrics['meets_criteria'] = meets_criteria
        val_metrics['criteria_checks'] = checks
        
        # Calculate composite score
        composite_score = EvaluationCriteria.calculate_composite_score(val_metrics)
        val_metrics['composite_score'] = composite_score
        
        # Find optimal threshold
        optimal_threshold, threshold_metrics = EvaluationCriteria.find_optimal_threshold(
            y_val, y_val_proba, target_recall=0.90
        )
        
        # Store results
        results = {
            'model_name': model_name,
            'model': search.best_estimator_,
            'best_params': search.best_params_,
            'cv_score': search.best_score_,
            'val_metrics': val_metrics,
            'optimal_threshold': optimal_threshold,
            'threshold_metrics': threshold_metrics,
            'composite_score': composite_score,
            'meets_criteria': meets_criteria
        }
        
        # Save model
        model_path = os.path.join(self.output_dir, f"{model_name.replace(' ', '_').lower()}.joblib")
        joblib.dump(search.best_estimator_, model_path)
        logger.info(f"💾 Saved model to {model_path}")
        
        self.models[model_name] = results
        
        return results
    
    def train_all_models(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray
    ) -> Dict[str, Dict[str, Any]]:
        """
        Train all three models and compare performance.
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features
            y_val: Validation labels
            
        Returns:
            Dictionary of all model results
        """
        logger.info(f"\n🚀 Starting training pipeline for 3 models...\n")
        
        # 1. Logistic Regression
        lr_pipeline, lr_params = self.create_logistic_regression_pipeline()
        self.train_with_grid_search(
            "Logistic Regression",
            lr_pipeline,
            lr_params,
            X_train, y_train,
            X_val, y_val,
            use_randomized=False  # Small grid, use exhaustive search
        )
        
        # 2. Random Forest
        rf_pipeline, rf_params = self.create_random_forest_pipeline()
        self.train_with_grid_search(
            "Random Forest",
            rf_pipeline,
            rf_params,
            X_train, y_train,
            X_val, y_val,
            use_randomized=True,
            n_iter=50
        )
        
        # 3. XGBoost
        xgb_pipeline, xgb_params = self.create_xgboost_pipeline()
        self.train_with_grid_search(
            "XGBoost",
            xgb_pipeline,
            xgb_params,
            X_train, y_train,
            X_val, y_val,
            use_randomized=True,
            n_iter=50
        )
        
        # Select best model
        self._select_best_model()
        
        return self.models
    
    def _select_best_model(self):
        """Select best model based on composite score and criteria."""
        logger.info(f"\n{'='*60}")
        logger.info("MODEL COMPARISON & SELECTION")
        logger.info(f"{'='*60}\n")
        
        # Create comparison table
        logger.info(f"{'Model':<20} {'Recall':>8} {'F1':>8} {'ROC-AUC':>8} {'Composite':>10} {'Meets Criteria':>15}")
        logger.info(f"{'-'*80}")
        
        for model_name, results in self.models.items():
            metrics = results['val_metrics']
            logger.info(
                f"{model_name:<20} "
                f"{metrics['recall']:>8.4f} "
                f"{metrics['f1']:>8.4f} "
                f"{metrics['roc_auc']:>8.4f} "
                f"{results['composite_score']:>10.4f} "
                f"{'YES' if results['meets_criteria'] else 'NO':>15}"
            )
        
        # Select model with highest composite score that meets criteria
        valid_models = {
            name: results for name, results in self.models.items()
            if results['meets_criteria']
        }
        
        if valid_models:
            best_name = max(valid_models.items(), key=lambda x: x[1]['composite_score'])[0]
            self.best_model = valid_models[best_name]['model']
            self.best_model_name = best_name
            logger.info(f"\n🏆 BEST MODEL: {best_name}")
            logger.info(f"   Composite Score: {valid_models[best_name]['composite_score']:.4f}")
        else:
            # If no model meets criteria, select best by recall
            logger.warning(f"\n⚠️  No model meets all criteria. Selecting best by recall...")
            best_name = max(self.models.items(), key=lambda x: x[1]['val_metrics']['recall'])[0]
            self.best_model = self.models[best_name]['model']
            self.best_model_name = best_name
            logger.info(f"\n🏆 BEST MODEL (by recall): {best_name}")
        
        logger.info(f"{'='*60}\n")
    
    def save_results_summary(self, output_path: str = None):
        """Save training results summary to JSON."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.output_dir, f"training_results_{timestamp}.json")
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'best_model': self.best_model_name,
            'models': {}
        }
        
        for model_name, results in self.models.items():
            summary['models'][model_name] = {
                'best_params': results['best_params'],
                'cv_score': float(results['cv_score']),
                'val_metrics': {k: float(v) if isinstance(v, (int, float, np.number)) else v 
                               for k, v in results['val_metrics'].items() 
                               if k not in ['criteria_checks']},
                'composite_score': float(results['composite_score']),
                'meets_criteria': results['meets_criteria'],
                'optimal_threshold': float(results['optimal_threshold'])
            }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"💾 Saved training summary to {output_path}")
