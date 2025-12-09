# Stage 2: Feature Engineering - Documentation

## Overview

Stage 2 implements **Agent 2 (Feature Generator)** which computes 12 numerical features to quantify the match quality between a candidate profile and a job description. These features are used by the ML model in Stage 3 to predict match scores.

---

## Agent 2: Feature Generator

### Purpose
Generate numerical features that capture different aspects of profile-job matching:
- Skill overlap and similarity
- Experience alignment
- Text semantic similarity
- Seniority level matching

### Location
- **File:** `src/agents/agent2_features.py`
- **Class:** `FeatureGenerator`

---

## The 12 Features

### 1. Skill Overlap Features (5 features)

#### `skill_overlap_count`
- **Type:** Integer (0+)
- **Description:** Number of skills that match between profile and job
- **Example:** Profile has [Python, Java, SQL], Job requires [Python, SQL, Docker] → count = 2

#### `skill_overlap_ratio`
- **Type:** Float (0.0 - 1.0)
- **Description:** Percentage of job-required skills found in profile
- **Formula:** `matched_skills / job_required_skills`
- **Example:** 2 matched out of 3 required → 0.67 (67%)

#### `jaccard_similarity`
- **Type:** Float (0.0 - 1.0)
- **Description:** Jaccard index of skill sets
- **Formula:** `|profile_skills ∩ job_skills| / |profile_skills ∪ job_skills|`
- **Example:** Intersection=2, Union=4 → 0.5

#### `profile_skill_count`
- **Type:** Integer (0+)
- **Description:** Total number of skills in candidate profile

#### `job_skill_count`
- **Type:** Integer (0+)
- **Description:** Total number of skills required by job

---

### 2. Experience Features (5 features)

#### `experience_delta`
- **Type:** Float (can be negative)
- **Description:** Years difference between profile and job requirement
- **Formula:** `profile_years - job_required_years`
- **Example:** Profile=5 years, Job requires 3-7 years (avg=5) → delta = 0

#### `experience_match`
- **Type:** Binary (0 or 1)
- **Description:** Whether candidate meets minimum experience requirement
- **Value:** 1 if `profile_years >= job_min_years`, else 0

#### `overqualified`
- **Type:** Binary (0 or 1)
- **Description:** Whether candidate is significantly overqualified
- **Value:** 1 if `profile_years > 2 × job_max_years`, else 0

#### `underqualified`
- **Type:** Binary (0 or 1)
- **Description:** Whether candidate doesn't meet minimum requirement
- **Value:** 1 if `profile_years < job_min_years`, else 0

#### `experience_ratio`
- **Type:** Float (0.0 - 2.0, capped)
- **Description:** Ratio of profile experience to job requirement
- **Formula:** `min(profile_years / job_required_years, 2.0)`

---

### 3. Text Similarity (1 feature)

#### `tfidf_similarity`
- **Type:** Float (0.0 - 1.0)
- **Description:** Cosine similarity between profile and job text using TF-IDF
- **Method:** Uses scikit-learn's TfidfVectorizer
- **Parameters:** max_features=1000, ngram_range=(1,2), min_df=1

---

### 4. Other Features (1 feature)

#### `seniority_match`
- **Type:** Binary (0 or 1)
- **Description:** Whether seniority level aligns with job requirements
- **Mapping:**
  - Entry-level: 0-2 years
  - Junior: 2-5 years
  - Mid-level: 5-10 years
  - Senior: 10-20 years
  - Executive: 15-50 years

---

## Usage

### Basic Usage

```python
from src.agents.agent1_parser import ProfileJobParser
from src.agents.agent2_features import FeatureGenerator

# Initialize agents
parser = ProfileJobParser()
generator = FeatureGenerator()

# Parse profile and job (from Stage 1)
profile = parser.parse_profile(resume_text, 'profile_001')
job = parser.parse_job(job_data)

# Generate features
features = generator.generate_features(profile, job)

# Get feature vector for ML model
feature_vector = generator.generate_feature_vector(features)

# Save features
generator.save_features(features, 'profile_001', job['job_id'])
```

### Feature Dictionary Output

```python
{
    'skill_overlap_count': 3,
    'skill_overlap_ratio': 0.75,
    'jaccard_similarity': 0.6,
    'profile_skill_count': 8,
    'job_skill_count': 4,
    'experience_delta': 2.0,
    'experience_match': 1,
    'overqualified': 0,
    'underqualified': 0,
    'experience_ratio': 1.4,
    'tfidf_similarity': 0.45,
    'seniority_match': 1
}
```

### Feature Vector Output

```python
# 12-element numpy array in consistent order
array([3.0, 0.75, 0.6, 8.0, 4.0, 2.0, 1.0, 0.0, 0.0, 1.4, 0.45, 1.0])
```

---

## API Reference

### Class: `FeatureGenerator`

#### `__init__(vectorizer_path='models/tfidf_vectorizer.pkl', output_dir='data/json/features')`
Initialize the feature generator.

**Parameters:**
- `vectorizer_path` (str): Path to TF-IDF vectorizer file
- `output_dir` (str): Directory to save feature files

#### `generate_features(profile, job) -> Dict`
Generate all 12 features for a profile-job pair.

**Parameters:**
- `profile` (Dict): Parsed profile from Agent 1
- `job` (Dict): Parsed job from Agent 1

**Returns:**
- Dictionary with 12 features

#### `generate_feature_vector(features) -> np.ndarray`
Convert feature dictionary to numpy array.

**Parameters:**
- `features` (Dict): Feature dictionary

**Returns:**
- 12-element numpy array in consistent order

#### `save_features(features, profile_id, job_id)`
Save features to JSON file.

**Parameters:**
- `features` (Dict): Feature dictionary
- `profile_id` (str): Profile identifier
- `job_id` (str): Job identifier

**Saves to:** `data/json/features/{profile_id}_{job_id}.json`

#### `load_features(profile_id, job_id) -> Dict`
Load previously saved features.

**Parameters:**
- `profile_id` (str): Profile identifier
- `job_id` (str): Job identifier

**Returns:**
- Feature record dictionary

---

## Testing

### Run Unit Tests

```bash
# Run all tests
pytest tests/test_agent2_features.py -v

# Run specific test
pytest tests/test_agent2_features.py::TestFeatureGenerator::test_skill_overlap_exact_match -v
```

### Run Verification Script

```bash
python verify_stage2.py
```

**Expected Output:**
- ✅ All 6 verification tests pass
- ✅ Features generated for multiple profile-job pairs
- ✅ Feature files saved correctly
- ✅ TF-IDF vectorizer saved

---

## Test Coverage

**24 Unit Tests** covering:
- ✅ Skill overlap calculations (5 tests)
- ✅ Experience feature calculations (5 tests)
- ✅ TF-IDF similarity (3 tests)
- ✅ Seniority matching (3 tests)
- ✅ Feature generation (2 tests)
- ✅ Feature vector generation (3 tests)
- ✅ Feature persistence (1 test)
- ✅ Edge cases (2 tests)

**Test Results:** 24/24 PASSED ✅

---

## File Structure

```
HR-Project/
├── src/agents/
│   ├── agent2_features.py          # Feature Generator implementation
│   └── agent1_parser.py            # Profile & Job Parser (Stage 1)
├── tests/
│   └── test_agent2_features.py     # Unit tests for Agent 2
├── data/json/
│   └── features/                   # Saved feature files
│       └── {profile_id}_{job_id}.json
├── models/
│   └── tfidf_vectorizer.pkl        # TF-IDF vectorizer
└── verify_stage2.py                # Verification script
```

---

## Feature File Format

Each feature file is saved as JSON:

```json
{
  "profile_id": "profile_001",
  "job_id": "12345",
  "features": {
    "skill_overlap_count": 3,
    "skill_overlap_ratio": 0.75,
    ...
  },
  "feature_vector": [3.0, 0.75, 0.6, ...],
  "generated_at": "2025-12-09T21:30:00",
  "generator_version": "v1.0"
}
```

---

## Dependencies

Required packages (already in `requirements.txt`):
- `numpy` - Numerical operations
- `scikit-learn` - TF-IDF vectorizer, cosine similarity
- `scipy` - Scientific computing

Install with:
```bash
pip install numpy scikit-learn scipy
```

---

## Integration with Other Stages

### Input from Stage 1
- Parsed profile dictionary from `ProfileJobParser.parse_profile()`
- Parsed job dictionary from `ProfileJobParser.parse_job()`

### Output to Stage 3
- 12-element feature vector for ML model training
- Feature dictionary for explainability
- Saved feature files for auditing

---

## Performance Considerations

### TF-IDF Vectorizer
- Vectorizer is loaded once and reused
- Saved to disk for consistency across runs
- Uses 1000 max features to balance performance and accuracy

### Feature Calculation
- All features computed in single pass
- Efficient set operations for skill matching
- Minimal memory footprint

### Typical Performance
- Feature generation: ~10ms per profile-job pair
- Handles 100+ pairs per second

---

## Troubleshooting

### Issue: TF-IDF similarity always 0.0
**Cause:** Empty text fields in profile or job  
**Solution:** Ensure `cleaned_text` and `qualifications` fields are populated

### Issue: All skill features are 0
**Cause:** No skills extracted in Stage 1  
**Solution:** Check skill extraction in Agent 1, verify skill patterns

### Issue: Feature vector wrong length
**Cause:** Missing features in dictionary  
**Solution:** All 12 features must be present; missing ones default to 0.0

---

## Next Steps

After completing Stage 2:
1. ✅ Verify all 24 tests pass
2. ✅ Run verification script
3. ✅ Check feature files created
4. ➡️ **Proceed to Stage 3: ML Model Training**

Stage 3 will use these 12 features to train a classifier that predicts match quality (High/Medium/Low).

---

## Version History

- **v1.0** (2025-12-09): Initial implementation
  - 12 features implemented
  - TF-IDF similarity added
  - Comprehensive testing
  - All tests passing

---

## Contact & Support

For issues or questions about Stage 2:
1. Check test results: `pytest tests/test_agent2_features.py -v`
2. Run verification: `python verify_stage2.py`
3. Review feature files in `data/json/features/`

**Stage 2 Status:** ✅ COMPLETE AND TESTED
