"""
Quick script to display training results metadata
"""
import json
from pathlib import Path

# Find the latest experiment
experiments_dir = Path("models/experiments")
if not experiments_dir.exists():
    print("No experiments directory found")
    exit(1)

experiments = sorted([d for d in experiments_dir.iterdir() if d.is_dir()], 
                    key=lambda x: x.name, reverse=True)

if not experiments:
    print("No experiment directories found")
    exit(1)

latest_exp = experiments[0]
print(f"{'='*80}")
print(f"LATEST EXPERIMENT: {latest_exp.name}")
print(f"{'='*80}\n")

# Check for models
models_found = list(latest_exp.glob("*.joblib"))
print(f"📦 MODELS TRAINED: {len(models_found)}")
for model_path in models_found:
    print(f"  - {model_path.name}")
print()

# Check for learning curves
curves_found = list(latest_exp.glob("learning_curve_*.png"))
print(f"📊 LEARNING CURVES: {len(curves_found)}")
for curve_path in curves_found:
    print(f"  - {curve_path.name}")
print()

# Check for training summary
summary_path = latest_exp / "training_summary.json"
if summary_path.exists():
    with open(summary_path, 'r') as f:
        summary = json.load(f)
    
    print(f"{'='*80}")
    print("TRAINING SUMMARY")
    print(f"{'='*80}\n")
    print(f"Timestamp: {summary.get('timestamp', 'N/A')}")
    print(f"Best Model: {summary.get('best_model', 'N/A')}\n")
    
    print(f"{'Model':<25} {'CV Score':<12} {'Val Recall':<12} {'Val F1':<12} {'Composite':<12} {'Meets Criteria'}")
    print(f"{'-'*100}")
    
    for model_name, results in summary.get('models', {}).items():
        cv_score = results.get('cv_score', 0)
        val_metrics = results.get('val_metrics', {})
        recall = val_metrics.get('recall', 0)
        f1 = val_metrics.get('f1', 0)
        composite = results.get('composite_score', 0)
        meets = '✅ YES' if results.get('meets_criteria', False) else '❌ NO'
        
        print(f"{model_name:<25} {cv_score:<12.4f} {recall:<12.4f} {f1:<12.4f} {composite:<12.4f} {meets}")
    
    print(f"\n{'='*80}\n")
    
    # Detailed metrics for best model
    best_model_name = summary.get('best_model')
    if best_model_name and best_model_name in summary.get('models', {}):
        print(f"BEST MODEL DETAILS: {best_model_name}")
        print(f"{'='*80}\n")
        
        best_results = summary['models'][best_model_name]
        
        print("Best Parameters:")
        for param, value in best_results.get('best_params', {}).items():
            print(f"  {param}: {value}")
        
        print("\nValidation Metrics:")
        val_metrics = best_results.get('val_metrics', {})
        for metric in ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']:
            if metric in val_metrics:
                print(f"  {metric.replace('_', ' ').title():<20} {val_metrics[metric]:.4f}")
        
        print("\nConfusion Matrix:")
        if 'true_positives' in val_metrics:
            print(f"  True Positives:  {val_metrics.get('true_positives', 0):4d}")
            print(f"  True Negatives:  {val_metrics.get('true_negatives', 0):4d}")
            print(f"  False Positives: {val_metrics.get('false_positives', 0):4d}")
            print(f"  False Negatives: {val_metrics.get('false_negatives', 0):4d}")
        
        print(f"\nOptimal Threshold: {best_results.get('optimal_threshold', 0.5):.4f}")
        print(f"Composite Score: {best_results.get('composite_score', 0):.4f}")
        print(f"Meets Criteria: {'✅ YES' if best_results.get('meets_criteria', False) else '❌ NO'}")
    
else:
    print("⚠️  No training summary found - training may have been interrupted")

# Check production models
print(f"\n{'='*80}")
print("PRODUCTION MODELS")
print(f"{'='*80}\n")

prod_dir = Path("models/production")
if prod_dir.exists():
    prod_model = prod_dir / "ats_model.joblib"
    prod_fe = prod_dir / "feature_engineer.joblib"
    prod_meta = prod_dir / "model_metadata.json"
    
    if prod_model.exists():
        print(f"✅ Production Model: {prod_model.name}")
    else:
        print("❌ Production Model: Not found")
    
    if prod_fe.exists():
        print(f"✅ Feature Engineer: {prod_fe.name}")
    else:
        print("❌ Feature Engineer: Not found")
    
    if prod_meta.exists():
        print(f"✅ Model Metadata: {prod_meta.name}")
        with open(prod_meta, 'r') as f:
            meta = json.load(f)
        
        print(f"\n  Model Name: {meta.get('model_name', 'N/A')}")
        print(f"  Timestamp: {meta.get('timestamp', 'N/A')}")
        print(f"  Features: {meta.get('feature_count', 0)}")
        print(f"  Optimal Threshold: {meta.get('optimal_threshold', 0.5):.4f}")
        
        test_metrics = meta.get('test_metrics', {})
        if test_metrics:
            print("\n  Test Set Performance:")
            for metric in ['recall', 'f1', 'roc_auc', 'precision', 'accuracy']:
                if metric in test_metrics:
                    print(f"    {metric.replace('_', ' ').title():<15} {test_metrics[metric]:.4f}")
    else:
        print("❌ Model Metadata: Not found")
else:
    print("❌ Production directory not found")

print(f"\n{'='*80}\n")
