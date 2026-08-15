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

## Where things stand — 12 Aug 2026

| Phase | State |
|---|---|
| 0 · Process | ☑ |
| 1 · Make it run | ☑ the suite installs from a clean clone and CI is green |
| 2 · Make it correct | ☑ Agent 3 split, one skill vocabulary, weights honoured |
| 3 · Make it fast | ☑ 16.64s → 0.74s per upload (22×) |
| 4 · Make it safe | ☑ CORS, upload guards, rate limits, provider abstraction |
| 5 · Make it feel good | ☑ **fully closed** - interface rebuilt on the design system, landing page added, legacy API aliases removed, explanation provenance surfaced |
| 6 · Build clean | ◐ CI enforces tests, coverage, lint (both sides) and a byte scan; one launcher replaces the three-terminal script; `black` sweep and frontend tests outstanding |

**Gates, as of the close of Phase 5:**

| Gate | Result |
|---|---|
| `pytest --cov-branch --cov-fail-under=81` | 509 passed, 2 skipped, 0 failed · **83.32%** |
| `ruff check src/ scripts/ tests/` | clean |
| `scripts/validate_corpus.py` | 20/20 |
| `scripts/check_control_chars.py` | clean |
| `npm run build` | clean |
| `npx tsc --noEmit` | clean |
| `npm run lint` | clean — **first run in the project's history** |
| `scripts/check_secrets.py` | clean across 176 tracked files |
| `scripts/check_control_chars.py` | clean across 134 files |
| `black --check` | 28 of 30 files would reformat · non-blocking (6.3) |

**Running it:** `.\run.ps1` starts both services in one window (6.8).
**LLM:** OpenRouter configured and verified live; every explanation now states
which provider wrote it (6.9).

---

## Backlog audit — 12 Aug 2026

Every ☑ in this file was re-checked against the code, and every ☐ was checked
for whether it is still a real problem. Method: run it, grep it, or import it —
not read the entry and agree with it.

**Verified still true (the ☑ claims hold):**

| Claim | How it was checked |
|---|---|
| A0 fixed — vocabulary flattens correctly | `python -> Python`, `java -> Java`; 679 canonicals, 1,554 aliases; no family name is a canonical |
| 2.6 dead code deleted | `src/utils/` and `src/core/orchestrator.py` do not exist |
| 4.1 CORS restricted | `src.api._cors_origins == ['http://localhost:3000']` |
| 4.8 lifespan migration | no `@app.on_event` remains (one docstring mention) |
| 1.1/1.2 model + requirements | all three artifacts present, three requirement files tracked |
| Corpus | 800 jobs, 8 categories, every record has a description |
| Referenced files | `CONTRIBUTING.md`, `JOBS_DATASET_SPEC.md`, all three ADRs, both scripts exist |

**Corrected — entries that were stale:**

- **N7** (`run_api.py` crashes on Windows) was still listed open. The file has
  **zero non-ASCII bytes**; it was fixed and never ticked.
- **A11** (`cache.py` is a stub) is now done — deleted in `5650f3b`.
- **3.3** was already marked obsolete in an earlier pass; re-confirmed. Acting
  on it as written would **delete the live corpus**.

**Confirmed still open and still real** (so Phase 5 starts from facts):

- **5.3** — `/jobs` accepts only `skip` and `limit`. No `search` parameter
  exists, so a search box on that page cannot work.
- **N8** — the sidebar links `/`, `/history`, `/results`, `/shortlist`.
  **`/jobs` and `/upload` are unreachable from navigation**, and `/upload` is
  the primary action of the product.
- **N9** — `layout.tsx` sets one title and **no page overrides it**, so every
  tab reads "AI Resume Matcher - Dashboard".
- **5.8** — `recharts` and `class-variance-authority` are declared in
  `package.json` and imported in **zero** files. `/history` and `/match/history`
  are still near-duplicate endpoints.
- **N11** — the "3,000+" claim is already gone; the count is derived from the
  API. This part of N11 is closed.

**New, found during the audit** — the `/match` payload names three scores
misleadingly: `parser_score` is the **rule-based total** (nothing to do with
Agent 1), `matcher_score` is the **skill score**, and `scorer_score` is
**experience only**. A reader of the API would draw the wrong conclusion from
all three. Renaming them is frontend-coupled, so it belongs in Phase 5 — logged
as **5.9**.

---

## Issue register — every known problem and its fix

Complete as of 9 Aug 2026. Every row was reproduced against the working tree, not inherited
from a report. **Severity** is about consequence, not effort.

### 🔴 Correctness — the product gives wrong answers

| ID | Problem | Best solution | Phase |
|---|---|---|---|
| **A0** | `_get_canonical_skill` read a category-nested dict as flat, so every skill normalized to its category name | ✅ **FIXED** — alias index built once at load, O(1) lookup. 12/17 tests failed before, 17/17 after. Real `/match` output went from `['programming_languages','devops','tools']` to `['FastAPI']`, and Backend Engineer replaced Frontend Engineer at the top for a backend CV | 2.2 ☑ |
| **A0-T** | Nothing guards it | ✅ **Done** — 17 tests, 12 confirmed failing before the fix | 2.1 ☑ |
| **N13** | `_extract_keywords` sliced `[:20]` out of a **set**. Python randomizes string hashing per process, so the same CV+job scored **0.40 or 0.45 depending on process** — measured across 5 runs. Violates ADR-1's determinism rule | ✅ **Fixed** — rank by frequency, tie-break alphabetically. Verified identical across 5 processes. More useful than hash order too: a repeated term matters more | 2.2 ☑ |
| **N14** | `JobPosting` set no `extra` policy, so Pydantic v2 **silently dropped** the new `category` key — `hasattr(job,'category')` was `False`. The spec's claimed "validated at load" safety net did not exist | ✅ **Fixed** — `category` declared with a validator rejecting anything outside the eight. Corpus-wide rules enforced by `scripts/validate_corpus.py` instead | C.3 ☑ |
| **N15** | `_score_education` reads `job.education_level`, which is `None` on all 6,146 archived jobs — verified — so it has always defaulted to `3` (Associate) for every job. The scorer has never done anything | Populating it in the new corpus makes it work for the first time. **Scores will shift with no code change to point at** — note in the PR, pin two known pairs in a test | C.4 |
| **W** | `config/agents.yaml` declares weights `0.60/0.25/0.10/0.05`; `agent3_scorer.py:108` hardcodes `0.50/0.17/0.20/0.08/0.05` incl. a `title` term the YAML never mentions. The YAML is decorative | ✅ **Fixed** (`c27b86f`) — `agents.yaml` is the only source, `title_weight` declared, sum validated in `__post_init__`. **Scores byte-identical**, which was the point | 2.3 ☑ |
| **A3** | `salary` + `salary_log` were model features. Correct to remove — but **removing them changed nothing**: metrics came back byte-identical (precision 1.000, ROC-AUC 1.000, same 121/28/0/1 confusion matrix). Salary was never the cause | ✅ Removed + guard test. **Real cause is N18** — the dataset, not the features | 1.4 ☑ |
| **N18** | **The dataset cannot produce an honest ATS model.** `Recruiter Decision` is a pure threshold on `AI Score` (≥65 → Hire, **100% accuracy from one column**). `AI Score` is excluded from training, but the remaining columns reconstruct the decision anyway: **`Experience` alone → ROC-AUC 0.9244; `Experience + Projects Count` → 0.9933**. Two ordinary columns. There is no leak left to remove — the task is trivial by construction | **Stop trying to fix the number; report it.** No feature removal makes this dataset non-trivial. The honest framing is the strongest portfolio asset here — see below | 6.5 |
| **N2** | Two metadata files describe different models (RF+XGBoost 3-class @0.608 vs LogReg binary @1.000). Only the second loads | Pick the lineage, archive the other, document the choice | 1.3 |
| **Vocab** | Vocabulary recognises 2.3% of corpus skills; 60.9% of jobs unmatchable. Fixing A0 alone does not fix this | Generate corpus *against* a controlled vocabulary so the invariant holds by construction | C.3/C.4 |

### 🔴 Won't run / won't build

| ID | Problem | Best solution | Phase |
|---|---|---|---|
| **N4** | `npm run build` failed — `matched_skills` missing from `Match`; root cause was `/match` never sending it | ✅ **Fixed** — `/match` returns both fields; type declares them | 1.5 ☑ |
| **A1** | `requirements.txt` omits 6 imported packages (`sklearn`, `joblib`, `xgboost`, `imblearn`, `matplotlib`, `seaborn`); pins 6 unused (`spacy`, `crewai`, `openai`, `ollama`, `streamlit`, `plotly`) | Split into `requirements.txt` / `-ml.txt` / `-dev.txt`; add ruff; re-add `openai` only when `OpenRouterProvider` imports it | 1.2 |
| **A2** | Model artifacts do not exist and never did | Retrain after 1.2 + 1.4, then commit (ignore rule already prepared) | 1.1 ◐ |
| **—** | No job corpus — `/match` returns 503 | Generate per `JOBS_DATASET_SPEC.md` | C.4 |
| **N7** | `python run_api.py` dies on Windows (emoji vs cp1252) | ✅ **Fixed** — no non-ASCII bytes remain in the file | N7 ☑ |
| **N5** | `next@14.2.3` has a published security advisory | Patch within 14.x, re-run the build | 1.6 |

### 🟠 Tests — the safety net does not exist

| ID | Problem | Best solution | Phase |
|---|---|---|---|
| **N12a** | 19 tests call `/api/v1/health`, `/api/v1/score`, `/api/v1/batch` — endpoints this repo has **never** served. All 404 | Delete them, or build that surface. Do not leave tests asserting against an imaginary API | 6.7 |
| **N12b** | `test_pipeline.py` + `test_storage.py` built `JobPosting` without 7 now-required fields → 9 failures, incl. **all 5 Agent 3 scoring tests** | ✅ **Fixed** — fixtures updated; 26/26 now pass. Errors dropped 10 → 2 | 6.7 ☑ |
| **N16** | **The test that should have caught A0 was bent around it.** `test_skill_matching` asserts `any('python' in s or 'programming' in s or 'fastapi' in s ...)` — someone saw `programming_languages` in the output and *added `'programming'` to the assertion* rather than investigating. So even once the fixtures were fixed, the test passes with A0 present | Delete the `'programming'` clause as part of 2.2, or the A0 regression test is toothless. **This is the mechanism by which A0 survived** | 2.2 |
| **N12c** | `test_cross_validation.py`: `plot_validation_curve()` missing an argument, unpack arity changed ×4 | Realign tests with current signatures | 6.7 |
| **N12d** | Missing fixture `test_resume_abdelrahman.txt`; `test_data_loader` asserts `3 == 30`; `test_api_client` needs a live server on :8000 | Add the fixture, fix the assertion, mark the client tests `@pytest.mark.integration` and skip without a server | 6.7 |
| **N12e** | Tests write PNGs into tracked `models/experiments/` | Point `output_dir` at `tmp_path` | 6.7 |
| **N3** | Agents 1, 2, 3 have **zero** unit tests | ✅ **Fixed** (`92cbc0e`) — 51 unit tests incl. the Agent 3 determinism tests ADR-1 requires | 2.5 ☑ |
| **—** | `pytest.ini` forces coverage on every run | Move `--cov` to an explicit CI invocation | 6.7 |

### 🟠 Code quality — never enforced

| ID | Problem | Best solution | Phase |
|---|---|---|---|
| **Q1** | `black --check src/` → **28 of 30 files** would be reformatted | Run `black src/` once, commit as a pure-format commit, then enforce in CI | 6.3 |
| **Q2** | `flake8 src/` → **1,565 issues** | Adopt `ruff` (replaces flake8+isort, one config), fix or explicitly ignore, then enforce | 6.3 |
| **Q3** | `ruff` is not installed despite being the recommendation | Add to `requirements-dev.txt` | 1.2 |
| **Q4** | `next lint` has **never been configured** — it prompts interactively, so the frontend has never been linted, though `eslint-config-next` is installed | ☑ Fixed 12 Aug 2026. Next 16 removed `next lint` outright, so the script could only fail; `eslint.config.mjs` (flat config) replaces it, the script is `eslint .`, its first run found 9 real errors, all fixed, and CI now blocks on it | 6.3 ☑ |
| **A0c** | `src/utils/` = 619 LOC, zero imports | ✅ **Fixed** (`d0cb1c9`) — 973 LOC deleted incl. `orchestrator.py` (354); 10 skills salvaged first | 2.6 ☑ |
| **A11** | `src/storage/cache.py` is a docstring and `pass` | ✅ **Deleted** (`5650f3b`) with its two `LLMConfig` keys. A config key that switches nothing reads as a feature | 5.8 ☑ |

### 🟠 Safety — unsafe on a public URL

| ID | Problem | Best solution | Phase |
|---|---|---|---|
| **A4** | `allow_origins=["*"]` **with** `allow_credentials=True` — browsers reject it, and `config.cors_origins` already exists unused | Read `CORS_ORIGINS`, default `localhost:3000`, restrict methods | 4.1 |
| **A5 + N10** | No upload cap anywhere; config says 10 MB; the UI **advertises 200 MB** | Check `file.size` before read, 413 over 10 MB, validate real content type, fix the copy in the same PR | 4.2 |
| **A7** | `/match` mutates the module-level `pipeline.agent4` per request → cross-request leakage under >1 worker | Pass `use_llm` as an argument; make Agent 4 stateless (same work as the provider refactor) | 4.6 |
| **A8** | Bare `except:` ×3; `load_jobs()` swallows per-record failures silently | `except OSError`; count and log skipped records at startup | 4.5 |
| **4.4** | `explain=true` generates for *every* job ≥0.6 — unbounded on a public URL | Hard-cap K ≤ 3, add `slowapi` limits, semaphore, daily quota counter | 4.4 |

### 🟡 Performance

| ID | Problem | Best solution | Phase |
|---|---|---|---|
| **B1** | Persists ~4,000 rows per upload but returns 10 — measured 7.16 s vs 0.0098 s for the batched equivalent | Sort → slice top-K → one `executemany`; `PRAGMA journal_mode=WAL` | 3.1 |
| **B2** | 45-key synonym dict rebuilt on every call, ~80,000×/upload — 3.26 s | ✅ **Dict deleted** (`589cc9e`) — it was unreachable dead code, not just slow. Residue: `role_keywords` rebuilt per call | 3.2 ◐ |
| **B3** | 4,000 separate `predict_proba` calls | One DataFrame, one transform, one predict | 3.6 |
| **B4** | CV skills re-normalized per job | Normalize once before the loop | 3.4 |
| **B5** | Every job gets full scoring | Zero-shared-skills → floor score, skip the expensive path | 3.5 |
| **—** | Measured **27.6 s** for one CV vs 4,000 jobs *with ML off* | The 800-record corpus (C.4) plus 3.1–3.6 should bring this under 3 s | C.4 + Phase 3 |

### 🟡 UI / UX

**All closed in Phase 5** except B10's field aliases. Kept as the record of
what was wrong and how it was found.

| ID | Problem | Resolution | Phase |
|---|---|---|---|
| **N6** | `page.tsx:352` renders `Math.random()` → hydration mismatch, 6 console errors, React discards the server DOM | ☑ Markup deleted. Two further sources found and fixed: locale-dependent date formatting, and `useState(() => localStorage…)` | 6.0 ☑ |
| **N8** | `/upload` and `/jobs` have no nav link — reachable only by URL | ☑ All six routes in the sidebar | N8 ☑ |
| **N9** | Every page's tab title is "AI Resume Matcher - Dashboard" | ☑ Each route is a server component owning its `metadata`, under a `%s · Recruiter Pro` template | N9 ☑ |
| **N11** | Four false statements in UI copy (200 MB, 3,000+ jobs, max 5 jobs, PDF/DOCX only) | ☑ Every count now derived from the API; the size limit matches the API's real 10 MB | N11 ☑ |
| **A9** | Landing page catch has no toast — the slowest call, on the first page a visitor sees | ☑ Toast plus an inline message in the pipeline panel | 5.1 ☑ |
| **A10** | Drag-drop silently discards DOCX/TXT; file picker validates nothing | ☑ One `cv-dropzone.tsx` for all three upload surfaces, naming the file and the reason on reject | 5.2 ☑ |
| **B7** | `/jobs` search confirmed dead — `search=nurse` returns byte-identical results | ☑ Server-side, plus three facet filters from `/jobs/facets` | 5.3 ☑ |
| **B8** | 2.5 s of deliberate fake delay | ☑ Timeouts deleted; `processing_time` measured and displayed | 5.4 ☑ |
| **B9** | Results stringified into `localStorage`, 5+ keys, `QuotaExceededError` uncaught | ☑ One key via `useSyncExternalStore`, writes wrapped | 5.5 ☑ |
| **B10** | `any[]` for results; duplicated legacy field aliases | ◐ `any` gone and lint-enforced; the aliases are still emitted — a breaking change deserving its own commit | 5.6 ◐ |
| **B11** | No loading skeletons | ☑ Skeletons, empty states and error states with retry | 5.7 ☑ |
| **—** | `header.tsx` unused by `/` and `/upload` | ☑ Deleted; `page-header.tsx` used by every page | 5.8 ☑ |

### 🟢 Cleanup

| ID | Problem | Best solution | Phase |
|---|---|---|---|
| **B6** | Corpus bloat | ✅ Superseded — legacy files archived, 800-record replacement specified | C.1 ☑ |
| **⑤** | `models/tfidf_vectorizer.pkl` orphaned; `models/experiments/` 10 PNGs incl. a committed test artifact | Delete the orphan; move experiments to a Release | 6.6 |
| **—** | `/history` and `/match/history` are near-duplicates | ☑ `/history` deleted | 5.8 ☑ |
| **—** | `recharts`, `class-variance-authority` unused | ☑ Dropped, along with `react-dropzone`, which `cv-dropzone.tsx` replaced | 5.8 ☑ |

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
| 1.5 | N4 | `npm run build` is broken on `main` | 5 | 5 | 1 | **50** ☑ `next build` clean, 9/9 pages |
| 1.2 | A1 | Split and repair `requirements.txt` | 5 | 5 | 2 | **40** ☑ |
| 1.4 | A3 | Remove target leakage, retrain, report the honest number | 4 | 5 | 3 | **27** ☑ |
| 1.1 | A2 | Ship the trained model artifacts | 5 | 5 | 1 | **50** ☑ |
| 1.3 | N2 | Resolve the two contradictory model metadata files | 3 | 4 | 2 | **28** ☑ |
| 1.6 | N5 | `next@14.2.3` has a published security advisory | 2 | 4 | 2 | **24** ☑ **upgraded to 16.3.0 — `found 0 vulnerabilities`** |

> **Revised order, 9 Aug 2026.** 1.1 was written as the first task and cannot be. The
> artifacts it says to commit **do not exist**, so producing them means retraining, which
> means 1.2 (install deps) and 1.4 (drop the leaking features) come first — otherwise the
> retrain bakes in a model that 1.4 immediately throws away. Work the phase in the table
> order above, not by number.

### ☑ 1.1 — A2 · The trained model is not in the repo — **DONE**
`branch: fix/ml-remove-salary-leakage`

**Hybrid ML scoring runs for the first time in this repository.**

```
ATSPredictor.load_model()        -> True
Agent 3 ml_predictor is None?    -> False      # hybrid scoring is LIVE
models/production/ats_model.joblib          32 KB
models/production/feature_engineer.joblib    4 KB
```

Both artifacts are committed (the ignore-rule allowlist prepared earlier did its job), and
the model is the retrained, salary-free one — 28 features, no `salary`, no `salary_log`.

Everything below is the record of how it got here.

---

### ☑ 1.4 — A3 · Leakage removal, and what it actually revealed

`salary` and `salary_log` are gone from `FeatureEngineer`, `LEAKING_FEATURES` names them so
they cannot return quietly, and two guard tests enforce it — one asserting no salary-derived
feature is ever produced, one proving the pipeline trains on a dataset with no `Salary`
column at all. An existing test was **asserting the leak existed** (`assert 'salary' in
feature_names`); it was updated, and it is worth noting that the test suite was actively
holding the leak in place.

**Then the retrain produced identical metrics.** Accuracy 0.9933, precision 1.000,
ROC-AUC 1.000, confusion matrix 121/28/0/1 — the same numbers, to the digit. Salary was
never what was driving the perfect score.

**N18 — the real cause, measured:**

| Predictor | ROC-AUC |
|---|---|
| `AI Score ≥ 65` (single threshold) | **1.0000 — perfect classification of the label** |
| `Experience` alone | 0.9244 |
| `Experience` + `Projects Count` | **0.9933** |
| `Experience` + `Projects Count` + skill count | 0.9961 |

`Recruiter Decision` is a deterministic threshold on `AI Score`, and although `AI Score` is
excluded from training, two perfectly ordinary columns reproduce the decision anyway. The
dataset is synthetic and the label is a smooth function of its own inputs. **No amount of
feature engineering makes this task non-trivial**, so there is no honest number to recover by
removing more features.

**This is the most valuable thing in the repository for portfolio purposes, and it should be
written up as a finding rather than hidden.** The story is not "my model scores 0.99" — it is
*"I did not believe my own 1.000, removed the feature I suspected, got the identical result,
kept digging, and found the label was a threshold on a column I had already excluded. The
dataset cannot support the claim. Here is the evidence."* That reasoning is worth more than
any score, and almost no portfolio project can show it. → 6.5.

**Also fixed on the way through (N17):** `save_results_summary` crashed with
`TypeError: Object of type bool_ is not JSON serializable` on the final line of training —
`numpy.bool_` is not JSON-serializable. It ran *after* the production artifacts were written,
so a successful training run looked like a failed one, `training_summary.json` was never
produced, and the process exited non-zero, which would have failed CI.

---

### ☑ Original diagnosis of 1.1 (kept — the reasoning was wrong in an instructive way)

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

### ☑ 1.6 — N5 · Next.js upgraded to 16.3.0 — **all advisories closed**
`branch: chore/deps-upgrade-next-16`

`npm audit` went from **8 high/critical to `found 0 vulnerabilities`**.

The 14.x patch (14.2.35) closed seven of eight but left the Image Optimizer `remotePatterns`
DoS, which affects **every release below 16.3.0** — so it genuinely required the major
upgrade. Attempted it rather than assuming it was too risky, and it was not:

- **Next 16 accepts React 18** (`^18.2.0 || ^19.0.0`), so no React 19 migration was needed —
  that is the usual blocker on this upgrade and it does not apply here.
- The only conflict was `eslint-config-next@16` requiring ESLint ≥ 9. Upgraded ESLint to 9
  as well, which cost nothing because **this project has never had an ESLint config** (N-lint)
  — there was no legacy `.eslintrc` to migrate to flat config.
- Next 16 rewrote `tsconfig.json` on first build (`jsx: react-jsx`, added `.next/dev/types`).
  Expected and committed.

Verified beyond the build, since "it compiles" is not "it works": `tsc --noEmit` 0 errors,
`next build` clean across all 7 routes, then the app run against a live backend — `/jobs`
rendered 800 real jobs, the header read "Browse and search 800 job descriptions" from the
API, and the expanded description had `white-space: pre-line` with 20 newlines preserved, so
the four-section format survives.

### ☑ 1.2 — A1 · `requirements.txt` is missing six packages the code imports

**Closed.** Three files: `requirements.txt`, `requirements-ml.txt`, `requirements-dev.txt`. The split is what lets the API be installed without the training stack.
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

### ☑ 1.3 — N2 · Two model metadata files describe two different models

**Closed.** One production card, `models/production/model_metadata.json`, beside the model it describes. What remains under `models/archive/` and `models/experiments/` is dated experiment output, which is a record of runs rather than a second answer to the same question.
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

### ☑ 1.4 — A3 · Model metrics are a red flag, and they are the highest-ROI fix here

**Closed — and it stayed a finding rather than becoming a fix.** The README states it outright at line 143: the label is reproducible from two ordinary columns, which reach 0.9933 on their own. `GET /stats` deliberately publishes no accuracy figure, and a contract test asserts none appears. Reporting the honest number meant reporting that the number is meaningless.
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

## Corpus replacement — in progress

> **Decided 9 Aug 2026.** The old corpus is archived at
> `data/archive/jobs-legacy-2026-08-09/` (not deleted — see its README for why it was
> retired). It is being replaced by a purpose-built 800-record dataset covering eight
> business categories, specified in [`JOBS_DATASET_SPEC.md`](JOBS_DATASET_SPEC.md).

**⚠️ The app has no job corpus right now.** `load_jobs()` returns `[]` and `POST /match`
returns `503 No jobs loaded` until `data/json/jobs.json` exists. Expected and temporary.

| # | Task | Status |
|---|---|---|
| C.1 | Archive the three legacy job files with a written rationale | ☑ |
| C.2 | Write the dataset spec + generation prompt | ☑ `JOBS_DATASET_SPEC.md` |
| C.2a | Declare `category` on `JobPosting` — Pydantic was silently dropping it (**N14**) | ☑ |
| C.2b | Fix `_extract_keywords` non-determinism before generating (**N13**) | ☑ |
| C.2c | `scripts/validate_corpus.py` — all 10 self-checks as mechanical assertions | ☑ verified on pass/fail fixtures |
| C.2d | Restructure generation into 3 passes (names → skeleton → prose) so corpus-wide invariants are checkable before prose is written | ☑ in spec |
| C.2e | Fix `JobPosting` fixture drift so the corpus/scoring path is clean before generating (**N12b**) | ☑ 26/26 |
| C.2f | `tests/unit/test_validate_corpus.py` — one planted defect **per rule**, 24 tests | ☑ found a real crash in the validator itself |
| C.3 | Generate `data/dictionaries/skills.json` | ☑ **667 skills / 15 families / 1,523 aliases** — independently verified |
| C.4a | Pass 1 + 2 — skeleton, all fields except `description` | ☑ **800 records, 16/19 checks pass** — the 3 failures are only the absent descriptions |
| C.4b | Pass 3 — descriptions | ☑ **800/800, all 20 validator checks pass** — independently re-verified |
| C.4c | Install `data/json/jobs.json` | ☑ |
| C.5 | `load_jobs()` reads `payload["jobs"]`; legacy branch deleted | ☑ 800 jobs load |
| C.6 | `jobs[:4000]` cap deleted | ☑ + regression test |
| C.7 | Point `config.skills_database_path` at the new vocabulary | ☑ 2.2 landed; also fixed `jobs_data_path`, which pointed at `data/jobs/` — a directory that never existed — and wired `load_jobs()` to read it |
| C.8 | Vocabulary-coverage test | ☑ `tests/unit/test_corpus_integrity.py`, 5 tests |
| C.9 | Re-measure coverage | ☑ **100%** re-measured 10 Aug 2026 against the live alias index: 654/654 distinct skills, 8,434/8,434 mentions, 0/800 jobs unmatchable (was 2.3% of skills / 60.9% of jobs unmatchable) |
| C.10 | `whitespace-pre-line` on the description element | ☑ + header count now derived from the API, not hardcoded |

**Independent cross-check, 9 Aug 2026.** Ran `scripts/validate_corpus.py` against the
generated files rather than trusting the generator's own 22/22:

- **10 of 11 claimed figures exact** — 667 skills, 15 families, 1,523 aliases, min 42/family,
  800 records, 46 cities, 60 companies all used, 800/800 unique `(title, company)`,
  remote 360/240/200, 100 per category.
- **One claim understated:** 136 distinct titles claimed, **145 actual** — they counted before
  adding the leadership titles. Wrong in the harmless direction.
- **A0 probe passes:** `python → Python`, `java → Java`, `react → React`,
  `mysql → MySQL` — all distinct.
- **Byte-identical on regeneration** (md5 `b6cf941d…`), so the corpus is reproducible rather
  than a one-off artifact.
- **Their stated deviation confirmed and sound:** `administrators` has 0 executives (moved to
  lead). Office administration genuinely tops out at manager.
- **Unclaimed spot-checks all clean:** every internship is `entry`; seniority mix within
  tolerance; 654 of 667 skills actually used.
- **Only blocker to `JobPosting` construction is the missing `description`** — adding one
  makes a record construct with `category` intact, confirming the N14 model fix works
  against real generated data.

⚠️ **Installing `skills.json` before 2.2 is safe but pointless.** Tested: the current
unfixed `_get_canonical_skill` returns `None` for every skill against the new
`_meta`/`families` layout, so `_normalize_skills` falls back to the raw string and
`python`/`java` stay distinct — it **fails safe** rather than collapsing to category names.
But no alias resolution happens (`py` will not match `Python`) until 2.2 lands. That
fail-safe behaviour is a real benefit of the `_meta`/`families` split, not luck.
| C.5 | `load_jobs()` reads `payload["jobs"]`; delete the legacy-shape branch | ☑ |
| C.6 | Delete the `jobs = jobs[:4000]` cap at `api.py:114` | ☑ |
| C.7 | Point `config.skills_database_path` at the new vocabulary | ☑ |
| C.8 | **Test: every job skill exists in the vocabulary** — the guard the old corpus lacked | ☑ |
| C.9 | Re-measure coverage; expect 100% by construction | ☑ |
| C.10 | Frontend: `whitespace-pre-line` on the description element (it now has newlines) | ☑ |

**C.3/C.4 supersede much of 2.4.** The unified-vocabulary task assumed merging four existing
sources; the corpus is now being generated *against* a single vocabulary instead, so the
invariant holds by construction rather than by migration. 2.2 (the alias-index fix) is still
required — the lookup code is broken independently of what data it reads.

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

> **Status: ☑ COMPLETE — 7 of 7.** All of Phase 2 is done and verified. Closed 12 Aug 2026.
>
> Tests went 165 → 251 passing across nine commits, with the same 31 pre-existing failures
> and **zero newly-failing tests at every commit** — established by comparing failure *sets*
> with `comm -13`, not counts, because a change can trade one failure for another and hold
> the total. Scores are unchanged since 2.6, confirmed by `scripts/score_probe.py`.

| # | ID | Task | I | R | E | Score | Status |
|---|---|---|---|---|---|---|---|
| 2.1 | A0-T | Regression test: `normalize("python") != normalize("java")` | 4 | 5 | 1 | **45** | ☑ 17 tests, 12 failed pre-fix |
| 2.2 | A0 | Flatten the canonical skill index | 5 | 5 | 2 | **40** | ☑ |
| 2.3 | W | One source of truth for scoring weights | 3 | 4 | 1 | **35** | ☑ config/agents.yaml is the only source; title_weight declared; scores byte-identical |
| 2.4 | A0b | Merge four skill vocabularies into one | 5 | 4 | 3 | **27** | ☑ one loader in `src/core/vocabulary.py`; Agents 2 and 3 inject it; 679 canonicals |
| 2.5 | N3 | Unit tests for Agents 1, 2, 3 | 4 | 5 | 3 | **27** | ☑ 51 unit tests across the three agents |
| 2.6 | A0c | Delete `src/utils/` — 619 LOC, zero imports | 2 | 2 | 1 | **20** | ☑ + `src/core/orchestrator.py` (354 LOC) and `scripts/setup/`; 10 skills salvaged first |
| 2.7 | ② | Agent contracts: typed results, constructor injection, no `__init__` side effects | 4 | 3 | 4 | **14** | ☑ Agent 3 split on the dependency seam; 544 → 122 LOC |

**2.7 remaining, stated precisely.** Agent 1 no longer touches the filesystem on
construction, logs instead of printing, writes only when asked, and rejects
documents it could not read. Agent 2 takes the vocabulary by constructor
injection and owns no private skill list. **Agent 3 has not been split.** The
five-way split this file originally prescribed was reviewed on 12 Aug 2026 and
**superseded** — it does not fit the code. See
[2.7 · Agent 3 — the decision](#27--agent-3--the-decision) for the measurement,
the three options considered, and the recommended shape.

**What closed since the 10 Aug audit** — the four vocabularies are now one, so the
partial-status notes that used to sit here no longer apply:

- **2.3** — `config/agents.yaml` is the only place the five rule weights are declared, and
  editing it now actually changes scoring. It previously did not: the scorer hardcoded a
  different set, and `title_weight` (17% of every score) was declared nowhere at all.
  Verified zero score movement — that was the entire point of the commit.
- **2.4** — one loader in `src/core/vocabulary.py`. `Agent2.SKILLS_DATABASE` and Agent 3's
  function-local `synonyms` dict are both deleted; both agents take the index by constructor
  injection. 679 canonicals / 1,554 aliases. **A skill Agent 2 extracts is now, by
  construction, a skill Agent 3 can match.**
- **2.5** — 51 unit tests added across Agents 1, 2 and 3, including the determinism tests
  ADR-1 requires (identical input → byte-identical breakdown; two separately-built agents
  agree; scoring does not mutate its inputs).
- **2.6** — 973 LOC deleted: `src/utils/` (619), `src/core/orchestrator.py` (354) and
  `scripts/setup/`. Ten genuinely-missing skills were salvaged into the vocabulary first.

**Three defects fixed along the way that were not in this backlog** — all found by reading
the code during 2.3/2.4, all live in production scoring at the time:

| Defect | Effect |
|---|---|
| Substring skill matching | **JavaScript satisfied a "Java" requirement.** Also Git→GitHub Actions, SQL→MySQL, and `.NET` reduced to "net" matching inside "Pe**net**ration Testing". 29 such collisions among 669 names |
| Punctuation stripped before vocabulary lookup | **Six canonical skills could not be found by their own name** — `.NET`, `T-SQL`, `Monday.com`, `Outreach.io`, `Stand-ups`, `Non-Conformance Management` |
| `title_score` computed, weighted, then discarded | The API's four returned components **could not reconstruct** `rule_based_score`. 17% of every score was invisible to every consumer |

### ☑ 2.1 — Write the regression test first — **DONE**
`branch: test/agent3-skill-normalization-regression`

Red before green. Assert `_normalize_skills(["python"]) != _normalize_skills(["java"])`,
and that a Python CV scores near zero skill match against a Java-only job. Confirm it
**fails** against today's code and paste the failure into the PR. This test is the guard
that should have existed, and it is the single most defensible artifact of the whole
refactor.

### ☑ 2.2 — A0 · Skill normalization collapses every skill into its category — **FIXED**
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

### ☑ 2.3 — W · Scoring weights are declared in YAML and ignored in code — **FIXED** (`c27b86f`)
`branch: fix/agent3-weights-single-source`

**✔ Verified.** `config/agents.yaml` declares `skill 0.60 / experience 0.25 / education 0.10
/ keyword 0.05`. `agent3_scorer.py:108–114` hardcodes `skills 0.50 / title 0.17 / experience
0.20 / education 0.08 / keywords 0.05` — a different split, and it includes a `title` term
the YAML has never heard of. The YAML is decorative.

Pick one set, delete the other, load from config, and validate the sum is 1.0 at startup so
this cannot drift again. Ten-line fix that reads very badly if a reviewer finds it first.

### ☑ 2.4 — A0b · Four competing skill vocabularies — **now one** (`5707e2d`)
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

### ☑ 2.5 — N3 · The core pipeline has no unit tests — **51 added** (`92cbc0e`)
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

### ☑ 2.6 — A0c · `src/utils/` is entirely dead code — **deleted** (`d0cb1c9`)
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

### ☑ 2.7 — ② · One contract for all four agents — **DONE** (`c59096d`, `b5b86d8`, `655bb09`)
`branch: refactor/agents-typed-contracts`

The honest answer to "designed correctly" is a single rule, not new patterns: **each agent
takes its dependencies via constructor injection, holds no mutable per-request state, and
returns a typed result object.** That one rule fixes the A7 race (4.3), makes each agent
independently testable, and needs no framework.

| Agent | Today | Target |
|---|---|---|
| **1 Parser** | 272 LOC. `mkdir()` **side effect in `__init__`** (line 53); 4× `print()`; writes profile JSONs to `data/processed/raw_profiles/` that nothing reads | Pure `parse(path) -> RawDocument`. No disk writes, logger only. Reject <50 extracted chars so a scanned-image PDF fails loudly instead of returning empty |
| **2 Extractor** | 373 LOC. Owns a private 178-skill `SKILLS_DATABASE`. Name detection guarded by a hardcoded blocklist of Cairo neighbourhoods (`maadi`, `zamalek`, `heliopolis`, `dokki`) — heuristics overfit to a handful of test CVs | Inject the shared vocabulary. Return typed `ExtractedProfile`, not a bare dict. Record `extraction_method` per field |
| **3 Scorer** | 544 LOC, one class, 18 methods | ~~Five-way split~~ — **superseded, see below.** Extract the two collaborators that own a dependency; leave the rest as pure functions |
| **4 Explainer** | 406 + 247 LOC behind a factory, both hardcoding Ollama | Phase 4 |

### 2.7 · Agent 3 — the decision

`branch: refactor/agent3-extract-collaborators`

Agents 1 and 2 are done. This is all that is left in Phase 2.

#### What was actually measured

Every method of `HybridScoringAgent` was parsed and checked for which `self`
attributes it touches. That is the only question that matters for a split: a
method that reaches for no state is not coupled to the class, and moving it is
free.

| Group | Methods | LOC | Depends on |
|---|---|---|---|
| **Vocabulary** | `_score_skills`, `_find_skill_matches`, `_has_skill_match`, `_skill_tokens`, `_normalize_skills`, `_get_canonical_skill`, `_load_skills_database`, `_build_alias_index` | **147** | `self.skills_database` |
| **ML** | `_get_ml_score` + its `__init__` block | **~41** | `self.ml_predictor`, disk, sklearn |
| **Pure** | `_score_experience` (34), `_score_title_similarity` (91), `_score_education` (27), `_score_keywords` (18), `_extract_keywords` (27), `_is_overqualified` (8), `_is_underqualified` (4) | **209** | **nothing — (cv, job) in, float out** |
| **Composition** | `score_match` (75), `__init__` (23) | 98 | both collaborators + weights |

**209 LOC — 38% of the file — already has zero dependencies.** Only two things
in this class own state worth injecting: the skill vocabulary and the ML
predictor.

#### Why the prescribed five-way split was wrong

Two independent problems, both found by reading rather than assuming:

1. **It has no home for two of the seven scoring components.**
   `_score_title_similarity` is the single largest method in the file at 91 LOC,
   and keyword scoring is another 45. Neither is skills, experience, education
   or ML. Under the five-class shape they land in `HybridScorer`, which then is
   not a combiner — it is a combiner plus two scorers. That is the god-class
   rebuilt at smaller scale, and it puts the *biggest* method in the class
   named for doing the least.
2. **Four of the five classes would wrap pure functions.** `ExperienceScorer`
   and `EducationScorer` would be classes with an empty `__init__` and one
   method that never reads `self`. Constructor injection is the rule 2.7
   exists to enforce; a class with nothing to inject satisfies it vacuously
   while adding an object to build, pass and mock. It is ceremony charged
   against the reader.

#### Options considered

| | Shape | Risk | Verdict |
|---|---|---|---|
| **A** | The prescribed five classes | Medium | ✗ Leaves 136 LOC homeless; four empty constructors |
| **B** | Seven classes, one per component | Medium-high | ✗ Consistent but maximal churn; same empty constructors, now five of them |
| **C** | **Two collaborators + pure functions** | **Low** | ✔ **Recommended** |

#### ✔ Recommended: option C — split on the dependency seam

Extract only what owns something. Everything else moves as-is.

```
src/agents/scoring/
  skill_matcher.py   SkillMatcher(skills_index)  -> SkillMatch     (~150 LOC)
  ml_scorer.py       MLScorer(predictor|None)    -> float | None   (~55 LOC)
  components.py      pure functions, no class:                     (~210 LOC)
                       score_experience(cv, job) -> float
                       score_title_similarity(cv, job) -> float
                       score_education(cv, job) -> float
                       score_keywords(cv, job) -> float
                       is_overqualified(...) / is_underqualified(...)
agent3_scorer.py     HybridScoringAgent: composes the above,
                     applies the weights, builds ScoreBreakdown    (~120 LOC)
```

Why this is both the lowest-risk and the best-result option:

- **It delivers exactly what 2.7 asks for.** The rule is *"dependencies via
  constructor injection, no mutable per-request state, typed result."* Both
  injectable dependencies become injectable. `SkillMatcher` can be built with a
  five-word test vocabulary — the same pattern already proven on Agent 2 in
  `5707e2d`. The pure functions were always trivially testable; wrapping them
  changes nothing about that.
- **The risky part shrinks to one file.** `skill_matcher.py` is the only piece
  where a mistake alters a score, and it is the piece with 51 existing tests
  around it. The 209 pure LOC move verbatim — no signature change beyond
  dropping `self`, so a diff proves the move faithful by inspection.
- **Fewest moving parts.** Two classes instead of five or seven, and no
  constructor exists that has nothing to construct.

**Cost of being wrong is low.** If `TitleScorer` is later wanted as a class —
say title matching grows a config or a model — promoting a pure function to a
class is a contained change. Going the other way, deleting four classes already
threaded through the agent, is not.

#### Two free wins to take during the move

Both are the same defect class as the synonym dict already deleted in `589cc9e`,
and both are ~5-line fixes that are natural during an extraction and awkward
outside one:

- **`role_keywords`** (`agent3_scorer.py:329`) is a 15-key dict literal rebuilt
  **on every call** to `_score_title_similarity` — once per job per upload.
  Module constant. Folds into backlog **3.2**.
- **`_score_skills` walks the CV twice.** It calls `_find_skill_matches` for the
  matches, then `_has_skill_match` once per required *and* once per preferred
  skill — and each of those rebuilds `cv_token_sets` from scratch. A
  `SkillMatcher` that computes the match set once and derives matched / missing
  / extra from it removes the whole redundant pass. Folds into backlog **3.4**.
- Minor: `import re` sits inside `_score_title_similarity` (:311) and
  `_extract_keywords` (:438) while the module already imports `re` at :12.

#### How to verify — non-negotiable

**A faithful extraction changes no score.** That is the entire acceptance test,
and it is checkable to the byte:

```bash
PYTHONHASHSEED=0 python score_probe.py before.csv   # on HEAD
# ... perform the extraction ...
PYTHONHASHSEED=0 python score_probe.py after.csv
diff before.csv after.csv                            # MUST be empty
```

`PYTHONHASHSEED=0` and `include_ml=False` are both mandatory — `matched_skills`
and friends are built through `set()`, so without a pinned seed the CSV reorders
between runs and the diff fills with phantom changes. This harness carried every
Phase 2 commit; it is what proved `c27b86f` moved zero scores across all 800
jobs.

> ☑ **Done — `scripts/score_probe.py` (`1d12c57`).** It previously lived only in
> a scratch directory: the one instrument that made every Phase 2 refactor
> verifiable was the one thing not under version control. Made portable on the
> way in (repo root from `__file__`, not a hardcoded Windows path) and confirmed
> byte-identical output before committing.

Also required, as with every Phase 2 commit: capture the failure **set** before
and after and compare with `comm -13`, not the counts — a change can trade one
failure for another and hold the total at 31.

**Suggested commits** — the pure move first, so the reviewable-by-inspection
part is never mixed with the part that could move a number:

| # | Commit | Result |
|---|---|---|
| 1 | `chore(scripts)`: track the score-diff harness | ☑ `1d12c57` |
| 2 | `refactor(agent3)`: move the dependency-free scorers to components.py | ☑ `c59096d` — empty diff |
| 3 | `refactor(agent3)`: extract SkillMatcher with the vocabulary injected | ☑ `b5b86d8` — empty diff |
| 4 | `refactor(agent3)`: extract MLScorer; the agent becomes composition only | ☑ `655bb09` — empty diff |
| 5 | `perf(agent3)`: hoist role_keywords; match the CV once | ☐ **deferred to Phase 3** (3.2 / 3.4) |

### ☑ Outcome — closed 12 Aug 2026

`HybridScoringAgent` went from **544 lines to 122** and holds no scoring logic:
two collaborators, the configured weights, a `ScoreBreakdown`.

```
src/agents/scoring/
  skill_matcher.py   SkillMatcher(skills_index)   197 LOC   owns the vocabulary
  ml_scorer.py       MLScorer(predictor)           89 LOC   owns the ATS model
  components.py      7 pure functions             237 LOC   own nothing
agent3_scorer.py     HybridScoringAgent           122 LOC   composition only
```

**Every commit produced an empty diff** from `scripts/score_probe.py` across all
800 jobs, and no commit added a failing test — checked by `comm -13` on failure
*sets*, not counts.

The ML path needed a separate proof, since the probe runs `include_ml=False` and
therefore never reaches `MLScorer`. `MLScorer.score()` was compared against the
original inline expression over 60 jobs: **0 mismatches**.

One test moved fail→pass during commit 4 — `test_pipeline_with_smote`, the known
collection-order flake in ML training code none of this touched. **Not claimed
as a fix.**

Two payoffs beyond the line count. The skill regression tests now construct a
`SkillMatcher` instead of a whole agent that loads a trained model off disk in
order to ask whether "Java" matches "JavaScript". And `MLScorer.load()` is a
classmethod rather than constructor work, so building a scorer no longer reads
the filesystem — the same rule Agent 1 was fixed to obey in `78b6dc9`.

Deferred deliberately, both recorded in `components.py`: `role_keywords` is
still rebuilt per call, and `is_overqualified` still takes an `exp_score` it
never reads. Fixing either during the move would have cost the empty diff that
makes the move provable.

---

## Phase 3 — Make it fast

**Goal: a match completes in under three seconds.** This is also a hard prerequisite for
deployment — the target free tier gives 0.1 CPU, and today's sequential loop will simply
time out there.

> ⚠ **Read this before acting on any number in this phase.** Every measurement below was
> taken against the **old ~4,000-job corpus**, before the C.1–C.10 replacement. The live
> corpus is now **800 jobs** (`data/json/jobs.json`, 1.5 MB), and `jobs_cleaned.json` no
> longer exists. The measurements are kept as-written because they are a record of what was
> actually measured — but **divide the per-job costs by five** before estimating anything,
> and **re-measure before claiming a win.** Two entries below were invalidated outright by
> Phase 2 and are marked. Corpus figures re-checked 12 Aug 2026.

**The headline number.** `POST /match` scores one CV against every job sequentially,
building a 1-row DataFrame for a single sklearn prediction and **opening a new SQLite
connection, INSERTing, committing and closing it — per job.** The frontend timeout is set to
150 seconds with the comment `// Increased to 150 seconds (2.5 minutes) for 3000 jobs` —
that comment is the smoking gun. (The synonym-dict rebuild that used to head this list is
gone; see 3.2.)

| # | ID | Task | Backlog score | Measured cost | Status |
|---|---|---|---|---|---|
| 3.6 | B3 | Vectorize ML scoring | 18 *(ranked last)* | **8.13 s** | ☑ `2ed18e5` — 245x on the model call |
| 3.1 | B1 | Stop writing one row per job per upload | 36 | **7.18 s** | ☑ `ef7394b` — 156x/row, and only top-K written |
| 3.2 | B2 | Hoist `role_keywords` to a module constant | 30 | **~0.005 s** | ☐ not worth doing alone |
| 3.4 | B4 | Precompute the CV's normalized skill set once | 20 | ~0.07 s | ☐ open |
| 3.5 | B5 | Cheap pre-filter before expensive scoring | 20 | n/a | ☐ open — value dropped, see below |
| 3.3 | B6 | Stop shipping 13 MB of duplicated JSON | 28 | — | ✗ **OBSOLETE — do not action as written** |

### ☑ Target met — one CV vs 800 jobs, scoring + persistence

```
                        BEFORE      AFTER
scoring (800 jobs)      9.453s     0.730s
persistence             7.184s     0.014s
TOTAL                  16.637s     0.744s     22x
```

**Phase 3's "under three seconds" is met with 3.2, 3.4 and 3.5 untouched.**

**The priority scores were inverted.** 3.6 was ranked last (18, below four other
items) and was the single largest cost in the request; 3.2 was ranked second
(30) and is worth about 5 ms. The estimates predate both the ML model landing
and the corpus shrinking 5x. Where the 16.6 s actually went:

| | Time | Share |
|---|---|---|
| ML, one `predict` per job | 8.13 s | 49% |
| Persistence, one connection per row | 7.18 s | 43% |
| Rule scoring, all five components | 0.30 s | 2% |

Within that 0.30 s: skills 0.21, keywords 0.07, title 0.016, education 0.001,
experience 0.001. **3.2 lives inside the 0.016.**

**Remaining items are now marginal.** 3.4 is worth ~0.07 s of a 0.74 s request.
3.5 (pre-filter to skip expensive scoring) was premised on ML being per-job —
now that the model runs once for the whole corpus, there is far less left to
skip, and it is the one item that can change results. Neither is worth the risk
until something re-measures above them.

> ⚠ **Finding, not a performance item.** For a fixed CV the model produced only
> **3 distinct probabilities across all 800 jobs** — the only per-job feature it
> sees is `Job Role`. The ML half carries `ml_weight` of every hybrid score
> while contributing almost no ranking signal. That is a modelling question for
> 6.5 (the honest-metrics write-up), not something Phase 3 can fix.

### Verification standard used

Batching a model is only safe if the fitted pipeline is row-independent. That
was proven, not assumed, at three levels: probabilities agree with the per-row
path to 1.33e-15 (BLAS summation order); `ml_score` — `int(proba * 100)`, the
only value that reaches a caller — is exactly equal for every row; and end to
end, 800 jobs x 13 `ScoreBreakdown` fields gave **0 differences with an
identical full ranking**.

### ☑ 3.1 — B1 · Biggest single win

**Closed `ef7394b`.** `pipeline.py:305` writes the top matches once, guarded, after the loop. The comment above it records that `save_match` used to be called inside it — once per job per upload.
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

### ◐ 3.2 — B2 · Dictionary rebuilt on every call
`branch: perf/agent3-hoist-synonym-index`

**The original finding is closed.** The 45-key `synonyms` dict rebuilt inside
`_find_skill_matches` was deleted in `589cc9e` — not for speed, but because it was a fifth
competing vocabulary that could never fire (its keys are lowercase; 667 of 669 canonical
names carry uppercase). Canonicalisation is now one `dict.get` against an index built once
at load. **The measured 3.26 s per upload is gone.**

**What is left is the same defect, smaller.** `role_keywords` (`agent3_scorer.py:329`) is a
15-key dict literal rebuilt on **every** call to `_score_title_similarity` — once per job per
upload. Hoist to a module constant.

⚠ **Sequence after 2.7.** Both this and 3.4 touch code the Agent 3 extraction moves. Doing
them first means doing them twice and diffing a moving target; the 2.7 plan folds both in as
its optional commit 5.

### ✗ 3.3 — B6 · **OBSOLETE — do not action as written**
`branch: chore/data-trim-job-corpus`

**This task would now delete the live corpus.** Every premise expired with the C.1–C.10
corpus replacement:

| Claimed | Actual, 12 Aug 2026 |
|---|---|
| `jobs.json` is a 5.8 MB legacy file | `jobs.json` **is the corpus** — 800 records, 1.5 MB |
| `jobs_cleaned.json` (6.5 MB) is current | **Does not exist.** Archived with the old corpus |
| `load_jobs()` keeps a dead legacy branch at `api.py:78–90` | Already removed; `api.py:77` reads `get_config().jobs_data_path` |
| 13 MB duplicated, needs Git LFS | 1.5 MB tracked, one file. **Nothing to trim** |

The only surviving fragment of intent — *"500 jobs demos as well as 4,000"* — was answered
by C.4 building an 800-record corpus deliberately. **Close this; do not re-scope it.**

*(`data/json/jobs.skeleton.json`, 719 KB, is the untracked build intermediate for the corpus
generator. Correctly gitignored. Not a duplicate.)*

### ☐ 3.4 — B4 · Normalize the CV once, not once per job
`branch: perf/agent3-precompute-cv-skills`

`_score_skills` calls `self._normalize_skills(cv.skills)` (`agent3_scorer.py:162`) inside the
per-job loop. The CV does not change. Normalize once before the loop and pass the frozen set
in.

**Second finding, same method, larger** (12 Aug 2026): `_score_skills` walks the CV **twice
over**. It calls `_find_skill_matches` for the matches, then `_has_skill_match` once per
required *and* once per preferred skill — and each of those calls rebuilds `cv_token_sets`
from scratch. For a job with 8 required + 5 preferred skills that is 14 rebuilds where 1 is
needed. Compute the match set once and derive matched / missing / extra from it.

⚠ **Sequence after 2.7**, with 3.2 — a `SkillMatcher` that holds the CV's token sets removes
both problems structurally rather than by patching them in place.

### ☐ 3.5 — B5 · Skip the expensive path for obviously irrelevant jobs
`branch: perf/agent3-cheap-prefilter`

Every job currently gets the full treatment. Gate first: zero shared required skills →
assign a floor score and skip title similarity, ML and education scoring. Typically
eliminates 80–90% of the corpus. Results stay identical for anything that could plausibly
reach the top 10 — assert that in a test rather than assuming it.

### ☑ 3.6 — B3 · One `predict_proba`, not 4,000

**Closed `2ed18e5`.** `ats_predictor.py:162` runs one transform and one `predict_proba` over the whole frame.
`branch: perf/agent3-vectorized-ml-scoring`

**✔ Verified** at `agent3_scorer.py:467–491` — `_get_ml_score` builds a dict, wraps it in a
1-row DataFrame, transforms and predicts, 4,000 times. `ATSPredictor.predict_batch` already
exists, is never called, and internally just loops `predict()` anyway.

The only per-job feature is `Job Role`. Build one 4,000-row DataFrame, one `transform`, one
`predict_proba` → a 4,000-length array. Rewrite `predict_batch` to actually be vectorized.
**Seconds → tens of milliseconds.**

---

## Phase 4 — Make it safe

> **Status: ☑ COMPLETE — 9 of 9.** Closed 12 Aug 2026.

**Goal: safe to put on a public URL.** Cheap fixes, and the first things a reviewer checks.
Agent 4's redesign lives here because the stateless rewrite and the A7 race fix are the
same work — see [ADR-2](docs/adr/002-llm-provider-abstraction.md).

| # | ID | Task | Score | Status |
|---|---|---|---|---|
| 4.1 | A4 | Fix the CORS wildcard + credentials combination | **35** | ☑ `eabddee` |
| 4.2 | A5 | Cap upload size and validate content type | **35** | ☑ `eabddee` |
| 4.3 | SEC | `OPENROUTER_API_KEY` from env only, `.env.example`, never logged | **35** | ☑ `74139ce` |
| 4.4 | RL | Endpoint rate limiting + top-K explanation cap + daily quota counter | **28** | ☑ `b743dd5` + `8159892` |
| 4.5 | A8 | Replace bare `except:`; count and log skipped jobs | **25** | ☑ `b743dd5` |
| 4.6 | A7 | Stop mutating the shared pipeline singleton per request | **24** | ☑ `b743dd5` |
| 4.7 | ③ | `OpenRouterProvider` behind the provider protocol | **18** | ☑ `e906911` |
| 4.8 | A6 | Migrate deprecated startup hooks to `lifespan` | **15** | ☑ `eabddee` |
| 4.9 | ② | Extract the `LLMProvider` protocol from Agent 4 | **14** | ☑ `e906911` |

### ☑ 4.4 — three limits, three different problems (`8159892`)

```
explanation cap   calls per upload     <= 3
daily budget      calls per day        200, degrading at 90%
rate limiter      requests per IP      /match 5/min, /upload 10/min
```

None substitutes for another: a rate limiter still permits 5 uploads a minute
**forever**, and a daily quota still permits one client to burn all of it in a
burst.

**Degrading at 90% rather than 100% is the feature.** Explanations switch to
rule-based *before* the provider starts returning 429s, so running out of quota
looks like a slightly plainer explanation instead of a stall followed by an
error. Failed calls are not charged — counting them would degrade the instance
early on the strength of the provider's own errors — and a budget that cannot
be read **fails open**, since silently downgrading every explanation with
nothing to point at is worse than briefly overspending.

**The counter is in SQLite, not memory.** The deployment target restarts on
idle; an in-process counter would reset the budget on every wake, which is the
same as having none. One UPSERT rather than read-modify-write, verified with 20
concurrent increments.

`Throttle` bounds concurrent calls and honours `Retry-After` — guessing a
backoff when the server has stated the answer is a slower way to get
rate-limited again. GET endpoints are deliberately unlimited: reads are cheap
and limiting them would break the frontend's polling.

> ⚠ **Another instance of the defect this phase keeps finding.** The
> `.env.example` entries added in `74139ce` documented `RATE_LIMIT_ENABLED` and
> the quota variables, but `Config._load_from_env` read **none** of them — the
> same class as `CORS_ORIGINS` (4.1) and `config.llm.provider` (4.9), and
> committed by me two commits earlier. Wired now, plus `LLM_PROVIDER`, each
> verified by setting it and reading it back. **Documenting a setting is not
> the same as reading it; check both.**

### ☑ ADR-2 implemented — Agent 4 providers (`e906911`)

All nine ADR-2 action items are done. `config.llm.provider` — the field that
declared `# ollama, openai, anthropic` and was read by nothing — now selects
between four providers:

```
src/agents/explaining/
  protocol.py    LLMProvider, ExplanationContext, Explanation
  rule_based.py  RuleBasedProvider   always available, no network
  ollama.py      OllamaProvider      local development
  openrouter.py  OpenRouterProvider  hosted demo (512 MB tier can't run Ollama)
  langchain_provider.py               optional fourth path
  prompt.py      one prompt, shared   (was three drifting copies)
  insights.py    structured insights
```

Net **−659 LOC** of the old explainers, **+45 unit tests**. Suite 251 → 296.

**A second determinism defect, same class as A0's.** The rule-based generator
picked its opening sentence with `hash(candidate) % 3`. Python randomises string
hashing per process, so **the same candidate got a different explanation after
every server restart** — exactly the ADR-1 violation already fixed in Agent 3's
keyword scoring, sitting undiscovered in a second place. Now `crc32`; verified
byte-identical under `PYTHONHASHSEED` 0, 999 and random.

**4.6 is now structural rather than patched.** The provider is fixed at
construction and `llm_available` is a read-only property, so there is no mutable
state left for a concurrent request to disturb.

**`explanation_source` on `MatchResult`.** A rule-based fallback after a quota
failure is visible instead of being passed off as model output.

> **Left for a follow-up:** the remaining half of 4.4 — the `slowapi` endpoint
> rate limiter and the daily quota counter. The explanation cap that bounds the
> spend is already in. And ADR-2's note to revisit: if `LangChainProvider` is
> never selected in practice, delete it and the four `langchain*` pins.

> 🔴 **A regression this backlog's own process did not catch.** `655bb09`
> (Phase 2, MLScorer extraction) removed `HybridScoringAgent.ml_predictor`,
> which `api.py` referenced in four places — `/health`, `/match` ×2 and the
> startup hook. **The server would not start.** It sat on `main` for three
> commits and was found only when Phase 4 opened `api.py`. Fixed in `c98db1a`.
>
> The verification bar in use was "no newly failing tests", compared as sets
> with `comm -13`. The API tests were already among the 31 pre-existing
> failures, so a fresh `AttributeError` inside them changed nothing observable —
> **an already-broken module absorbs new bugs in silence.** The score-diff
> harness proved nothing either: it imports the agent directly and never touches
> `api.py`.
>
> **Rule going forward: any change to `src/api.py`, `src/agents/pipeline.py` or
> an agent's public attributes must boot the app and hit `/health`,
> `/jobs` and `/match`.** `TestClient(app)` as a context manager runs the
> lifespan, so this is four lines and a few seconds. "The suite is no worse" is
> not evidence the application runs. This is also the strongest argument yet for
> 6.1 (CI) and 6.7 (deleting the ~23 tests that target an API that never
> existed) — while a quarter of the suite is red, the failure-set comparison is
> the only signal available, and it has now demonstrably missed a total outage.

### ☑ 4.1 — A4 · CORS

**Closed `eabddee`.** `api.py:122-130` reads the allowlist from config and logs what it restricted to. The wildcard-plus-credentials combination is gone.
`branch: fix/api-cors-wildcard-credentials`

**✔ Verified** at `api.py:45–47`: `allow_origins=["*"]` **with** `allow_credentials=True`.
Browsers reject that combination outright, and it is a flagged anti-pattern. `config.py:111`
already defines `cors_origins` and `config.py:205` already reads a `CORS_ORIGINS` env var —
the API module simply never consults either. Wire it up: default
`["http://localhost:3000"]`, the Vercel URL in production, `allow_methods=["GET","POST","DELETE"]`.

### ☑ 4.2 — A5 · Unbounded upload

**Closed `eabddee`.** `api.py:237-244` caps the read at `max_upload_size_mb` and answers 413 by name. Content is checked against the extension before a parser sees it.
`branch: fix/api-upload-size-limit`

**✔ Verified** — `await file.read()` straight into memory at `api.py:247`, `:329` and `:463`
with no cap. `config.py:113` defines `max_upload_size_mb: int = 10`, also never used. A
500 MB POST takes the process down. Check `file.size` before reading, reject >10 MB with
413, and validate real content type rather than trusting the extension.

### ☑ 4.3 — SEC · Two OpenRouter keys were in public git history — disabled 14 Aug 2026

> **Found 14 Aug 2026 while checking whether the repo was clean before a key
> was configured. It is not a hypothetical.**

A full history scan with the new `scripts/check_secrets.py --history` found
**two distinct OpenRouter keys, 24 occurrences, across four files** - not the
one file the first grep suggested:

| File | Keys |
|---|---|
| `tests/test_agent2_5_llm_scorer.py` | `sk-or-v1-835...5d4b` |
| `docs/API_KEY_SETUP.md` | `sk-or-v1-835...5d4b`, `sk-or-v1-45f...f4cd` |
| `docs/AGENT2_5_LLM_QUICKSTART.md` | `sk-or-v1-835...5d4b` |
| `docs/LLM_IMPLEMENTATION_SUMMARY.md` | `sk-or-v1-835...5d4b` |

`docs/` is gitignored *now*, which is why none of this shows in the working
tree - and why a check that only looks at the working tree sees nothing.

The state of it:

| | |
|---|---|
| Present at `HEAD` | no — the file was deleted in `bf05511` |
| Present in history | **yes** — 16 commits contain it |
| Reachable from `origin/main` | **yes** — earliest at `18a61b0` |
| Remote | `github.com/Sharawey74/Recruiter-Pro` |
| Repository visibility | **public** — the unauthenticated GitHub API returns 200 |

Deleting the file did not help. Anyone who clones the repository gets the key,
and automated scrapers watch public pushes for exactly this pattern.

**Closed by disabling the keys, not by editing history.** The owner disabled
both at openrouter.ai on 14 Aug 2026, which is what actually ends the
exposure: the strings stay in the repository forever and are now worthless.

That is the whole reason a history rewrite is unnecessary here. `git
filter-repo` rewrites every commit hash, needs a force push, and breaks every
existing clone and branch — a large, disruptive change that buys nothing once
the credential is dead. It is worth doing only if the audit trail matters more
than the disruption, and here it does not.

A sweep for other credential shapes - `sk-ant-`, `sk-proj-`, `ghp_`, `AKIA`,
`AIza`, Slack tokens, private-key blocks - found nothing. Two `hf_` hits are
false positives in deleted binary model artifacts.

**The recurrence is now blocked.** `scripts/check_secrets.py` runs in CI
against every tracked file and asserts `.env` is both gitignored and
untracked; `--staged` suits a pre-commit hook, and `--history` is the audit
that found the above. Patterns are prefix-anchored per vendor rather than
"long random string", because a check that fires on hashes and minified JS
gets switched off. Matches are masked in output - enough to locate, never
enough to use.

`--history` is deliberately **not** in CI: it is slow, and it would fail
forever on commits that cannot now be changed. Revocation closes an exposure
that has already happened; CI stops the next one.

**`.env` created 14 Aug 2026** with `LLM_PROVIDER=openrouter` and
`OPENROUTER_API_KEY=` left empty for the owner to fill - an assistant does not
handle credentials. Protections verified rather than assumed:

| Check | Result |
|---|---|
| Gitignored | yes - `.gitignore:88` |
| Tracked by git | no |
| In any commit, ever | no |
| Filesystem ACL | inheritance broken; owner read/write only. `BUILTIN\Users` previously had Modify |
| Logged anywhere | no - grep over `src/` finds no logging of `api_key` |
| Returned by an endpoint | no - config is never serialised into a response |
| Echoed in an error | no - the provider's `except` logs `type(e).__name__` and the message, never the request context, which can carry the `Authorization` header |
| Behaviour while empty | `/match?explain=true` returns 200 with a rule-based explanation - verified |
| Spend ceiling | `LLM_DAILY_QUOTA=200` in SQLite, degrading at 90%, ~66 uploads/day at 3 calls each |

**Verifying a rotation.** `scripts/check_llm_key.py` queries OpenRouter's
`GET /api/v1/key` and reports whether the configured key is live or rejected,
without printing it. It costs no generation tokens and no daily quota, so it
is safe to run repeatedly. It exists because the obvious test — upload a CV
and see whether the prose looks LLM-written — cannot distinguish a working key
from the rule-based fallback, which also produces plausible prose.

> Its no-key path is verified. The live-network path is **not** verified in
> this environment: Python `requests` cannot complete a TLS handshake to any
> host in this sandbox, while `curl` can. `curl` against
> `https://openrouter.ai/api/v1/key` with an invalid key does return **401**,
> which is the status the script keys off, so the logic is right — but the
> script itself has not been exercised against a live response. Run it once
> after pasting a new key; if it reports an SSL error rather than LIVE or
> REVOKED, that is this same environment issue and not the key.

**Then the original item, which still stands:** env only, never committed,
never logged, never returned in a response. `.env.example` carries the names
with no values, `.env` is gitignored (`.gitignore:88`), and the working tree
and `HEAD` are both clean. What was missing was a check on *history*, and a
scan for key shapes belongs in CI next to the control-character scan — the
argument is identical: a human reading a diff does not reliably catch either.

### ☑ 4.4 — RL · Two rate-limit layers plus a hard cap

**Closed `b743dd5` + `8159892`.** Per-IP limits on `/match` and `/upload`, the top-K explanation cap, and the daily quota counter. As of 16 Aug 2026 the limiter's own test enables it for its own duration rather than skipping when configuration turns it off, so the behaviour is asserted rather than assumed.
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

### ☑ 4.5 — A8 · Silent failure handling

**Closed `b743dd5`.** No bare `except:` remains anywhere in `src/`.
`branch: fix/api-specific-exception-handling`

**✔ Verified** — bare `except:` at `api.py:292`, `:434`, `:526`, all around temp-file
cleanup. Use `except OSError`. Separately, `load_jobs()` swallows per-record parse failures
with `except Exception: continue`, so there is no way to know how many of the ~4,000 jobs
never load. Count them and log at startup: `Loaded 3,847 jobs, skipped 153 malformed`.

### ☑ 4.6 — A7 · Per-request mutation of a module-level singleton

**Closed `b743dd5`.** Nothing in `api.py` assigns to the shared pipeline's agents; per-request behaviour is passed as an argument.
`branch: fix/api-stateless-explainer-invocation`

**✔ Verified** at `api.py:335–362`. The `/match` handler reassigns `pipeline.agent4` and
`pipeline.agent4.llm_available` on a module-level singleton, then restores them in a
`finally`. With two concurrent requests, request B's toggle leaks into request A. Under
uvicorn with more than one worker this is a live race — and the restore is skipped entirely
on some raise paths.

Do not mutate the singleton. Pass `use_llm` / `use_langchain` down as arguments to
`process_cv_batch(...)` and let Agent 4 decide per call. This is the same change as 4.9.

### ☑ 4.7 / 4.9 — ②③ · Agent 4 provider abstraction, then OpenRouter

**Closed `e906911`.** `src/agents/explaining/` holds `protocol.py` with `ollama.py`, `openrouter.py`, `langchain_provider.py` and `rule_based.py` behind it. Which one answered is reported per match as `explanation_source`.
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

> **Superseded 12 Aug 2026 by the Phase 5 rebuild.** Every finding below is
> closed except B10's field aliases. Kept because it is the measurement the
> phase was planned from, and because the component table records a layout
> that no longer exists.

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

| Component | State | Findings | Now |
|---|---|---|---|
| `layout/sidebar` | ✅ | **N8** lists only 4 of 6 pages · Scoring indicator added this session, verified live | Rewritten — all six routes; the scoring indicator moved to `layout/top-bar`, which the design system reserves the sidebar for navigation alone |
| `layout/header` | ⚠️ | 10 lines, presentational only — `/` and `/upload` do not use it, so heading styles diverge | Deleted → `layout/page-header` |
| `upload/match-card` | ⚠️ | Was the build break (1.5). Skill badges now populated — but will show **category names** until 2.2 | Moved → `match/match-card` |
| `upload/match-summary` | ✅ | renders | Moved → `match/match-summary` |
| `ui/circular-progress` | ✅ | renders | Deleted → `ui/score-ring`, which states the band in text and an icon rather than colour alone |
| `ui/skill-badge` | ✅ | renders; `matched` / `missing` variants both used | Rewritten — four variants, each with its own icon |

Added in the rebuild: `ui/score-bar`, `ui/stat-card`, `ui/feedback`,
`jobs/job-card`, `pipeline/processing-pipeline`, `upload/cv-dropzone`,
`lib/scores.ts`, `lib/store.ts`.

### New findings

**☑ N8 · Two of six pages are unreachable from the UI** — fixed 12 Aug 2026
 — `fix/frontend-sidebar-nav`
`sidebar.tsx` `navItems` lists Dashboard, Results, History, Shortlist. **`/upload` and
`/jobs` have no link anywhere in the app** — reachable only by typing the URL. `/upload` is
the fuller of the two upload flows. Either add both to the nav, or delete `/upload` and keep
the dashboard uploader — but decide, because shipping an orphaned page reads as unfinished.

**☑ N9 · Every page has the same browser-tab title** — fixed 12 Aug 2026
 — `fix/frontend-page-metadata`
`layout.tsx:7` sets `title: "AI Resume Matcher - Dashboard"` and **no page exports its own
`metadata`**. Every tab, bookmark and history entry says "Dashboard", including `/jobs` and
`/history`. One `export const metadata` per page.

**☑ N10 · The upload UI advertises a 200 MB limit** — fixed 12 Aug 2026; the API's 10 MB ceiling is now enforced (4.2) and stated once, in `cv-dropzone.tsx`
 — `fix/frontend-upload-limit-copy`
`upload/page.tsx:124` says *"Limit 200MB per file"*. `config.py:113` says 10 MB. The server
enforces **nothing** (A5). So the UI actively invites the exact request that takes the
server down. Fix the copy and the enforcement together — this makes 4.2 more urgent than its
score suggests.

**☑ N11 · Four pieces of copy state facts that are not true** — all four fixed 12 Aug 2026; counts are derived from the API rather than written into the markup
 — `fix/frontend-copy-accuracy`
Cheap to fix, and each one is visible to a visitor:

| Where | Says | Reality |
|---|---|---|
| `page.tsx:292` | "Supported formats: PDF, DOCX" | TXT also supported |
| `upload/page.tsx:124` | "Limit 200MB per file" | no limit enforced; config says 10 MB |
| `jobs/page.tsx:54` | "3,000+ job descriptions" | 4,000 loaded, 6,146 exist |
| `results/page.tsx:78` | "max 5 jobs each" | `/match` defaults to `top_k=10` |

---

## Phase 5 — Make it feel good ☑

**Goal: what a visitor actually experiences.** Closed 12 Aug 2026 across four
commits: `74f1d67` (API), `fcb9ddf` (naming), `df50cbd` (interface),
`9bb7be1` (tooling).

The scope grew once the design assets arrived in `frontend/Images/`. What was
planned as nine targeted UI fixes became a rebuild on a real design system,
because the fixes could not be applied to a surface that had no shared
vocabulary: every page carried its own palette, its own card treatment and its
own inline `>= 75 ? green : >= 50 ? yellow : red`.

| # | ID | Task | Status |
|---|---|---|---|
| 5.1 | A9 | Landing page swallows errors — the one page with no toast | ☑ |
| 5.2 | A10 | Unify file acceptance between drag-drop and file picker | ☑ |
| 5.3 | B7 | `/jobs` search box does nothing | ☑ |
| 5.4 | B8 | Delete the fake progress delay; show real `processing_time` | ☑ |
| 5.5 | B9 | One state source instead of five `localStorage` keys | ☑ |
| 5.6 | B10 | `Match[]` not `any[]`; one field shape, not legacy + new | ☑ |
| 5.7 | B11 | Loading skeletons and empty states | ☑ |
| 5.8 | ⑤ | Drop unused deps; ~~delete `cache.py`~~; dedupe `/history` | ☑ |
| 5.9 | — | Rename the misleading score fields in the `/match` payload | ☑ |
| 5.10 | — | One name for the application *(new)* | ☑ |
| 5.11 | — | Align the UI to `frontend/Images` *(new)* | ☑ |
| 5.12 | — | Job detail page — the missing step in the journey *(new)* | ☑ |
| 5.13 | — | Delete decoy controls *(new)* | ☑ |
| 5.14 | — | Icons on job-matching components and score indicators *(new)* | ☑ |
| 5.15 | — | Landing page, four slides, from the Stitch spec *(new)* | ☑ |
| 6.0 | N6 | Zero runtime console errors — fix the hydration mismatch | ☑ |
| N8 | — | `/jobs` and `/upload` are unreachable from the sidebar | ☑ |
| N9 | — | Every page shares one browser-tab title | ☑ |

**Gates at close:** 501 backend tests passing, 0 failing, branch coverage
81.84% against an 81% floor; `ruff` clean; corpus validator 20/20; no control
characters; `next build` clean; `tsc --noEmit` clean; `eslint .` clean — the
first time ESLint has ever run in this repository.

**Verified against a live stack, not just a build:** both servers started, a
résumé uploaded through the real dropzone, 800 roles scored in 481ms, the
ranking rendered, the session survived navigation to `/results`, the shortlist
loaded from the database with skill badges, and `/match/single` returned its
full breakdown from the new job detail page.

---

### The design system — `frontend/Images/`

Eight files: three rendered mockups (dashboard, results, jobs), one history
screen, three HTML reference pages, and `Image 9.markdown`, which is the
system itself — a Material 3 token set named **Deep Tech Luminance**.

`tailwind.config.ts` now carries those tokens verbatim rather than renamed to
something friendlier, because the three HTML reference pages are written
against those exact class names and any rename makes them unusable as a
reference.

| | Before | After |
|---|---|---|
| Palette | 4 ad-hoc navy shades + whatever purple each page reached for | 51 Material 3 tokens |
| Type | system font stack | Inter + JetBrains Mono, five roles |
| Score colours | stock `green-500` / `yellow-500` / `red-500`, redefined in 6 files | 3 desaturated tokens, defined once in `lib/scores.ts` |
| Cards | 5 different border/gradient treatments | `glass-panel`, `gradient-border-card` |
| Radius | `rounded-xl` everywhere | 8px controls, 16px cards, 24px wrappers |

**One deliberate departure from the mockups.** They put a notification bell, a
settings gear and an account avatar in the top bar. This application has no
notification stream, no settings surface and no accounts, so all three would
be dead controls — which the brief rules out. The slot keeps its size and
holds live API health, corpus size and scoring mode instead. The search field
stays, because it can be made real: it is the Jobs filter.

---

### ☑ 5.9 — the `/match` payload named three scores misleadingly

`api.py` returned:

| Field | What it actually is |
|---|---|
| `parser_score` | the **rule-based total** — nothing to do with Agent 1, the parser |
| `matcher_score` | the **skill score** |
| `scorer_score` | **experience only** |

The names suggested a per-agent breakdown that does not exist, and the UI
believed them: it labelled the skill score **"ATS"** and the experience score
**"Matching"** on three separate pages.

Now `rule_based_score`, `skill_score`, `experience_score`, with `ml_score`
alongside, on both `/match` and `/match/history` — one match shape whether it
arrived from a live run or from storage. `test_api_contract.py` asserts the
old names cannot come back.

### ☑ 5.1 / 5.1b (N6) — the landing page

Both closed. Failures now surface as a toast *and* an inline message in the
pipeline panel, rather than resetting the stepper to idle so that a dead
backend looked identical to never having pressed the button.

The hydration mismatch is gone with the markup that caused it —
`ID: v{Math.floor(Math.random() * 100)}0ZXY` rendered directly in JSX, so the
server and client produced different numbers and React discarded the
server-rendered DOM for the whole subtree. Two more sources were found and
fixed while here:

- `new Date().toLocaleDateString()` in render, and `formatDate` with no locale
  argument — the runtime's own locale differs between Node and the browser on
  any machine not set to en-US. `lib/utils.ts` now pins locale and time zone.
- `useState(() => localStorage.getItem(…))`, which runs on the server where
  there is no localStorage. See 5.5.

### ☑ 5.2 — file acceptance

`components/upload/cv-dropzone.tsx` is now the only definition, used by all
three upload surfaces. It exports `ACCEPTED_EXTENSIONS`, the 10 MB ceiling
matching the API's own, and `describeRejection()`, so a rejected file always
produces a message naming the file and the reason.

The dashboard's drop handler took `file.type === "application/pdf"` and
discarded everything else in silence, while its own picker advertised `.docx`
— so dragging a .docx onto the dashboard did nothing at all, with no feedback.

### ☑ 5.3 — `/jobs` search

The frontend had been sending `search` since it was written. FastAPI ignores
unknown query parameters, so every request succeeded and returned the
unfiltered page.

`GET /jobs` now takes `search`, `category`, `remote_type` and `seniority`,
filters server-side, and reports `total` as the filtered count — paging past
the end of a filtered set depends on that. Two endpoints joined it:

- `/jobs/facets`, so the dropdowns come from the corpus rather than a
  hardcoded list that drifts out of step with it.
- `/jobs/{job_id}`, which serves the untruncated requirement list. The list
  view caps `required_skills` at 10; a detail page showing a truncated
  requirement list would be actively misleading.

The active filters are mirrored into the URL, so a filtered view is shareable
and the top bar's quick find can land on `/jobs` with a query applied.

### ☑ 5.4 — real timing

`processing_time` was hardcoded `None`. The dashboard covered for it with
`setTimeout(1000)`, `setTimeout(1000)`, the real request, `setTimeout(500)` —
2.5 seconds of theatre around a call that takes about 700ms — and printed
*"Identified 45 technical skills and 12 soft skills"* underneath on every run,
a constant string in the markup.

The API measures with `perf_counter` and returns `processing_time` and
`jobs_evaluated`. The panel shows one in-flight state with a measured counter,
and on completion each stage reports the figure it actually produced:
**"800 jobs scored in 481ms"**.

There is no honest way to show stage three finishing before stage four starts
— the pipeline is a single HTTP request and the server does not stream
progress. Per-stage progress would need SSE; that is a real feature, not a
timer, and it is not in this phase.

### ☑ 5.5 — one state source

Five keys — `matchResults`, `latestAnalysis`, `selectedFileName`,
`candidateStatus`, `useLLM` — written by four pages that never agreed on who
owned what. Clearing history meant remembering to delete all five by hand, and
a page mounting after another had written never learned about it, because
localStorage fires no event in the tab that wrote it.

`lib/store.ts` is one key read through `useSyncExternalStore`, with quota
failures caught, cross-tab updates via the `storage` event, and a `hydrated`
flag so pages render skeletons rather than zeroes before storage has been
read.

### ☑ 5.6 — types done, and the legacy aliases are gone (`4ab29d7`)

`any` is gone: `Match[]` everywhere, `catch (caught: unknown)` narrowed by
`apiErrorMessage`, and `@typescript-eslint/no-explicit-any` is an error so it
cannot come back. This mattered more than it looks — `useState<any[]>` is why
renaming a wire field changed nothing at compile time and produced `NaN` at
runtime.

**The aliases are now gone too**, as their own commit — which is why they were
held back. `company`, `location` and `job_type` are removed from all three
endpoints; a job carries `title`, a match carries `job_title`, and neither
carries both. `match_job_fields()` renames the one field that differs between
the two shapes rather than sending both.

Emitting each of those twice was not free: every consumer wrote
`match.company_name || match.company` and guessed which was authoritative, and
a component reading only the alias would have rendered nothing silently the
day the alias stopped being populated. A contract test now asserts none of
them return.

### ☑ 5.7 — skeletons, empty states, error states

`components/ui/feedback.tsx`: `CardSkeleton`, `CardSkeletonGrid`,
`RowSkeleton`, `EmptyState`, `ErrorState`.

Every empty state names the next action and links to it. Every failed fetch
shows the reason and a retry button — the pages previously fired a toast and
then rendered their empty state, so once the toast faded a network failure was
indistinguishable from having no data.

`aria-live` on the status chips, `role="img"` with a spoken label on the score
ring, and `prefers-reduced-motion` honoured for the pulse and skeleton
animations.

### ☑ 5.8 — dependencies and the duplicate endpoint

Three dependencies removed, not two: `recharts` and
`class-variance-authority` were already unused, and `react-dropzone` became
unused when `cv-dropzone.tsx` replaced it — 38 packages.

`GET /history` is deleted. It served the same rows as `/match/history` under
an incompatible shape (`score` vs `final_score`, `cv_name` vs
`candidate_name`, a flat `decision` vs a status) and no client called it. Two
encodings of one resource is how the two drifted far enough apart for one of
them to return 500 on every call for months.

### ☑ 5.10 — one name

The project answered to four names: `Recruiter-Pro-AI` in module docstrings,
`Recruiter Pro AI` in the API title and startup banner, `AI Resume Matcher` in
the browser tab, `AI Matcher` in the sidebar. All are now **Recruiter Pro**.
GitHub URLs and clone paths keep the repository's real name.

### ☑ 5.11 — the pages, rebuilt

Each page is now a server component that owns its `metadata` and renders a
client component — which is what fixes N9 without a `layout.tsx` per route.

| Route | What changed |
|---|---|
| `/` | Real pipeline, real timing, real skill counts, errors surfaced, top 3 with a link to the full ranking |
| `/upload` | Batch runs continue past a failed file instead of discarding every result already collected; per-file summary and timing |
| `/jobs` | Server-side search and three facet filters, URL-synced, debounced, stale-response guarded |
| `/jobs/[jobId]` | **New** — see 5.12 |
| `/results` | Reads the current run from the session store. It used to load `/match/history`, so a page headed "Match Results" showed every match ever stored. CSV export now works |
| `/history` | Skill badges from stored data, banded scores, working clear-all, filter over loaded rows (labelled as such — the API has no history search) |
| `/shortlist` | Manual verdicts marked as manual and resettable, so a human decision is distinguishable from automatic banding |

### ☑ 5.12 — the job detail page

Every job card in the reference design carries a **Details →** affordance with
nowhere to go: the route did not exist. `/jobs/[jobId]` is the missing step —
full description, untruncated requirements, salary, education, and a direct
CV-to-this-job match.

That match is what finally calls `/match/single`. It is the only endpoint
returning the five-component breakdown plus strengths, red flags and
recommendations, and `matchSingleJob()` had been written for it in `lib/api.ts`
with no caller anywhere in the app.

### ☑ 5.13 — decoy elements removed

| Element | Why it went |
|---|---|
| Notification bell, settings gear, account avatar | No notification stream, no settings surface, no accounts |
| **Export** on `/results` and `/history` | Wired to nothing. `/results` now writes a real CSV, quoted — job titles contain commas |
| **Filter** button on the dashboard | No handler |
| "Comprehensive AI Analysis / RECOMMENDED" mode cards | Two cards selecting one boolean, one labelled RECOMMENDED for a path needing a provider that may not be configured. One honest checkbox |
| `ID: v{random}0ZXY` chip | Decorative, and the hydration mismatch |
| Hardcoded Figma sentence and `["React", "TypeScript"]` fallbacks | Invented content — a warehouse role described in terms of Figma |
| `MAX 20 MB` / `Limit 200MB per file` | The API's ceiling is 10 MB. Both figures were wrong, and differently wrong |
| Disabled-forever filter clear button | Rendered only when it has something to clear |

### ☑ 5.14 — icons

- **Job cards** key their glyph off the corpus's eight real categories
  (`engineering` → CPU, `maintenance` → wrench, …), so the icon carries
  information in a mixed grid rather than being decoration.
- **Score components** each have a fixed icon — skill coverage, experience
  fit, rule-based total, model score — which only works because they mean the
  same thing on every card.
- **Score bands** carry an icon *and* a text label, never colour alone. Colour
  alone leaves roughly 1 in 12 users unable to tell an accepted match from a
  rejected one.
- **Skill badges** state their relationship by icon: ✓ matched, ✗ missing,
  ∗ required, + preferred. "Matched" and "missing" are opposite verdicts that
  previously differed only by hue.
- Every icon is `lucide-react`, already a dependency. The mockups use Material
  Symbols, which would mean a second icon font over the network.

### ☑ 5.15 — Landing page (`b672824`)

Four scroll-snapped slides at `/`, built to the Stitch spec in
`frontend/Images/stitch_design_enhancement_and_refinement/`. The dashboard
moved to `/dashboard` — the spec's own CTA reads "Enter Dashboard" — and the
sidebar gained Home.

| Slide | Built |
|---|---|
| Neural matching | Canvas particle field, cursor-following glow, staggered reveals, drifting ambient washes |
| Intelligent parsing | Four cards with rotating conic-gradient borders, hover lift, icon scale |
| Global reach | Ranked bar chart of real markets, counters that tick up |
| Final CTA | Neon pulse on the button, scanning line down the slide, stack row |

**The numbers were the real decision.** The spec asked for 99% Accuracy, 10x
Faster, 50M+ Profiles, 1,204 Active Job Boards, 5.4M+ Candidate Profiles,
"Join 500+ top recruiting teams", and a logo wall naming Vertex, Omni, Delta
and Hexa. This system has 800 jobs, no candidate database and no customers.

One of those is worse than merely untrue. **1.4 in this file** records that the
classifier's 99% is an artifact — the label is a threshold on a column the
model does not train on, and two ordinary features reproduce it — and calls
that finding the most valuable thing in the repository. A landing page
advertising "99% accurate" would contradict it. So `GET /stats` serves no
accuracy figure at all, and a contract test asserts none appears.

| Spec | Shipped | Source |
|---|---|---|
| 99% Accuracy | *(omitted)* | see 1.4 |
| 10x Faster | **22×** | measured, Phase 3: 16.64s → 0.74s |
| 50M+ Profiles | **800** roles · **654** distinct skills | live `/stats` |
| 24/7 Processing | **0.74s** per résumé | measured |
| 1,204 Job Boards · 5.4M Profiles | **27** countries · **46** cities · **60** companies | live `/stats` |
| "Trusted by" Vertex/Omni/Delta/Hexa | the stack: FastAPI, Next.js, scikit-learn, OpenRouter, SQLite | true |
| "Discerning true seniority from inflated titles" | what the four agents actually do | the code |

Better copy as well as honest: an engineer who reads "5.4M+ profiles" on a
portfolio project discounts everything after it.

**Two robustness defects surfaced during verification**, both the same shape —
decoration able to hide the page it decorates:

- Reveal-on-scroll hid content with `opacity: 0` and cleared it when an
  IntersectionObserver fired. An observer that never fires — no JS, a slide
  never reached, a throttled tab — means a blank screen with the text present
  in the DOM and invisible. The hidden state is now applied by script and
  always cleared, by the observer or by a failsafe.
- The entrance keyframe animated opacity with `animation-fill-mode: both`,
  which holds the `from` state through the delay and indefinitely if the
  animation never starts. It animates transform only now; visibility is
  declarative. Counters got a failsafe outside their observer for the same
  reason — a `0` under a label reading ROLES INDEXED is worse than no
  animation.

Verified with animations and observers entirely inert: **0 of 21 blocks
invisible, every counter showing its real figure.**

**Second review pass (`58ac2be`).** Against the Stitch "Global Market Reach"
screen:

| Asked | Done |
|---|---|
| Remove the ruled grid on slide 1 | Replaced with constellation lines between nearby particles |
| Slide 3: a geographic design with animation | Real world map - 27 country nodes at true coordinates, sized by job count, arcs with travelling lights |
| Slide 4: glassmorphic button | Translucent surface, lit border, blur behind, glow in the halo not the body |
| Slide 4: highlight and brighten the heading | White with a two-stage text shadow in the primary |

**On the map's honesty.** Land is a stippled silhouette from coarse
hand-authored continent rings - dots rather than coastlines precisely because
the shape is an approximation and should not imply otherwise. The *nodes* are
the accurate part: real coordinates, real counts, verified by asserting each
lands in the right quadrant (US upper-left, Australia lower-right, New Zealand
far bottom-right).

The reference's overlay reads "LIVE PIPELINE ACTIVITY / Syncing global
nodes...". Nothing syncs - the corpus is a file read once at startup - so it
says "Corpus loaded / 27 of 27 markets plotted" instead. An animated "syncing"
label over static data is a lie with a pulse on it.

`/stats` also stopped truncating `top_countries` to twelve: the map draws one
node per market beneath a headline stating how many exist, so twelve nodes sat
under a sentence claiming 27.

**Review pass, 14 Aug 2026 (`c1ee397`).** Notes from the running app:

| Asked | Done |
|---|---|
| Smoother slide transitions | `--enter` custom property driven by a 21-threshold observer; CSS interpolates opacity and translate. `scroll-snap-stop` relaxed to `normal` |
| Slide 3 animation not showing | **A real bug** — see below |
| CTA over-sharp, not reactive | `rounded-full`, hover scale, arrow slide, active press |
| Grid does not fit when zooming | `clamp()` type, `repeat(auto-fit, minmax())` grids, `min-h` not `h` on slides |
| Cards not interactive | One `.card-interactive`: lift, brighter edge, glow, on hover *and* focus-within |
| Remove the pipeline chip and Built-with row | Removed |
| Dashboard: Top matches / checkbox collision | **A real bug** — see below |
| Checkbox shape | One `.checkbox`, drawn rather than OS-painted, used everywhere |
| Remove corpus/scoring chips and the duplicate title | Removed; one Live/Offline presence indicator remains |

**The slide-3 bars never grew.** The keyframe was `scale3d(1, 0, 1)` — scaleY
— on a *horizontal* bar, so it collapsed vertically and grew in the wrong
axis, while `transform-origin: left` had nothing to act on. With
`fill-mode: both` the chart stayed collapsed until the animation ran, and
forever if it did not. That is the **third** instance this session of `both`
plus a delay being a way to hide content indefinitely; the rule now is
`forwards` everywhere, so the failure mode is "un-animated", never "invisible".

**The dashboard collision was real, not a rendering artifact.** The "Write
explanations" label sized itself beside a `shrink-0` button, so at some widths
its second sentence overflowed the row and ran into the "Top matches" heading
below. `min-w-0` lets the text wrap and `flex-wrap` drops the button under it.

**On the top bar.** The corpus size and scoring mode were properties of the
engine, not of the session — they do not change while you work, so three chips
of standing facts crowded the bar. The one thing that does change is whether
the backend is answering. "Rules only" still appears, but only when true.

Also worth recording: three separate verifications this session were read off
**stale servers** still holding ports 8000 and 3000 from earlier runs, once
reporting the API shape as unchanged when it had changed. Checking process
start times, and comparing the served asset against the built one, is now the
habit — `run.ps1 -Force` exists for exactly this.

**Review pass, 15 Aug 2026 (`58ac2be`).** Two of the five items reported were
layout bugs with the same shape, and one was not a UI problem at all.

| Asked | Done |
|---|---|
| More particles, moving faster | Density doubled (area/8000, capped 180), drift 2.5x, link radius 130 -> 112 so the denser field does not become a mesh |
| Slides cut off top and bottom | `snap-mandatory` -> `snap-proximity`; slide padding py-16 -> py-8/10 |
| Dashboard spacing | **A real bug** -- see below |
| Jobs search and filter display | **A real bug** -- see below |
| Slide 4 display | Lit top edge, chip, ambient wash, a reassurance line, and the three live figures closing the panel |
| Jordan Ellis appearing on every run | **Not a UI bug at all** -- see below |

**`height: 100%` inside a stretched cell, twice.** The dropzone was
`h-full` in a grid cell whose height is set by the *other* column, so it
claimed the whole cell regardless of the analyse row beside it -- and that row
was pushed out of the bottom of the cell. The next section's margin is measured
from the cell, not from the overflowing content, so its heading landed on top
of the row. `flex-1` in a flex column asks for what is left instead of all of
it. Measured before: analyse row bottom 949, cell bottom 840. After: both 788,
with the heading a clean 105px below.

**The jobs toolbar overflowed *because* the container was wide.** `.field`
carries `w-full`, and the three selects were `lg:flex-none` -- and `flex-none`
means `flex-basis: auto`, which defers to that `width: 100%`. Each select
therefore asked for the full width of its row, the row asked for three times
its own width, and the toolbar ran off the screen. Zooming out made it worse,
which is the tell: the bug scaled with the container. Every item now declares
its own `flex-basis`, which outranks a width, so nothing is sized by a
percentage of its parent and nothing by its own contents. Verified at 420,
1100, 1920 and 3840 CSS px: no horizontal scroll, nothing past the panel.

**Jordan Ellis was the test suite writing to the application's database.**
`/match` persists, `src/api.py` builds its pipeline at module scope, and
nothing pointed the tests anywhere else -- so every `pytest` run inserted the
contract suite's sample candidate into `data/database/match_history.db`. 78 of
the 81 rows in that file were test output, and the History page listed them as
real analyses. `tests/conftest.py` now redirects `DATABASE_PATH` to a temporary
directory before the first import, which is the only moment early enough;
`tests/unit/test_database_isolation.py` fails if that stops working. The 78
rows are deleted and the file backed up first.

The same conftest also pins `RATE_LIMIT_ENABLED=false`. Four contract tests
failed with 429 on a laptop and passed in CI purely because CI sets it -- a
suite whose result depends on the developer's `.env` is not a suite. The
limiter's own test used to skip itself whenever the limiter was off, so the one
assertion covering it ran nowhere that mattered; it now enables the limiter for
its own duration and asserts.

**The particle field was a third of the size it looked.** `h-full w-full`
resolved against the slide's centred content column while `inset-0` anchored to
the slide, so the canvas covered 1430x489 of a 1920x920 slide -- and since the
point count comes from the canvas area, it drew 44 points where the formula
asked for 174. `Slide` now takes a `backdrop` rendered outside the content
column. A canvas is a replaced element, so `inset-0` alone does not stretch it;
the percentages are what size it, and they need the right parent.

**Not verified visually.** The browser pane in use does not composite, so
`requestAnimationFrame` never fires and the canvas is never painted -- every
check above is geometry and DOM state read back from the live page, not a
screenshot.

**Mobile shell, 15 Aug 2026.** The frame was three siblings with no
breakpoint between them: a `fixed w-64` sidebar, a top bar sized
`calc(100% - 16rem)`, and a `main` with a hard `ml-64`. Below roughly 700px the
sidebar covered most of the screen and the content took what was left -- at
420px the jobs toolbar had 84px to work in -- while the top bar's width
calculation subtracted a sidebar that, on a phone, should not have been there
at all, leaving a 16rem strip of every screen uncovered.

Below `lg` the sidebar is a drawer now: a menu button in the top bar, a
backdrop that fades, Escape to close, the page held still underneath, and the
drawer closing itself when a link is followed. `AppShell` exists to hold the
one piece of state both halves need; `children` is still passed through from
the root layout, so the pages remain server components.

**Focusability is not an animation's job.** The usual way to keep an
off-screen drawer out of the tab order is `visibility: hidden` under a
`transition-[transform,visibility]`, which works because visibility flips at
the end of a hide and the start of a show. It also makes reaching the menu
depend on a transition completing -- and a transition that never runs leaves
the drawer permanently unreachable, which is exactly what happened in the
browser used to verify this. The drawer is `inert` when closed instead, driven
by a media query through `useMediaQuery` in `lib/media.ts`. That hook also
replaced the copy of the same matchMedia store that had grown inside the
landing primitives.

Verified at 375px on all seven routes: no horizontal scroll and nothing past
the viewport, with the drawer closed and open, and after following a link from
it. The history table is 1035px wide there and scrolls inside its own
`overflow-x-auto` container, which is the intended treatment rather than a
defect. Desktop geometry is unchanged: sidebar 0-256, top bar and main from
256, grid columns 830/586 as before.

**Warnings triaged, 16 Aug 2026.** The suite reported 20; it reports 2, and
both of those belong to a dependency (`SwigPyPacked` / `SwigPyObject` have no
`__module__`, raised through the langchain import path).

**`l1_ratio` was being searched where it does nothing.** The logistic
regression grid was one flat dict crossing `penalty` with `l1_ratio`, and a
flat dict is expanded as a Cartesian product -- so the search ran 6 x 3 x 3 =
54 combinations for 30 distinct models. Every l1 and l2 fit was repeated three
times, once per irrelevant `l1_ratio`, and sklearn warned each time.

The wasted fits were the cheap part. `best_params_` reported an `l1_ratio`
beside a penalty it had no bearing on, and `scripts/ml_utils/create_complete_metadata.py`
copies that value into the model card as a hyperparameter of the trained model
-- a number in the documentation that never touched the weights. sklearn takes
a **list** of grids for exactly this case: `l1_ratio` now varies only under
`penalty='elasticnet'`. Same 30 candidates, none invalid.
`test_l1_ratio_is_only_searched_where_it_does_something` asserts on the
expanded `ParameterGrid` rather than the shape of the grid, so it survives the
space being expressed differently.

Fixing it exposed a second one directly above. The choice between exhaustive
and randomized search was `len(param_grid) > 3` -- the number of *keys* --
which measured the wrong thing in both directions: a three-key grid of 54
combinations was searched exhaustively while a six-key grid of 40 was sampled,
and callers asking for `use_randomized=True, n_iter=2` got all 54 fits anyway.
It counts candidates through `ParameterGrid` now and samples only when there is
more to search than the budget allows. That is also why the nine
`UndefinedMetricWarning`s went with it: those tests ask for two samples and
now get two.

**Pydantic.** Four models in `src/storage/models.py` used the class-based
`class Config`, deprecated since 2.0 and removed in 3.0, which warned on every
import of the module; they use `ConfigDict` now. Two tests called `.dict()`
instead of `.model_dump()`.

**The one remaining skip is honest.** `test_the_detail_view_does_not_truncate_the_requirements`
guards against a list view capping `required_skills` at 10 while the detail
view shows fewer. No job in the corpus has 10 -- the maximum is 9, and the
distribution is 5:169, 6:179, 7:137, 8:160, 9:155 -- so the condition it
protects against cannot arise, and it skips rather than passing vacuously.

**Slide transitions, 16 Aug 2026.** They were driven by an
IntersectionObserver reporting `intersectionRatio` into a `--enter` custom
property, with a 600ms CSS transition smoothing the steps between its 21
thresholds. Both halves were wrong, and the second one was a real defect rather
than a matter of feel.

**The transition fought the scroll.** A transition interpolates towards a
target over its own duration; this target moved on every frame of a scroll, so
each new value restarted the interpolation part-way and the content trailed the
scroll by up to 600ms. Transitions are for values that change at discrete
moments. A scroll position is not one. `--enter` is now recomputed from the
scroll position itself, one measurement per frame, and the CSS transition is
gone -- a value that is already continuous does not want smoothing, it wants to
be applied.

**And the ratio could not reach 1 on a slide taller than the viewport.**
`intersectionRatio` is the fraction of the *slide* inside the container, so its
ceiling is `containerHeight / slideHeight`. Measured at a 1440x700 window: the
map slide is 898px in a 620px container, capping the ratio at **0.690** -- so
`opacity: 0.35 + ratio * 0.65` held it at **0.799 at every scroll position**,
permanently, with no scroll position able to improve it. Any laptop-height
window saw a dimmed slide 3. The new measure is distance from the centre of the
view with a plateau: anything within a quarter of a viewport of centre is fully
present, which also covers a slide coming to rest slightly off under proximity
snapping. Verified at that window: 1.000 at all three of top-aligned,
mid-scroll and scrolled-to-read-the-bottom.

Two smaller things went with it. The `scale()` was dropped -- scaling live text
by a fraction re-rasterises glyphs at a non-integer size every frame, which
reads as a shimmer on the headings it is presenting. And the effect moved from
`.landing-slide > *` to the content column alone, so the ornaments and the
particle canvas stay put; a background that slides with the foreground is not
parallax, it is everything moving.

**Backlog swept.** Fourteen `☐` headings across Phases 1, 3, 4 and 6
described work whose own status rows already recorded a commit -- the tables had
been kept current and the detail headings had not, so the file listed as open a
dozen things it also recorded as done. Each was checked against the code today
rather than taken from its table, and closed with what was found. Three remain
genuinely open: **3.4** and **3.5**, both measured as not worth doing alone, and
**6.2 Deploy**, parked by decision.

### Left for later

**Phase 5 has no remaining items.** What follows is adjacent work that was
considered and deliberately not done here.

- **Per-stage pipeline progress over SSE** — a real feature, not a timer.
- **Backend `black` sweep** — still `continue-on-error` in CI; 28 of 30 files
  reformat, and that diff should land alone (6.3).
- **Frontend tests** — there are none. The backend has 514; the interface has
  a type checker, a linter and a build. Playwright over the three journeys
  (upload → results, search → detail → single match, history → shortlist)
  would be the highest-value addition, and it is Phase 6 work.

### ☑ 5.9 — the `/match` payload names three scores misleadingly

**Closed `4ab29d7`.** `api.py:805-810` returns `rule_based_score`, `skill_score`, `experience_score` and `ml_score`, named for what they measure, and the comment above them records what they used to be called. The frontend was renamed in the same commit, which is what made it a Phase 5 item rather than a Phase 4 one.

Found during the backlog audit. `api.py:599-601` returns:

| Field | What it actually is |
|---|---|
| `parser_score` | the **rule-based total** — nothing to do with Agent 1, the parser |
| `matcher_score` | the **skill score** |
| `scorer_score` | **experience only** |

A reader of the API would draw the wrong conclusion from all three, and the
names suggest a per-agent breakdown that does not exist. `/match/single`
already returns honest names (`skill_match`, `title_match`, …) — this endpoint
should match it.

The frontend reads these keys, which is why it belongs here rather than in
Phase 4: renaming them is a coordinated change across both sides.

### ☑ 5.1 — A9

**Closed by a different decision.** The landing page is now the one page that deliberately does *not* toast on failure: it renders without figures and the copy still reads. A dead API is not a visitor's problem, and an error toast on the first thing someone sees is worse than a page that is quietly missing four numbers. The other five pages toast, as they did.
**✔ Verified** at `frontend/app/page.tsx:117`. Five of six pages wire `toast.error`
correctly — `upload`, `shortlist`, `results`, `history`, `jobs`. The gap is exactly one
file, and it is the landing page: on failure the spinner resets to idle and **nothing else
happens**. It is also the slowest call in the app, so it is the one most likely to fail.
Add a toast distinguishing timeout / 503 no-jobs / 500, matching the pattern the other five
already use.

### ☑ 5.1b — N6 · Hydration mismatch on the landing page

**Closed — the file no longer exists in that form.** The landing page was rebuilt as four slides. The only `Math.random()` left in the frontend is inside the particle field's `resize()`, which runs in an effect and never renders, and no `new Date()` is called during render anywhere.
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

### ☑ 5.2 — A10

**Closed.** `ACCEPTED_EXTENSIONS`, `MAX_FILE_BYTES` and `describeRejection()` live in `cv-dropzone.tsx` and are the single definition of what the app accepts. No `file.type === 'application/pdf'` check survives anywhere, and every rejection is reported by name.
`handleDrop` checks `file.type === 'application/pdf'` and **silently discards** DOCX and TXT
— both of which the backend supports. `handleFileInput` has no check at all. One shared
`acceptFile()` validating `.pdf/.docx/.txt` plus size, with a toast on reject.

### ☑ 5.3 — B7

**Closed.** `api.py:496-501` takes `search`, `category`, `remote_type` and `seniority`, with `/jobs/facets` serving the option lists from the corpus so the filters cannot drift from it.
`frontend/lib/api.ts` sends a `search` param. `api.py:180` `get_jobs()` accepts only `skip`
and `limit`. The search box slices the same page every time — very visible in a demo.
Implement server-side (case-insensitive over title / company / skills) and add `remote_type`
and `seniority_level` filters while in there.

### ☑ 5.4 — B8

**Closed.** The three timeouts are gone; the only `setTimeout` left in `processing-pipeline.tsx` is in the comment recording that they were there. `/match` returns a measured `processing_time` and `jobs_evaluated`, and the UI states both.
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

### ☑ 5.5 — B9

**Closed.** One key, `recruiter-pro.session.v1`, behind `useSyncExternalStore` in `lib/store.ts`. Writes are wrapped, so a full quota costs persistence rather than throwing inside an effect. The five old key names survive only in that file's comment.
Match results are `JSON.stringify`'d into `localStorage` on every change; full result sets
with explanations will exceed the ~5 MB quota and throw `QuotaExceededError`, uncaught,
inside a `useEffect`. Five-plus keys (`matchResults`, `latestAnalysis`, `selectedFileName`,
`shortlist`, `candidateStatus`) are cleared by hand in `history/page.tsx`. One React Context
or Zustand store as the source of truth; persist a small summary only; wrap writes in
try/catch; centralize clearing.

### ☑ 5.6 — B10

**Closed `4ab29d7`.** No `: any` remains in `frontend/app`, `frontend/components` or `frontend/lib`. The duplicated aliases went with it — `job_payload()` emits one name per concept.
`useState<any[]>` for match results and `catch (error: any)` across six files, while
`lib/types.ts` already has a perfectly good `Match` interface. Every `Match`/`Job` also
carries duplicated legacy fields (`company` *and* `company_name`, `location` *and*
`location_city`) — the API builds both and every component does `match.company_name ||
match.company`. Pick one shape; deleting the aliases removes ~40 lines from `api.py`.

### ☑ 5.7 — B11

**Closed.** `components/ui/feedback.tsx` provides `CardSkeletonGrid`, `EmptyState` and `ErrorState`, and every fetching page uses all three.
Pages fetch in `useEffect` with no skeleton and no empty state: during load a visitor sees a
bare layout, and with no data, nothing at all. Tailwind `animate-pulse` skeleton cards plus
a real empty state. Half a day, and it is the difference between "student project" and
"product". Add `aria-live` on score values while here.

### ☑ 5.8 — ⑤

**Closed.** `recharts`, `class-variance-authority` and `react-dropzone` are all out of `package.json` — the dropzone is hand-written. `src/storage/cache.py` is deleted along with the two config keys that advertised it. One history endpoint remains, `/match/history`.
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
| Zero console errors on every page at runtime | ✅ **done** — N6 closed with the landing rebuild |
| `pytest` green | ✅ **514 passed, 0 failed** (was 29 failed / 2 errors / 165 passed) |
| CI enforces it | ✅ **GitHub Actions on push and PR** |
| `ruff check src/ scripts/ tests/` | ✅ **clean, blocking in CI** |
| `black --check src/` | ❌ 28 of 30 files — non-blocking until a format commit lands |
| `eslint .` | ☑ clean — `eslint.config.mjs` added 12 Aug 2026, blocking in CI |
| App starts from a clean clone | ✅ **requirements split + repaired**; `run_api.py` fixed on Windows |
| App serves matches | ✅ **`/match` returns 5 real matches in 14.6s**, `scoring_mode: hybrid` |
| ML scoring runs | ✅ **model shipped** — `load_model() -> True`, hybrid scoring live |

| # | ID | Task | Score | Status |
|---|---|---|---|---|
| 6.7 | — | Run `pytest`; fix or quarantine failures; record the real number | **32** | ☑ `2f668f1` — **344 passed, 0 failed** |
| 6.1 | B12 | GitHub Actions: pytest + ruff + black + `next build` | **28** | ☑ `a98b68c` |
| 6.3 | ⑥ | `black`, `ruff`, `mypy` on `src/` — wired into CI, not just installed | **20** | ◐ ruff and eslint blocking and clean; black non-blocking pending a format commit; mypy not started |
| 6.6 | ⑤ | Delete committed test output and the orphan `tfidf_vectorizer.pkl` | **10** | ☑ `e2733c3` |
| 6.0 | N6 | Zero runtime console errors — fix the hydration mismatch | **35** | ☑ closed with the landing rebuild — see 5.1b |
| 6.5 | B13 | README: honest scope, "what I fixed" | **15** | ☑ `715543a` |
| — | — | *parked:* Docker, Vercel/Render deploy, hero GIF, live link | — | *deferred* |

### ☑ The suite is green — 344 passed, 0 failed (`2f668f1`)

It has never been green before. It began this session at **29 failed / 2 errors
/ 165 passed**, and that count was carried as "31 known failures" throughout.

**23 tests deleted for testing an API that has never existed.** `/api/v1/health`,
`/api/v1/score`, `/api/v1/batch` — all 404, on every run, since they were
written. Replaced by `test_api_contract.py`, 19 tests against the real surface.

**Writing those found two endpoints returning 500 on every call ever made to
them.** `/match/single` read `match.timestamp` (the model has `created_at`);
`/history` called `db.get_all_matches()`, which does not exist, then read four
more fields absent from `MatchHistory`. The 19 dead tests were not merely
useless — they occupied the place where these would have been caught.

**A further 10 tests passed while measuring nothing.** `test_load_testing.py`
collected every timing inside `if response.status_code == 200:` against
`/api/v1/*`. Nothing was ever 200, so the lists stayed empty and every
assertion sat behind `if response_times:`. Replaced with 4 that assert
unconditionally and guard the Phase 3 result.

**The SMOTE flake was an unseeded fixture**, not a SMOTE bug: `np.random.*` with
no seed gave a different class balance each run, and `sampling_strategy=0.7`
raises when the data is already more balanced than that.

### ☑ CI (`a98b68c`)

Backend: ruff (blocking, clean), black (non-blocking), pytest + coverage, the
corpus validator, and a byte-level control-character scan. Frontend: `tsc
--noEmit`, `eslint .`, `next build`.

**Running the suite under CI's exact environment found three tests coupled to
this machine** and, more seriously, **a lost-write bug**: lazy schema creation
checked a flag with no lock, so concurrent first-writers raced and the losers'
writes were dropped — the LLM budget recorded 11 of 20 increments, meaning the
instance would overspend its quota. Fixed with an init lock and
`busy_timeout=5000`.

> ⚠ **Only `black` is `continue-on-error`, and on purpose.** black would
> reformat 28 of 30 files, which belongs in its own commit rather than being
> forced through on unrelated work. The frontend lint step is blocking as of
> 12 Aug 2026.
> Marking it non-blocking is honest — leaving it out would hide that it fails.
> It becomes blocking when that commit lands.

### ☑ 6.7 — N12 · A quarter of the test suite fails

**Closed `2f668f1`, and it has stayed closed.** 514 passed, 1 skipped, 2 warnings as of 16 Aug 2026 — from 29 failed / 10 errors / 109 passed. The last of the environment coupling this entry describes went on 15 Aug: the suite had still been writing to the application's own database, and inheriting the developer's `.env` for rate limiting.
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

**Tests write into the repo.** Running the suite created
`models/experiments/validation_curve_TestModel_C.png`. This is not new — the already-tracked
`models/experiments/learning_curve_TestModel.png` is the same artifact from an earlier run,
committed by accident. Point `CrossValidationEvaluator`'s `output_dir` at `tmp_path` in
tests, and delete the committed one as part of 6.6.

**Until this is green, 6.1 (CI) has nothing meaningful to enforce and "builds clean" is
only true of the frontend.**

### ☑ 6.8 — One launcher, and a byte check that would have caught it (`f4b1eba`)

`Run.ps1` opened three detached terminals and exited. `run.ps1` replaces it:
both services in one window, `[api]` / `[web]` prefixed logs, Ctrl-C stops
both. Flags: `-Prod`, `-ApiPort`, `-WebPort`, `-Force`, `-NoBrowser`.

The rewrite was not cosmetic. On a busy port the old script ran

```powershell
Get-Process | Where-Object { $_.ProcessName -match "uvicorn|python" } | Stop-Process -Force
```

and the same for `node`. That matches on process *name*, so freeing one port
killed every Python and Node process on the machine — language servers, other
projects' dev servers, notebooks. The replacement resolves the PID actually
listening on that port and touches nothing else, and only under `-Force`.

Two more went with it:

- The port probe used `BeginConnect` + `WaitOne`, whose handle signals on a
  refused connection exactly as on a successful one, so free ports often read
  as busy.
- "Launched" was printed when the windows opened, so a backend that died on
  startup looked identical to one that came up. It now waits on `/health` and
  reports the corpus size and whether hybrid scoring is running.

`-ApiPort` / `-WebPort` propagate to both `CORS_ORIGINS` and
`NEXT_PUBLIC_API_URL`. Without that a non-default port starts cleanly and then
fails every browser request with a CORS error naming neither cause nor cure.

**Verified:** default ports; alternate ports 8010/3010 with a real OPTIONS
preflight returning `access-control-allow-origin: http://localhost:3010`; and
the failure path — killing the API mid-run has the watchdog stop the frontend
and release both ports.

`frontend/AGENTS.md` and `CLAUDE.md` are now tracked, because `next dev`
rewrites them on every run and the launcher would otherwise dirty the tree
each time it is used.

**And the check that should have caught the bug this introduced.** Writing the
README section for it put a raw `0x0D` into `.
un.ps1`, which renders as
`.un.ps1` — a copy-pasteable command that cannot work. That is the third
control-character incident in this repository, and
`scripts/check_control_chars.py` missed it three separate ways: it scanned only
`*.py`, only under `src/tests/scripts`, and allowed `0x0D` unconditionally
because CRLF is normal on Windows. It now covers TypeScript, Markdown and
PowerShell, walks the frontend and the repo root, and rejects a **bare** CR
while still allowing CRLF. 127 files scanned, and a regression test confirms it
catches exactly this byte.

### ☑ 6.9 — LLM provider configured, and no longer invisible

**Closed 14 Aug 2026.** Both halves: a provider is configured, and the UI now
states which one actually answered.

Before, there was no `.env` at all, so config fell through to
`config/agents.yaml`: `LLM_PROVIDER=ollama` against a `localhost:11500` that
was not running. The app reported `ollama_enabled: true` at `/health` and on
startup, then fell back to rule-based at call time. Explanations were
produced — simply not LLM-written, with nothing saying so.

Now `.env` sets `LLM_PROVIDER=openrouter` with a key verified live via
`scripts/check_llm_key.py`, and `/match` returns `explanation_source` beside
every explanation.

Two things to decide, neither blocking:

1. **Pick a provider.** Either start Ollama locally, or set
   `LLM_PROVIDER=openrouter` with `OPENROUTER_API_KEY` in `.env`. The key is
   read from the environment only, by `src/agents/explaining/openrouter.py`;
   it is never logged and never returned in a response.

   **The model is now chosen.** The workload is narrower than "pick a good
   LLM" suggests: `prompt.py` sends ~300 tokens of already-structured facts
   and asks for under 200 words at temperature 0.2, three times per upload
   (`MAX_EXPLANATIONS`). No reasoning, no tools, no images, no long context —
   instruction-following, fluency and speed, because the call blocks the UI.
   Ranked by round-trip time for ~280 output tokens across the free tier:

   | Model | Latency | tps | ~280 tok |
   |---|---|---|---|
   | `nvidia/nemotron-3-nano-30b-a3b:free` | 0.66s | 88 | **~3.9s** |
   | `nvidia/nemotron-3-super-120b-a12b:free` | 0.94s | 46 | ~7.0s |
   | `google/gemma-4-26b-a4b-it:free` | 0.96s | 38 | ~8.3s |
   | `google/gemma-4-31b-it:free` | 1.18s | 28 | ~11.2s |
   | `openai/gpt-oss-20b:free` *(was the default)* | 3.98s | 17 | ~20.5s |
   | `nvidia/nemotron-3-ultra-550b-a55b:free` | 7.28s | 15 | ~26.0s |

   `DEFAULT_MODEL` is now `nemotron-3-nano-30b-a3b`. The old default was the
   slowest practical option on the list and is most of why the docs quoted
   30–60s per CV with explanations on. Its 96.77% uptime is the lowest of the
   set and matters least here — an unreachable provider fails `is_available()`
   and falls through to rule-based, so downtime costs prose quality, not
   availability. Fall back to `gemma-4-31b-it` if the writing disappoints;
   avoid the reasoning/omni variants (a 16k hidden thinking budget spent on a
   200-word summary) and `nemotron-3.5-content-safety`, which is a guardrail
   classifier that returns safe/unsafe labels rather than prose.
2. **☑ The provider that answered is now surfaced.** `/match` reports
   `explanation_source` — `openrouter`, `ollama` or `rule_based` — and the
   match card renders it as a chip. The pipeline had recorded it since ADR-2;
   nothing served it. Shipped with the 5.6 API cleanup in `4ab29d7`, as
   predicted.

   Its value showed immediately: with a live key configured, the sandbox used
   for development still returns `rule_based`, because it cannot open a TLS
   connection to OpenRouter. Without the field that is invisible — the prose
   is equally fluent either way.

   `/match/history` returns null rather than guessing: `MatchHistory` has no
   column for the provider. Adding one is a schema migration, and the honest
   null is better than an invented answer. Worth doing when the schema is next
   touched.

### ☑ 6.1 — CI is the highest-signal cheap win in this phase

**Closed `a98b68c`.** `.github/workflows/ci.yml`: ruff, pytest with coverage, the corpus validator, the control-character and secret scanners, and `tsc` / `eslint` / `next build` for the frontend.
There is no `.github/workflows/`. There are 15 test files that **nobody browsing the repo can
tell exist**. A green CI badge on a repo with real tests is one of the highest-signal things
on a portfolio, and it is an afternoon of work.

### ☑ 6.5 — README

**Closed `715543a`.** The two sections that carry the weight are there: **Scope and known limitations** at line 124, leading with the leakage finding, and the record of what was fixed and why.
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
| **Phase 2 execution + re-audit, 10–12 Aug 2026** | **Three defects found by reading, none previously in this file:** substring skill matching credited JavaScript for Java (29 collisions among 669 names) · punctuation stripped before vocabulary lookup left 6 canonical skills unfindable by their own name · `title_score` weighted at 17% then discarded, so the API's components could not reconstruct the total. **Two stale backlog entries corrected:** 3.2's synonym dict no longer exists, and **3.3 would have deleted the live corpus** — every one of its premises expired with the C.1–C.10 replacement. **Agent 3's prescribed five-way split superseded** after measuring that 209 of 544 LOC have no dependencies at all. Two self-inflicted bugs caught pre-commit and recorded in the commit bodies rather than quietly fixed (a `logger` call in a module with no `logging` import; a literal `0x08` byte inside Agent 2's tokenising regex, which the terminal rendered as correct text and which silently cut skill extraction from 15 to 1) |
| Data + GUI audit, 9 Aug 2026 | **Job corpus audit** (6,146 records, 2,146 discarded, 2.3% vocabulary coverage, 60.9% of jobs unmatched) · **GUI audit** all 6 pages + 6 components · **N8** two pages unreachable from nav · **N9** every page shares one tab title · **N10** UI advertises a 200 MB upload limit · **N11** four false statements in UI copy · **N12** 26% of the test suite fails, 19 tests target an API that never existed |

### ☑ N7 · `run_api.py` crashes on Windows before starting — **FIXED**
`branch: fix/repo-run-api-encoding`

`python run_api.py` dies immediately with
`UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f680'` — the emoji in the
`print()` at line 17 cannot be encoded by the `cp1252` default console codepage. Low severity
because it is **not** the documented entrypoint: the README (line 166) and `Run.ps1` both use
`uvicorn src.api:app`, which works. But it is a root-level file that crashes on the platform
this project's own tooling targets. Replace the emoji, or set `PYTHONIOENCODING=utf-8`.

`Plans/` is gitignored — the reports are working notes. This file is the tracked record.
