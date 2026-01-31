# 🏗️ Recruiter Pro AI - Architecture Guide

## Overview

This document explains the complete architecture of the Recruiter Pro AI system, clarifying what each component does and how they work together.

---

## 🎯 Quick Answer to Common Confusion

### **Is there 1 server or 2 servers?**

**ONLY 1 SERVER** - The FastAPI server (Python)

### **What is nodejs_client.js?**

It's **NOT a server** - it's example code showing how to **CALL** the FastAPI server from JavaScript/Node.js applications. It's a client library.

### **What is python_client.py?**

Also **NOT a server** - it's example code showing how to **CALL** the FastAPI server from Python applications. Another client library.

---

## 📊 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT APPLICATIONS                       │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  Python Client   │         │  Node.js Client  │         │
│  │  (examples/      │         │  (examples/      │         │
│  │   python_client) │         │   nodejs_client) │         │
│  └────────┬─────────┘         └────────┬─────────┘         │
│           │                             │                    │
│           │    HTTP/REST API Calls      │                   │
└───────────┼─────────────────────────────┼───────────────────┘
            │                             │
            ▼                             ▼
   ┌────────────────────────────────────────────────────┐
   │          FASTAPI SERVER (THE ONLY SERVER)          │
   │              (src/api_server.py)                   │
   │                                                     │
   │  Endpoints:                                        │
   │  • GET  /api/v1/health    - Health check          │
   │  • GET  /api/v1/model/info - Model information    │
   │  • POST /api/v1/score     - Score single resume   │
   │  • POST /api/v1/batch     - Score multiple resumes│
   │                                                     │
   └────────────────────┬──────────────────────────────┘
                        │
                        ▼
   ┌─────────────────────────────────────────────────────┐
   │              ML ENGINE (Python Modules)              │
   │                                                      │
   │  ┌─────────────────────────────────────────────┐   │
   │  │  ATSPredictor (ats_predictor.py)            │   │
   │  │  - Loads trained ML model                   │   │
   │  │  - Makes predictions on resumes             │   │
   │  │  - Returns probabilities and confidence     │   │
   │  └────────────┬────────────────────────────────┘   │
   │               │                                      │
   │               ▼                                      │
   │  ┌─────────────────────────────────────────────┐   │
   │  │  Feature Engineering (feature_engineering)  │   │
   │  │  - Extracts 30 features from resumes        │   │
   │  │  - Normalizes and scales data               │   │
   │  └─────────────────────────────────────────────┘   │
   │                                                      │
   │  Training Components (used offline):                │
   │  • ATSModelTrainer (model_trainer.py)              │
   │  • CrossValidationEvaluator (cross_validation.py)  │
   │  • EvaluationCriteria (evaluation_criteria.py)     │
   │  • ATSDataLoader (data_loader.py)                  │
   └──────────────────────────────────────────────────────┘
```

---

## 🔑 Component Breakdown

### 1. **FastAPI Server** (`src/api_server.py`)

**Role**: The ONLY server in the system - Production REST API

**Technology**: FastAPI (Python web framework)

**What it does**:
- Exposes 4 HTTP endpoints for resume scoring
- Loads ML model on startup
- Receives resume data via HTTP POST requests
- Returns scoring predictions as JSON responses
- Handles errors and validation

**How to run**:
```bash
# Development mode
uvicorn src.api_server:app --reload --port 8000

# Production mode
gunicorn src.api_server:app -w 4 -k uvicorn.workers.UvicornWorker
```

**Endpoints**:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/health` | GET | Check if server is running |
| `/api/v1/model/info` | GET | Get model metadata |
| `/api/v1/score` | POST | Score single resume |
| `/api/v1/batch` | POST | Score up to 100 resumes |

**Access API documentation**:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

---

### 2. **Python Client SDK** (`examples/python_client.py`)

**Role**: **NOT a server** - Client library for Python applications

**What it does**:
- Provides easy-to-use Python functions to call the FastAPI server
- Handles HTTP requests/responses
- Provides type-safe dataclasses for Resume and ScoringResult

**Example usage**:
```python
from python_client import ATSClient, Resume, Education

# Create client (points to FastAPI server)
client = ATSClient("http://localhost:8000")

# Create resume
resume = Resume(
    skills="Python, Machine Learning",
    experience_years=5,
    education=Education.MASTERS,
    projects_count=10
)

# Score resume (calls FastAPI server)
result = client.score_resume(resume)
print(f"Probability: {result.ml_probability}")
print(f"Decision: {result.decision}")
```

---

### 3. **Node.js Client SDK** (`examples/nodejs_client.js`)

**Role**: **NOT a server** - Client library for JavaScript/Node.js applications

**What it does**:
- Provides easy-to-use JavaScript functions to call the FastAPI server
- Uses async/await for HTTP requests
- Provides builder pattern for creating resumes

**Example usage**:
```javascript
const { ATSClient, Resume, Education } = require('./nodejs_client');

// Create client (points to FastAPI server)
const client = new ATSClient('http://localhost:8000');

// Create resume
const resume = new Resume()
    .setSkills('Python, Machine Learning')
    .setExperienceYears(5)
    .setEducation(Education.MASTERS)
    .setProjectsCount(10);

// Score resume (calls FastAPI server)
const result = await client.scoreResume(resume);
console.log(`Probability: ${result.ml_probability}`);
console.log(`Decision: ${result.decision}`);
```

---

### 4. **ML Engine** (`src/ml_engine/`)

**Role**: Machine Learning components for training and prediction

**Components**:

#### **Production Components** (used by API server):

- **ATSPredictor** (`ats_predictor.py`)
  - Loads trained model
  - Makes predictions on new resumes
  - Returns probabilities and confidence scores

- **FeatureEngineer** (`feature_engineering.py`)
  - Extracts 30 features from resume data
  - Normalizes and scales features
  - Handles missing values

#### **Training Components** (used offline):

- **ATSModelTrainer** (`model_trainer.py`)
  - Trains Logistic Regression, Random Forest, XGBoost
  - Uses SMOTE for class balancing
  - Hyperparameter tuning with GridSearchCV

- **CrossValidationEvaluator** (`cross_validation.py`)
  - K-fold cross-validation
  - Learning curves to detect overfitting
  - Validation curves for hyperparameter analysis

- **EvaluationCriteria** (`evaluation_criteria.py`)
  - Calculates accuracy, precision, recall, F1-score
  - Composite scoring combining multiple metrics
  - Threshold-based decision making

- **ATSDataLoader** (`data_loader.py`)
  - Loads CSV datasets
  - Normalizes data
  - Stratified train/test splitting

---

## 🔄 Complete Workflow

### Training Phase (Offline):
```
1. ATSDataLoader loads CSV data
2. FeatureEngineer extracts 30 features
3. ATSModelTrainer trains 3 models with SMOTE
4. CrossValidationEvaluator validates performance
5. Best model saved to models/production/
```

### Production Phase (Online):
```
1. FastAPI server starts → loads ATSPredictor
2. Client application sends HTTP POST to /api/v1/score
3. FastAPI validates input (Pydantic models)
4. ATSPredictor processes resume and returns prediction
5. FastAPI returns JSON response to client
```

---

## 📁 Directory Structure

```
Recruiter-Pro-AI/
├── src/
│   ├── api_server.py          # ✅ THE ONLY SERVER (FastAPI)
│   ├── ml_engine/
│   │   ├── ats_predictor.py   # Production: Makes predictions
│   │   ├── feature_engineering.py  # Production: Feature extraction
│   │   ├── model_trainer.py    # Training: ATSModelTrainer
│   │   ├── cross_validation.py # Training: CrossValidationEvaluator
│   │   ├── evaluation_criteria.py  # Training: Metrics
│   │   └── data_loader.py      # Training: Data loading
│   └── ...
│
├── examples/
│   ├── python_client.py       # ❌ NOT a server - Python SDK
│   └── nodejs_client.js       # ❌ NOT a server - Node.js SDK
│
├── tests/
│   ├── test_api/              # API endpoint tests
│   ├── test_ml_engine/        # ML component unit tests
│   ├── test_integration/      # Pipeline integration tests
│   ├── test_system/           # End-to-end system tests
│   └── test_performance/      # Load and performance tests
│
└── models/
    └── production/            # Trained models
        ├── ats_model.joblib
        └── feature_engineer.joblib
```

---

## 🧪 Testing Architecture

### Test Categories:

1. **Unit Tests** (`tests/test_ml_engine/`)
   - Test individual ML components in isolation
   - 6 test files, 115 tests total
   - Run: `pytest -m unit`

2. **API Tests** (`tests/test_api/`)
   - Test FastAPI endpoints
   - 18 tests covering all 4 endpoints
   - Run: `pytest -m api`

3. **Integration Tests** (`tests/test_integration/`)
   - Test complete ML pipeline workflows
   - 10 tests for end-to-end ML processes
   - Run: `pytest -m integration`

4. **System Tests** (`tests/test_system/`)
   - Test entire system including API + ML
   - 15 end-to-end scenarios
   - Run: `pytest -m system`

5. **Performance Tests** (`tests/test_performance/`)
   - Load testing, benchmarks, scalability
   - 14 performance tests
   - Run: `pytest -m performance`

---

## 🚀 Deployment Scenarios

### Local Development:
```bash
# Terminal 1: Start FastAPI server
uvicorn src.api_server:app --reload --port 8000

# Terminal 2: Test with Python client
python examples/python_client.py

# Terminal 3: Test with Node.js client
node examples/nodejs_client.js
```

### Production (Docker):
```bash
# Build image
docker build -t recruiter-pro-ai .

# Run container
docker run -p 8000:8000 recruiter-pro-ai
```

### Production (Gunicorn):
```bash
gunicorn src.api_server:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

---

## 🔍 Key Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| API Server | FastAPI 0.104.1 | REST API framework |
| ASGI Server | Uvicorn / Gunicorn | Production server |
| ML Framework | scikit-learn 1.3.2 | Model training |
| Boosting | XGBoost 2.0.3 | Advanced ML model |
| Class Balancing | imbalanced-learn | SMOTE sampling |
| Validation | Pydantic 2.5.0 | Request/response validation |
| Testing | pytest 7.4.3 | Test framework |
| Python Client | requests 2.31.0 | HTTP client |
| Node.js Client | axios 1.6.0 | HTTP client |

---

## ❓ Common Questions

### Q: Why do I need the client SDKs?
**A**: The client SDKs make it easy to call the FastAPI server from your applications. They handle HTTP requests, data formatting, and error handling for you.

### Q: Can I use the API without the client SDKs?
**A**: Yes! You can call the FastAPI endpoints directly using any HTTP client (curl, Postman, fetch, etc.). The SDKs just make it easier.

### Q: Where does the ML training happen?
**A**: ML training is done **offline** using scripts in `src/ml_engine/train.py`. The trained model is then loaded by the FastAPI server.

### Q: What's the difference between `src/backend.py` and `src/api_server.py`?
**A**: 
- `src/backend.py` - Old multi-agent rule-based system (Phase 1)
- `src/api_server.py` - New FastAPI ML-powered system (Phase 3)

### Q: How do I know if the server is running?
**A**: Visit http://localhost:8000/api/docs in your browser. If you see the API documentation, it's running!

---

## 🎯 Summary

**1 Server, 2 Client Libraries:**

- ✅ **FastAPI Server** (`src/api_server.py`) - The ONLY server
- ❌ **Python Client** (`examples/python_client.py`) - NOT a server
- ❌ **Node.js Client** (`examples/nodejs_client.js`) - NOT a server

**Complete Flow:**
```
Your App → Client SDK → HTTP Request → FastAPI Server → ML Engine → Response
```

The client SDKs are optional convenience libraries that make it easier to call the FastAPI server from your applications.
