"""
Data Loader for ATS Resume Dataset

Handles loading, cleaning, and stratified train/val/test splitting.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from typing import Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ATSDataLoader:
    """Load and split ATS resume dataset with stratified sampling"""
    
    def __init__(self, data_path: str = "resumes.csv"):
        """
        Initialize data loader.
        
        Args:
            data_path: Path to the CSV file containing resume data
        """
        self.data_path = data_path
        self.df = None
        
    def load_data(self, exclude_ai_score: bool = True) -> pd.DataFrame:
        """
        Load and clean the dataset.
        
        Args:
            exclude_ai_score: Whether to exclude AI Score column (default True to prevent leakage)
            
        Returns:
            Cleaned dataframe
        """
        logger.info(f"Loading data from {self.data_path}...")
        
        try:
            self.df = pd.read_csv(self.data_path, encoding='utf-8')
        except UnicodeDecodeError:
            self.df = pd.read_csv(self.data_path, encoding='latin-1')
        
        logger.info(f"Loaded {len(self.df)} records with {len(self.df.columns)} columns")
        
        # Normalize column names
        column_mapping = {
            'Experience (Years)': 'Experience',
            'Salary Expectation ($)': 'Salary',
            'AI Score (0-100)': 'AI Score'
        }
        self.df.rename(columns=column_mapping, inplace=True)
        
        # Exclude AI Score to prevent data leakage
        if exclude_ai_score and 'AI Score' in self.df.columns:
            logger.warning("⚠️  Excluding 'AI Score' column to prevent data leakage")
            self.df = self.df.drop(columns=['AI Score'])
        
        # Basic cleaning
        logger.info("Cleaning data...")
        
        # Remove duplicates
        initial_count = len(self.df)
        self.df = self.df.drop_duplicates()
        if len(self.df) < initial_count:
            logger.info(f"Removed {initial_count - len(self.df)} duplicate records")
        
        # Handle missing values in target
        if 'Recruiter Decision' in self.df.columns:
            self.df = self.df.dropna(subset=['Recruiter Decision'])
            logger.info(f"Final dataset: {len(self.df)} records")
        
        # Display class distribution
        if 'Recruiter Decision' in self.df.columns:
            class_dist = self.df['Recruiter Decision'].value_counts()
            logger.info(f"Class distribution:\n{class_dist}")
            logger.info(f"Class balance: {class_dist.min() / class_dist.max() * 100:.1f}%")
        
        return self.df
    
    def split_data(
        self, 
        test_size: float = 0.15, 
        val_size: float = 0.15, 
        random_state: int = 42
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Create stratified train/val/test splits.
        
        Args:
            test_size: Proportion of data for test set (default 0.15)
            val_size: Proportion of remaining data for validation set (default 0.15)
            random_state: Random seed for reproducibility
            
        Returns:
            train_df, val_df, test_df
        """
        if self.df is None:
            raise RuntimeError("Must call load_data() before split_data()")
        
        if 'Recruiter Decision' not in self.df.columns:
            raise ValueError("Target column 'Recruiter Decision' not found")
        
        logger.info(f"Splitting data: train={1-test_size-val_size:.0%}, val={val_size:.0%}, test={test_size:.0%}")
        
        # First split: separate test set
        train_val_df, test_df = train_test_split(
            self.df,
            test_size=test_size,
            stratify=self.df['Recruiter Decision'],
            random_state=random_state
        )
        
        # Second split: separate validation from training
        val_size_adjusted = val_size / (1 - test_size)  # Adjust proportion
        train_df, val_df = train_test_split(
            train_val_df,
            test_size=val_size_adjusted,
            stratify=train_val_df['Recruiter Decision'],
            random_state=random_state
        )
        
        # Log split statistics
        logger.info(f"✅ Split complete:")
        logger.info(f"  Train: {len(train_df)} samples ({len(train_df)/len(self.df)*100:.1f}%)")
        logger.info(f"  Val:   {len(val_df)} samples ({len(val_df)/len(self.df)*100:.1f}%)")
        logger.info(f"  Test:  {len(test_df)} samples ({len(test_df)/len(self.df)*100:.1f}%)")
        
        # Verify stratification
        for name, df in [('Train', train_df), ('Val', val_df), ('Test', test_df)]:
            hire_pct = (df['Recruiter Decision'] == 'Hire').sum() / len(df) * 100
            logger.info(f"  {name} Hire%: {hire_pct:.1f}%")
        
        return train_df, val_df, test_df
    
    def get_X_y(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Separate features and target.
        
        Args:
            df: Input dataframe
            
        Returns:
            X (features), y (target)
        """
        if 'Recruiter Decision' not in df.columns:
            raise ValueError("Target column 'Recruiter Decision' not found")
        
        y = df['Recruiter Decision'].map({'Reject': 0, 'Hire': 1})
        X = df.drop(columns=['Recruiter Decision'])
        
        return X, y
