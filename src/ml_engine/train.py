"""
Main Training Script for ATS ML Engine

Orchestrates the complete training pipeline:
1. Load and split data
2. Feature engineering
3. Cross-validation evaluation
4. Model training with hyperparameter tuning
5. Final evaluation on test set
6. Save best model and artifacts
"""

import sys
import os
import argparse
import logging
import joblib
import json
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.ml_engine.data_loader import ATSDataLoader
from src.ml_engine.feature_engineering import FeatureEngineer
from src.ml_engine.cross_validation import CrossValidationEvaluator
from src.ml_engine.model_trainer import ATSModelTrainer
from src.ml_engine.evaluation_criteria import EvaluationCriteria

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main(args):
    """Main training pipeline."""
    
    logger.info(f"\n{'='*80}")
    logger.info("ATS ML ENGINE - TRAINING PIPELINE")
    logger.info(f"{'='*80}\n")
    
    # Create output directories
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    experiment_dir = os.path.join(args.output_dir, f"experiment_{timestamp}")
    production_dir = "models/production"
    
    os.makedirs(experiment_dir, exist_ok=True)
    os.makedirs(production_dir, exist_ok=True)
    
    # ========== PHASE 1: LOAD DATA ==========
    logger.info("PHASE 1: Loading and splitting data...")
    
    data_loader = ATSDataLoader(data_path=args.data_path)
    df = data_loader.load_data(exclude_ai_score=True)
    
    train_df, val_df, test_df = data_loader.split_data(
        test_size=args.test_size,
        val_size=args.val_size,
        random_state=args.random_state
    )
    
    # Separate features and targets
    X_train_raw, y_train = data_loader.get_X_y(train_df)
    X_val_raw, y_val = data_loader.get_X_y(val_df)
    X_test_raw, y_test = data_loader.get_X_y(test_df)
    
    logger.info(f"✅ Data loaded and split successfully\n")
    
    # ========== PHASE 2: FEATURE ENGINEERING ==========
    logger.info("PHASE 2: Feature engineering...")
    
    feature_engineer = FeatureEngineer()
    X_train, feature_names = feature_engineer.fit_transform(X_train_raw)
    X_val = feature_engineer.transform(X_val_raw)
    X_test = feature_engineer.transform(X_test_raw)
    
    logger.info(f"✅ Features engineered: {len(feature_names)} features\n")
    
    # ========== PHASE 3: CROSS-VALIDATION ANALYSIS ==========
    if args.run_cv_analysis:
        logger.info("PHASE 3: Cross-validation analysis...")
        
        cv_evaluator = CrossValidationEvaluator(
            n_folds=5,
            random_state=args.random_state,
            output_dir=experiment_dir
        )
        
        # Create baseline models for CV analysis
        from sklearn.linear_model import LogisticRegression
        from sklearn.ensemble import RandomForestClassifier
        from xgboost import XGBClassifier
        
        baseline_models = {
            'Logistic Regression': LogisticRegression(random_state=args.random_state, max_iter=1000),
            'Random Forest': RandomForestClassifier(random_state=args.random_state, n_estimators=100),
            'XGBoost': XGBClassifier(random_state=args.random_state, n_estimators=100, use_label_encoder=False)
        }
        
        for model_name, model in baseline_models.items():
            # CV performance
            cv_results = cv_evaluator.evaluate_cv_performance(model, X_train, y_train, scoring='recall')
            cv_evaluator.analyze_variance(cv_results)
            
            # Learning curves
            cv_evaluator.plot_learning_curves(model, X_train, y_train, model_name, scoring='recall')
        
        logger.info(f"✅ CV analysis complete. Plots saved to {experiment_dir}\n")
    
    # ========== PHASE 4: MODEL TRAINING ==========
    logger.info("PHASE 4: Training models with hyperparameter tuning...")
    
    trainer = ATSModelTrainer(
        random_state=args.random_state,
        output_dir=experiment_dir
    )
    
    # Train all models
    all_results = trainer.train_all_models(X_train, y_train, X_val, y_val)
    
    logger.info(f"✅ All models trained\n")
    
    # ========== PHASE 5: FINAL TEST EVALUATION ==========
    logger.info("PHASE 5: Final evaluation on test set...")
    
    best_model = trainer.best_model
    best_model_name = trainer.best_model_name
    
    # Predict on test set
    y_test_pred = best_model.predict(X_test)
    y_test_proba = best_model.predict_proba(X_test)[:, 1]
    
    # Calculate metrics
    test_metrics = EvaluationCriteria.calculate_metrics(y_test, y_test_pred, y_test_proba)
    
    # Print final report
    EvaluationCriteria.print_evaluation_report(
        f"{best_model_name} (Test Set)",
        test_metrics,
        y_test,
        y_test_pred
    )
    
    # Find optimal threshold on test set
    optimal_threshold, threshold_metrics = EvaluationCriteria.find_optimal_threshold(
        y_test, y_test_proba, target_recall=0.90
    )
    
    logger.info(f"✅ Test evaluation complete\n")
    
    # ========== PHASE 6: SAVE PRODUCTION MODEL ==========
    logger.info("PHASE 6: Saving production artifacts...")
    
    # Save best model
    model_path = os.path.join(production_dir, "ats_model.joblib")
    joblib.dump(best_model, model_path)
    logger.info(f"💾 Saved model to {model_path}")
    
    # Save feature engineer
    feature_engineer_path = os.path.join(production_dir, "feature_engineer.joblib")
    joblib.dump(feature_engineer, feature_engineer_path)
    logger.info(f"💾 Saved feature engineer to {feature_engineer_path}")
    
    # Save metadata
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'model_name': best_model_name,
        'feature_count': len(feature_names),
        'feature_names': feature_names,
        'optimal_threshold': float(optimal_threshold),
        'train_size': len(X_train),
        'val_size': len(X_val),
        'test_size': len(X_test),
        'test_metrics': {
            k: float(v) if isinstance(v, (int, float)) else v
            for k, v in test_metrics.items()
            if k not in ['criteria_checks']
        },
        'best_params': all_results[best_model_name]['best_params'],
        'meets_criteria': bool(EvaluationCriteria.meets_criteria(test_metrics)[0])
    }
    
    metadata_path = os.path.join(production_dir, "model_metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"💾 Saved metadata to {metadata_path}")
    
    # Save training summary
    trainer.save_results_summary(os.path.join(experiment_dir, "training_summary.json"))
    
    logger.info(f"\n{'='*80}")
    logger.info("✅ TRAINING PIPELINE COMPLETE!")
    logger.info(f"{'='*80}")
    logger.info(f"\nProduction artifacts saved to: {production_dir}")
    logger.info(f"Experiment results saved to: {experiment_dir}")
    logger.info(f"\nBest Model: {best_model_name}")
    logger.info(f"Test Recall: {test_metrics['recall']:.4f}")
    logger.info(f"Test F1: {test_metrics['f1']:.4f}")
    logger.info(f"Meets Criteria: {metadata['meets_criteria']}")
    logger.info(f"{'='*80}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train ATS ML models")
    
    parser.add_argument(
        '--data-path',
        type=str,
        default='resumes.csv',
        help='Path to the resume dataset CSV file'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='models/experiments',
        help='Directory to save experiment results'
    )
    
    parser.add_argument(
        '--test-size',
        type=float,
        default=0.15,
        help='Proportion of data for test set'
    )
    
    parser.add_argument(
        '--val-size',
        type=float,
        default=0.15,
        help='Proportion of data for validation set'
    )
    
    parser.add_argument(
        '--random-state',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )
    
    parser.add_argument(
        '--run-cv-analysis',
        action='store_true',
        help='Run cross-validation analysis and generate learning curves'
    )
    
    args = parser.parse_args()
    
    main(args)
