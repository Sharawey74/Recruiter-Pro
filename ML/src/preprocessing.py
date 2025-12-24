import pandas as pd
import numpy as np
import re
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder, FunctionTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.impute import SimpleImputer

def load_data(filepath='ML/data/resumes.csv'):
    """Loads the dataset from CSV."""
    df = pd.read_csv(filepath)
    return df

def clean_text(text):
    """Cleans text by lowercasing and removing punctuation."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s,]', '', text) # Keep commas for skill separation if needed, but usually we just want words
    return text

def feature_engineering(df):
    """Generates new features from existing columns."""
    df = df.copy()
    
    # Clean Skills
    df['Skills_Cleaned'] = df['Skills'].apply(clean_text)
    
    # Skill Count
    df['skill_count'] = df['Skills'].apply(lambda x: len(str(x).split(',')) if pd.notnull(x) else 0)
    
    # Has Certification
    df['has_cert'] = df['Certifications'].apply(lambda x: 0 if str(x).strip() == 'None' or pd.isnull(x) else 1)
    
    # Seniority Bucket
    def get_seniority(years):
        if years <= 2: return 'Entry'
        elif years <= 5: return 'Mid'
        elif years <= 10: return 'Senior'
        else: return 'Expert'
    
    df['seniority_bucket'] = df['Experience (Years)'].apply(get_seniority)
    
    return df

def get_preprocessor():
    """Returns the ColumnTransformer for preprocessing."""
    
    # Numeric Features
    numeric_features = ['Experience (Years)', 'Salary Expectation ($)', 'Projects Count', 'skill_count', 'has_cert']
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    # Categorical Features
    categorical_features = ['Education', 'Job Role', 'seniority_bucket']
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])
    
    # Text Features (Skills)
    text_features = 'Skills_Cleaned'
    text_transformer = Pipeline(steps=[
        ('tfidf', TfidfVectorizer(max_features=500, stop_words='english')),
        ('svd', TruncatedSVD(n_components=10)) # Reduce dimensions
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features),
            ('text', text_transformer, text_features)
        ]
    )
    
    return preprocessor
