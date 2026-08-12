# Scripts Directory

Utility scripts for Recruiter Pro project management and development.

## Structure

```
scripts/
├── setup/              # Environment setup scripts
├── data_prep/          # Data preparation tools
├── ml_utils/           # ML training & evaluation utilities
│
└── setup_database.py   # Initialize SQLite database
```

## Quick Reference

### Setup Scripts
- `setup_database.py` - Initialize match history database

### Data Preparation (`data_prep/`)
- `clean_jobs_dataset.py` - Clean job postings
- `normalize_jobs.py` - Normalize job titles/requirements
- `prepare_jobs_json.py` - Convert jobs to JSON format

### ML Utilities (`ml_utils/`)
- `train_ats_model.py` - Train ML models from scratch (20-30 min)
- `show_training_results.py` - View latest training results
- `show_complete_metadata.py` - Display model metadata
- See [ml_utils/README.md](ml_utils/README.md) for details

## Usage

**Setup Database:**
```bash
python scripts/setup_database.py
```

**Prepare Job Data:**
```bash
# Clean and normalize job postings
python scripts/data_prep/clean_jobs_dataset.py

# Convert to JSON format
python scripts/data_prep/prepare_jobs_json.py
```

**Train ML Model:**
```bash
python scripts/ml_utils/train_ats_model.py
```

---

**Note:** Development/debug scripts have been removed to keep the project clean and production-focused.
```bash
python scripts/benchmark/benchmark_cvs.py
```

**Debug Imports:**
```bash
python scripts/debug/debug_imports.py
```

**Prepare Data:**
```bash
python scripts/data_prep/prepare_jobs_json.py
```

## Development

When adding new scripts:
1. Choose appropriate category folder
2. Add descriptive docstring
3. Update this README
4. Make script runnable from project root
