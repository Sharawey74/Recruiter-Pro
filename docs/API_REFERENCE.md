# 🚀 API Quick Reference

## Start Server

```powershell
.\start_server.ps1    # Opens in new window
# OR
python run_api.py     # Current terminal
```

**API Docs:** http://localhost:8000/docs

---

## Endpoints

### 1. Health Check
```bash
GET /health
```

### 2. List Jobs
```bash
GET /jobs?limit=10&skip=0
```

### 3. Upload & Parse CV
```bash
POST /upload
Content-Type: multipart/form-data
file: <CV file>
```

### 4. Match CV to All Jobs ⭐ MAIN
```bash
POST /match?top_k=10&explain=false
Content-Type: multipart/form-data
file: <CV file>
```

### 5. Match to Single Job
```bash
POST /match/single?job_id=abc123&explain=true
Content-Type: multipart/form-data
file: <CV file>
```

### 6. View History
```bash
GET /history?limit=50&skip=0
```

---

## Python Example

```python
import requests

# Match CV
with open('resume.pdf', 'rb') as f:
    resp = requests.post(
        'http://localhost:8000/match',
        files={'file': f},
        params={'top_k': 5}
    )

for match in resp.json()['matches']:
    print(f"{match['job_title']}: {match['score']}%")
```

---

## Response Structure

```json
{
  "success": true,
  "matches": [{
    "job_id": "...",
    "job_title": "Senior Python Developer",
    "company": "Tech Corp",
    "score": 85.4,        // 0-100%
    "decision": "ACCEPT", // ACCEPT/MAYBE/REJECT
    "confidence": 92.1,   // 0-100%
    "scores": {
      "skill_match": 90.0,
      "experience_match": 85.0,
      "education_match": 80.0,
      "hybrid": 85.4
    },
    "matched_skills": ["python", "fastapi"],
    "missing_skills": ["kubernetes"],
    "strengths": [...],
    "red_flags": [...],
    "recommendations": [...]
  }]
}
```

---

## System Stats

- **Jobs Loaded:** 13,032
- **ML Model:** 99.54% accuracy
- **Test Coverage:** 26/26 tests passing
- **Agents:** Parser → Extractor → Scorer → Explainer

---

**Full docs:** [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)
