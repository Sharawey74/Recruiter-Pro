# Stage 1 - Quick Start Guide

## ✅ STAGE 1 IS COMPLETE AND WORKING!

### How to Run (From Your Virtual Environment)

**Important**: Always run from the `HR-Project/HR-Project` directory!

```bash
# 1. Activate your virtual environment (if not already active)
cd c:\Users\hp\OneDrive\Desktop\HR-Project
.venv\Scripts\Activate.ps1

# 2. Navigate to the project directory
cd HR-Project

# 3. Run verification (Quick test - 30 seconds)
python verify_stage1.py

# 4. Run full demo (Complete demonstration)
python demo_stage1.py

# 5. Run unit tests
python -m pytest tests/test_agent1_parser.py -v
```

### What Just Worked ✅

When you ran `verify_stage1.py`, the system:

1. ✅ **Initialized Agent 1 Parser** using spaCy
2. ✅ **Loaded 5 sample resumes** from `data/json/resumes_sample.json`
3. ✅ **Loaded 100 jobs** from `data/json/jobs.json`
4. ✅ **Parsed a resume** and extracted:
   - 25+ skills (Python, Java, AWS, Docker, etc.)
   - Email address
   - Years of experience
   - Seniority level
   - Education
5. ✅ **Parsed a job** and extracted requirements
6. ✅ **Calculated match score** between profile and job

### Files Created

All parsed profiles are saved in:
```
HR-Project/data/json/parsed_profiles/
```

Current files:
- `verify_test.json` - Latest test result
- `batch_test_1.json` through `batch_test_5.json` - All sample resumes
- Each contains structured JSON with skills, experience, education

### Example Output

The parser extracted from a resume:
```json
{
  "profile_id": "verify_test",
  "contact": {
    "email": "john.doe@email.com"
  },
  "skills": [
    "python", "java", "javascript", "aws", "docker", 
    "kubernetes", "react", "node.js", "postgresql", 
    "mongodb", "redis", "jenkins", "git", "jira"
  ],
  "experience_years": 5,
  "education": ["Bachelor's"],
  "seniority": "mid-level"
}
```

### Next Steps

**Stage 1 is COMPLETE!** ✅

You can now:
1. ✅ Parse any resume text
2. ✅ Parse job descriptions  
3. ✅ Extract skills automatically
4. ✅ Calculate experience
5. ✅ Detect education levels
6. ✅ Save results as JSON

**Ready for Stage 2**: Feature Engineering (Agent 2)

### Troubleshooting

**If you get "FileNotFoundError":**
- Make sure you're in the `HR-Project/HR-Project` directory
- Run: `cd c:\Users\hp\OneDrive\Desktop\HR-Project\HR-Project`
- Then run the scripts

**If you get "Module not found":**
- Make sure virtual environment is activated
- Run: `pip install spacy nltk pandas scikit-learn numpy pytest`

### Quick Commands Reference

```bash
# From HR-Project directory:
cd HR-Project

# Verify everything works
python verify_stage1.py

# See full demo
python demo_stage1.py

# Test with your own resume
python test_agent1.py

# Run unit tests
python -m pytest tests/ -v
```

---

**Status**: ✅ **FULLY OPERATIONAL**  
**Date**: December 8, 2025  
**Next**: Stage 2 - Feature Engineering
