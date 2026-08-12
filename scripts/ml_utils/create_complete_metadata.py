"""
Create complete metadata for all trained models including all evaluation metrics
"""
import joblib
import json
from pathlib import Path
import sys
import numpy as np

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.ml_engine.data_loader import ATSDataLoader
from src.ml_engine.evaluation_criteria import EvaluationCriteria

# Helper function to convert numpy types to Python types
def convert_to_serializable(obj):
    """Convert numpy types to Python native types for JSON serialization."""
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    return obj

print("="*100)
print(" "*25 + "CREATING COMPLETE MODEL METADATA WITH EVALUATION METRICS")
print("="*100)
print()

# Load data
print("📂 Loading dataset...")
data_loader = ATSDataLoader("data/AI_Resume_Screening.csv")
df = data_loader.load_data(exclude_ai_score=True)
train_df, val_df, test_df = data_loader.split_data()

X_train_raw, y_train = data_loader.get_X_y(train_df)
X_val_raw, y_val = data_loader.get_X_y(val_df)
X_test_raw, y_test = data_loader.get_X_y(test_df)

# Feature engineering
print("🔧 Engineering features...")
feature_engineer = joblib.load("models/production/feature_engineer.joblib")
X_train, feature_names = feature_engineer.fit_transform(X_train_raw)
X_val = feature_engineer.transform(X_val_raw)
X_test = feature_engineer.transform(X_test_raw)

print(f"✅ Data prepared: {len(X_train)} train, {len(X_val)} val, {len(X_test)} test samples")
print()

# Get latest experiment directory
experiments_dir = Path("models/experiments")
exp_dirs = sorted([d for d in experiments_dir.iterdir() if d.is_dir()])
latest_exp = exp_dirs[-1] if exp_dirs else None

if not latest_exp:
    print("❌ No experiment directory found")
    sys.exit(1)

print(f"📁 Using experiment directory: {latest_exp.name}")
print()

models_metadata = {}

# Evaluate each model
model_configs = [
    ("Logistic Regression", latest_exp / "logistic_regression.joblib"),
    ("Random Forest", latest_exp / "random_forest.joblib"),
    ("XGBoost", latest_exp / "xgboost.joblib")
]

for model_name, model_path in model_configs:
    if not model_path.exists():
        print(f"⚠️  {model_name} not found, skipping...")
        continue
    
    print(f"┌{'─'*98}┐")
    print(f"│{' '*30}EVALUATING: {model_name.upper():<40}│")
    print(f"└{'─'*98}┘")
    print()
    
    # Load model
    model = joblib.load(model_path)
    
    # Get model-specific details
    if "smote" in model.named_steps:
        smote = model.named_steps['smote']
        smote_config = {
            "sampling_strategy": float(smote.sampling_strategy) if isinstance(smote.sampling_strategy, (int, float)) else smote.sampling_strategy,
            "k_neighbors": int(smote.k_neighbors)
        }
    else:
        smote_config = None
    
    classifier = model.named_steps['classifier']
    hyperparameters = {}
    
    # Extract hyperparameters based on model type
    if model_name == "Logistic Regression":
        hyperparameters = {
            "penalty": str(classifier.penalty),
            "C": float(classifier.C),
            "l1_ratio": float(classifier.l1_ratio) if classifier.l1_ratio is not None else None,
            "solver": str(classifier.solver),
            "max_iter": int(classifier.max_iter),
            "class_weight": str(classifier.class_weight)
        }
    elif model_name == "Random Forest":
        hyperparameters = {
            "n_estimators": int(classifier.n_estimators),
            "max_depth": int(classifier.max_depth) if classifier.max_depth is not None else None,
            "min_samples_split": int(classifier.min_samples_split),
            "min_samples_leaf": int(classifier.min_samples_leaf),
            "max_features": float(classifier.max_features) if isinstance(classifier.max_features, float) else str(classifier.max_features),
            "class_weight": str(classifier.class_weight),
            "bootstrap": bool(classifier.bootstrap)
        }
    elif model_name == "XGBoost":
        hyperparameters = {
            "n_estimators": int(classifier.n_estimators),
            "learning_rate": float(classifier.learning_rate),
            "max_depth": int(classifier.max_depth),
            "min_child_weight": float(classifier.min_child_weight),
            "gamma": float(classifier.gamma),
            "subsample": float(classifier.subsample),
            "colsample_bytree": float(classifier.colsample_bytree),
            "reg_alpha": float(classifier.reg_alpha),
            "reg_lambda": float(classifier.reg_lambda)
        }
    
    # Get feature importance
    if hasattr(classifier, 'coef_'):
        # Logistic Regression
        coef = classifier.coef_[0]
        top_indices = np.argsort(np.abs(coef))[-10:][::-1]
        top_features = [
            {"feature": feature_names[i], "coefficient": float(coef[i])}
            for i in top_indices
        ]
    elif hasattr(classifier, 'feature_importances_'):
        # Tree-based models
        importances = classifier.feature_importances_
        top_indices = np.argsort(importances)[-10:][::-1]
        top_features = [
            {"feature": feature_names[i], "importance": float(importances[i])}
            for i in top_indices
        ]
    else:
        top_features = []
    
    # Validation metrics
    y_val_pred = model.predict(X_val)
    y_val_proba = model.predict_proba(X_val)[:, 1]
    val_metrics = EvaluationCriteria.calculate_metrics(y_val, y_val_pred, y_val_proba)
    val_composite = EvaluationCriteria.calculate_composite_score(val_metrics)
    val_meets_criteria, val_checks = EvaluationCriteria.meets_criteria(val_metrics)
    val_optimal_threshold, _ = EvaluationCriteria.find_optimal_threshold(y_val, y_val_proba, target_recall=0.90)
    
    print("📊 VALIDATION SET METRICS:")
    print(f"  Recall: {val_metrics['recall']:.4f}, F1: {val_metrics['f1']:.4f}, ROC-AUC: {val_metrics['roc_auc']:.4f}")
    print(f"  Composite: {val_composite:.4f}, Meets Criteria: {val_meets_criteria}")
    print()
    
    # Test metrics
    y_test_pred = model.predict(X_test)
    y_test_proba = model.predict_proba(X_test)[:, 1]
    test_metrics = EvaluationCriteria.calculate_metrics(y_test, y_test_pred, y_test_proba)
    test_composite = EvaluationCriteria.calculate_composite_score(test_metrics)
    test_meets_criteria, test_checks = EvaluationCriteria.meets_criteria(test_metrics)
    test_optimal_threshold, _ = EvaluationCriteria.find_optimal_threshold(y_test, y_test_proba, target_recall=0.90)
    
    print("📊 TEST SET METRICS:")
    print(f"  Recall: {test_metrics['recall']:.4f}, F1: {test_metrics['f1']:.4f}, ROC-AUC: {test_metrics['roc_auc']:.4f}")
    print(f"  Composite: {test_composite:.4f}, Meets Criteria: {test_meets_criteria}")
    print()
    
    # Build metadata dictionary
    models_metadata[model_name] = {
        "smote": smote_config,
        "hyperparameters": hyperparameters,
        "top_features": top_features,
        "validation_metrics": {
            "accuracy": float(val_metrics['accuracy']),
            "precision": float(val_metrics['precision']),
            "recall": float(val_metrics['recall']),
            "f1": float(val_metrics['f1']),
            "roc_auc": float(val_metrics['roc_auc']),
            "specificity": float(val_metrics['specificity']),
            "false_negative_rate": float(val_metrics['false_negative_rate']),
            "false_positive_rate": float(val_metrics['false_positive_rate']),
            "confusion_matrix": {
                "true_positives": int(val_metrics['true_positives']),
                "true_negatives": int(val_metrics['true_negatives']),
                "false_positives": int(val_metrics['false_positives']),
                "false_negatives": int(val_metrics['false_negatives'])
            }
        },
        "validation_composite_score": float(val_composite),
        "validation_meets_criteria": bool(val_meets_criteria),
        "validation_criteria_checks": convert_to_serializable(val_checks),
        "validation_optimal_threshold": float(val_optimal_threshold),
        "test_metrics": {
            "accuracy": float(test_metrics['accuracy']),
            "precision": float(test_metrics['precision']),
            "recall": float(test_metrics['recall']),
            "f1": float(test_metrics['f1']),
            "roc_auc": float(test_metrics['roc_auc']),
            "specificity": float(test_metrics['specificity']),
            "false_negative_rate": float(test_metrics['false_negative_rate']),
            "false_positive_rate": float(test_metrics['false_positive_rate']),
            "confusion_matrix": {
                "true_positives": int(test_metrics['true_positives']),
                "true_negatives": int(test_metrics['true_negatives']),
                "false_positives": int(test_metrics['false_positives']),
                "false_negatives": int(test_metrics['false_negatives'])
            }
        },
        "test_composite_score": float(test_composite),
        "test_meets_criteria": bool(test_meets_criteria),
        "test_criteria_checks": convert_to_serializable(test_checks),
        "test_optimal_threshold": float(test_optimal_threshold)
    }

# Save to experiment directory
metadata_path = latest_exp / "all_models_metadata_complete.json"
with open(metadata_path, 'w', encoding='utf-8') as f:
    json.dump(models_metadata, f, indent=2)

print()
print("="*100)
print(f"💾 Complete metadata saved to: {metadata_path}")
print("="*100)
print()

print("📋 SUMMARY:")
print(f"  Total models: {len(models_metadata)}")
print(f"  Total features: {len(feature_names)}")
print()

# Print model comparison
print("="*100)
print(" "*35 + "MODEL COMPARISON")
print("="*100)
print()
print(f"{'Model':<25} {'Val Recall':>10} {'Val F1':>10} {'Test Recall':>11} {'Test F1':>10} {'Best':>6}")
print("-"*100)

best_model = None
best_score = 0

for model_name, metadata in models_metadata.items():
    val_recall = metadata['validation_metrics']['recall']
    val_f1 = metadata['validation_metrics']['f1']
    test_recall = metadata['test_metrics']['recall']
    test_f1 = metadata['test_metrics']['f1']
    test_composite = metadata['test_composite_score']
    
    is_best = ""
    if test_composite > best_score:
        best_score = test_composite
        best_model = model_name
        is_best = "🏆"
    
    print(f"{model_name:<25} {val_recall:>10.4f} {val_f1:>10.4f} {test_recall:>11.4f} {test_f1:>10.4f} {is_best:>6}")

print()
print(f"🏆 BEST MODEL (Test Set): {best_model}")
print(f"   Composite Score: {best_score:.4f}")
print()
print("="*100)
