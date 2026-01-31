"""
ATS Predictor - Production Wrapper for Resume Scoring

Loads trained model and provides clean prediction interface.
"""

import os
import joblib
import json
import pandas as pd
import numpy as np
from typing import Dict, Union, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ATSPredictor:
    """
    Production predictor for ATS resume scoring.
    
    Usage:
        predictor = ATSPredictor()
        predictor.load_model()
        result = predictor.predict(cv_data)
    """
    
    def __init__(self, model_dir: str = "models/production"):
        """
        Initialize predictor.
        
        Args:
            model_dir: Directory containing trained model and artifacts
        """
        self.model_dir = model_dir
        self.model = None
        self.feature_engineer = None
        self.metadata = None
        self.optimal_threshold = 0.5
        
    def load_model(self) -> bool:
        """
        Load trained model and artifacts.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load model
            model_path = os.path.join(self.model_dir, "ats_model.joblib")
            if not os.path.exists(model_path):
                logger.error(f"Model not found at {model_path}")
                return False
            
            self.model = joblib.load(model_path)
            logger.info(f"✅ Loaded model from {model_path}")
            
            # Load feature engineer
            feature_engineer_path = os.path.join(self.model_dir, "feature_engineer.joblib")
            if not os.path.exists(feature_engineer_path):
                logger.error(f"Feature engineer not found at {feature_engineer_path}")
                return False
            
            self.feature_engineer = joblib.load(feature_engineer_path)
            logger.info(f"✅ Loaded feature engineer from {feature_engineer_path}")
            
            # Load metadata
            metadata_path = os.path.join(self.model_dir, "model_metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                self.optimal_threshold = self.metadata.get('optimal_threshold', 0.5)
                logger.info(f"✅ Loaded metadata. Optimal threshold: {self.optimal_threshold:.4f}")
            else:
                logger.warning(f"Metadata not found at {metadata_path}. Using default threshold.")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def predict(
        self, 
        cv_data: Union[Dict, pd.DataFrame],
        use_optimal_threshold: bool = True
    ) -> Dict:
        """
        Predict hiring decision for a resume.
        
        Args:
            cv_data: Resume data (dict or DataFrame)
            use_optimal_threshold: Use optimal threshold for classification
            
        Returns:
            Dictionary with prediction, probability, score, and risk level
        """
        if self.model is None or self.feature_engineer is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        # Convert to DataFrame if dict
        if isinstance(cv_data, dict):
            cv_df = pd.DataFrame([cv_data])
        elif isinstance(cv_data, pd.DataFrame):
            cv_df = cv_data
        else:
            raise ValueError("cv_data must be dict or DataFrame")
        
        # Feature engineering
        X = self.feature_engineer.transform(cv_df)
        
        # Predict probability
        proba = self.model.predict_proba(X)[0, 1]  # Probability of "Hire"
        
        # Classify
        threshold = self.optimal_threshold if use_optimal_threshold else 0.5
        prediction = int(proba >= threshold)
        decision = "Hire" if prediction == 1 else "Reject"
        
        # Calculate ML score (0-100)
        ml_score = int(proba * 100)
        
        # Determine risk level
        if proba >= 0.8:
            risk_level = "Low Risk"
        elif proba >= 0.6:
            risk_level = "Medium Risk"
        else:
            risk_level = "High Risk"
        
        # Confidence
        confidence = max(proba, 1 - proba)
        
        result = {
            'decision': decision,
            'ml_score': ml_score,
            'probability': float(proba),
            'confidence': float(confidence),
            'risk_level': risk_level,
            'threshold_used': float(threshold),
            'model_name': self.metadata.get('model_name', 'Unknown') if self.metadata else 'Unknown'
        }
        
        return result
    
    def predict_batch(
        self,
        cv_data_list: Union[List[Dict], pd.DataFrame],
        use_optimal_threshold: bool = True
    ) -> List[Dict]:
        """
        Predict for multiple resumes.
        
        Args:
            cv_data_list: List of resume dicts or DataFrame
            use_optimal_threshold: Use optimal threshold for classification
            
        Returns:
            List of prediction dictionaries
        """
        if isinstance(cv_data_list, list):
            cv_df = pd.DataFrame(cv_data_list)
        else:
            cv_df = cv_data_list
        
        results = []
        for idx in range(len(cv_df)):
            cv_row = cv_df.iloc[idx:idx+1]
            result = self.predict(cv_row, use_optimal_threshold=use_optimal_threshold)
            results.append(result)
        
        return results
    
    def get_feature_importance(self, top_n: int = 20) -> Dict[str, float]:
        """
        Get feature importance from the trained model.
        
        Args:
            top_n: Number of top features to return
            
        Returns:
            Dictionary of feature names and importance scores
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        # Extract classifier from pipeline
        if hasattr(self.model, 'named_steps'):
            classifier = self.model.named_steps['classifier']
        else:
            classifier = self.model
        
        # Get feature importances
        if hasattr(classifier, 'feature_importances_'):
            # Tree-based models (RF, XGBoost)
            importances = classifier.feature_importances_
        elif hasattr(classifier, 'coef_'):
            # Linear models (LR)
            importances = np.abs(classifier.coef_[0])
        else:
            logger.warning("Model does not have feature importances")
            return {}
        
        # Get feature names
        feature_names = self.metadata.get('feature_names', []) if self.metadata else []
        
        if len(feature_names) != len(importances):
            logger.warning(f"Feature name count mismatch: {len(feature_names)} vs {len(importances)}")
            feature_names = [f"feature_{i}" for i in range(len(importances))]
        
        # Create importance dict
        importance_dict = dict(zip(feature_names, importances))
        
        # Sort and return top N
        sorted_importance = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
        top_features = dict(sorted_importance[:top_n])
        
        return top_features
    
    def get_model_info(self) -> Dict:
        """
        Get information about the loaded model.
        
        Returns:
            Model metadata dictionary
        """
        if self.metadata is None:
            return {'status': 'Metadata not available'}
        
        return {
            'model_name': self.metadata.get('model_name', 'Unknown'),
            'timestamp': self.metadata.get('timestamp', 'Unknown'),
            'feature_count': self.metadata.get('feature_count', 0),
            'optimal_threshold': self.metadata.get('optimal_threshold', 0.5),
            'test_metrics': self.metadata.get('test_metrics', {}),
            'meets_criteria': self.metadata.get('meets_criteria', False)
        }


# Convenience function for quick predictions
def predict_resume(cv_data: Union[Dict, pd.DataFrame], model_dir: str = "models/production") -> Dict:
    """
    Quick prediction function.
    
    Args:
        cv_data: Resume data (dict or DataFrame)
        model_dir: Directory containing trained model
        
    Returns:
        Prediction dictionary
    """
    predictor = ATSPredictor(model_dir=model_dir)
    if not predictor.load_model():
        raise RuntimeError("Failed to load model")
    
    return predictor.predict(cv_data)
