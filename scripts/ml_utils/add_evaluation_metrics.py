"""
Add evaluation metrics to model metadata
"""

import joblib
import json
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.ml_engine.data_loader import ATSDataLoader
from src.ml_engine.feature_engineering import FeatureEngineer
from src.ml_engine.evaluation_criteria import EvaluationCriteria

print("=" * 100)
print(" " * 30 + "EVALUATING MODELS - ADDING METRICS TO METADATA")
print("=" * 100)
print()

# Load data
print("📂 Loading dataset...")
data_loader = ATSDataLoader("data/AI_Resume_Screening.csv")
df = data_loader.load_data(exclude_ai_score=True)
train_df, val_df, test_df = data_loader.split_data()

X_train_raw, y_train = data_loader.get_X_y(train_df)
X_val_raw, y_val = data_loader.get_X_y(val_df)

# Feature engineering
print("🔧 Engineering features...")
feature_engineer = FeatureEngineer()
X_train, feature_names = feature_engineer.fit_transform(X_train_raw)
X_val = feature_engineer.transform(X_val_raw)

print(f"✅ Data prepared: {len(X_train)} train, {len(X_val)} val samples")
print()

# Load existing metadata
exp_dir = Path("models/experiments/experiment_20260129_193757")
metadata_path = exp_dir / "models_metadata_detailed.json"

with open(metadata_path, "r") as f:
    models_metadata = json.load(f)

# Evaluate Logistic Regression
print("┌" + "─" * 98 + "┐")
print("│" + " " * 30 + "EVALUATING: LOGISTIC REGRESSION" + " " * 37 + "│")
print("└" + "─" * 98 + "┘")

lr_path = exp_dir / "logistic_regression.joblib"
lr_model = joblib.load(lr_path)

y_val_pred_lr = lr_model.predict(X_val)
y_val_proba_lr = lr_model.predict_proba(X_val)[:, 1]

lr_metrics = EvaluationCriteria.calculate_metrics(y_val, y_val_pred_lr, y_val_proba_lr)
lr_composite = EvaluationCriteria.calculate_composite_score(lr_metrics)
lr_meets_criteria, lr_checks = EvaluationCriteria.meets_criteria(lr_metrics)
lr_optimal_threshold, lr_threshold_metrics = EvaluationCriteria.find_optimal_threshold(
    y_val, y_val_proba_lr, target_recall=0.90
)

# Print report
EvaluationCriteria.print_evaluation_report("Logistic Regression", lr_metrics, y_val, y_val_pred_lr)

# Add to metadata
models_metadata["Logistic Regression"]["validation_metrics"] = {
    "accuracy": float(lr_metrics["accuracy"]),
    "precision": float(lr_metrics["precision"]),
    "recall": float(lr_metrics["recall"]),
    "f1": float(lr_metrics["f1"]),
    "roc_auc": float(lr_metrics["roc_auc"]),
    "specificity": float(lr_metrics["specificity"]),
    "false_negative_rate": float(lr_metrics["false_negative_rate"]),
    "false_positive_rate": float(lr_metrics["false_positive_rate"]),
    "confusion_matrix": {
        "true_positives": int(lr_metrics["true_positives"]),
        "true_negatives": int(lr_metrics["true_negatives"]),
        "false_positives": int(lr_metrics["false_positives"]),
        "false_negatives": int(lr_metrics["false_negatives"]),
    },
}
models_metadata["Logistic Regression"]["composite_score"] = float(lr_composite)
models_metadata["Logistic Regression"]["meets_criteria"] = bool(lr_meets_criteria)
models_metadata["Logistic Regression"]["criteria_checks"] = {
    k: bool(v) for k, v in lr_checks.items()
}
models_metadata["Logistic Regression"]["optimal_threshold"] = float(lr_optimal_threshold)

print()

# Evaluate Random Forest
print("┌" + "─" * 98 + "┐")
print("│" + " " * 32 + "EVALUATING: RANDOM FOREST" + " " * 41 + "│")
print("└" + "─" * 98 + "┘")

rf_path = exp_dir / "random_forest.joblib"
rf_model = joblib.load(rf_path)

y_val_pred_rf = rf_model.predict(X_val)
y_val_proba_rf = rf_model.predict_proba(X_val)[:, 1]

rf_metrics = EvaluationCriteria.calculate_metrics(y_val, y_val_pred_rf, y_val_proba_rf)
rf_composite = EvaluationCriteria.calculate_composite_score(rf_metrics)
rf_meets_criteria, rf_checks = EvaluationCriteria.meets_criteria(rf_metrics)
rf_optimal_threshold, rf_threshold_metrics = EvaluationCriteria.find_optimal_threshold(
    y_val, y_val_proba_rf, target_recall=0.90
)

# Print report
EvaluationCriteria.print_evaluation_report("Random Forest", rf_metrics, y_val, y_val_pred_rf)

# Add to metadata
models_metadata["Random Forest"]["validation_metrics"] = {
    "accuracy": float(rf_metrics["accuracy"]),
    "precision": float(rf_metrics["precision"]),
    "recall": float(rf_metrics["recall"]),
    "f1": float(rf_metrics["f1"]),
    "roc_auc": float(rf_metrics["roc_auc"]),
    "specificity": float(rf_metrics["specificity"]),
    "false_negative_rate": float(rf_metrics["false_negative_rate"]),
    "false_positive_rate": float(rf_metrics["false_positive_rate"]),
    "confusion_matrix": {
        "true_positives": int(rf_metrics["true_positives"]),
        "true_negatives": int(rf_metrics["true_negatives"]),
        "false_positives": int(rf_metrics["false_positives"]),
        "false_negatives": int(rf_metrics["false_negatives"]),
    },
}
models_metadata["Random Forest"]["composite_score"] = float(rf_composite)
models_metadata["Random Forest"]["meets_criteria"] = bool(rf_meets_criteria)
models_metadata["Random Forest"]["criteria_checks"] = {k: bool(v) for k, v in rf_checks.items()}
models_metadata["Random Forest"]["optimal_threshold"] = float(rf_optimal_threshold)

print()

# Model comparison
print("=" * 100)
print(" " * 35 + "MODEL COMPARISON")
print("=" * 100)
print()
print(
    f"{'Model':<25} {'Recall':>8} {'F1':>8} {'ROC-AUC':>8} {'Composite':>10} {'Meets Criteria':>15}"
)
print("-" * 100)
print(
    f"{'Logistic Regression':<25} {lr_metrics['recall']:>8.4f} {lr_metrics['f1']:>8.4f} {lr_metrics['roc_auc']:>8.4f} {lr_composite:>10.4f} {'✅ YES' if lr_meets_criteria else '❌ NO':>15}"
)
print(
    f"{'Random Forest':<25} {rf_metrics['recall']:>8.4f} {rf_metrics['f1']:>8.4f} {rf_metrics['roc_auc']:>8.4f} {rf_composite:>10.4f} {'✅ YES' if rf_meets_criteria else '❌ NO':>15}"
)
print()

# Determine best model
if lr_composite > rf_composite:
    best_model_name = "Logistic Regression"
    best_composite = lr_composite
else:
    best_model_name = "Random Forest"
    best_composite = rf_composite

print(f"🏆 BEST MODEL (so far): {best_model_name}")
print(f"   Composite Score: {best_composite:.4f}")
print()

# Save updated metadata
with open(metadata_path, "w", encoding="utf-8") as f:
    json.dump(models_metadata, f, indent=2)

print("=" * 100)
print(f"💾 Updated metadata saved to: {metadata_path}")
print("=" * 100)
print()

print("📋 METADATA NOW INCLUDES:")
print("  ✅ Hyperparameters")
print("  ✅ SMOTE configuration")
print("  ✅ Feature importance/coefficients")
print("  ✅ Validation metrics (accuracy, precision, recall, F1, ROC-AUC)")
print("  ✅ Business metrics (FNR, FPR, specificity)")
print("  ✅ Confusion matrix")
print("  ✅ Composite score")
print("  ✅ Criteria checks")
print("  ✅ Optimal threshold")
print()
print("=" * 100)
