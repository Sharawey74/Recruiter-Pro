# ATS ML Engine

Production-ready machine learning pipeline for Applicant Tracking System (ATS) resume screening.

## Overview

The ML Engine provides automated resume scoring using ensemble methods with comprehensive evaluation criteria and cross-validation to prevent overfitting/underfitting.

### Architecture

```
src/ml_engine/
├── __init__.py                 # Module interface
├── data_loader.py              # Dataset loading & stratified splits
├── feature_engineering.py      # Feature extraction & preprocessing
├── evaluation_criteria.py      # Performance metrics & thresholds
├── cross_validation.py         # CV strategies & diagnostics
├── model_trainer.py            # Model training & hyperparameter tuning
├── train.py                    # Main training script
└── ats_predictor.py           # Production prediction wrapper
```

## Features

### 🎯 Evaluation Criteria (Built-in)
- **Primary Metric**: Recall >= 90% (minimize false negatives - don't miss qualified candidates)
- **Secondary Metrics**:
  - F1 Score >= 75% (balanced precision-recall)
  - ROC-AUC >= 0.85 (good discrimination)
  - Precision >= 70% (acceptable false positive rate)
  - Accuracy >= 80% (overall correctness)
- **Composite Scoring**: Weighted combination for model selection
- **Business Metrics**: False negative rate, false positive rate, specificity

### 🔧 Feature Engineering
- **Skills**: 14 binary features + skill count (Python, Java, SQL, ML, etc.)
- **Education**: Ordinal encoding (High School=0, Bachelor=1, Master=2, PhD=3)
- **Certifications**: One-hot encoding
- **Job Role**: One-hot encoding
- **Experience**: Raw + squared + log transformations
- **Projects**: Count + years_per_project ratio
- **Salary**: Raw + log + normalized
- **Data Leakage Prevention**: AI Score excluded from training

### 🤖 Models Trained
1. **Logistic Regression**
   - Regularization: L1, L2, ElasticNet
   - Hyperparameters: C=[0.001-100], l1_ratio=[0.3-0.7]
   
2. **Random Forest**
   - Regularization: max_depth, min_samples_split/leaf
   - Hyperparameters: n_estimators=[100-300], max_depth=[10-25]
   
3. **XGBoost**
   - Regularization: learning_rate, max_depth, gamma, reg_alpha/lambda
   - Hyperparameters: learning_rate=[0.01-0.1], max_depth=[3-7], gamma=[0-0.5]

### 🎲 Class Imbalance Handling
- **SMOTE**: Synthetic oversampling (sampling_strategy=0.7)
- **Class Weights**: Balanced class weights for all models
- **Stratified Splits**: Maintains class distribution in train/val/test

### 🔬 Cross-Validation & Regularization
- **Stratified K-Fold CV**: 5-fold with stratification
- **Learning Curves**: Detect underfitting/overfitting
- **Validation Curves**: Hyperparameter effect analysis
- **GridSearchCV/RandomizedSearchCV**: Exhaustive hyperparameter search
- **Early Stopping**: XGBoost regularization
- **Train-Val Gap Analysis**: Monitor overfitting indicators

## Quick Start

### 1. Train Models

Run the quick start script:

```bash
python train_ats_model.py
```

Or run the training script directly:

```bash
python src/ml_engine/train.py \
    --data-path resumes.csv \
    --output-dir models/experiments \
    --test-size 0.15 \
    --val-size 0.15 \
    --random-state 42 \
    --run-cv-analysis
```

### 2. Training Pipeline

The training pipeline executes 6 phases:

**Phase 1: Data Loading**
- Load resumes.csv (1,001 records)
- Exclude AI Score column (prevent leakage)
- Stratified split: 70% train, 15% val, 15% test

**Phase 2: Feature Engineering**
- Extract skills (14 binary + count)
- Encode education (ordinal)
- One-hot encode certifications & job roles
- Create numerical features (experience², log(salary), etc.)
- Scale numerical features

**Phase 3: Cross-Validation Analysis** (optional)
- 5-fold stratified CV for baseline models
- Generate learning curves (detect under/overfitting)
- Analyze variance (overfitting indicators)

**Phase 4: Model Training**
- Apply SMOTE for class balancing
- Train 3 models with hyperparameter tuning:
  - Logistic Regression (GridSearchCV)
  - Random Forest (RandomizedSearchCV, 50 iterations)
  - XGBoost (RandomizedSearchCV, 50 iterations)
- Evaluate on validation set
- Calculate composite scores

**Phase 5: Model Selection & Test Evaluation**
- Select best model by composite score
- Evaluate on held-out test set
- Find optimal classification threshold (target: 90% recall)
- Generate comprehensive evaluation report

**Phase 6: Save Production Artifacts**
- Save best model: `models/production/ats_model.joblib`
- Save feature engineer: `models/production/feature_engineer.joblib`
- Save metadata: `models/production/model_metadata.json`

### 3. Use Trained Model

```python
from src.ml_engine.ats_predictor import ATSPredictor

# Initialize predictor
predictor = ATSPredictor(model_dir="models/production")
predictor.load_model()

# Predict for a single CV
cv_data = {
    'Skills': 'Python, Machine Learning, SQL, Docker',
    'Experience': 5,
    'Education': 'Master',
    'Certifications': 'AWS Certified',
    'Job Role': 'Data Scientist',
    'Projects Count': 3,
    'Salary': 80000
}

result = predictor.predict(cv_data)
print(result)
# {
#     'decision': 'Hire',
#     'ml_score': 87,
#     'probability': 0.87,
#     'confidence': 0.87,
#     'risk_level': 'Low Risk',
#     'threshold_used': 0.32,
#     'model_name': 'Random Forest'
# }

# Get feature importance
importance = predictor.get_feature_importance(top_n=10)
print(importance)

# Get model info
info = predictor.get_model_info()
print(info)
```

### 4. Batch Prediction

```python
cv_list = [
    {'Skills': 'Java, Spring, SQL', 'Experience': 3, ...},
    {'Skills': 'Python, Django, React', 'Experience': 4, ...},
]

results = predictor.predict_batch(cv_list)
```

## Output Structure

```
models/
├── production/              # Production-ready artifacts
│   ├── ats_model.joblib    # Best trained model
│   ├── feature_engineer.joblib  # Fitted feature transformer
│   └── model_metadata.json  # Model info & test metrics
└── experiments/             # Training experiments
    └── experiment_20260129_143022/
        ├── logistic_regression.joblib
        ├── random_forest.joblib
        ├── xgboost.joblib
        ├── learning_curve_Logistic_Regression.png
        ├── learning_curve_Random_Forest.png
        ├── learning_curve_XGBoost.png
        └── training_summary.json
```

## Evaluation Criteria Details

### Metrics Hierarchy

1. **Recall** (40% weight) - Most important
   - Target: >= 90%
   - Minimizes false negatives (missed qualified candidates)
   - Business impact: Don't lose good talent

2. **F1 Score** (25% weight)
   - Target: >= 75%
   - Balances precision and recall
   - Ensures model doesn't sacrifice too much precision

3. **ROC-AUC** (20% weight)
   - Target: >= 0.85
   - Measures discrimination ability
   - Independent of classification threshold

4. **Precision** (10% weight)
   - Target: >= 70%
   - Controls false positives (wasted interviews)
   - Business impact: Recruiter efficiency

5. **Accuracy** (5% weight)
   - Target: >= 80%
   - Overall correctness
   - Less important due to class imbalance

### Model Selection Logic

1. Filter models that meet **recall >= 90%** (critical threshold)
2. Among valid models, require **3 out of 4** other criteria passed
3. Select model with **highest composite score**
4. If no model meets all criteria, select **best by recall**

### Business Metrics

- **False Negative Rate**: % of qualified candidates missed
- **False Positive Rate**: % of unqualified candidates passed
- **Specificity**: % of unqualified correctly rejected

## Cross-Validation Techniques

### 1. Stratified K-Fold (5 folds)
- Maintains class distribution in each fold
- Reduces variance in performance estimates
- Used for model evaluation and hyperparameter tuning

### 2. Learning Curves
- Plot training/validation scores vs. training set size
- **Underfitting Detection**: Both curves low and close
- **Overfitting Detection**: Large gap between curves
- **Good Fit**: Both curves high and converging

### 3. Validation Curves
- Plot scores vs. hyperparameter values
- Identify optimal parameter ranges
- Detect overfitting at extreme values

### 4. Variance Analysis
- Calculate coefficient of variation (CV%)
- **CV% < 5%**: Very stable
- **CV% 5-10%**: Stable
- **CV% 10-15%**: Moderate variance (monitor)
- **CV% > 15%**: High variance (overfitting)

## Regularization Techniques

### Logistic Regression
- L1 (Lasso): Feature selection
- L2 (Ridge): Coefficient shrinkage
- ElasticNet: Combination of L1 + L2
- Class weights: Handle imbalance

### Random Forest
- max_depth: Limit tree depth
- min_samples_split: Minimum samples to split
- min_samples_leaf: Minimum samples per leaf
- max_features: Feature sampling
- Class weights: Handle imbalance

### XGBoost
- learning_rate: Shrinkage
- max_depth: Tree depth limit
- min_child_weight: Minimum sum of instance weights
- gamma: Minimum loss reduction
- subsample: Row sampling fraction
- colsample_bytree: Column sampling fraction
- reg_alpha: L1 regularization
- reg_lambda: L2 regularization
- early_stopping_rounds: Stop if no improvement

## Integration with Agent 3

The trained model integrates seamlessly with Agent 3 (Hybrid Scorer):

```python
# agent3_scorer.py automatically loads the ML predictor
from src.ml_engine.ats_predictor import ATSPredictor

class HybridScoringAgent:
    def __init__(self):
        self.ml_predictor = ATSPredictor()
        self.ml_predictor.load_model()
    
    def score_match(self, cv, job):
        # Get ML prediction
        ml_result = self.ml_predictor.predict(cv_data)
        
        # Combine with rule-based score (60% rules + 40% ML)
        hybrid_score = (
            rule_based_score * 0.60 +
            ml_result['ml_score'] * 0.40
        )
```

## Performance Monitoring

Monitor these metrics in production:

- **Recall**: Should stay >= 90%
- **False Negative Rate**: Should stay <= 10%
- **Prediction Latency**: Should be < 100ms
- **Model Drift**: Compare new data distribution vs. training data

## Troubleshooting

### Model not loading
- Check `models/production/` directory exists
- Verify `ats_model.joblib` and `feature_engineer.joblib` present
- Run `train_ats_model.py` to train model

### Low recall on new data
- Check class distribution of new data
- Consider retraining with updated dataset
- Review feature distributions

### High variance in CV
- Increase regularization strength
- Reduce model complexity
- Collect more training data

## Future Enhancements

- [ ] Feature importance visualization
- [ ] SHAP values for explainability
- [ ] Automated model retraining pipeline
- [ ] A/B testing framework
- [ ] Model versioning and rollback
- [ ] Real-time prediction API
- [ ] Monitoring dashboard

## References

- Dataset: `resumes.csv` (1,001 records, 11 features)
- Sklearn Documentation: https://scikit-learn.org/
- XGBoost Documentation: https://xgboost.readthedocs.io/
- Imbalanced-Learn: https://imbalanced-learn.org/
