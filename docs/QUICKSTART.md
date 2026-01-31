# Recruiter-Pro-AI Quick Start Guide

Get started with the Recruiter-Pro-AI ATS system in 5 minutes!

## Prerequisites

- Python 3.10+
- Git
- 4GB RAM minimum

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Sharawey74/Recruiter-Pro-AI.git
cd Recruiter-Pro-AI
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Verify Installation
```bash
# Run tests
pytest tests/test_api/test_api_endpoints.py -v

# Check ML model exists
ls models/production/
# Should see: ats_model.joblib, feature_engineer.joblib, model_metadata.json
```

---

## Starting the API Server

### Development Mode
```bash
uvicorn src.api_server:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
gunicorn src.api_server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Verify Server is Running
```bash
# Check health
curl http://localhost:8000/api/v1/health

# Expected response:
# {"status":"healthy","model_loaded":true,"version":"1.0.0"}
```

---

## Quick API Usage

### Using cURL

#### 1. Score a Single Resume
```bash
curl -X POST http://localhost:8000/api/v1/score \
  -H "Content-Type: application/json" \
  -d '{
    "skills": "Python, Machine Learning, SQL",
    "experience_years": 5,
    "education": "Masters",
    "certifications": "AWS Certified",
    "projects_count": 10,
    "current_role": "Senior Engineer",
    "expected_salary": 120000
  }'
```

**Response:**
```json
{
  "ml_prediction": 1,
  "ml_probability": 0.92,
  "ml_confidence": 0.84,
  "decision": "Accept",
  "top_features": {
    "skill_python": 0.45,
    "skill_machine_learning": 0.38,
    "experience_years": 0.32
  }
}
```

#### 2. Batch Score Multiple Resumes
```bash
curl -X POST http://localhost:8000/api/v1/batch \
  -H "Content-Type: application/json" \
  -d '{
    "resumes": [
      {
        "skills": "Python, Django",
        "experience_years": 3,
        "education": "Bachelors",
        "certifications": "None",
        "projects_count": 8,
        "current_role": "Engineer",
        "expected_salary": 85000
      },
      {
        "skills": "Java, Spring Boot",
        "experience_years": 7,
        "education": "Masters",
        "certifications": "AWS",
        "projects_count": 20,
        "current_role": "Senior Engineer",
        "expected_salary": 140000
      }
    ]
  }'
```

### Using Python

```python
from examples.python_client import ATSClient, Resume, Education

# Initialize client
client = ATSClient("http://localhost:8000")

# Score single resume
resume = Resume(
    skills="Python, Machine Learning, SQL",
    experience_years=5,
    education=Education.MASTERS.value,
    certifications="AWS Certified",
    projects_count=10,
    current_role="Senior Engineer",
    expected_salary=120000
)

result = client.score_resume(resume)
print(f"Decision: {result.decision}")
print(f"Probability: {result.ml_probability:.2%}")
```

**Full example:** `examples/python_client.py`

### Using JavaScript/Node.js

```javascript
const { ATSClient, Resume, Education } = require('./examples/nodejs_client');

async function main() {
  const client = new ATSClient('http://localhost:8000');
  
  const resume = new Resume()
    .skills('Python, Machine Learning, SQL')
    .experienceYears(5)
    .education(Education.MASTERS)
    .certifications('AWS Certified')
    .projectsCount(10)
    .currentRole('Senior Engineer')
    .expectedSalary(120000)
    .build();
  
  const result = await client.scoreResume(resume);
  console.log(`Decision: ${result.decision}`);
  console.log(`Probability: ${(result.ml_probability * 100).toFixed(2)}%`);
}

main();
```

**Full example:** `examples/nodejs_client.js`

---

## Interactive API Documentation

Once the server is running, access:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

Try the endpoints directly in your browser!

---

## Running Tests

### All Tests
```bash
pytest -v
```

### By Category
```bash
# Unit tests only (fast)
pytest -m unit -v

# ML tests
pytest -m ml -v

# API tests
pytest -m api -v

# Integration tests
pytest -m integration -v

# System tests
pytest -m system -v

# Performance tests (slow)
pytest -m performance -v
```

### With Coverage
```bash
pytest --cov=src --cov-report=html
# Open htmlcov/index.html to view coverage report
```

---

## Common Tasks

### Check Model Performance
```bash
curl http://localhost:8000/api/v1/model/info
```

### Process CSV of Resumes
```python
import pandas as pd
from examples.python_client import ATSClient

client = ATSClient()

# Read CSV
df = pd.read_csv("resumes.csv")

# Convert to list of dicts
resumes = df.to_dict('records')

# Score in batches of 100
for i in range(0, len(resumes), 100):
    batch = resumes[i:i+100]
    results = client.score_batch(batch)
    print(f"Batch {i//100 + 1}: {results['summary']}")
```

### Monitor API Health
```python
from examples.python_client import ATSClient
import time

client = ATSClient()

while True:
    if client.is_healthy():
        print("✓ API is healthy")
    else:
        print("✗ API is down")
    time.sleep(60)  # Check every minute
```

---

## Docker Deployment

### Build Image
```bash
docker build -t recruiter-pro-api .
```

### Run Container
```bash
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/models:/app/models \
  --name recruiter-api \
  recruiter-pro-api
```

### Check Logs
```bash
docker logs -f recruiter-api
```

---

## Troubleshooting

### Issue: Model Not Loaded
**Symptoms:** API returns 503 errors

**Solution:**
```bash
# Check if model files exist
ls -lh models/production/

# Expected files:
# - ats_model.joblib
# - feature_engineer.joblib
# - model_metadata.json

# If missing, train the model first:
python src/ml_engine/model_trainer.py
```

### Issue: Port Already in Use
**Symptoms:** `Address already in use`

**Solution:**
```bash
# Use a different port
uvicorn src.api_server:app --reload --port 8001

# Or kill the process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8000 | xargs kill -9
```

### Issue: Validation Errors (422)
**Symptoms:** API returns validation errors

**Solution:**
- Ensure `experience_years` is between 0-50
- Ensure `education` is one of: "High School", "Bachelors", "Masters", "PhD"
- Ensure all required fields are present
- Check API docs: http://localhost:8000/api/docs

---

## Next Steps

1. **Explore API Documentation**: http://localhost:8000/api/docs
2. **Read Testing Guide**: [TESTING_DOCUMENTATION.md](TESTING_DOCUMENTATION.md)
3. **Read Phase 3 Docs**: [PHASE_3_API_IMPLEMENTATION.md](PHASE_3_API_IMPLEMENTATION.md)
4. **Run Performance Tests**: `pytest -m performance -v`
5. **Integrate with Your App**: Use Python or Node.js client

---

## Support

- **Documentation**: See `docs/` folder
- **Examples**: See `examples/` folder
- **Tests**: See `tests/` folder
- **Issues**: Create GitHub issue

---

## Quick Reference

### API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/health` | GET | Health check |
| `/api/v1/model/info` | GET | Model metadata |
| `/api/v1/score` | POST | Score single resume |
| `/api/v1/batch` | POST | Score multiple resumes |

### Test Commands
| Command | Purpose |
|---------|---------|
| `pytest -m unit` | Fast unit tests |
| `pytest -m integration` | Integration tests |
| `pytest -m system` | End-to-end tests |
| `pytest -m performance` | Load tests |
| `pytest --cov=src` | Coverage report |

### Decision Thresholds
| Probability | Decision |
|-------------|----------|
| ≥ 0.7 | Accept |
| 0.4 - 0.7 | Review |
| < 0.4 | Reject |

---

**Happy Screening! 🎯**
