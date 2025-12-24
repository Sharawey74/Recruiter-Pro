import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix,
    mean_squared_error, mean_absolute_error, r2_score
)
import os
import sys

# Add src to path if needed for direct execution, though module run is preferred
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils import save_json, save_text

def evaluate_classification(model, X_test, y_test, label_encoder, model_name='RandomForest', output_dir='ML/models/metadata'):
    """Evaluates classification model and saves metrics/plots."""
    os.makedirs(output_dir, exist_ok=True)
    
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else None
    
    # Metrics
    # Note: 'Hire' might be mapped to 0 or 1. Let's assume label_encoder handled it.
    # usually Hire is positive class (1). We need to check label mapping.
    # For automated metric calculation we might need to know which is pos_label.
    # We will assume binary classification for now.
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average='weighted')
    rec = recall_score(y_test, y_pred, average='weighted')
    f1 = f1_score(y_test, y_pred, average='weighted')
    
    metrics = {
        "Accuracy": acc,
        "Precision": prec,
        "Recall": rec,
        "F1 Score": f1
    }
    
    if y_prob is not None and len(np.unique(y_test)) == 2:
        try:
             roc = roc_auc_score(y_test, y_prob)
             metrics["ROC_AUC"] = roc
        except:
             metrics["ROC_AUC"] = "N/A (Multi-class or Error)"

    # Save JSON
    save_json(metrics, os.path.join(output_dir, f'{model_name}_metrics.json'))
    
    # Save Text
    txt_report = f"Classification Report for {model_name}:\n"
    for k, v in metrics.items():
        txt_report += f"{k}: {v}\n"
    
    cm = confusion_matrix(y_test, y_pred)
    txt_report += f"\nConfusion Matrix:\n{cm}\n"
    save_text(txt_report, os.path.join(output_dir, f'{model_name}_metrics.txt'))
    
    # Confusion Matrix Plot
    plt.figure(figsize=(6,5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title(f'Confusion Matrix - {model_name}')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.savefig(os.path.join(output_dir, f'{model_name}_confusion_matrix.png'))
    plt.close()
    
    return metrics

def evaluate_regression(model, X_test, y_test, model_name='Regression', output_dir='ML/models/metadata'):
    """Evaluates regression model and saves metrics/plots."""
    os.makedirs(output_dir, exist_ok=True)
    
    y_pred = model.predict(X_test)
    
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    metrics = {
        "RMSE": rmse,
        "MAE": mae,
        "R2 Score": r2
    }
    
    # Save JSON
    save_json(metrics, os.path.join(output_dir, f'{model_name}_metrics.json'))
    
    # Save Text
    txt_report = f"Regression Report for {model_name}:\n"
    for k, v in metrics.items():
        txt_report += f"{k}: {v}\n"
    save_text(txt_report, os.path.join(output_dir, f'{model_name}_metrics.txt'))
    
    # Residual Plot
    residuals = y_test - y_pred
    plt.figure(figsize=(8,6))
    plt.scatter(y_pred, residuals, alpha=0.5)
    plt.xlabel('Predicted Values')
    plt.ylabel('Residuals')
    plt.title(f'Residual Plot - {model_name}')
    plt.axhline(y=0, color='r', linestyle='--')
    plt.savefig(os.path.join(output_dir, f'{model_name}_residuals.png'))
    plt.close()
    
    return metrics
