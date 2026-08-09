# Recruiter-Pro — Refactor Backlog

**Single source of truth for what gets worked on and in what order.** Open this at the
start of every session.

Derived from three analysis reports plus a first-hand verification pass over the clone on
9 Aug 2026. Every claim below was checked against the actual code — items marked
**✔ verified** were reproduced directly, and the evidence is quoted with the finding.

Conventions for branches, commits and PRs: [`CONTRIBUTING.md`](CONTRIBUTING.md).
Decisions already made and not up for re-litigation: [`docs/adr/`](docs/adr/).

---

## How to use this file

1. Work top-down inside the current phase. Phases are ordered by dependency, not by taste.
2. One task per branch, one branch per PR. The task ID goes in the commit footer
   (`Refs: A0`) so history traces back to the finding.
3. Tick the box and add the PR number when it merges.
4. Anything discovered mid-task that is out of scope gets a new row here, not a bigger PR.

**Priority score** = `(Impact + Risk) × (6 − Effort)`, each on 1–5.
Impact = how much it slows work or degrades the product. Risk = what happens if it is never
fixed. Effort = 1 (under an hour) … 5 (multiple days). Score is a tiebreaker inside a
phase — it never reorders phases, because the dependencies are hard.

**Status:** ☐ not started · ◐ in progress · ☑ done

---

## Scope guardrail

Recorded here so it stays recorded. **No new abstraction unless it has ≥2 real
implementations today.** `LLMProvider` qualifies (rule-based, Ollama, OpenRouter, LangChain
— four). A `ScoringStrategy` interface does not; there is exactly one scoring approach and
an interface would be speculative generality.

Explicitly out of scope for this refactor, permanently: microservices, Celery/Redis task
queues, Postgres migration, auth or multi-tenancy, vector DB / embedding-based semantic
matching, Kubernetes, GraphQL, monorepo tooling, a custom design system, state machine
libraries, repository patterns over SQLite, DI containers, event buses.

Semantic skill matching via embeddings is the one genuinely tempting exclusion. It would
improve Agent 3 without putting an LLM in the hot path, but it needs a vector store, an
embedding model and an index build. Deferred — and the README should say it was considered
and why it was deferred, which reads better than not having considered it.

---

## Phase 0 — Process (session 1) ☑

No production code changed. This exists so everything after it flows through one process.

| # | ID | Task | Status |
|---|---|---|---|
| 0.1 | ① | Branch naming rules, commit format, PR workflow → `CONTRIBUTING.md` | ☑ |
| 0.2 | ① | `.github/PULL_REQUEST_TEMPLATE.md` with root-cause, verification and scoring-impact sections | ☑ |
| 0.3 | ① | `.gitmessage` commit template | ☑ |
| 0.4 | N1 | `.gitignore`: add `Plans/`; fix blanket `docs/` ignore so `docs/adr/` is tracked | ☑ |
| 0.5 | — | ADR-1 LLM allocation, ADR-2 LLMProvider abstraction, ADR-3 unified skill vocabulary | ☑ |
| 0.6 | — | This backlog | ☑ |

> **N1 — found this session, ✔ verified.** `.gitignore:4` was `docs/`, ignoring the entire
> documentation tree. The ADRs would have been written and silently never committed. A
> negation rule alone does not fix this: git does not descend into an excluded directory, so
> `!docs/adr/` under `docs/` is inert. The pattern has to be `docs/*` + `!docs/adr/`.
> Verified with `git check-ignore` in both directions.

---

## Phase 1 — Make it run

**Goal: a fresh clone installs, starts, and runs the feature the README advertises.**
Today it does none of the three. A repo that fails on clone is worse than no repo, and this
is the first thing a reviewer does.

| # | ID | Task | I | R | E | Score |
|---|---|---|---|---|---|---|
| 1.5 | N4 | `npm run build` is broken on `main` | 5 | 5 | 1 | **50** |
| 1.2 | A1 | Split and repair `requirements.txt` | 5 | 5 | 2 | **40** |
| 1.4 | A3 | Remove target leakage, retrain, report the honest number | 4 | 5 | 3 | **27** |
| 1.1 | A2 | Ship the trained model artifacts | 5 | 5 | 1 | **50** ◐ |
| 1.3 | N2 | Resolve the two contradictory model metadata files | 3 | 4 | 2 | **28** |
| 1.6 | N5 | `next@14.2.3` has a published security advisory | 2 | 4 | 2 | **24** |

> **Revised order, 9 Aug 2026.** 1.1 was written as the first task and cannot be. The
> artifacts it says to commit **do not exist**, so producing them means retraining, which
> means 1.2 (install deps) and 1.4 (drop the leaking features) come first — otherwise the
> retrain bakes in a model that 1.4 immediately throws away. Work the phase in the table
> order above, not by number.

### ◐ 1.1 — A2 · The trained model is not in the repo
`branch: fix/repo-ship-model-artifacts` — **partially done, blocked on 1.2 + 1.4**

**✔ Re-verified 9 Aug 2026, and the original diagnosis was wrong in a way that matters.**

The reports said the artifacts exist locally and are merely gitignored. They do not exist:

```
$ find . \( -name "*.joblib" -o -name "*.pkl" \)
./models/tfidf_vectorizer.pkl          # the orphan nothing loads

$ git log --all --diff-filter=A -- "*.joblib"
(empty — never committed in this repository's history)
```

`models/production/` contains only `model_metadata.json`, on disk and in every commit. So
there is nothing to un-ignore. **The fix is not "commit the files", it is "retrain, then
commit"** — and since the current feature set leaks (1.4), the only artifact worth
committing is the retrained leakage-free one. 1.1 and 1.4 are effectively one task.

Confirmed live: `ATSPredictor.load_model()` → `False`, `pipeline.agent3.ml_predictor` is
`None`, `/health` reports `ml_model_loaded: false`. The hybrid ML+rules scoring in the
README headline has never run in this working tree.

**Also corrected — two things this file previously claimed were missing already existed:**

- `/health` **already** returns `ml_model_loaded` (`api.py:172`). It was the *frontend* that
  discarded it, keeping only `status`.
- Startup **already** warned (`api.py:702`), as one line inside ~15 lines of startup output.

**Done this session** (the parts that do not depend on the artifacts existing):

- `.gitignore` — `ats_model.joblib` and `feature_engineer.joblib` named explicitly as an
  allowlist, so a stray experiment artifact in `models/production/` stays ignored. Verified
  with `git check-ignore` on probe files in both directions. Without this, a future
  retrain-then-commit would fail silently in exactly the same way.
- `/match` response now carries `ml_scoring_enabled` and `scoring_mode`. This was the real
  gap: a caller received rule-based scores with no way to tell they were not the advertised
  hybrid ones, because both produce plausible numbers. Verified by a live `/match` call —
  returns `scoring_mode: "rule_based_only"`.
- Startup warning made genuinely loud, naming the consequence, the two expected paths, and
  the exact retrain command.
- Sidebar shows a Scoring indicator (`Hybrid (ML + rules)` / amber `Rules only`) off the
  `ml_model_loaded` the API was already sending.

**The retrain command.** `--data-path` is required — its default is `resumes.csv`, which
does not exist in this repo. Run from the repository root:

```bash
python -m src.ml_engine.train --data-path data/AI_Resume_Screening.csv
```

Add `--run-cv-analysis` to also produce learning curves (slower, writes PNGs to
`models/experiments/`). Optional flags: `--test-size 0.15 --val-size 0.15
--random-state 42`. It writes `ats_model.joblib`, `feature_engineer.joblib` and
`model_metadata.json` into `models/production/`, and a timestamped folder under
`models/experiments/`.

Prerequisites, both currently unmet: the training packages are missing from
`requirements.txt` (1.2 — `scikit-learn`, `joblib`, `xgboost`, `imbalanced-learn`,
`matplotlib`, `seaborn`; all six happen to be installed in this environment already), and
`salary`/`salary_log` must be dropped first (1.4) or the retrain reproduces the leak.

**Still to do, once 1.2 and 1.4 land:**

- [ ] Fix the `--data-path` default so the command works without the flag
- [ ] Confirm the two artifacts appear and `git status` sees them (the ignore rule is ready)
- [ ] Confirm `/health` flips to `ml_model_loaded: true` and the sidebar turns green
- [ ] If they exceed ~5 MB, switch to a GitHub Release plus `scripts/fetch_model.py`

**Measured while verifying:** one CV against 4,000 jobs took **27.6 s** — and that is with
the ML path *disabled*. Restoring the model adds 4,000 per-row `predict_proba` calls on top,
so Phase 3 gets worse before it gets better. Confirms 3.6 as a hard prerequisite for deploy.

### ☑ 1.5 — N4 · `npm run build` fails on `main` — **FIXED**
`branch: fix/frontend-match-type-fields`

**Build now passes: 0 type errors, 0 compile failures, 9/9 pages generated.**

```
✓ Compiled successfully
✓ Generating static pages (9/9)
npx tsc --noEmit → 0 errors   (was 10)
```

The root cause was worse than a type error. `match-card.tsx` reads `match.matched_skills`
and `match.missing_skills`, but **only `/match/single` ever sent them**, nested as
`skills.matched` / `skills.missing`. The main `/match` endpoint the UI actually calls never
sent them at all — so those skill badges have been **permanently empty since they were
written**. Adding the fields to the type alone would have made the build pass and left the
feature dead. Fixed at the source: `/match` now returns both flat, and `Match` declares them.

⚠️ **This makes A0 visible.** A live match now returns:

```
matched_skills: ['programming_languages', 'databases']
```

The badges will render **category names** to the user, because of 2.2. Verified live: a
Python/FastAPI/Postgres CV scored **93.0 against "Product Engineer"**. So 1.5 and 2.2 are
coupled — do not show this UI to anyone before 2.2 lands.

> **Found this session — not in any of the three reports. ✔ Verified against unmodified
> `HEAD` with the working tree stashed, so this is not a side effect of any change here.**

`npm run build` is the exact command Vercel runs on deploy, and it fails:

```
./components/upload/match-card.tsx:78:16
Type error: Property 'matched_skills' does not exist on type 'Match'.
```

`npx tsc --noEmit` reports **10 errors, all in `match-card.tsx`**: `matched_skills` (×3) and
`missing_skills` (×3) are absent from the `Match` interface in `lib/types.ts`, plus 4
consequent implicit-`any` parameters. The API does return both fields; the type never
declared them.

**The frontend cannot currently be deployed at all.** That outranks every UI item in Phase 5
and most of Phase 1. Fix: add both fields to `Match` — which overlaps 5.6, so do them
together and drop the legacy aliases in the same pass.

### ☐ 1.6 — N5 · `next@14.2.3` security advisory
`branch: chore/deps-upgrade-next`

`npm install` reports: `next@14.2.3: This version has a security vulnerability. Please
upgrade to a patched version.` Also flagged: `glob@10.3.10` and `eslint@8.57.1` as
unsupported. Patch Next within the 14.x line first and re-run 1.5's build to confirm
nothing else breaks; treat a major upgrade as separate work.

### ☐ 1.2 — A1 · `requirements.txt` is missing six packages the code imports
`branch: chore/deps-split-requirements`

**✔ Verified by import count across `src/` and `scripts/`.** Imported but *absent* from
requirements: `sklearn` (10), `joblib` (8), `xgboost` (2), `imblearn` (2), `matplotlib` (1),
`seaborn` (1). `pip install -r requirements.txt && python run_api.py` → `ImportError`.

Meanwhile, pinned but with **zero imports anywhere**: `spacy==3.7.2` (0 — the report's
estimate of 1 was generous), `crewai==0.86.0` (0), `openai==1.51.0` (0, despite the comment
`# For OpenRouter/GPT-OSS-20B access`), `ollama==0.4.4` (0 — Agent 4 calls the Ollama HTTP
API through `requests`), `streamlit` (0), `plotly` (0). Keep `nltk` — 3 real imports.

Split three ways:
- `requirements.txt` — runtime API: fastapi, uvicorn, pydantic, pandas, numpy,
  scikit-learn, joblib, pdfminer.six, python-docx, PyMuPDF, python-multipart, pyyaml,
  python-dotenv, requests, nltk
- `requirements-ml.txt` — training only: xgboost, imbalanced-learn, matplotlib, seaborn
- `requirements-dev.txt` — pytest, pytest-cov, pytest-mock, black, ruff, mypy

Re-add `openai` in Phase 4 when `OpenRouterProvider` actually imports it. Dropping the
unused set cuts hundreds of MB off the deploy image, which Phase 6's 512 MB target needs.

### ☐ 1.3 — N2 · Two model metadata files describe two different models
`branch: fix/ml-reconcile-model-provenance`

> **Found this session — not in any of the three reports. ✔ Verified.**

Two tracked metadata files claim to describe "the model", and they do not agree on anything:

| | `models/model_metadata.json` | `models/production/model_metadata.json` |
|---|---|---|
| Trained | 2025-12-11 | 2026-01-29 |
| Model | RandomForest + XGBoost ensemble | Logistic Regression |
| Task | 3-class (High / Medium / Low) | binary |
| Features | 13, sentence-BERT enabled | 30, hand-engineered |
| Accuracy | **0.608** | 0.993 |
| F1 (macro) | 0.596 | 0.996 |

`ATSPredictor(model_dir="models/production")` loads the second one. So the first file is
either a dead artifact from an abandoned approach or evidence that the real pipeline was
replaced without cleanup — and a reviewer opening `models/` sees the 0.608 file first.

The 0.608 ensemble is, notably, the **believable** result. Decide which lineage is the
project's, delete or archive the other, and document the choice. Feeds directly into 1.4.

### ☐ 1.4 — A3 · Model metrics are a red flag, and they are the highest-ROI fix here
`branch: fix/ml-remove-salary-leakage`

**✔ Verified.** `models/production/model_metadata.json`: **precision 1.0, ROC-AUC 1.0,
specificity 1.0, false positives 0**, on train/val/test = 700/150/150.

No real ATS model gets a perfect ROC-AUC. The cause is visible in `feature_names`: `salary`
and `salary_log` are inputs. Salary is a *consequence* of the hire decision — textbook
target leakage. The source `AI_Resume_Screening.csv` is also a small synthetic set where the
label is close to a deterministic function of the columns.

Any senior engineer notices this instantly. Drop `salary`/`salary_log`, retrain, report the
honest number, and add a **"Known limitations & data leakage analysis"** section to the
README explaining what was found and how it was fixed.

This turns the weakest artifact in the repo into the strongest signal in it. Finding
leakage in your own model and writing it up is a better story than a suspicious 1.0.

---

## Job corpus audit — measured 9 Aug 2026

Run against `data/json/jobs_cleaned.json`. **The data itself is clean; what surrounds it is
not.**

### Integrity — good

| Check | Result |
|---|---|
| Records in file | **6,146** |
| Field presence (all 14 fields) | **100%** — no nulls, no missing keys |
| Duplicate `job_id` | **0** |
| `required_skills` empty | **0** |
| `description` empty or under 30 chars | **0** |
| `min_experience_years > max` | **0** |

### Problems — three, in severity order

**① 2,146 jobs (34.9%) are silently discarded.** `api.py:114` does `jobs = jobs[:4000]`
with the comment *"Limit to 4000 jobs for better matching coverage"* — which is backwards,
since it *reduces* coverage. A third of the corpus can never be matched or searched, and
nothing anywhere says so. `/jobs` reports `total: 4000`, so the API actively misreports the
corpus size. **Decide deliberately**: raise the cap, or keep it and state it. Do not leave it
as an unexplained slice. Interacts with 3.3, which proposes trimming to ~500 for deployment
— that is a *deliberate* trim and should be labelled as such in the UI.

**② The skill vocabulary covers almost none of the corpus.** This is the finding that
reframes 2.4, and it is worse than "four vocabularies disagree":

| | |
|---|---|
| Distinct skill strings across all job postings | **4,603** |
| Skills in `skills_canonical.json` | **105** (222 aliases) |
| Distinct job skills the vocabulary recognizes | **108 / 4,603 — 2.3%** |
| Skill *mentions* recognized | **21.2%** |
| **Jobs where not one required skill is in the vocabulary** | **3,745 — 60.9%** |

Measured with the *corrected* alias index from 2.2, so this is the ceiling **after** A0 is
fixed, not before. Common skills simply absent: `sql` (301 mentions), `html` (337),
`css` (221), `jquery` (408), `json` (297), `oop` (283), `xml` (276), `hibernate` (211).

**So fixing A0 is necessary but not sufficient.** Unifying four small vocabularies into one
small vocabulary still leaves ~61% of jobs with nothing to match on. 2.4 must also **grow**
the vocabulary from the corpus — extract the top ~500 skill strings by frequency, map them to
canonical entries, and re-measure coverage. Target: >80% of mentions. Add the coverage number
to the test suite so it cannot silently regress.

**③ 486 duplicate `(title, company)` pairs.** Distinct `job_id`s, same role at the same
company. Harmless for scoring, but a candidate sees the same job repeated in their top
matches, which looks broken. Deduplicate on display, or merge at load.

### Distribution — reasonable, no action needed

`remote_type` remote 3,059 / hybrid 1,807 / on-site 1,280 · `employment_type` full-time
5,814 / contract 182 / internship 147 / part-time 3 · `seniority_level` mid 3,839 /
senior 948 / manager 599 / entry 536 / lead 179 / executive 45 · 6 countries led by
USA 1,053.

---

## Phase 2 — Make it correct

**Goal: the scores mean something.** Everything downstream inherits this, which is why it
comes before performance. Making a wrong answer arrive faster is not progress.

| # | ID | Task | I | R | E | Score |
|---|---|---|---|---|---|---|
| 2.1 | A0-T | Regression test: `normalize("python") != normalize("java")` | 4 | 5 | 1 | **45** |
| 2.2 | A0 | Flatten the canonical skill index | 5 | 5 | 2 | **40** |
| 2.3 | W | One source of truth for scoring weights | 3 | 4 | 1 | **35** |
| 2.4 | A0b | Merge four skill vocabularies into one | 5 | 4 | 3 | **27** |
| 2.5 | N3 | Unit tests for Agents 1, 2, 3 — currently zero | 4 | 5 | 3 | **27** |
| 2.6 | A0c | Delete `src/utils/` — 619 LOC, zero imports | 2 | 2 | 1 | **20** |
| 2.7 | ② | Agent contracts: typed results, constructor injection, no `__init__` side effects | 4 | 3 | 4 | **14** |

### ☐ 2.1 — Write the regression test first
`branch: test/agent3-skill-normalization-regression`

Red before green. Assert `_normalize_skills(["python"]) != _normalize_skills(["java"])`,
and that a Python CV scores near zero skill match against a Java-only job. Confirm it
**fails** against today's code and paste the failure into the PR. This test is the guard
that should have existed, and it is the single most defensible artifact of the whole
refactor.

### ☐ 2.2 — A0 · Skill normalization collapses every skill into its category
`branch: fix/agent3-skill-category-collapse`

**✔ Verified by reading `agent3_scorer.py:510–526` against the real
`skills_canonical.json`.** This is the worst bug in the repository.

`_get_canonical_skill` assumes the file is flat — `{canonical: [aliases]}`. It is nested by
category:

```json
{ "comment": "...",
  "programming_languages": { "Python": ["python","py"], "Java": ["java","jdk"] },
  "frameworks":            { "React": ["react"], "Django": ["django"] } }
```

So `for canonical, aliases in self.skills_database.items()` binds `canonical` to
`"programming_languages"` and `aliases` to the **inner dict**. `[a.lower() for a in
aliases]` then iterates that dict's *keys* — `["python", "javascript", "java", …]` — the
membership test passes, and the function returns **the category name**.

| CV / job skill | normalizes to |
|---|---|
| `python`, `java`, `javascript` | `programming_languages` |
| `react`, `django` | `frameworks` |
| `mysql` | `databases` |
| `docker` | `devops` |

Both `cv.skills` and `job.required_skills` go through `_normalize_skills`, so **a Python
developer scores a perfect skill match against a Java job.** Skills are 50% of the
rule-based score (`agent3_scorer.py:109`), which is 60% of the hybrid score — roughly a
third of every score reported by this product is noise, biased upward. It fails silently:
no exception, no log line. It also explains why the matching engine "works" but the results
feel arbitrary.

Fix — build the alias index once at load time and drop the `comment` key:

```python
def _build_alias_index(raw: dict) -> dict[str, str]:
    index = {}
    for category, entries in raw.items():
        if not isinstance(entries, dict):      # skips "comment"
            continue
        for canonical, aliases in entries.items():
            index[canonical.lower()] = canonical
            for a in aliases:
                index[a.lower()] = canonical
    return index
```

Lookup becomes O(1) instead of a linear scan, which is also most of 3.2 and 3.4 — **which
is exactly why A0 must land before the performance work.** They rewrite the same function.

### ☐ 2.3 — W · Scoring weights are declared in YAML and ignored in code
`branch: fix/agent3-weights-single-source`

**✔ Verified.** `config/agents.yaml` declares `skill 0.60 / experience 0.25 / education 0.10
/ keyword 0.05`. `agent3_scorer.py:108–114` hardcodes `skills 0.50 / title 0.17 / experience
0.20 / education 0.08 / keywords 0.05` — a different split, and it includes a `title` term
the YAML has never heard of. The YAML is decorative.

Pick one set, delete the other, load from config, and validate the sum is 1.0 at startup so
this cannot drift again. Ten-line fix that reads very badly if a reviewer finds it first.

### ☐ 2.4 — A0b · Four competing skill vocabularies
`branch: refactor/data-unified-skill-vocabulary`

**✔ Verified.** Four sources of truth that disagree, which is why A0 went unnoticed:

| Location | Size | Used? |
|---|---|---|
| `Agent2.SKILLS_DATABASE` (class constant) | 178 skills | ✅ extraction |
| `Agent3._find_skill_matches` local `synonyms` dict | 45 groups | ✅ matching |
| `data/dictionaries/skills_canonical.json` | 8 categories | ⚠️ loaded, broken (A0) |
| `src/utils/skill_extraction.py` | 6 functions | ❌ never imported |

Add a skill in one place and the other three do not know. Merge all four into one
`data/skills.json`, load it once into the alias index from 2.2, and inject it into Agents 2
and 3 rather than each owning a private copy. See [ADR-3](docs/adr/003-unified-skill-vocabulary.md).

### ☐ 2.5 — N3 · The core pipeline has no unit tests
`branch: test/agents-unit-coverage`

> **Found this session — not in any of the three reports. ✔ Verified.**

The reports credit "15 test files, good coverage story". That coverage is real but it is
pointed almost entirely at the ML engine and storage, **not at the product**:

| `tests/unit/` covers | Agents 1 / 2 / 3 |
|---|---|
| `feature_engineering` (18), `cross_validation` (16), `evaluation_criteria` (15), `storage` (14), `data_loader` (10), `agent4_modes` (4), `model_trainer` (4), `ats_predictor` (3) | **zero unit tests** |

Only two integration files touch the agents at all (`test_pipeline.py`,
`test_enhanced_matching.py`), end-to-end, where a silently wrong skill normalization still
produces a plausible-looking number. **This is the structural reason A0 survived to
production.** A single unit test on `_get_canonical_skill` would have caught it on day one.

Add unit tests per agent — parse fidelity for Agent 1, field extraction for Agent 2, and a
determinism test for Agent 3 (same inputs → byte-identical breakdown, per [ADR-1](docs/adr/001-llm-allocation.md)).

### ☐ 2.6 — A0c · `src/utils/` is entirely dead code
`branch: chore/remove-dead-utils`

**✔ Verified** — grepped every import across `src/`, `tests/` and `scripts/`: zero hits.

| File | LOC |
|---|---|
| `src/utils/skill_extraction.py` | 251 |
| `src/utils/text_processing.py` | 216 |
| `src/utils/job_normalizer.py` | 147 |
| `src/utils/validators.py` | 5 |

Delete `text_processing.py`, `job_normalizer.py`, `validators.py`. Salvage the useful parts
of `skill_extraction.py` into the unified vocabulary from 2.4, then delete the original.
Also delete `scripts/setup/`, which contains only an empty `__init__.py`. Sequence this
**after** 2.4 so the salvage has somewhere to land.

### ☐ 2.7 — ② · One contract for all four agents
`branch: refactor/agents-typed-contracts`

The honest answer to "designed correctly" is a single rule, not new patterns: **each agent
takes its dependencies via constructor injection, holds no mutable per-request state, and
returns a typed result object.** That one rule fixes the A7 race (4.3), makes each agent
independently testable, and needs no framework.

| Agent | Today | Target |
|---|---|---|
| **1 Parser** | 272 LOC. `mkdir()` **side effect in `__init__`** (line 53); 4× `print()`; writes profile JSONs to `data/processed/raw_profiles/` that nothing reads | Pure `parse(path) -> RawDocument`. No disk writes, logger only. Reject <50 extracted chars so a scanned-image PDF fails loudly instead of returning empty |
| **2 Extractor** | 373 LOC. Owns a private 178-skill `SKILLS_DATABASE`. Name detection guarded by a hardcoded blocklist of Cairo neighbourhoods (`maadi`, `zamalek`, `heliopolis`, `dokki`) — heuristics overfit to a handful of test CVs | Inject the shared vocabulary. Return typed `ExtractedProfile`, not a bare dict. Record `extraction_method` per field |
| **3 Scorer** | 540 LOC, one class | Split into `SkillMatcher` / `ExperienceScorer` / `EducationScorer` / `MLScorer` / `HybridScorer`. **No further** — five small classes, not a framework |
| **4 Explainer** | 406 + 247 LOC behind a factory, both hardcoding Ollama | Phase 4 |

---

## Phase 3 — Make it fast

**Goal: a match completes in under three seconds.** This is also a hard prerequisite for
deployment — the target free tier gives 0.1 CPU, and today's sequential loop will simply
time out there.

**The headline number.** `POST /match` scores one CV against ~4,000 jobs sequentially, and
per job it rebuilds a 45-entry synonym dict twice, builds a 1-row DataFrame for a single
sklearn prediction, and **opens a new SQLite connection, INSERTs, commits and closes it.**
The frontend timeout is set to 150 seconds with the comment `// Increased to 150 seconds
(2.5 minutes) for 3000 jobs` — that comment is the smoking gun.

| # | ID | Task | I | R | E | Score |
|---|---|---|---|---|---|---|
| 3.1 | B1 | Stop writing 4,000 rows per upload | 5 | 4 | 2 | **36** |
| 3.2 | B2 | Hoist the synonym dict to a module constant | 4 | 2 | 1 | **30** |
| 3.3 | B6 | Stop shipping 13 MB of duplicated JSON | 4 | 3 | 2 | **28** |
| 3.4 | B4 | Precompute the CV's normalized skill set once | 3 | 2 | 2 | **20** |
| 3.5 | B5 | Cheap pre-filter before expensive scoring | 3 | 2 | 2 | **20** |
| 3.6 | B3 | Vectorize ML scoring | 4 | 2 | 3 | **18** |

### ☐ 3.1 — B1 · Biggest single win
`branch: perf/pipeline-batch-persistence`

**✔ Verified** at `pipeline.py:162` and `:237` — `self.db.save_match(...)` is called inside
the job loop, and `database.py:42` opens a fresh `sqlite3.connect` per call. The endpoint
returns `top_k=10` and persists all ~4,000, so 99.75% of the rows are noise that also bloats
`/history`.

Benchmarked pattern comparison: new connection + commit per row ≈ **7.16 s / 2,000 rows**;
one connection + `executemany` ≈ **0.0098 s** — **731× faster**. At 4,000 jobs that is
~14 seconds of pure SQLite overhead on every upload.

Move persistence out of the loop: sort → slice `top_k` → one `save_matches_batch(top)` on a
single connection. Add `PRAGMA journal_mode=WAL` and `synchronous=NORMAL` on connect.
**~14 s → ~0.01 s.**

### ☐ 3.2 — B2 · 80,000 dictionary rebuilds per upload
`branch: perf/agent3-hoist-synonym-index`

**✔ Verified** at `agent3_scorer.py:203–244` — a 45-key dict literal is constructed inside
`_find_skill_matches`, on every call. `_has_skill_match` (line 275) calls
`_find_skill_matches` again for every missing skill, so the rebuild count multiplies.
Measured waste: **3.26 s per upload**.

Move it to a module-level constant and precompute a flat `ALIAS_TO_CANONICAL` once — which
also turns an O(45) scan into an O(1) lookup. Folds into the 2.2 index; do not build two.

### ☐ 3.3 — B6 · 13 MB of duplicated job data
`branch: chore/data-trim-job-corpus`

`data/json/jobs.json` (5.8 MB, legacy shape) and `jobs_cleaned.json` (6.5 MB, current shape)
are both committed. `load_jobs()` reads only the cleaned one but keeps the legacy branch
alive as dead code (`api.py:78–90`). Delete `jobs.json` and that branch. Ship a trimmed
`jobs.sample.json` (300–500 jobs) as the demo corpus, full file via Release or Git LFS.
500 jobs demos exactly as well as 4,000 and is the difference between fitting in 512 MB and
not.

### ☐ 3.4 — B4 · Normalize the CV once, not once per job
`branch: perf/agent3-precompute-cv-skills`

`_score_skills` calls `self._normalize_skills(cv.skills)` (line 161) inside the per-job
loop. The CV does not change. Normalize once before the loop and pass the frozen set in.

### ☐ 3.5 — B5 · Skip the expensive path for obviously irrelevant jobs
`branch: perf/agent3-cheap-prefilter`

Every job currently gets the full treatment. Gate first: zero shared required skills →
assign a floor score and skip title similarity, ML and education scoring. Typically
eliminates 80–90% of the corpus. Results stay identical for anything that could plausibly
reach the top 10 — assert that in a test rather than assuming it.

### ☐ 3.6 — B3 · One `predict_proba`, not 4,000
`branch: perf/agent3-vectorized-ml-scoring`

**✔ Verified** at `agent3_scorer.py:467–491` — `_get_ml_score` builds a dict, wraps it in a
1-row DataFrame, transforms and predicts, 4,000 times. `ATSPredictor.predict_batch` already
exists, is never called, and internally just loops `predict()` anyway.

The only per-job feature is `Job Role`. Build one 4,000-row DataFrame, one `transform`, one
`predict_proba` → a 4,000-length array. Rewrite `predict_batch` to actually be vectorized.
**Seconds → tens of milliseconds.**

---

## Phase 4 — Make it safe

**Goal: safe to put on a public URL.** Cheap fixes, and the first things a reviewer checks.
Agent 4's redesign lives here because the stateless rewrite and the A7 race fix are the
same work — see [ADR-2](docs/adr/002-llm-provider-abstraction.md).

| # | ID | Task | I | R | E | Score |
|---|---|---|---|---|---|---|
| 4.1 | A4 | Fix the CORS wildcard + credentials combination | 2 | 5 | 1 | **35** |
| 4.2 | A5 | Cap upload size and validate content type | 2 | 5 | 1 | **35** |
| 4.3 | SEC | `OPENROUTER_API_KEY` from env only, `.env.example`, never logged | 2 | 5 | 1 | **35** |
| 4.4 | RL | Endpoint rate limiting + top-K explanation cap + daily quota counter | 2 | 5 | 2 | **28** |
| 4.5 | A8 | Replace bare `except:`; count and log skipped jobs | 2 | 3 | 1 | **25** |
| 4.6 | A7 | Stop mutating the shared pipeline singleton per request | 3 | 5 | 3 | **24** |
| 4.7 | ③ | `OpenRouterProvider` behind the provider protocol | 3 | 3 | 3 | **18** |
| 4.8 | A6 | Migrate deprecated startup hooks to `lifespan` | 1 | 2 | 1 | **15** |
| 4.9 | ② | Extract the `LLMProvider` protocol from Agent 4 | 4 | 3 | 4 | **14** |

### ☐ 4.1 — A4 · CORS
`branch: fix/api-cors-wildcard-credentials`

**✔ Verified** at `api.py:45–47`: `allow_origins=["*"]` **with** `allow_credentials=True`.
Browsers reject that combination outright, and it is a flagged anti-pattern. `config.py:111`
already defines `cors_origins` and `config.py:205` already reads a `CORS_ORIGINS` env var —
the API module simply never consults either. Wire it up: default
`["http://localhost:3000"]`, the Vercel URL in production, `allow_methods=["GET","POST","DELETE"]`.

### ☐ 4.2 — A5 · Unbounded upload
`branch: fix/api-upload-size-limit`

**✔ Verified** — `await file.read()` straight into memory at `api.py:247`, `:329` and `:463`
with no cap. `config.py:113` defines `max_upload_size_mb: int = 10`, also never used. A
500 MB POST takes the process down. Check `file.size` before reading, reject >10 MB with
413, and validate real content type rather than trusting the extension.

### ☐ 4.3 — SEC · Secrets hygiene, before the first commit that touches a key
Env only. Never committed, never logged, never returned in a response. Add `.env.example`
with the key name and no value. Confirm `.env` is gitignored *before* that first commit,
not after.

### ☐ 4.4 — RL · Two rate-limit layers plus a hard cap
`branch: feat/api-rate-limiting-and-quota`

Two layers solving different problems, plus the cap that actually matters:

| Layer | Protects | Setting |
|---|---|---|
| Endpoint (`slowapi`, ~15 lines) | the instance from abuse on a public URL | `/match` 5/min/IP, `/upload` 10/min/IP |
| Provider (semaphore + backoff) | the LLM quota from 429s | ≤2 concurrent calls; respect `Retry-After` |
| **Top-K explanation cap** | **the quota, at the source** | **K ≤ 3, hard** |

`explain=true` currently generates an explanation for **every** job scoring ≥ 0.6 — on a
public demo that is unbounded. The cap is the real protection; the rate limiter is the
backstop. Add a daily request counter in SQLite that auto-switches to rule-based at 90% of
quota, so running out **degrades the demo instead of breaking it**.

### ☐ 4.5 — A8 · Silent failure handling
`branch: fix/api-specific-exception-handling`

**✔ Verified** — bare `except:` at `api.py:292`, `:434`, `:526`, all around temp-file
cleanup. Use `except OSError`. Separately, `load_jobs()` swallows per-record parse failures
with `except Exception: continue`, so there is no way to know how many of the ~4,000 jobs
never load. Count them and log at startup: `Loaded 3,847 jobs, skipped 153 malformed`.

### ☐ 4.6 — A7 · Per-request mutation of a module-level singleton
`branch: fix/api-stateless-explainer-invocation`

**✔ Verified** at `api.py:335–362`. The `/match` handler reassigns `pipeline.agent4` and
`pipeline.agent4.llm_available` on a module-level singleton, then restores them in a
`finally`. With two concurrent requests, request B's toggle leaks into request A. Under
uvicorn with more than one worker this is a live race — and the restore is skipped entirely
on some raise paths.

Do not mutate the singleton. Pass `use_llm` / `use_langchain` down as arguments to
`process_cv_batch(...)` and let Agent 4 decide per call. This is the same change as 4.9.

### ☐ 4.7 / 4.9 — ②③ · Agent 4 provider abstraction, then OpenRouter
`branch: refactor/agent4-provider-abstraction` → `feat/agent4-openrouter-provider`

**✔ Verified** — `config.py:89` declares `provider: str = "ollama"  # ollama, openai,
anthropic` and **nothing in the repository ever reads it**. Both implementations hardcode
Ollama: `agent4_llm_explainer.py` pings `/api/tags` and POSTs `/api/generate` with Ollama's
payload shape; `agent4_langchain_explainer.py` instantiates `ChatOllama` directly. And
`openai` is pinned with an OpenRouter comment but never imported. **The OpenRouter intent
exists only as a comment** — this is a real refactor, not a config tweak.

```python
class LLMProvider(Protocol):
    def is_available(self) -> bool: ...
    def explain(self, batch: list[ExplanationContext]) -> list[Explanation]: ...
```

`RuleBasedProvider` (always available, zero network — the production default) ·
`OllamaProvider` (local dev) · `OpenRouterProvider` (hosted demo, via the `openai` SDK
pointed at `https://openrouter.ai/api/v1`) · `LangChainProvider` (optional fourth).
Selected by `config.llm.provider`, finally read. Rationale and the two-implementation
guardrail: [ADR-2](docs/adr/002-llm-provider-abstraction.md).

**Order matters: 4.9 before 4.7.** Adding a provider to today's per-request-mutated
singleton bakes in the A7 race.

---

## GUI audit — every page and component, reviewed 9 Aug 2026

Reviewed in a real browser against a live backend, with all caches and browser storage
cleared first, so every empty state below is a genuine first-run experience.

### Pages

| Route | Renders | State | Findings |
|---|---|---|---|
| `/` Dashboard | ✅ | works | **N6** hydration errors (6 on first paint) · **N11** says "PDF, DOCX", omits TXT · **A9** no error toast · **B8** 2.5 s fake delay · has its own uploader, duplicating `/upload` |
| `/upload` | ✅ | works | **N10** advertises "Limit 200MB per file" · **N8** no nav link — unreachable from the UI · **A10** drag-drop silently drops DOCX/TXT |
| `/jobs` | ✅ | works | **B7** search box confirmed dead · **N8** no nav link · **N11** says "3,000+" (4,000 load, 6,146 exist) |
| `/results` | ✅ | clean empty state | **N11** "max 5 jobs each" but `/match` defaults `top_k=10` |
| `/history` | ✅ | clean empty state ✓ | correct after cache clear · double-fetches `/match/history` |
| `/shortlist` | ✅ | clean empty state ✓ | tabs + counters all render at 0 correctly |
| `/_not-found` | ✅ | default | no custom 404 |

**All six pages render, no crashes, no failed requests, no 4xx/5xx.** Empty states on
`/results`, `/history` and `/shortlist` are genuinely good — clear message plus a next
action. `/jobs` and both uploaders work. The structure is sound; the problems are wiring
and copy, not layout.

### Components

| Component | State | Findings |
|---|---|---|
| `layout/sidebar` | ✅ | **N8** lists only 4 of 6 pages · Scoring indicator added this session, verified live |
| `layout/header` | ⚠️ | 10 lines, presentational only — `/` and `/upload` do not use it, so heading styles diverge |
| `upload/match-card` | ⚠️ | Was the build break (1.5). Skill badges now populated — but will show **category names** until 2.2 |
| `upload/match-summary` | ✅ | renders |
| `ui/circular-progress` | ✅ | renders |
| `ui/skill-badge` | ✅ | renders; `matched` / `missing` variants both used |

### New findings

**☐ N8 · Two of six pages are unreachable from the UI** — `fix/frontend-sidebar-nav`
`sidebar.tsx` `navItems` lists Dashboard, Results, History, Shortlist. **`/upload` and
`/jobs` have no link anywhere in the app** — reachable only by typing the URL. `/upload` is
the fuller of the two upload flows. Either add both to the nav, or delete `/upload` and keep
the dashboard uploader — but decide, because shipping an orphaned page reads as unfinished.

**☐ N9 · Every page has the same browser-tab title** — `fix/frontend-page-metadata`
`layout.tsx:7` sets `title: "AI Resume Matcher - Dashboard"` and **no page exports its own
`metadata`**. Every tab, bookmark and history entry says "Dashboard", including `/jobs` and
`/history`. One `export const metadata` per page.

**☐ N10 · The upload UI advertises a 200 MB limit** — `fix/frontend-upload-limit-copy`
`upload/page.tsx:124` says *"Limit 200MB per file"*. `config.py:113` says 10 MB. The server
enforces **nothing** (A5). So the UI actively invites the exact request that takes the
server down. Fix the copy and the enforcement together — this makes 4.2 more urgent than its
score suggests.

**☐ N11 · Four pieces of copy state facts that are not true** — `fix/frontend-copy-accuracy`
Cheap to fix, and each one is visible to a visitor:

| Where | Says | Reality |
|---|---|---|
| `page.tsx:292` | "Supported formats: PDF, DOCX" | TXT also supported |
| `upload/page.tsx:124` | "Limit 200MB per file" | no limit enforced; config says 10 MB |
| `jobs/page.tsx:54` | "3,000+ job descriptions" | 4,000 loaded, 6,146 exist |
| `results/page.tsx:78` | "max 5 jobs each" | `/match` defaults to `top_k=10` |

---

## Phase 5 — Make it feel good

**Goal: what a visitor actually experiences.** Grounded in what is verifiably weak — this
is not a redesign, and it does not add a component library. `clsx` + `tailwind-merge` + the
existing `cn()` helper in `lib/utils.ts` are enough.

| # | ID | Task | I | R | E | Score |
|---|---|---|---|---|---|---|
| 5.1 | A9 | Landing page swallows errors — the one page with no toast | 3 | 3 | 1 | **30** |
| 5.2 | A10 | Unify file acceptance between drag-drop and file picker | 2 | 2 | 1 | **20** |
| 5.3 | B7 | `/jobs` search box does nothing | 3 | 2 | 2 | **20** |
| 5.4 | B8 | Delete the fake progress delay; show real `processing_time` | 4 | 1 | 2 | **20** |
| 5.5 | B9 | One state source instead of five `localStorage` keys | 3 | 3 | 3 | **18** |
| 5.6 | B10 | `Match[]` not `any[]`; one field shape, not legacy + new | 2 | 2 | 2 | **16** |
| 5.7 | B11 | Loading skeletons and empty states | 3 | 1 | 2 | **16** |
| 5.8 | ⑤ | Drop `recharts` and `class-variance-authority`; delete `cache.py`; dedupe `/history` | 1 | 2 | 1 | **15** |

### ☐ 5.1 — A9
**✔ Verified** at `frontend/app/page.tsx:117`. Five of six pages wire `toast.error`
correctly — `upload`, `shortlist`, `results`, `history`, `jobs`. The gap is exactly one
file, and it is the landing page: on failure the spinner resets to idle and **nothing else
happens**. It is also the slowest call in the app, so it is the one most likely to fail.
Add a toast distinguishing timeout / 503 no-jobs / 500, matching the pattern the other five
already use.

### ☐ 5.1b — N6 · Hydration mismatch on the landing page
`branch: fix/frontend-landing-hydration`

> **Found this session, in the browser. ✔ Verified — `page.tsx` is untouched by this
> session's work, so it is pre-existing.**

`frontend/app/page.tsx:352` renders `ID: v{Math.floor(Math.random() * 100)}0ZXY` directly in
JSX, so the server and the client generate different numbers. React logs
`Text content did not match. Server: "64" Client: "34"`, then
`An error occurred during hydration. The server HTML was replaced with client content` —
six console errors on first paint of the landing page, and React discards the server-rendered
DOM for the whole subtree. `page.tsx:318` calls `new Date().toLocaleDateString()` in render
for the same reason and will do the same across a midnight boundary or a timezone
difference.

Fix: generate the ID once in a `useEffect` (or `useId`), or drop the decorative ID entirely.
Pairs naturally with 5.1 — same file, same landing page.

### ☐ 5.2 — A10
`handleDrop` checks `file.type === 'application/pdf'` and **silently discards** DOCX and TXT
— both of which the backend supports. `handleFileInput` has no check at all. One shared
`acceptFile()` validating `.pdf/.docx/.txt` plus size, with a toast on reject.

### ☐ 5.3 — B7
`frontend/lib/api.ts` sends a `search` param. `api.py:180` `get_jobs()` accepts only `skip`
and `limit`. The search box slices the same page every time — very visible in a demo.
Implement server-side (case-insensitive over title / company / skills) and add `remote_type`
and `seniority_level` filters while in there.

### ☐ 5.4 — B8
**✔ Verified** — `page.tsx:101` (1000 ms), `:104` (1000 ms), `:112` (500 ms):
**2.5 seconds of deliberately added latency** animating a pipeline that already takes a
minute. Once Phase 3 lands and matching is ~2 s, the fake delay would be more than half the
wall time.

Delete the timeouts. Keep the 4-agent visual — it is a genuinely good portfolio detail —
but make it real: drive the stages off the actual request lifecycle, or stream stage events
via SSE. Return the real `processing_time`, currently hardcoded `None` at `api.py:423`, and
display it. **"Matched against 4,000 jobs in 1.8 s" is the single highest-impact UI change
in this phase** — it makes the Phase 3 engineering visible to someone who will never read
the code.

### ☐ 5.5 — B9
Match results are `JSON.stringify`'d into `localStorage` on every change; full result sets
with explanations will exceed the ~5 MB quota and throw `QuotaExceededError`, uncaught,
inside a `useEffect`. Five-plus keys (`matchResults`, `latestAnalysis`, `selectedFileName`,
`shortlist`, `candidateStatus`) are cleared by hand in `history/page.tsx`. One React Context
or Zustand store as the source of truth; persist a small summary only; wrap writes in
try/catch; centralize clearing.

### ☐ 5.6 — B10
`useState<any[]>` for match results and `catch (error: any)` across six files, while
`lib/types.ts` already has a perfectly good `Match` interface. Every `Match`/`Job` also
carries duplicated legacy fields (`company` *and* `company_name`, `location` *and*
`location_city`) — the API builds both and every component does `match.company_name ||
match.company`. Pick one shape; deleting the aliases removes ~40 lines from `api.py`.

### ☐ 5.7 — B11
Pages fetch in `useEffect` with no skeleton and no empty state: during load a visitor sees a
bare layout, and with no data, nothing at all. Tailwind `animate-pulse` skeleton cards plus
a real empty state. Half a day, and it is the difference between "student project" and
"product". Add `aria-live` on score values while here.

### ☐ 5.8 — ⑤
`recharts` and `class-variance-authority` are in `package.json` with no usages —
`react-dropzone` *is* used (`upload/page.tsx`), so keep it. `src/storage/cache.py` is a
docstring and `pass`; either implement a ~30-line TTL cache (genuinely useful for LLM
explanations) or delete it and the config keys it advertises — a "TODO: Phase 3" file reads
as abandoned work. `/history` and `/match/history` are near-identical; keep one.

---

## Phase 6 — Build clean

> **Deploy is deferred, 9 Aug 2026, by decision.** The goal of this phase is now **the app
> builds and runs with zero errors and zero compile failures** — not shipping it anywhere.
> Deploy items are parked at the bottom and are not worked until the rest of the phase is
> green. Getting a correct app first is the right order; a deployed wrong answer is worse
> than an undeployed one.

**Definition of done for "builds clean":**

| Gate | Status |
|---|---|
| `npx tsc --noEmit` → 0 errors | ✅ **done** (was 10) |
| `next build` → compiles, all pages generated | ✅ **done** (9/9) |
| Zero console errors on every page at runtime | ❌ blocked by **N6** |
| `pytest` green | ❌ **29 failed, 10 errors, 109 passed** (26% failing) |
| `ruff` / `black` clean | ❌ not wired |
| App starts from a clean clone | ❌ blocked by **1.2** |

| # | ID | Task | I | R | E | Score |
|---|---|---|---|---|---|---|
| 6.0 | N6 | Zero runtime console errors — fix the hydration mismatch | 4 | 3 | 1 | **35** |
| 6.7 | — | Run `pytest`; fix or quarantine failures; record the real number | 4 | 4 | 2 | **32** |
| 6.1 | B12 | GitHub Actions: pytest + ruff + black + `next build` | 4 | 3 | 2 | **28** |
| 6.3 | ⑥ | `black`, `ruff`, `mypy` on `src/` — wired into CI, not just installed | 3 | 2 | 2 | **20** |
| 6.5 | B13 | README: honest scope, "what I fixed" | 4 | 1 | 3 | **15** |
| 6.6 | ⑤ | `models/experiments/` (10 PNGs, ~800 KB) → Release; delete orphan `tfidf_vectorizer.pkl` | 1 | 1 | 1 | **10** |
| — | — | *parked:* Docker, Vercel/Render deploy, hero GIF, live link | — | — | — | *deferred* |

### ☐ 6.7 — N12 · A quarter of the test suite fails
`branch: test/repair-suite-baseline`

> **Measured 9 Aug 2026 — `python -m pytest -q --no-cov`. Not in any of the three reports,
> which described the 15 test files as "good coverage story". It is a count, not a result.**

```
29 failed, 10 errors, 109 passed  in 107s        (148 total, 26% not passing)
```

Four distinct causes, and the first two mean these tests have **never** passed against this
codebase:

**① Tests target an API that does not exist — ~19 failures.**
`test_api_endpoints.py` and `test_e2e_resume_scoring.py` call `/api/v1/health`,
`/api/v1/score`, `/api/v1/batch`, `/api/v1/model-info`. The real API serves `/health`,
`/match`, `/upload`, `/jobs`. Every one returns 404. This is not drift — no version of this
repo has served `/api/v1/*`. These test a design that was never built.

**② `JobPosting` schema drift — 10 errors.**
`test_pipeline.py` constructs `JobPosting(job_id, title, required_skills, preferred_skills,
min_experience_years, education_level, description)`. The model now also requires
`company_name`, `location_city`, `location_country`, `remote_type`, `employment_type`,
`seniority_level`, `max_experience_years` → 6–7 validation errors per instantiation. The
model gained required fields; the fixtures were never updated. **This is why Agent 3 has no
working test coverage** (2.5) — the tests that would have exercised it cannot construct a job.

**③ Production signatures changed under the tests — 5 failures.**
`test_cross_validation.py`: `plot_validation_curve()` missing a required argument,
`too many values to unpack` ×3. The implementation's return arity changed.

**④ Missing fixture + a stale assertion — 2 failures.**
`test_enhanced_matching.py` needs `test_resume_abdelrahman.txt`, which is not in the repo.
`test_data_loader.py::test_missing_values_handling` asserts `3 == 30`.

**Order:** ② first — it unblocks the Agent 3 coverage that 2.5 depends on, and it is
mechanical. Then ③ and ④. Then decide on ①: either build the `/api/v1` surface those tests
describe, or **delete them**. Do not leave 19 tests asserting against an imaginary API —
they are worse than no tests, because they make the suite look larger than it is.

Also drop `--cov=src --cov-report=html` from `pytest.ini`'s `addopts` so the suite can be run
quickly during a fix loop; move coverage to an explicit CI invocation.

**Until this is green, 6.1 (CI) has nothing meaningful to enforce and "builds clean" is
only true of the frontend.**

### ☐ 6.1 — CI is the highest-signal cheap win in this phase
There is no `.github/workflows/`. There are 15 test files that **nobody browsing the repo can
tell exist**. A green CI badge on a repo with real tests is one of the highest-signal things
on a portfolio, and it is an afternoon of work.

### ☐ 6.5 — README
24 KB of text with no visual, and recruiters spend about twenty seconds. Hero GIF of the
match flow above the fold; architecture deep-dives below it; a live demo link that works on
the first click. Then the two sections that carry the most weight:

- **Known limitations** — the leakage finding (1.4), the demo running rule-based
  explanations, the trimmed corpus, and semantic matching considered-and-deferred.
- **What I fixed and why** — A0 in particular. *Finding a silent correctness bug in your own
  scoring engine, explaining the root cause, and shipping a regression test is a stronger
  signal than any feature you could add.* Most portfolio projects cannot show that, because
  nobody looked hard enough.

Architecture diagram in Mermaid — GitHub renders it natively.

### ☐ 6.2 — Deploy
**Vercel** (frontend, root directory `frontend/`, `NEXT_PUBLIC_API_URL` set) +
**Render** free web service (backend). Two hard constraints, both already handled upstream:
512 MB RAM needs 1.2 and 3.3 done; 0.1 CPU makes **all of Phase 3 a prerequisite, not an
optimization**. Mitigate Render's 15-minute spin-down with an uptime pinger on `/health`,
and have the frontend show "waking up the server…" if `/health` exceeds 3 s — that one
message turns a confusing 60-second hang into a deliberate-looking detail.

Ollama cannot run on any free tier (a 3B model needs several GB), so the hosted demo ships
with the rule-based or OpenRouter provider, and the README says so.

---

## Open question — blocks nothing until Phase 4

**Is the hosted demo's default explanation mode rule-based or OpenRouter?**

- **Rule-based default, OpenRouter opt-in via a UI toggle** — zero cost risk, but a visitor
  who never toggles never sees the LLM feature at all.
- **OpenRouter default, capped** — the demo shows the best work immediately, but needs the
  budget guard, the concurrency cap and the top-3 explanation limit all working first.

The second is better *provided the guards in 4.4 land first* — an LLM explanation is the
differentiator, and a demo nobody interacts with proves nothing. But it is real quota on a
public URL, so it is a decision to make deliberately, and it should be recorded as ADR-4
once made.

---

## Traceability

| Source | Items |
|---|---|
| `Plans/Recruiter-Pro-Refactor-Plan.md` | A0, A0b, A0c, A1–A11, B1–B13 |
| `Plans/Recruiter-Pro-Addons-Scope.md` | ①–⑧, cleanup inventory, guardrails |
| `Plans/Recruiter-Pro-Agent-Design.md` | Agent contracts, LLM allocation, guardrails → ADR-1, ADR-2, ADR-3 |
| Verification pass, 9 Aug 2026 | **N1** docs/ ignore rule · **N2** conflicting model metadata · **N3** zero agent unit tests · refined dependency import counts (spacy/crewai/openai/ollama at 0, not 1) |
| Execution pass, 9 Aug 2026 | **N4** `npm run build` broken on `main` · **N5** `next@14.2.3` advisory · **N6** landing-page hydration mismatch · **N7** `run_api.py` crashes on Windows · A2 re-diagnosed (artifacts never existed, so 1.1 depends on 1.2+1.4) · corrected two false claims in this file's own 1.1 (`/health` and the startup warning already existed) |
| Data + GUI audit, 9 Aug 2026 | **Job corpus audit** (6,146 records, 2,146 discarded, 2.3% vocabulary coverage, 60.9% of jobs unmatched) · **GUI audit** all 6 pages + 6 components · **N8** two pages unreachable from nav · **N9** every page shares one tab title · **N10** UI advertises a 200 MB upload limit · **N11** four false statements in UI copy · **N12** 26% of the test suite fails, 19 tests target an API that never existed |

### ☐ N7 · `run_api.py` crashes on Windows before starting — *minor*
`branch: fix/repo-run-api-encoding`

`python run_api.py` dies immediately with
`UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f680'` — the emoji in the
`print()` at line 17 cannot be encoded by the `cp1252` default console codepage. Low severity
because it is **not** the documented entrypoint: the README (line 166) and `Run.ps1` both use
`uvicorn src.api:app`, which works. But it is a root-level file that crashes on the platform
this project's own tooling targets. Replace the emoji, or set `PYTHONIOENCODING=utf-8`.

`Plans/` is gitignored — the reports are working notes. This file is the tracked record.
