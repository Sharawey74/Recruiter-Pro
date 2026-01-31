# ATS ML Model - Training Guide

## 🎯 Current Status

**ML Model:** ⚠️ **NOT TRAINED YET**  
**Fallback Mode:** ✅ **Mock/Rule-based scoring active**

The ATS engine currently uses **rule-based mock scoring** because:
1. Trained model files (`.joblib`) are NOT in git (too large, in `.gitignore`)
2. Model needs to be trained locally or on each deployment

---

## 📍 Model Location

**Expected Path:** `ML/models/opt_rf_model.joblib`

**Current Search Order:**
1. `ML/models/opt_rf_model.joblib` ← Primary location
2. `ML/models/random_forest_model.joblib` ← Alternative name
3. `ML/archive/ML2_backup/models/opt_rf_model.joblib` ← Archived (if exists)
4. Custom path (passed to ATSEngine constructor)

---

## 🚀 How to Train the Model

### Option 1: Quick Train (Recommended)

```bash
cd ML
python src/train_models.py
```

This will:
- Load training data from `ML/data/resumes.csv`
- Train Random Forest classifier
- Save model to `ML/models/opt_rf_model.joblib`
- Generate metrics and visualizations

### Option 2: Custom Training

```python
from ML.src import train_models

# Train with custom parameters
train_models.train()
```

### Option 3: Use Pre-trained Model

If you have a pre-trained model:

```bash
# Copy to expected location
cp /path/to/your/model.joblib ML/models/opt_rf_model.joblib
```

---

## 📊 Training Data Requirements

**Required File:** `ML/data/resumes.csv`

**Required Columns:**
- `Skills` - Comma-separated skills
- `Certifications` - Certifications held
- `Job Role` - Role title
- `Experience (Years)` - Years of experience
- `Projects Count` - Number of projects
- `Salary Expectation ($)` - Expected salary
- `Education` - Education level
- `Recruiter Decision` - Target (Hire/Reject)
- `AI Score (0-100)` - Target score

**Check if data exists:**
```bash
ls -l ML/data/resumes.csv
```

---

## 🔧 Current Behavior

### Without Trained Model (Current State)

**Mock Scoring Logic:**
```python
base_score = 65.0
if 'python' in cv_text.lower(): score += 10
if 'experience' in cv_text.lower(): score += 5
score = min(95, score)
```

**Risk Levels:**
- **Score ≥ 75:** LOW risk
- **Score 50-74:** MEDIUM risk  
- **Score < 50:** HIGH risk

### With Trained Model

Uses **Random Forest classifier** trained on historical data:
- Predicts probability of "Hire" decision
- Converts to 0-100 score
- More accurate, data-driven predictions

---

## 🎨 Integration with Agent 3

**Location:** `src/agents/agent3_scorer.py`

**Hybrid Scoring:**
```
Final Score = (Rule-based 60%) + (ML 40%)
```

**Rule-based:** Skills, experience, education matching  
**ML-based:** ATS model prediction (mock or trained)

**Current:**
- Rule-based: ✅ Working
- ML-based: ✅ Working (mock mode)
- Hybrid: ✅ Working

---

## ✅ Verification

### Check Model Status

```python
from src.ml.ats_model import ATSEngine

engine = ATSEngine()
engine.initialize()

# Output will show:
# ✅ ATS ML Model loaded from ML/models/opt_rf_model.joblib
# OR
# ⚠️ No trained ML model found. Using rule-based mock scoring.
```

### Test Prediction

```python
from src.ml.ats_model import ATSEngine

engine = ATSEngine()
engine.initialize()

result = engine.predict(
    cv_text="Python developer with 5 years experience",
    metadata={
        'skills': 'Python, Django, REST API',
        'experience': 5,
        'role': 'Software Engineer'
    }
)

print(result)
# {'ats_score': 80.0, 'risk_level': 'LOW', 'assessment': '...'}
```

---

## 📝 Training Output

After training, you'll see:

```
ML/models/
├── opt_rf_model.joblib           ← Trained model (not in git)
│
└── metadata/
    ├── RandomForest_metrics.json  ← Accuracy, precision, recall
    ├── RandomForest_metrics.txt   ← Human-readable metrics
    ├── RandomForest_confusion_matrix.png
    ├── rf_feature_importance.png
    ├── class_distribution.png
    └── ai_score_distribution.png
```

---

## 🔐 Security Note

**Model files (`.joblib`) are in `.gitignore`** for these reasons:

1. **Size** - Can be 10-100+ MB
2. **Security** - Don't expose model internals
3. **Flexibility** - Train per environment
4. **Version Control** - Track code, not binaries

**Deployment Strategy:**
- Train model in CI/CD pipeline
- Or: Upload pre-trained model to cloud storage
- Or: Train on first deployment
- Or: Keep using mock mode (decent for demo)

---

## 🎯 Production Checklist

- [ ] Training data available (`ML/data/resumes.csv`)
- [ ] Train model: `python ML/src/train_models.py`
- [ ] Verify model exists: `ls ML/models/opt_rf_model.joblib`
- [ ] Test predictions work
- [ ] Validate accuracy metrics (>80% recommended)
- [ ] Integrate with Agent 3 (already done ✅)

---

## 🆘 Troubleshooting

### "No trained ML model found"
**Solution:** Train the model (see above) or use mock mode

### "Training data not found"
**Solution:** Ensure `ML/data/resumes.csv` exists with required columns

### "Model prediction error"
**Solution:** Check model was trained with same feature columns

### "Mock scores seem inaccurate"
**Solution:** Train the actual model for better predictions

---

## 📚 Related Files

- **Model Code:** `src/ml/ats_model.py`
- **Training Script:** `ML/src/train_models.py`
- **Feature Engineering:** `src/ml/feature_engineering.py`
- **Agent Integration:** `src/agents/agent3_scorer.py`
- **ML Documentation:** `ML/README.md`

---

**Status:** Mock mode is working fine for development. Train model when ready for production.
