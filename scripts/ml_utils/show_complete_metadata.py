"""
Complete Model Metadata Summary
"""

import joblib
import json
from pathlib import Path
import numpy as np

# Load a sample to get feature names
from src.ml_engine.data_loader import ATSDataLoader
from src.ml_engine.feature_engineering import FeatureEngineer

print("=" * 100)
print(" " * 35 + "ATS ML ENGINE - MODEL METADATA")
print("=" * 100)
print()

# Get feature names
print("Loading dataset to extract feature names...")
data_loader = ATSDataLoader("data/AI_Resume_Screening.csv")
df = data_loader.load_data(exclude_ai_score=True)
train_df, val_df, test_df = data_loader.split_data()
X_train_raw, y_train = data_loader.get_X_y(train_df)

feature_engineer = FeatureEngineer()
X_train, feature_names = feature_engineer.fit_transform(X_train_raw)

print(f"✅ Total Features Engineered: {len(feature_names)}")
print(f"   Feature Names: {', '.join(feature_names[:10])}...")
print()

# Load models
exp_dir = Path("models/experiments/experiment_20260129_193757")

models_metadata = {}

# ==== LOGISTIC REGRESSION ====
lr_path = exp_dir / "logistic_regression.joblib"
if lr_path.exists():
    print("┌" + "─" * 98 + "┐")
    print("│" + " " * 35 + "LOGISTIC REGRESSION MODEL" + " " * 38 + "│")
    print("├" + "─" * 98 + "┤")

    lr_model = joblib.load(lr_path)
    lr_meta = {}

    if hasattr(lr_model, "named_steps"):
        # SMOTE
        if "smote" in lr_model.named_steps:
            smote = lr_model.named_steps["smote"]
            lr_meta["smote"] = {
                "sampling_strategy": float(smote.sampling_strategy),
                "k_neighbors": int(smote.k_neighbors),
            }

        # Classifier
        if "classifier" in lr_model.named_steps:
            clf = lr_model.named_steps["classifier"]
            lr_meta["hyperparameters"] = {
                "penalty": clf.penalty,
                "C": float(clf.C),
                "l1_ratio": float(clf.l1_ratio) if hasattr(clf, "l1_ratio") else None,
                "solver": clf.solver,
                "max_iter": int(clf.max_iter),
                "class_weight": clf.class_weight,
            }

            # Feature importance
            if hasattr(clf, "coef_"):
                coef = np.abs(clf.coef_[0])
                top_10_indices = np.argsort(coef)[-10:][::-1]

                lr_meta["top_features"] = []
                for idx in top_10_indices:
                    lr_meta["top_features"].append(
                        {"feature": feature_names[idx], "coefficient": float(coef[idx])}
                    )

    models_metadata["Logistic Regression"] = lr_meta

    # Print formatted
    print("│ 📋 Hyperparameters:" + " " * 79 + "│")
    for key, value in lr_meta.get("hyperparameters", {}).items():
        print(f"│   • {key:<20} {str(value):<75} │")

    print("│" + " " * 98 + "│")
    print("│ 🎯 Regularization Strategy:" + " " * 69 + "│")
    print("│   • Type: L1 (Lasso) - Feature Selection" + " " * 55 + "│")
    print(
        f"│   • Strength (C): {lr_meta['hyperparameters']['C']} (higher = less regularization)"
        + " " * 28
        + "│"
    )

    print("│" + " " * 98 + "│")
    print("│ ⚖️  Class Imbalance Handling:" + " " * 67 + "│")
    print(
        f"│   • SMOTE Sampling: {lr_meta['smote']['sampling_strategy']} (70% minority class)"
        + " " * 38
        + "│"
    )
    print("│   • Class Weights: Balanced" + " " * 69 + "│")

    print("│" + " " * 98 + "│")
    print("│ ⭐ Top 10 Most Important Features:" + " " * 63 + "│")
    for i, feat in enumerate(lr_meta.get("top_features", []), 1):
        feat_name = feat["feature"][:40]
        coef = feat["coefficient"]
        print(
            f"│   {i:2d}. {feat_name:<45} Coefficient: {coef:>8.4f}"
            + " " * (33 - len(f"{coef:.4f}"))
            + "│"
        )

    print("└" + "─" * 98 + "┘")
    print()

# ==== RANDOM FOREST ====
rf_path = exp_dir / "random_forest.joblib"
if rf_path.exists():
    print("┌" + "─" * 98 + "┐")
    print("│" + " " * 38 + "RANDOM FOREST MODEL" + " " * 41 + "│")
    print("├" + "─" * 98 + "┤")

    rf_model = joblib.load(rf_path)
    rf_meta = {}

    if hasattr(rf_model, "named_steps"):
        # SMOTE
        if "smote" in rf_model.named_steps:
            smote = rf_model.named_steps["smote"]
            rf_meta["smote"] = {
                "sampling_strategy": float(smote.sampling_strategy),
                "k_neighbors": int(smote.k_neighbors),
            }

        # Classifier
        if "classifier" in rf_model.named_steps:
            clf = rf_model.named_steps["classifier"]
            rf_meta["hyperparameters"] = {
                "n_estimators": int(clf.n_estimators),
                "max_depth": int(clf.max_depth) if clf.max_depth else None,
                "min_samples_split": int(clf.min_samples_split),
                "min_samples_leaf": int(clf.min_samples_leaf),
                "max_features": clf.max_features,
                "class_weight": clf.class_weight,
                "bootstrap": bool(clf.bootstrap),
            }

            # Feature importance
            if hasattr(clf, "feature_importances_"):
                importances = clf.feature_importances_
                top_10_indices = np.argsort(importances)[-10:][::-1]

                rf_meta["top_features"] = []
                for idx in top_10_indices:
                    rf_meta["top_features"].append(
                        {"feature": feature_names[idx], "importance": float(importances[idx])}
                    )

    models_metadata["Random Forest"] = rf_meta

    # Print formatted
    print("│ 📋 Hyperparameters:" + " " * 79 + "│")
    for key, value in rf_meta.get("hyperparameters", {}).items():
        print(f"│   • {key:<20} {str(value):<75} │")

    print("│" + " " * 98 + "│")
    print("│ 🎯 Regularization Strategy:" + " " * 69 + "│")
    print(
        f"│   • Max Depth: {rf_meta['hyperparameters']['max_depth']} (prevents overfitting)"
        + " " * 46
        + "│"
    )
    print(
        f"│   • Min Samples Split: {rf_meta['hyperparameters']['min_samples_split']} (requires more samples to split)"
        + " " * 29
        + "│"
    )
    print(
        f"│   • Min Samples Leaf: {rf_meta['hyperparameters']['min_samples_leaf']} (minimum samples per leaf node)"
        + " " * 32
        + "│"
    )
    print(
        f"│   • Max Features: {rf_meta['hyperparameters']['max_features']} (feature sampling per split)"
        + " " * 35
        + "│"
    )

    print("│" + " " * 98 + "│")
    print("│ ⚖️  Class Imbalance Handling:" + " " * 67 + "│")
    print(
        f"│   • SMOTE Sampling: {rf_meta['smote']['sampling_strategy']} (70% minority class)"
        + " " * 38
        + "│"
    )
    print("│   • Class Weights: Balanced" + " " * 69 + "│")

    print("│" + " " * 98 + "│")
    print("│ ⭐ Top 10 Most Important Features:" + " " * 63 + "│")
    for i, feat in enumerate(rf_meta.get("top_features", []), 1):
        feat_name = feat["feature"][:40]
        imp = feat["importance"]
        print(
            f"│   {i:2d}. {feat_name:<45} Importance: {imp:>8.4f}"
            + " " * (33 - len(f"{imp:.4f}"))
            + "│"
        )

    print("└" + "─" * 98 + "┘")
    print()

# Save metadata to JSON
metadata_path = exp_dir / "models_metadata_detailed.json"
with open(metadata_path, "w", encoding="utf-8") as f:
    json.dump(models_metadata, f, indent=2)

print("=" * 100)
print(f"💾 Metadata saved to: {metadata_path}")
print("=" * 100)
print()

# Summary
print("📊 TRAINING STATUS SUMMARY:")
print("-" * 100)
print("✅ Logistic Regression - TRAINED & SAVED")
print("✅ Random Forest - TRAINED & SAVED")
print("❌ XGBoost - NOT TRAINED (training interrupted)")
print("❌ Production Deployment - INCOMPLETE (no test evaluation)")
print("-" * 100)
print()
print("💡 To complete the training pipeline:")
print("   1. Re-run: python train_ats_model.py")
print("   2. This will train XGBoost and perform test set evaluation")
print("   3. Best model will be saved to models/production/")
print("=" * 100)
