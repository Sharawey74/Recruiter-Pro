"""
Extract metadata from saved model files
"""

import joblib
from pathlib import Path
import numpy as np

exp_dir = Path("models/experiments/experiment_20260129_193757")

print("=" * 80)
print("EXTRACTING METADATA FROM TRAINED MODELS")
print("=" * 80)
print()

# Load Logistic Regression
lr_path = exp_dir / "logistic_regression.joblib"
if lr_path.exists():
    print("📊 LOGISTIC REGRESSION")
    print("-" * 80)
    lr_model = joblib.load(lr_path)

    # Get pipeline components
    if hasattr(lr_model, "named_steps"):
        print(f"Pipeline Steps: {list(lr_model.named_steps.keys())}")

        # SMOTE parameters
        if "smote" in lr_model.named_steps:
            smote = lr_model.named_steps["smote"]
            print("\nSMOTE Configuration:")
            print(f"  Sampling Strategy: {smote.sampling_strategy}")
            print(f"  k_neighbors: {smote.k_neighbors}")

        # Classifier parameters
        if "classifier" in lr_model.named_steps:
            clf = lr_model.named_steps["classifier"]
            print(f"\nClassifier: {type(clf).__name__}")
            print(f"  Penalty: {clf.penalty}")
            print(f"  C (regularization): {clf.C}")
            if hasattr(clf, "l1_ratio"):
                print(f"  L1 Ratio: {clf.l1_ratio}")
            print(f"  Solver: {clf.solver}")
            print(f"  Max Iterations: {clf.max_iter}")
            print(f"  Class Weight: {clf.class_weight}")

            # Feature importance (coefficients for Logistic Regression)
            if hasattr(clf, "coef_"):
                coef = np.abs(clf.coef_[0])
                print("\n  Top 10 Feature Coefficients (absolute):")
                top_indices = np.argsort(coef)[-10:][::-1]
                for idx in top_indices:
                    print(f"    Feature {idx}: {coef[idx]:.4f}")
    print()

# Load Random Forest
rf_path = exp_dir / "random_forest.joblib"
if rf_path.exists():
    print("🌲 RANDOM FOREST")
    print("-" * 80)
    rf_model = joblib.load(rf_path)

    # Get pipeline components
    if hasattr(rf_model, "named_steps"):
        print(f"Pipeline Steps: {list(rf_model.named_steps.keys())}")

        # SMOTE parameters
        if "smote" in rf_model.named_steps:
            smote = rf_model.named_steps["smote"]
            print("\nSMOTE Configuration:")
            print(f"  Sampling Strategy: {smote.sampling_strategy}")
            print(f"  k_neighbors: {smote.k_neighbors}")

        # Classifier parameters
        if "classifier" in rf_model.named_steps:
            clf = rf_model.named_steps["classifier"]
            print(f"\nClassifier: {type(clf).__name__}")
            print(f"  n_estimators: {clf.n_estimators}")
            print(f"  max_depth: {clf.max_depth}")
            print(f"  min_samples_split: {clf.min_samples_split}")
            print(f"  min_samples_leaf: {clf.min_samples_leaf}")
            print(f"  max_features: {clf.max_features}")
            print(f"  Class Weight: {clf.class_weight}")
            print(f"  Bootstrap: {clf.bootstrap}")
            print(f"  n_jobs: {clf.n_jobs}")

            # Feature importance
            if hasattr(clf, "feature_importances_"):
                importances = clf.feature_importances_
                print("\n  Top 10 Feature Importances:")
                top_indices = np.argsort(importances)[-10:][::-1]
                for idx in top_indices:
                    print(f"    Feature {idx}: {importances[idx]:.4f}")
    print()

print("=" * 80)
print()
print("NOTE: Training was interrupted before completion.")
print("The following models were NOT trained:")
print("  - XGBoost")
print()
print("To complete training, re-run: python train_ats_model.py")
print("=" * 80)
