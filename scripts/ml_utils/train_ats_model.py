"""
Quick Start Script for ATS ML Training

Run this script to train the ATS ML models from scratch.
"""

import subprocess
import sys
import os


def main():
    """Run the training pipeline"""

    print("=" * 80)
    print("ATS ML ENGINE - QUICK START TRAINING")
    print("=" * 80)
    print()
    print("This script will:")
    print("  1. Load data/AI_Resume_Screening.csv dataset")
    print("  2. Split data (70% train, 15% val, 15% test)")
    print("  3. Engineer features (exclude AI Score)")
    print("  4. Train 3 models: Logistic Regression, Random Forest, XGBoost")
    print("  5. Perform hyperparameter tuning with cross-validation")
    print("  6. Evaluate on test set")
    print("  7. Save best model to models/production/")
    print()
    print("Estimated time: 20-30 minutes")
    print("=" * 80)
    print()

    response = input("Continue? (yes/no): ")
    if response.lower() not in ["yes", "y"]:
        print("Training cancelled.")
        return

    # Run training script
    print("\n🚀 Starting training pipeline...\n")

    cmd = [
        sys.executable,
        "src/ml_engine/train.py",
        "--data-path",
        "resumes.csv",
        "--output-dir",
        "models/experiments",
        "--test-size",
        "0.15",
        "--val-size",
        "0.15",
        "--random-state",
        "42",
        "--run-cv-analysis",
    ]

    try:
        subprocess.run(cmd, cwd=os.getcwd(), check=True)

        print("\n" + "=" * 80)
        print("✅ TRAINING COMPLETE!")
        print("=" * 80)
        print("\nNext steps:")
        print("  1. Check models/production/ for the trained model")
        print("  2. Review models/experiments/ for detailed results")
        print("  3. Test the model using ATSPredictor")
        print("  4. Integrate with Agent 3 in the pipeline")
        print()

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Training failed with error code {e.returncode}")
        print("Check the logs above for details.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
