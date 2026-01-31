"""
ML Engine for ATS (Applicant Tracking System) Resume Scoring

This module provides machine learning capabilities for automated resume screening
using ensemble methods (Logistic Regression, Random Forest, XGBoost) with 
comprehensive evaluation criteria and cross-validation.

Components:
- feature_engineering: Feature extraction and preprocessing
- data_loader: Dataset loading and stratified splitting  
- evaluation_criteria: Evaluation metrics and performance criteria
- cross_validation: Cross-validation strategies and diagnostics
- model_trainer: Model training with hyperparameter tuning
- ats_predictor: Production prediction wrapper
"""

__version__ = "1.0.0"

from .ats_predictor import ATSPredictor

__all__ = ["ATSPredictor"]
