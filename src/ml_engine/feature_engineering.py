"""
Feature Engineering for ATS Resume Screening

Handles feature extraction, encoding, and transformation for resume data.
Excludes AI Score to prevent data leakage.
"""

import re
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Feature engineering pipeline for ATS resume scoring.
    
    Features engineered:
    - Skills: 14 binary features + skill count
    - Education: Ordinal encoding (High School=0, Bachelor=1, Master=2, PhD=3)
    - Certifications: One-hot encoding
    - Job Role: One-hot encoding
    - Experience: Raw + squared + log
    - Projects: Count + years_per_project
    - Salary: Raw + log + normalized
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.education_encoder = LabelEncoder()
        self.cert_encoder = None
        self.role_encoder = None
        self.skill_keywords = [
            'python', 'java', 'javascript', 'sql', 'machine learning',
            'deep learning', 'data analysis', 'aws', 'docker', 'kubernetes',
            'react', 'node', 'tensorflow', 'pytorch'
        ]
        self.education_order = ['High School', 'Bachelor', 'Master', 'PhD']
        self.fitted = False
        
    def _parse_skills(self, skills_text: str) -> Dict[str, int]:
        """Extract binary skill features from text"""
        if pd.isna(skills_text):
            skills_text = ""
        
        skills_lower = str(skills_text).lower()
        features = {}
        
        # Binary features for each keyword
        for skill in self.skill_keywords:
            features[f'has_{skill.replace(" ", "_")}'] = int(skill in skills_lower)
        
        # Skill count (number of commas + 1, assuming comma-separated)
        skill_count = len([s.strip() for s in str(skills_text).split(',') if s.strip()])
        features['skill_count'] = skill_count
        
        return features
    
    def _encode_education(self, education_series: pd.Series, fit: bool = False) -> np.ndarray:
        """Ordinal encoding for education levels"""
        # Map to ordered categories
        education_mapped = education_series.map(
            lambda x: self.education_order.index(x) if x in self.education_order else 1
        )
        return education_mapped.values.reshape(-1, 1)
    
    def _create_numerical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create engineered numerical features"""
        features = pd.DataFrame()
        
        # Experience features
        features['experience'] = df['Experience'].fillna(0)
        features['experience_squared'] = features['experience'] ** 2
        features['experience_log'] = np.log1p(features['experience'])
        
        # Projects features
        features['projects_count'] = df['Projects Count'].fillna(0)
        features['years_per_project'] = np.where(
            features['projects_count'] > 0,
            features['experience'] / features['projects_count'],
            0
        )
        
        # Salary features
        features['salary'] = df['Salary'].fillna(df['Salary'].median() if not df['Salary'].isna().all() else 50000)
        features['salary_log'] = np.log1p(features['salary'])
        
        return features
    
    def fit_transform(self, df: pd.DataFrame, exclude_ai_score: bool = True) -> Tuple[np.ndarray, List[str]]:
        """
        Fit the feature engineering pipeline and transform data.
        
        Args:
            df: Input dataframe with resume data
            exclude_ai_score: Whether to exclude AI Score feature (default True to prevent leakage)
            
        Returns:
            Transformed feature matrix and feature names
        """
        logger.info("Starting feature engineering (fit_transform)...")
        
        # Normalize column names (handle variations)
        df = df.copy().reset_index(drop=True)
        column_mapping = {
            'Experience (Years)': 'Experience',
            'Salary Expectation ($)': 'Salary',
            'AI Score (0-100)': 'AI Score'
        }
        df.rename(columns=column_mapping, inplace=True)
        
        # Validate required columns
        required_cols = ['Skills', 'Experience', 'Education', 'Certifications', 
                        'Job Role', 'Projects Count', 'Salary']
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # 1. Skills features
        logger.info("Extracting skill features...")
        skills_df = pd.DataFrame([self._parse_skills(text) for text in df['Skills']]).reset_index(drop=True)
        
        # 2. Education encoding
        logger.info("Encoding education levels...")
        education_encoded = self._encode_education(df['Education'], fit=True)
        education_df = pd.DataFrame(education_encoded, columns=['education_level']).reset_index(drop=True)
        
        # 3. Certifications one-hot encoding
        logger.info("Encoding certifications...")
        cert_dummies = pd.get_dummies(df['Certifications'], prefix='cert').reset_index(drop=True)
        self.cert_encoder = cert_dummies.columns.tolist()
        
        # 4. Job Role one-hot encoding
        logger.info("Encoding job roles...")
        role_dummies = pd.get_dummies(df['Job Role'], prefix='role').reset_index(drop=True)
        self.role_encoder = role_dummies.columns.tolist()
        
        # 5. Numerical features
        logger.info("Creating numerical features...")
        numerical_features = self._create_numerical_features(df).reset_index(drop=True)
        
        # Combine all features
        all_features = pd.concat([
            skills_df,
            education_df,
            cert_dummies,
            role_dummies,
            numerical_features
        ], axis=1)
        
        # Get feature names before scaling
        self.feature_names = all_features.columns.tolist()
        
        # Scale numerical features
        logger.info("Scaling features...")
        numerical_cols = numerical_features.columns.tolist()
        numerical_indices = [all_features.columns.tolist().index(col) for col in numerical_cols]
        
        X = all_features.values
        X[:, numerical_indices] = self.scaler.fit_transform(X[:, numerical_indices])
        
        self.fitted = True
        logger.info(f"✅ Feature engineering complete. Shape: {X.shape}, Features: {len(self.feature_names)}")
        
        return X, self.feature_names
    
    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """
        Transform new data using fitted pipeline.
        
        Args:
            df: Input dataframe with resume data
            
        Returns:
            Transformed feature matrix
        """
        if not self.fitted:
            raise RuntimeError("FeatureEngineer must be fitted before transform. Call fit_transform first.")
        
        logger.info("Transforming data with fitted pipeline...")
        
        # Normalize column names (handle variations)
        df = df.copy().reset_index(drop=True)
        column_mapping = {
            'Experience (Years)': 'Experience',
            'Salary Expectation ($)': 'Salary',
            'AI Score (0-100)': 'AI Score'
        }
        df.rename(columns=column_mapping, inplace=True)
        
        # 1. Skills features
        skills_df = pd.DataFrame([self._parse_skills(text) for text in df['Skills']]).reset_index(drop=True)
        
        # 2. Education encoding
        education_encoded = self._encode_education(df['Education'], fit=False)
        education_df = pd.DataFrame(education_encoded, columns=['education_level']).reset_index(drop=True)
        
        # 3. Certifications one-hot encoding (ensure same columns)
        cert_dummies = pd.get_dummies(df['Certifications'], prefix='cert').reset_index(drop=True)
        for col in self.cert_encoder:
            if col not in cert_dummies.columns:
                cert_dummies[col] = 0
        cert_dummies = cert_dummies[self.cert_encoder]
        
        # 4. Job Role one-hot encoding (ensure same columns)
        role_dummies = pd.get_dummies(df['Job Role'], prefix='role').reset_index(drop=True)
        for col in self.role_encoder:
            if col not in role_dummies.columns:
                role_dummies[col] = 0
        role_dummies = role_dummies[self.role_encoder]
        
        # 5. Numerical features
        numerical_features = self._create_numerical_features(df).reset_index(drop=True)
        
        # Combine all features
        all_features = pd.concat([
            skills_df,
            education_df,
            cert_dummies,
            role_dummies,
            numerical_features
        ], axis=1)
        
        # Scale numerical features
        numerical_cols = [col for col in numerical_features.columns if col in all_features.columns]
        numerical_indices = [all_features.columns.tolist().index(col) for col in numerical_cols]
        
        X = all_features.values
        X[:, numerical_indices] = self.scaler.transform(X[:, numerical_indices])
        
        logger.info(f"✅ Transform complete. Shape: {X.shape}")
        
        return X
