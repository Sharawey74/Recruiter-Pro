# Archived job datasets — retired 2026-08-09

Kept for reference and rollback. **Nothing in the application reads these files.**
The live corpus is `data/json/jobs.json`, regenerated to the spec in
[`JOBS_DATASET_SPEC.md`](../../../JOBS_DATASET_SPEC.md).

| File | Size | Was it used? |
|---|---|---|
| `jobs_cleaned.json` | 6.8 MB | Yes — the corpus `load_jobs()` read until this date |
| `jobs.json` | 6.0 MB | No — superseded legacy shape; `load_jobs()` kept a dead branch for it |
| `jobs_canonical.json` | 1.8 KB | No — 3-record output sample from `scripts/data_prep/normalize_jobs.py` |

## Why they were retired

Measured against `jobs_cleaned.json` on 2026-08-09 (full detail in `TASKS.md`):

- **6,146 records, but `api.py` sliced to the first 4,000** — 2,146 jobs (34.9%) could never
  be matched or searched, and `/jobs` reported `total: 4000`, misstating the corpus size.
- **The skill vocabulary recognised 2.3% of the corpus's 4,603 distinct skill strings**, and
  **60.9% of jobs had not one required skill in it.** Common terms — `sql`, `html`, `css`,
  `jquery`, `json`, `oop` — were absent entirely.
- **Skill strings were unnormalised free text** scraped from a source that used `|` as a
  separator: `"Ms sql"`, `"Ssrs"`, `"Digital Painting"` — inconsistent casing, no canonical
  form, unmatchable without a vocabulary entry per spelling.
- **486 duplicate `(title, company)` pairs.**
- **No category field**, so the corpus could not be filtered, balanced, or reasoned about by
  job family.
- **Descriptions were template-generated** from one sentence pattern with the skill list
  interpolated, so keyword scoring against them was close to circular.

The data was structurally clean — 100% field presence, no null values, no duplicate
`job_id`, no inverted experience ranges. It was the *content* that could not support honest
matching.

## Restoring one

```bash
git mv data/archive/jobs-legacy-2026-08-09/jobs_cleaned.json data/json/jobs_cleaned.json
```

They also remain in git history, so `git log --all -- data/json/jobs_cleaned.json` finds
them regardless of what happens to this directory.
