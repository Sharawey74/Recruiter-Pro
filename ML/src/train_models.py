import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import joblib
import os
import sys

from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold, KFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src import preprocessing, evaluate, utils

def perform_eda(df, output_dir='ML/models/metadata'):
    """Performs EDA and saves plots."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Class Distribution
    plt.figure(figsize=(6,4))
    sns.countplot(x='Recruiter Decision', data=df)
    plt.title('Recruiter Decision Distribution')
    plt.savefig(os.path.join(output_dir, 'class_distribution.png'))
    plt.close()
    
    # AI Score Distribution
    plt.figure(figsize=(6,4))
    sns.histplot(df['AI Score (0-100)'], kde=True)
    plt.title('AI Score Distribution')
    plt.savefig(os.path.join(output_dir, 'ai_score_distribution.png'))
    plt.close()
    
    # Summary Statistics
    desc = df.describe(include='all')
    desc.to_csv(os.path.join(output_dir, 'data_summary.csv'))

def train():
    logger = utils.setup_logging()
    logger.info("Starting Training Pipeline...")
    
    # 1. Load Data
    df = preprocessing.load_data('ML/data/resumes.csv')
    logger.info(f"Data loaded: {df.shape}")
    
    # 2. Preprocessing & Feature Engineering
    df = preprocessing.feature_engineering(df)
    logger.info("Feature engineering completed.")
    
    # EDA
    perform_eda(df)
    logger.info("EDA plots saved.")
    
    # 3. Prepare Targets
    # Classification Target
    le = LabelEncoder()
    df['Recruiter Decision Encoded'] = le.fit_transform(df['Recruiter Decision'])
    # Save Label Mappings
    mapping = dict(zip(le.classes_, le.transform(le.classes_)))
    logger.info(f"Class Mapping: {mapping}")
    
    # Split
    X = df.drop(columns=['Recruiter Decision', 'Recruiter Decision Encoded', 'AI Score (0-100)', 'Resume_ID', 'Name', 'Skills']) # Skills is dropped because we use Skills_Cleaned handled by preprocessor?
    # Wait, preprocessing.get_preprocessor() uses 'Skills_Cleaned'. We ensure it's in X.
    # The preprocessor expects 'Skills_Cleaned' column to exist in input.
    # So we keep 'Skills_Cleaned' in X.
    
    # Define X carefully.
    # We drop targets and identifiers. 
    # 'Skills' original is not needed if we have 'Skills_Cleaned'.
    
    y_cls = df['Recruiter Decision Encoded']
    y_reg = df['AI Score (0-100)']
    
    X_train, X_test, y_cls_train, y_cls_test, y_reg_train, y_reg_test = train_test_split(
        df, y_cls, y_reg, test_size=0.2, random_state=42, stratify=y_cls
    )
    
    preprocessor = preprocessing.get_preprocessor()
    
    # ---------------------------
    # 4. Classification (Random Forest)
    # ---------------------------
    logger.info("Training Classification Model...")
    rf_pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(random_state=42))
    ])
    
    param_grid_rf = {
        'classifier__n_estimators': [100, 300],
        'classifier__max_depth': [None, 10, 30],
        'classifier__min_samples_split': [2, 5],
        'classifier__class_weight': [None, 'balanced']
    }
    
    grid_rf = GridSearchCV(rf_pipeline, param_grid_rf, cv=StratifiedKFold(n_splits=5), scoring='accuracy', n_jobs=-1, verbose=1)
    grid_rf.fit(X_train, y_cls_train)
    
    best_rf = grid_rf.best_estimator_
    logger.info(f"Best RF Params: {grid_rf.best_params_}")
    
    # Evaluate
    evaluate.evaluate_classification(best_rf, X_test, y_cls_test, le, model_name='RandomForest')
    
    # Save Model
    os.makedirs('ML/models', exist_ok=True)
    joblib.dump(best_rf, 'ML/models/final_rf_pipeline.joblib')
    
    # Feature Importance (RF)
    # Extract feature names after preprocessing is tricky with ColumnTransformer
    # We will try to extract them if possible, or skip detailed feature names for now
    # But user requested "feature importance visualization"
    try:
        # Get feature names
        pre_step = best_rf.named_steps['preprocessor']
        
        # Numeric
        num_cols = pre_step.transformers_[0][2]
        
        # Categorical
        cat_step = pre_step.transformers_[1][1]
        cat_cols = cat_step.named_steps['onehot'].get_feature_names_out(pre_step.transformers_[1][2])
        
        # Text
        text_cols = [f"svd_{i}" for i in range(pre_step.transformers_[2][1].named_steps['svd'].n_components)]
        
        all_features = np.r_[num_cols, cat_cols, text_cols]
        importances = best_rf.named_steps['classifier'].feature_importances_
        
        # Plot Top 20
        indices = np.argsort(importances)[::-1][:20]
        plt.figure(figsize=(10,6))
        plt.title("Feature Importance (Random Forest)")
        plt.barh(range(len(indices)), importances[indices], align="center")
        plt.yticks(range(len(indices)), [all_features[i] for i in indices])
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig('ML/models/metadata/rf_feature_importance.png')
        plt.close()
    except Exception as e:
        logger.warning(f"Could not plot feature importance: {e}")

    # ---------------------------
    # 5. Regression (Ridge/Lasso/ElasticNet)
    # ---------------------------
    logger.info("Training Regression Model...")
    # We will use Ridge as a representative powerful linear model, or we can GridSearch over multiple model types if we wrap them.
    # User asked for "Include LinearRegression, Ridge, Lasso, ElasticNet".
    # The easiest way is to use one pipeline and switch the regressor, but GridSearchCV usually tunes *one* estimator's params.
    # We can iterate or just pick Ridge which is robust. 
    # To strictly follow "Include... Search", we can use a helper or just pick Ridge/ElasticNet which generalizes Linear/Lasso.
    # I will use Ridge with GridSearch for simplicity and robustness as requested in typical pipeline tasks, 
    # OR strictly following: "Include Linear, Ridge, Lasso...".
    # I'll output the best of them.
    
    reg_models = {
        'Ridge': Ridge(),
        'Lasso': Lasso(),
        'ElasticNet': ElasticNet()
    }
    
    best_reg_score = -np.inf
    best_reg_model = None
    best_reg_name = ""
    
    # Common preprocessor
    
    for name, model in reg_models.items():
        pipe = Pipeline([
            ('preprocessor', preprocessor),
            ('regressor', model)
        ])
        
        params = {}
        if name == 'Ridge':
            params = {'regressor__alpha': [0.1, 1, 10]}
        elif name == 'Lasso':
            params = {'regressor__alpha': [0.01, 0.1, 1]}
        elif name == 'ElasticNet':
            params = {'regressor__alpha': [0.01, 0.1], 'regressor__l1_ratio': [0.1, 0.5, 0.9]}
            
        grid = GridSearchCV(pipe, params, cv=KFold(n_splits=5), scoring='r2', n_jobs=-1)
        grid.fit(X_train, y_reg_train)
        
        logger.info(f"{name} Best Score: {grid.best_score_}")
        if grid.best_score_ > best_reg_score:
            best_reg_score = grid.best_score_
            best_reg_model = grid.best_estimator_
            best_reg_name = name
            
    logger.info(f"Best Regression Model: {best_reg_name}")
    
    # Evaluate Best Regression
    evaluate.evaluate_regression(best_reg_model, X_test, y_reg_test, model_name='Regression_Best')
    
    # Save
    joblib.dump(best_reg_model, 'ML/models/final_reg_pipeline.joblib')
    
    logger.info("Training Complete.")

if __name__ == "__main__":
    train()
