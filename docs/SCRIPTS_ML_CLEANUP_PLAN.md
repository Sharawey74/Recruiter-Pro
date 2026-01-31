# Scripts & ML Modules Cleanup Plan

**Date:** 2026-01-29  
**Status:** 📋 PLANNED - Ready to Execute

---

## 🎯 Objectives

1. **Organize scripts/** folder by purpose (benchmark, debug, data_prep, archive)
2. **Consolidate ML/** folder (remove ML2 duplicate, archive old models)
3. **Create documentation** for both folders
4. **Update .gitignore** with new patterns

---

## 📂 Scripts Folder Reorganization Plan

### Current State (Before)
```
scripts/
├── benchmark_arabic_cvs.py
├── benchmark_cvs.py
├── check_autogen.py
├── check_ports.py
├── clean_jobs_dataset.py
├── cleanup_old_files.py
├── debug_imports.py
├── debug_robotics_cv.py
├── normalize_jobs.py
├── pre_phase3_cleanup.py
├── prepare_jobs_json.py
├── setup_database.py
├── verify_golden_cv.py
└── verify_name.py
```

### Target State (After)
```
scripts/
├── benchmark/
│   ├── __init__.py
│   ├── benchmark_arabic_cvs.py
│   └── benchmark_cvs.py
│
├── debug/
│   ├── __init__.py
│   ├── check_autogen.py
│   ├── check_ports.py
│   ├── debug_imports.py
│   └── debug_robotics_cv.py
│
├── data_prep/
│   ├── __init__.py
│   ├── clean_jobs_dataset.py
│   ├── normalize_jobs.py
│   ├── prepare_jobs_json.py
│   ├── verify_golden_cv.py
│   └── verify_name.py
│
├── archive/
│   ├── __init__.py
│   └── cleanup_old_files.py
│
├── setup/
│   └── __init__.py
│
├── setup_database.py           (keep in root)
├── pre_phase3_cleanup.py       (keep in root)
├── cleanup_scripts_and_ml.py   (new cleanup script)
└── README.md                   (exists)
```

### Actions Required

**1. Create category directories:**
```powershell
cd scripts
mkdir benchmark, debug, data_prep, archive, setup
New-Item __init__.py -Path benchmark, debug, data_prep, archive, setup
```

**2. Move scripts to categories:**
```powershell
# Benchmark
Move-Item benchmark_arabic_cvs.py, benchmark_cvs.py → benchmark/

# Debug
Move-Item check_autogen.py, check_ports.py, debug_imports.py, debug_robotics_cv.py → debug/

# Data Prep
Move-Item clean_jobs_dataset.py, normalize_jobs.py, prepare_jobs_json.py, verify_golden_cv.py, verify_name.py → data_prep/

# Archive
Move-Item cleanup_old_files.py → archive/
```

**3. Keep in root:**
- `setup_database.py` - Critical setup script
- `pre_phase3_cleanup.py` - Recent cleanup script
- `cleanup_scripts_and_ml.py` - This cleanup script
- `README.md` - Documentation

---

## 🧠 ML Folder Reorganization Plan

### Current State (Before)
```
ML/
├── src/
│   ├── train_models.py
│   ├── evaluate.py
│   ├── preprocessing.py
│   └── utils.py
│
├── ML2/                    ← DUPLICATE (needs consolidation)
│   ├── src/
│   │   ├── features.py
│   │   └── optimization.py
│   ├── models/
│   └── data/
│
├── models/
│   └── metadata/
│       ├── *.png          ← Archive (10 PNG files)
│       ├── *.json         ← Archive (4 JSON files)
│       └── *.txt          ← Archive (4 TXT files)
│
├── data/
│   └── resumes.csv
│
├── __init__.py
├── ml_code_review.md.resolved
├── requirements.txt
└── README.md (exists)
```

### Target State (After)
```
ML/
├── src/
│   ├── __init__.py
│   ├── train_models.py
│   ├── evaluate.py
│   ├── preprocessing.py
│   └── utils.py
│
├── models/
│   └── metadata/
│       └── (keep directory, archive files)
│
├── data/
│   └── resumes.csv
│
├── notebooks/              ← NEW (Jupyter experiments)
│   └── .gitkeep
│
├── experiments/            ← NEW (experimental features)
│   └── .gitkeep
│
├── archive/                ← NEW
│   ├── ML2_backup/        ← Archived duplicate folder
│   │   └── (entire ML2/ content)
│   │
│   └── models_metadata_20260129/  ← Archived metrics
│       ├── *.png (10 files)
│       ├── *.json (4 files)
│       └── *.txt (4 files)
│
├── __init__.py
├── requirements.txt
└── README.md (exists)
```

### Actions Required

**1. Create new directories:**
```powershell
cd ML
mkdir notebooks, experiments, archive
New-Item .gitkeep -Path notebooks, experiments
```

**2. Archive ML2 folder:**
```powershell
# Copy ML2 to archive
Copy-Item ML2 -Destination archive/ML2_backup -Recurse

# Extract unique features to production
Copy-Item ML2/src/features.py -Destination ../src/ml/feature_engineering.py

# Remove ML2
Remove-Item ML2 -Recurse -Force
```

**3. Archive old model metadata:**
```powershell
# Create dated archive folder
mkdir archive/models_metadata_20260129

# Move visualization/metric files only
Move-Item models/metadata/*.png -Destination archive/models_metadata_20260129/
Move-Item models/metadata/*.json -Destination archive/models_metadata_20260129/
Move-Item models/metadata/*.txt -Destination archive/models_metadata_20260129/
Move-Item models/metadata/*.csv -Destination archive/models_metadata_20260129/
```

**4. Cleanup resolved files:**
```powershell
Remove-Item ml_code_review.md.resolved
```

---

## 🔗 Integration with Production

### ML Code Movement

**From ML/ML2/ → src/ml/**
```
ML2/src/features.py → src/ml/feature_engineering.py
```

**Already integrated:**
```
ats_engine.py → src/ml/ats_model.py (done in Phase 2)
```

### Agent Integration

**Agent 3 (Hybrid Scorer):**
- Uses `src/ml/ats_model.py` for ML scoring (40% weight)
- Rule-based scoring (60% weight) in agent3_scorer.py
- Experimental ML stays in ML/ folder

---

## 📝 Documentation Updates

### Files to Create/Update

1. **scripts/README.md** - ✅ Exists (verify content)
2. **ML/README.md** - ✅ Exists (verify content)
3. **docs/SCRIPTS_ML_CLEANUP.md** - ✅ This file
4. **.gitignore** - Update with new patterns

### .gitignore Additions

```gitignore
# ML Folder - Archive and Experiments
ML/archive/*
!ML/archive/.gitkeep
ML/experiments/*
!ML/experiments/.gitkeep
ML/notebooks/*.ipynb_checkpoints
ML/models/metadata/*.png
ML/models/metadata/*.json
ML/models/metadata/*.txt

# Scripts - Organized structure
scripts/**/__pycache__/
scripts/**/temp_*.py
```

---

## ✅ Execution Checklist

### Phase 1: Scripts Folder
- [ ] Create category directories (benchmark, debug, data_prep, archive, setup)
- [ ] Create __init__.py in each category
- [ ] Move 11 scripts to appropriate categories
- [ ] Verify scripts/README.md content
- [ ] Test script imports still work

### Phase 2: ML Folder
- [ ] Create notebooks/, experiments/, archive/ directories
- [ ] Archive ML2/ → archive/ML2_backup/
- [ ] Extract ML2/src/features.py → src/ml/feature_engineering.py
- [ ] Archive model metadata (18 files) → archive/models_metadata_20260129/
- [ ] Remove ML2/ folder
- [ ] Remove ml_code_review.md.resolved
- [ ] Verify ML/README.md content

### Phase 3: Documentation
- [ ] Update .gitignore with new patterns
- [ ] Create summary document (this file)
- [ ] Update main README if needed
- [ ] Verify all tests still pass

### Phase 4: Verification
- [ ] Run pytest to ensure no broken imports
- [ ] Test script execution from new locations
- [ ] Verify archived files are accessible
- [ ] Check git status for untracked files

---

## 📊 Expected Outcomes

### Scripts Folder
- **Before:** 14 scripts in flat structure
- **After:** 11 scripts organized in 4 categories + 3 in root
- **Benefit:** Easier navigation, clear categorization

### ML Folder
- **Before:** Duplicate ML2/, 18 old metadata files, unclear structure
- **After:** Clean structure, archived duplicates, clear production integration
- **Benefit:** No duplication, clear experiment vs. production separation

---

## 🚀 Manual Execution Steps

Since automated script has issues, execute manually:

### Step 1: Scripts Organization (5 minutes)

```powershell
cd "c:\Users\DELL\Desktop\Recruiter-Pro-AI\scripts"

# Create directories
mkdir benchmark, debug, data_prep, archive, setup
"" | Out-File benchmark/__init__.py
"" | Out-File debug/__init__.py
"" | Out-File data_prep/__init__.py
"" | Out-File archive/__init__.py
"" | Out-File setup/__init__.py

# Move files (one by one to avoid errors)
Move-Item benchmark_arabic_cvs.py benchmark/
Move-Item benchmark_cvs.py benchmark/
Move-Item check_autogen.py debug/
Move-Item check_ports.py debug/
Move-Item debug_imports.py debug/
Move-Item debug_robotics_cv.py debug/
Move-Item clean_jobs_dataset.py data_prep/
Move-Item normalize_jobs.py data_prep/
Move-Item prepare_jobs_json.py data_prep/
Move-Item verify_golden_cv.py data_prep/
Move-Item verify_name.py data_prep/
Move-Item cleanup_old_files.py archive/

Write-Host "✅ Scripts organized"
```

### Step 2: ML Organization (10 minutes)

```powershell
cd "c:\Users\DELL\Desktop\Recruiter-Pro-AI\ML"

# Create directories
mkdir notebooks, experiments, archive
"" | Out-File notebooks/.gitkeep
"" | Out-File experiments/.gitkeep

# Archive ML2
Copy-Item ML2 -Destination archive/ML2_backup -Recurse
Write-Host "✅ ML2 backed up"

# Extract unique features
Copy-Item ML2/src/features.py -Destination ../src/ml/feature_engineering.py
Write-Host "✅ Features extracted to src/ml/"

# Remove ML2
Remove-Item ML2 -Recurse -Force
Write-Host "✅ ML2 removed"

# Archive model metadata
mkdir archive/models_metadata_20260129
Move-Item models/metadata/*.png archive/models_metadata_20260129/ -ErrorAction SilentlyContinue
Move-Item models/metadata/*.json archive/models_metadata_20260129/ -ErrorAction SilentlyContinue
Move-Item models/metadata/*.txt archive/models_metadata_20260129/ -ErrorAction SilentlyContinue
Move-Item models/metadata/*.csv archive/models_metadata_20260129/ -ErrorAction SilentlyContinue
Write-Host "✅ Model metadata archived"

# Cleanup
Remove-Item ml_code_review.md.resolved -ErrorAction SilentlyContinue

Write-Host "✅ ML folder organized"
```

### Step 3: Update .gitignore (2 minutes)

Add to `.gitignore`:
```gitignore

# ML Folder - Archive and Experiments
ML/archive/*
!ML/archive/.gitkeep
ML/experiments/*
!ML/experiments/.gitkeep
ML/notebooks/*.ipynb_checkpoints

# Scripts - Organized structure
scripts/**/__pycache__/
scripts/**/temp_*.py
```

### Step 4: Verify (3 minutes)

```powershell
# Check structure
Get-ChildItem scripts -Directory
Get-ChildItem ML -Directory

# Run tests
python -m pytest tests/unit/test_storage.py -v

# Verify agent still works
python -c "from src.agents import HybridScoringAgent; print('✅ Imports working')"
```

---

## 🎯 Success Criteria

- ✅ Scripts organized into 4 categories
- ✅ ML2 folder removed (archived)
- ✅ Unique ML2 code extracted to src/ml/
- ✅ Old model metadata archived
- ✅ All tests still passing
- ✅ No broken imports
- ✅ Documentation updated
- ✅ .gitignore updated

---

**Next Steps:** Execute manual steps above, then proceed to Phase 3 (API & Backend Integration).
