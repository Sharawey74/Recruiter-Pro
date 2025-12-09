# 🎯 Final Project Structure (Updated)

**Project:** Resume-Job Matching Multi-Agent System  
**Training Data:** `final_training_dataset_v2.csv` (35,730 records)  
**Target:** College Project - Streamlit Cloud Deployment  
**Updated:** December 7, 2025  

---

## 📊 Key Updates

✅ **Removed:** `notebooks/` folder  
✅ **Added:** `.env` configuration for LLM API keys  
✅ **Updated:** Agent 2.5 to classifier-only (no regression)  
✅ **Implemented:** Rule-based probability smoothing  

---

## 🏗️ COMPLETE PROJECT STRUCTURE

```
resume-job-matching/
│
├── 📁 data/
│   ├── raw/
│   │   └── final_training_dataset_v2.csv          # Your existing dataset (35,730 records)
│   │
│   └── json/
│       ├── jobs.json                               # Job templates (100 diverse jobs)
│       ├── jobs_features.json                      # Precomputed job features (optional)
│       ├── resumes_sample.json                     # Sample resumes for testing
│       │
│       ├── parsed_profiles/                        # Agent 1 outputs
│       │   ├── tmp_001.json
│       │   └── tmp_002.json
│       │
│       ├── features/                               # Agent 2 outputs (optional)
│       │   └── tmp_001_JOB_SE_BACK_001.json
│       │
│       ├── results/                                # Agent 3 outputs
│       │   └── tmp_001_results.json
│       │
│       └── logs/
│           └── predictions.log                     # Agent 4 logs
│
├── 📁 models/
│   ├── classifier.pkl                              # ✅ Trained classification model
│   ├── tfidf_vectorizer.pkl                        # TF-IDF vectorizer
│   ├── label_encoder.pkl                           # Label encoder (High/Medium/Low)
│   └── model_metadata.json                         # Model training info
│
├── 📁 src/
│   ├── __init__.py
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── agent1_parser.py                        # ✅ Profile & Job Parser (spaCy + NLTK)
│   │   ├── agent2_features.py                      # Feature Generator
│   │   ├── agent2_5_scorer.py                      # ✅ ML Scorer (Classifier + Rules)
│   │   ├── agent3_ranker.py                        # Decision & Explanation
│   │   └── agent4_analytics.py                     # Analytics & Logging
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── text_processing.py                      # NLP utilities
│   │   ├── skill_extraction.py                     # Skill extraction logic
│   │   └── config.py                               # Configuration loader
│   │
│   ├── models.py                                   # Model loading utilities
│   └── api.py                                      # FastAPI application
│
├── 📁 streamlit_app/
│   ├── app.py                                      # Main Streamlit app
│   ├── pages/
│   │   ├── 1_upload_cv.py                          # CV upload page
│   │   ├── 2_match_results.py                      # Results display
│   │   ├── 3_analytics.py                          # Analytics dashboard
│   │   └── 4_job_management.py                     # Job templates management
│   │
│   └── components/
│       ├── __init__.py
│       ├── cv_uploader.py                          # CV upload component
│       ├── job_selector.py                         # Job selection component
│       └── results_display.py                      # Results visualization
│
├── 📁 tests/
│   ├── __init__.py
│   ├── test_agent1_parser.py                       # Parser unit tests
│   ├── test_agent2_features.py                     # Feature gen tests
│   ├── test_agent2_5_scorer.py                     # ✅ ML scorer tests
│   ├── test_agent3_ranker.py                       # Ranker tests
│   └── test_utils.py                               # Utility function tests
│
├── 📁 scripts/
│   ├── prepare_jobs_json.py                        # ✅ Extract jobs from dataset
│   ├── train_models.py                             # ✅ Train classifier (no regression)
│   ├── compute_metrics.py                          # Analyze logs
│   └── export_sample_data.py                       # Create sample JSONs
│
├── 📁 config/
│   ├── rules.yaml                                  # Business rules for smoothing
│   └── thresholds.yaml                             # Decision thresholds
│
├── 📄 .env.example                                 # ✅ Environment template
├── 📄 .env                                         # ✅ Actual env vars (gitignored)
├── 📄 .gitignore                                   # ✅ Updated with .env
├── 📄 requirements.txt                             # ✅ Updated with python-dotenv
├── 📄 README.md                                    # Project documentation
└── 📄 run_local.sh                                 # Local startup script
```

---

## 🔧 Agent 2.5: Classifier + Rule Smoothing

### How It Works

```python
# Step 1: Classifier predicts probabilities
classifier.predict_proba(features)
# Output: [High: 0.78, Medium: 0.19, Low: 0.03]

# Step 2: Apply business rules
if High_prob > 0.85:
    enforce label = "High"
elif High_prob < 0.60 and predicted_label == "High":
    downgrade to "Medium"
elif Medium_prob < 0.35 and predicted_label == "Medium":
    downgrade to "Low"

# Step 3: Use probability as score
score = prob_dict[smoothed_label]  # e.g., 0.78

# Output
{
  "predicted_label": "High",
  "predicted_score": 0.78,
  "class_probabilities": {
    "High": 0.78,
    "Medium": 0.19,
    "Low": 0.03
  },
  "confidence": 0.85,
  "smoothing_flags": ["high_confidence_enforced"]
}
```

### Smoothing Rules

```python
rules = {
    'high_confidence_threshold': 0.85,      # Enforce High if prob > 0.85
    'medium_confidence_threshold': 0.60,    # Downgrade High if prob < 0.60
    'low_confidence_floor': 0.35,           # Downgrade Medium if prob < 0.35
    'ambiguous_threshold': 0.10             # Flag if top 2 differ by < 0.10
}
```

---

## 🔐 Environment Configuration

### `.env.example` (Template)

```bash
# LLM API Configuration (for Agent 3 - Optional)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7

# Application Settings
ENVIRONMENT=development
DEBUG=true

# Model Settings
MODEL_CONFIDENCE_THRESHOLD=0.60
HIGH_MATCH_THRESHOLD=0.85
MEDIUM_MATCH_THRESHOLD=0.60
```

### Setup

```bash
# Copy template
cp .env.example .env

# Edit .env with your actual API keys
nano .env
```

---

## 📦 Installation & Setup

### 1. Install Dependencies

```bash
# Install packages directly
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### 2. Prepare Data

```bash
# Extract jobs from dataset
python scripts/prepare_jobs_json.py
```

### 3. Train Model

```bash
# Train classifier (no regression)
python scripts/train_models.py
```

### 4. Test Agent 2.5

```bash
# Test scorer
python src/agents/agent2_5_scorer.py
```

### 5. Run Application

```bash
# Terminal 1: Start FastAPI
uvicorn src.api:app --reload --port 8000

# Terminal 2: Start Streamlit
streamlit run streamlit_app/app.py
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/test_agent2_5_scorer.py -v
```

---

## 📊 Model Training Output

```
Loading final_training_dataset_v2.csv...
✓ Loaded 35,730 training examples

Match distribution:
Low       13822
Medium    11269
High      10639

Vectorizing text with TF-IDF...
Label classes: ['High' 'Low' 'Medium']

Splitting data (70/15/15)...
Train: 25,011 samples
Val:   5,359 samples
Test:  5,360 samples

Training Random Forest Classifier...

=== Validation Set Evaluation ===
Classification Report:
              precision    recall  f1-score   support

        High       0.85      0.83      0.84      1596
         Low       0.78      0.81      0.79      2073
      Medium       0.76      0.74      0.75      1690

    accuracy                           0.79      5359

Validation Accuracy: 0.7945
Average max probability: 0.8234

✅ TRAINING COMPLETE!
```

---

## 🎯 7-Stage Implementation Plan

### Stage 0: Setup ✅
- [x] Create project structure
- [x] Install dependencies
- [x] Configure environment

### Stage 1: Data & Parsers ✅
- [x] Extract jobs.json
- [x] Implement Agent 1 (dual-mode parser)
- [x] Unit tests for parser

### Stage 2: Feature Engineering
- [ ] Implement Agent 2 (feature generator)
- [ ] Unit tests for features

### Stage 3: ML Model ✅
- [x] Train classifier (no regression)
- [x] Implement Agent 2.5 with rule smoothing
- [x] Unit tests for scorer

### Stage 4: Ranking & Explainability
- [ ] Implement Agent 3 (decision engine)
- [ ] Add explanation generation
- [ ] Unit tests for ranker

### Stage 5: FastAPI Gateway
- [ ] Implement /match endpoint
- [ ] Implement /jobs endpoint
- [ ] Test API

### Stage 6: Streamlit UI
- [ ] CV upload page
- [ ] Match results display
- [ ] Analytics dashboard
- [ ] Deploy to Streamlit Cloud

### Stage 7: Testing & Documentation
- [ ] Complete unit tests
- [ ] Integration testing
- [ ] Final documentation
- [ ] Demo video

---

## 🚀 Deployment (Streamlit Cloud)

### 1. Prepare for Deployment

```bash
# Ensure all dependencies in requirements.txt
# Add secrets to Streamlit Cloud dashboard
```

### 2. Streamlit Secrets

Create `.streamlit/secrets.toml`:

```toml
[api]
OPENAI_API_KEY = "your-key-here"

[model]
CONFIDENCE_THRESHOLD = 0.60
```

### 3. Deploy

1. Push to GitHub
2. Connect to Streamlit Cloud
3. Deploy from `streamlit_app/app.py`

---

## 📝 Key Files Created

✅ **Setup Files:**
- `.env.example` - Environment template
- `.gitignore` - Updated with .env
- `requirements.txt` - Updated with python-dotenv

✅ **Agent Implementations:**
- `src/agents/agent1_parser.py` - Dual-mode parser
- `src/agents/agent2_5_scorer.py` - Classifier + rule smoothing

✅ **Scripts:**
- `scripts/prepare_jobs_json.py` - Data extraction
- `scripts/train_models.py` - Classifier training (no regression)

---

## 🎓 Next Steps

1. **Review** this updated structure
2. **Implement** Agent 2 (feature generator)
3. **Implement** Agent 3 (decision engine)
4. **Build** FastAPI gateway
5. **Create** Streamlit UI
6. **Test** end-to-end flow
7. **Deploy** to Streamlit Cloud

---

**Status:** ✅ **Structure Updated & Ready for Implementation**  
**Model Approach:** Classifier-only with probability-based scoring  
**Deployment Target:** Streamlit Cloud (free tier)  
