import pandas as pd
import numpy as np
import re
from sklearn.base import BaseEstimator, TransformerMixin

class FeatureEngineer(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        df = X.copy()
        
        # 2.1 Skills Semantics
        # Skill Clean & Count
        df['Skills_Clean'] = df['Skills'].astype(str).apply(self._clean_skills)
        df['Skill_Count'] = df['Skills'].astype(str).apply(lambda x: len(x.split(',')) if x != 'nan' else 0)
        
        # 2.2 Structured Feature Enhancement
        
        # Certifications: Impact Score
        # Logic: simple presence = 1, specialized (contains 'Certified' or 'Specialization') = 2
        df['Cert_Count'] = df['Certifications'].astype(str).apply(lambda x: 0 if x in ['None', 'nan'] else 1)
        df['Cert_Impact'] = df['Certifications'].astype(str).apply(self._calc_cert_score)
        
        # Seniority Index: Experience + Role Mapping
        # Map roles to a base level
        role_map = {
            'Software Engineer': 1,
            'Cybersecurity Analyst': 1.2,
            'Data Scientist': 1.5,
            'AI Researcher': 1.8
        }
        df['Role_Level'] = df['Job Role'].map(role_map).fillna(1.0)
        df['Seniority_Index'] = df['Experience (Years)'] * df['Role_Level']
        
        # Experience-Weighted Skill Score
        # More skills matter more if you have experience to back them
        df['Exp_Weighted_Skills'] = df['Skill_Count'] * (np.log1p(df['Experience (Years)']))
        
        # Project Intensity Score
        # Projects per year of experience (handle div/0)
        df['Project_Intensity'] = df['Projects Count'] / (df['Experience (Years)'] + 1)
        
        # Salary-to-Experience Ratio ("Value Density")
        df['Value_Density'] = df['Salary Expectation ($)'] / (df['Experience (Years)'] + 1)
        
        # Drop raw text columns not needed for numeric correlation checking?
        # We keep them for now, Pipeline will select columns.
        
        return df

    def _clean_skills(self, text):
        if pd.isnull(text): return ""
        text = text.lower()
        text = re.sub(r'[^\w\s,]', '', text)
        return text

    def _calc_cert_score(self, text):
        if text in ['None', 'nan', '']:
            return 0
        score = 1
        text = text.lower()
        if 'certified' in text or 'specialization' in text:
            score += 1
        if 'google' in text or 'aws' in text: # Premium providers
            score += 1
        return score
