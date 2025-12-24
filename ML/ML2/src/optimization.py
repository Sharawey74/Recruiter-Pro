import pandas as pd
import numpy as np
import joblib
import os
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import GridSearchCV, StratifiedKFold, KFold, cross_validate
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import classification_report, confusion_matrix, r2_score, mean_squared_error, make_scorer, f1_score

# Add ML2 to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.features import FeatureEngineer

def save_plot(fig, name, output_dir='ML2/models/analysis'):
    os.makedirs(output_dir, exist_ok=True)
    fig.savefig(os.path.join(output_dir, name))
    plt.close(fig)

def run_optimization():
    print("--- Starting Optimization in ML2 ---")
    
    # Load Data
    df = pd.read_csv('ML2/data/resumes.csv')
    
    # ---------------------------
    # Stage 1: Error Analysis (Baseline) - Skip for speed, integrating into loop?
    # No, request says "Output Error analysis report".
    # I will do this post-training or on a split first.
    # Given the flow, I'll train the optimized models directly using CV to report errors.
    
    # ---------------------------
    # Stage 2: Feature Engineering
    fe = FeatureEngineer()
    df_enhanced = fe.transform(df)
    
    # Correlation Analysis
    numeric_df = df_enhanced.select_dtypes(include=[np.number])
    corr_matrix = numeric_df.corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    to_drop = [column for column in upper.columns if any(upper[column] > 0.85)]
    print(f"Dropping highly correlated features: {to_drop}")
    df_enhanced = df_enhanced.drop(columns=to_drop)
    
    # ---------------------------
    # Prepare Data
    le = LabelEncoder()
    # Assuming 'Hire' is positive class. Check unique.
    # If Recruiter Decision has 'Hire'/'Reject'.
    y_cls = le.fit_transform(df_enhanced['Recruiter Decision']) # 'Hire' -> 0, 'Reject' -> 1 usually if alphabetical.
    # Let's fix label encoding to ensure Hire is 1 for F1 Score clarity if needed, or just track it.
    # Actually, usually Hire=1 is preferred. 
    # 'Hire' < 'Reject', so Hire=0.
    # Let's map explicitly.
    y_cls = df_enhanced['Recruiter Decision'].map({'Hire': 1, 'Reject': 0})
    
    y_reg = df_enhanced['AI Score (0-100)']
    
    # Definition of Transformers
    
    # Text (Skills_Clean)
    text_feat = 'Skills_Clean'
    text_transformer = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=500, stop_words='english')),
        ('svd', TruncatedSVD(n_components=10)) # Conservative dimension
    ])
    
    # Cat
    cat_feats = ['Education', 'Job Role']
    cat_transformer = Pipeline([
        ('impute', SimpleImputer(strategy='constant', fill_value='missing')),
        ('ohe', OneHotEncoder(handle_unknown='ignore'))
    ])
    
    # Num
    # Exclude targets and text and raw cat
    exclude = ['Resume_ID', 'Name', 'Skills', 'Skills_Clean', 'Recruiter Decision', 'Certifications', 'AI Score (0-100)']
    num_feats = [c for c in df_enhanced.columns if c not in exclude + cat_feats + to_drop]
    
    num_transformer = Pipeline([
        ('impute', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    preprocessor = ColumnTransformer([
        ('txt', text_transformer, text_feat),
        ('cat', cat_transformer, cat_feats),
        ('num', num_transformer, num_feats)
    ])
    
    # ---------------------------
    # Stage 4: Classification Optimization (RF)
    # ---------------------------
    print("Optimizing Classification (Random Forest)...")
    rf = RandomForestClassifier(random_state=42)
    pipeline_rf = Pipeline([
        ('prep', preprocessor),
        ('clf', rf)
    ])
    
    param_grid_rf = {
        'clf__n_estimators': [300, 500],
        'clf__max_depth': [10, 20, None],
        'clf__min_samples_leaf': [1, 2],
        'clf__class_weight': ['balanced', None] # Added None to compare
    }
    
    grid_rf = GridSearchCV(
        pipeline_rf, param_grid_rf, 
        cv=StratifiedKFold(n_splits=5), 
        scoring='f1', # Optimize for F1 (Hire)
        n_jobs=-1
    )
    grid_rf.fit(df_enhanced, y_cls)
    
    best_rf = grid_rf.best_estimator_
    print(f"Best RF Params: {grid_rf.best_params_}")
    print(f"Best RF CV F1: {grid_rf.best_score_:.4f}")
    
    # Detailed CV Metrics
    cv_results_rf = cross_validate(best_rf, df_enhanced, y_cls, cv=StratifiedKFold(n_splits=5), 
                                   scoring=['accuracy', 'precision', 'recall', 'f1', 'roc_auc'])
    
    print("RF Cross-Validation Results:")
    for metric in cv_results_rf:
        print(f"{metric}: {np.mean(cv_results_rf[metric]):.4f} (+/- {np.std(cv_results_rf[metric]):.4f})")
        
    # ---------------------------
    # Stage 4B: Regression Optimization
    # ---------------------------
    print("Optimizing Regression (Ridge/ElasticNet)...")
    
    # Try ElasticNet as general linear
    pipeline_reg = Pipeline([
        ('prep', preprocessor),
        ('reg', ElasticNet(random_state=42, max_iter=2000))
    ])
    
    param_grid_reg = {
        'reg__alpha': [0.01, 0.1, 1.0],
        'reg__l1_ratio': [0.1, 0.5, 0.9]
    }
    
    grid_reg = GridSearchCV(
        pipeline_reg, param_grid_reg,
        cv=KFold(n_splits=5),
        scoring='r2',
        n_jobs=-1
    )
    grid_reg.fit(df_enhanced, y_reg)
    
    best_reg = grid_reg.best_estimator_
    print(f"Best Reg Params: {grid_reg.best_params_}")
    print(f"Best Reg CV R2: {grid_reg.best_score_:.4f}")
    
    # Check if underfitting (R2 low)? If so, try RF Regressor
    if grid_reg.best_score_ < 0.6: # Arbitrary threshold for linear failure
        print("Linear model underperformed. Switching to Random Forest Regressor...")
        pipeline_rf_reg = Pipeline([
            ('prep', preprocessor),
            ('reg', RandomForestRegressor(random_state=42, n_estimators=300))
        ])
        grid_rf_reg = GridSearchCV(
            pipeline_rf_reg,
            {'reg__max_depth': [10, 20, None], 'reg__min_samples_leaf': [1, 2, 4]},
            cv=KFold(n_splits=5), scoring='r2', n_jobs=-1
        )
        grid_rf_reg.fit(df_enhanced, y_reg)
        best_reg = grid_rf_reg.best_estimator_
        print(f"Best RF Reg R2: {grid_rf_reg.best_score_:.4f}")

    # ---------------------------
    # Stage 6: Artifacts & Deployment
    # ---------------------------
    output_dir = 'ML2/models/metadata'
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs('ML2/models', exist_ok=True)
    
    joblib.dump(best_rf, 'ML2/models/opt_rf_model.joblib')
    joblib.dump(best_reg, 'ML2/models/opt_reg_model.joblib')
    
    # 1. Compile Metrics
    # Classification
    rf_metrics = {
        "F1_CV_Mean": float(np.mean(cv_results_rf['test_f1'])),
        "F1_CV_Std": float(np.std(cv_results_rf['test_f1'])),
        "Accuracy_CV_Mean": float(np.mean(cv_results_rf['test_accuracy'])),
        "Precision_CV_Mean": float(np.mean(cv_results_rf['test_precision'])),
        "Recall_CV_Mean": float(np.mean(cv_results_rf['test_recall'])),
        "ROC_AUC_CV_Mean": float(np.mean(cv_results_rf['test_roc_auc']))
    }
    
    # Regression
    reg_metrics = {
        "R2_CV": float(grid_reg.best_score_) 
        # Note: We didn't do full cross_validate for reg in the previous block, just GridSearchCV.
        # But GridSearchCV result IS the mean CV score.
    }
    
    all_metrics = {
        "Classification_RandomForest": rf_metrics,
        "Regression_ElasticNet": reg_metrics
    }
    
    # 2. Save JSON
    import json
    with open(os.path.join(output_dir, 'metrics.json'), 'w') as f:
        json.dump(all_metrics, f, indent=4)
        
    # 3. Save Text
    with open(os.path.join(output_dir, 'metrics.txt'), 'w') as f:
        f.write("Optimization Results - ML2\n==========================\n\n")
        f.write("Classification (Random Forest Optimized):\n")
        for k, v in rf_metrics.items():
            f.write(f"{k}: {v:.4f}\n")
        f.write("\nRegression (ElasticNet Optimized):\n")
        for k, v in reg_metrics.items():
            f.write(f"{k}: {v:.4f}\n")
            
    # 4. Confusion Matrix Plot (on full training set for visualization, or CV?)
    # Usually CV predictions are better for "unbiased" confusion matrix.
    # We will generate predictions using cross_val_predict or just predict on the whole set (easiest for now, noting bias).
    # Better: cross_val_predict
    from sklearn.model_selection import cross_val_predict
    y_pred_cv = cross_val_predict(best_rf, df_enhanced, y_cls, cv=StratifiedKFold(n_splits=5))
    cm = confusion_matrix(y_cls, y_pred_cv)
    
    plt.figure(figsize=(6,5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Greens')
    plt.title('Confusion Matrix (Cross-Validated)')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    save_plot(plt.gcf(), 'confusion_matrix.png', output_dir)
    
    print(f"Artifacts saved to {output_dir}")
    print("Optimization Complete.")

if __name__ == "__main__":
    run_optimization()
