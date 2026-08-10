# Archived model artifacts

Superseded, kept for provenance. **Nothing in the application reads these.**
The live model is `models/production/`.

| File | What it was | Why it is here |
|---|---|---|
| `model_metadata_rf_xgboost_ensemble_2025-12-11.json` | RandomForest + XGBoost ensemble, 3-class (High/Medium/Low), 13 features, sentence-BERT enabled, **accuracy 0.608 / macro-F1 0.596** | Described a different model from the one `ATSPredictor` actually loads. Two files both claiming to be "the model" is a provenance problem, so the unused one moved here |
| `tfidf_vectorizer.pkl` | A TF-IDF vectorizer | Orphan — `grep -rn tfidf` finds no reference in `src/`, `scripts/` or `tests/`. Nothing has ever loaded it |

## The provenance question this settles

`models/model_metadata.json` sat at the top of `models/` and was the first thing a reader
saw, but `ATSPredictor(model_dir="models/production")` loads
`models/production/model_metadata.json` — a **Logistic Regression, binary, 30 features**.
Two files, two different models, two different task definitions, no indication which was
current.

The production lineage is the one kept. Worth recording, though, that **the archived 0.608
ensemble is the more believable result.** The production model reports ROC-AUC 1.000, and
that is not a sign it is better — it is a sign the task is trivial. See `TASKS.md` N18:
`Recruiter Decision` is a threshold on `AI Score`, and `Experience` + `Projects Count` alone
reach ROC-AUC 0.9933. No model trained on this dataset can produce an honest number.

If the ensemble approach is ever revived, this metadata is the record of what it scored.
