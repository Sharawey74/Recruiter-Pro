# Jobs dataset — regeneration spec and prompt

The old corpus is archived at [`data/archive/jobs-legacy-2026-08-09/`](data/archive/jobs-legacy-2026-08-09/README.md)
with a note on why. This document is both the **spec** for the replacement and the **prompt**
to generate it.

---

## Answers to your questions, up front

| | |
|---|---|
| **File name** | `jobs.json` |
| **Full path** | `data/json/jobs.json` |
| **Format / extension** | JSON, `.json` — UTF-8 (no BOM), LF line endings, 2-space indent |
| **Companion file** | `data/dictionaries/skills.json` — the skill vocabulary, generated *with* the jobs |
| **Record count** | **800** — 100 per category |
| **Top-level shape** | Object with `metadata` + `jobs` array (not a bare array) |

**Why `jobs.json`.** Both old names are retired, so the canonical name is free. `load_jobs()`
already falls back to this exact path, and a version lives *inside* the file
(`schema_version`) rather than in the filename — so regenerating never means renaming.

**Why `.json` and not CSV, JSONL or YAML.** `load_jobs()` calls `json.load()`. Records are
nested (`required_skills` is a list), which CSV cannot hold without escaping. JSONL would
stream better, but nothing here streams — the whole corpus loads into memory at startup
anyway. Stay with what the code reads.

**Why 800 and not 6,146.** The old file had 6,146 records and `api.py:114` silently used only
the first 4,000. 800 balanced, high-quality records remove the need for that cap entirely,
fit the 512 MB deployment target, and demo exactly as well. Quality of match is set by
vocabulary coverage, not corpus size.

**Why a companion skills file — the most important decision here.** The old corpus used free
text scraped from a source that split on `|`: `"Ms sql"`, `"Ssrs"`, `"Digital Painting"`. The
vocabulary recognised **2.3%** of its 4,603 distinct skill strings, and **60.9% of jobs had
not one matchable skill**. Generating a new corpus with free-form skills would rebuild that
exact failure. So the vocabulary is generated *first*, and **every skill on every job must
come from it.**

---

## Before you generate

⚠️ **The app currently has no jobs.** `data/json/` no longer contains a corpus, so
`load_jobs()` returns `[]` and `POST /match` returns `503 No jobs loaded`. That is expected
until the new file lands.

Two code changes are needed once it does — both small, both tracked in `TASKS.md`:

1. `load_jobs()` reads a bare array. It must read `payload["jobs"]` from the envelope, and the
   legacy-shape branch (dead since the old `jobs.json` was retired) should go with it.
2. Remove the `jobs = jobs[:4000]` cap at `api.py:114` — with 800 records it is dead weight,
   and leaving it in means a future larger corpus gets silently truncated again.

---

# THE PROMPT

Copy everything between the rules into a fresh Claude session.

---

You are generating a synthetic but professionally realistic job-posting dataset for
**Recruiter-Pro**, a CV-to-job matching engine. The dataset is the corpus every uploaded CV is
scored against, so internal consistency matters more than volume or variety.

Produce **two files**. Generate file B first, because file A depends on it.

## File B — `data/dictionaries/skills.json` (generate this first)

The controlled skill vocabulary. Every skill that appears anywhere in the job corpus must
exist here.

**Structure** — metadata and skill families in **separate subtrees**:

```json
{
  "_meta": {
    "comment": "Controlled skill vocabulary. Maps aliases to canonical skill names.",
    "schema_version": "2.0"
  },
  "families": {
    "programming_languages": {
      "Python": ["python", "py", "python3"],
      "JavaScript": ["javascript", "js", "ecmascript"]
    },
    "sales_and_crm": {
      "Salesforce": ["salesforce", "sfdc"],
      "Pipeline Management": ["pipeline management", "pipeline mgmt"]
    }
  }
}
```

> **Why `_meta` / `families` and not metadata keys sitting beside the families.** The old
> `skills_canonical.json` mixed a string `comment` in among the category objects, so any
> loader iterating the top level had to guess which values were data. Guessing wrong is
> precisely what caused A0 — the worst bug in this project. A loader can iterate
> `raw["families"]` with no type-sniffing at all, and the `isinstance` guard becomes a
> belt-and-braces check rather than the thing holding the design together.

Rules:
1. `families` contains only objects of canonical→aliases. Nothing else lives there.
2. Canonical names are human-readable and correctly cased: `PostgreSQL`, not `postgresql`.
3. Aliases are all-lowercase, and include the canonical name lowercased, every common
   spelling, abbreviation and punctuation variant: `.NET` → `["dotnet", ".net", "dot net"]`.
4. **Cover all eight categories, not just engineering.** The old vocabulary was 105
   engineering-leaning skills and could not match a sales or maintenance job at all. Include
   families such as: `programming_languages`, `frameworks`, `databases`, `cloud_devops`,
   `data_and_ml`, `sales_and_crm`, `marketing_and_content`, `finance_and_accounting`,
   `erp_and_business_systems`, `project_management`, `office_and_administration`,
   `maintenance_and_trades`, `operations_and_supply_chain`, `quality_and_compliance`,
   `soft_skills`.
5. Target **400–600 canonical skills**, distributed so no category has fewer than 40.
6. Include the plain, common terms the old vocabulary missed: `sql`, `html`, `css`, `json`,
   `xml`, `oop`, `excel`, `data entry`, `scheduling`, `invoicing`, `preventive maintenance`.
7. No duplicate canonical names, and no alias mapped to two different canonicals.

## File A — `data/json/jobs.json`

### Top-level envelope

```json
{
  "schema_version": "2.0",
  "generated_at": "YYYY-MM-DD",
  "record_count": 800,
  "skill_vocabulary": "data/dictionaries/skills.json",
  "skill_vocabulary_version": "2.0",
  "categories": {
    "engineering": 100, "sales": 100, "marketing": 100, "accounting": 100,
    "management": 100, "administrators": 100, "maintenance": 100, "operations": 100
  },
  "jobs": [ /* 800 job objects */ ]
}
```

### Job object — exact field contract

Field names and types must match exactly.

> **Do not rely on the loader to catch mistakes.** An earlier draft of this spec claimed
> "a mismatch raises at load". It does not. `JobPosting` sets no `extra` policy and Pydantic
> v2 defaults to `extra='ignore'`, so **unknown keys are silently dropped** — verified by
> constructing a record with `category` and finding `hasattr(job, 'category') == False`.
> Missing *required* fields do raise, so validation was only half-real, and the half being
> relied on for the new `category` field was the half that did not exist.
>
> Fixed in `src/storage/models.py`: `category` is now a declared field with a validator that
> rejects any value outside the eight. Correctness of everything else is enforced by
> `scripts/validate_corpus.py`, not by the model.

| Field | Type | Required | Rules |
|---|---|---|---|
| `job_id` | string | ✅ | `<PREFIX>-<4 digits>`, zero-padded, unique. Prefixes: `ENG`, `SAL`, `MKT`, `ACC`, `MGT`, `ADM`, `MNT`, `OPS`. e.g. `ENG-0001` |
| `category` | string | ✅ | Exactly one of the eight. Lowercase. **New field** |
| `title` | string | ✅ | A real position title. Title Case. No seniority prefix unless the role genuinely carries one |
| `company_name` | string | ✅ | Invented but plausible. Reuse ~60 companies across the corpus so repeat employers look natural |
| `location_city` | string | ✅ | Real city |
| `location_country` | string | ✅ | Real country, must match the city |
| `remote_type` | string | ✅ | `on-site` \| `hybrid` \| `remote` — **must be plausible for the category** (see below) |
| `employment_type` | string | ✅ | `full-time` \| `part-time` \| `contract` \| `internship` |
| `seniority_level` | string | ✅ | `entry` \| `mid` \| `senior` \| `lead` \| `manager` \| `executive` |
| `min_experience_years` | number | ✅ | Must fit the seniority band below |
| `max_experience_years` | number | ✅ | `> min`, and within the same band |
| `description` | string | ✅ | Structured plain text — format below |
| `required_skills` | string[] | ✅ | **5–9 canonical names from File B**, exact spelling |
| `preferred_skills` | string[] | ✅ | **2–5 canonical names from File B**, no overlap with required |
| `posted_date` | string | ✅ | `YYYY-MM-DD`, within the 90 days before `generated_at` |
| `education_level` | string | ✅ | `High School` \| `Diploma` \| `Associate` \| `Bachelor's` \| `Master's` \| `PhD` |
| `salary_range` | string | ✅ | `"45000-65000 USD"` — plausible for role, seniority and country |
| `is_active` | boolean | ✅ | `true` for all |

Do **not** emit `company`, `location`, `job_type`, or `created_at`. Those are deprecated
aliases the API generates itself.

### The eight categories, and the roles in each

`category` is the **business function**, never the rank. Seniority lives in
`seniority_level`. An Engineering Manager is `engineering` + `manager`, not `management`.

| Category | What it means | Example titles (use these and similar; vary, do not just cycle) |
|---|---|---|
| `engineering` | Builds/maintains technical products and infrastructure | Software Engineer · Backend Engineer · Frontend Engineer · Full Stack Engineer · Mobile Engineer · DevOps Engineer · Site Reliability Engineer · Data Engineer · Machine Learning Engineer · QA Engineer · Security Engineer · Cloud Engineer · Systems Engineer · Embedded Engineer · Solutions Architect · Engineering Manager |
| `sales` | Revenue generation, direct customer acquisition | Sales Development Representative · Account Executive · Account Manager · Key Account Manager · Sales Engineer · Inside Sales Representative · Business Development Manager · Channel Partner Manager · Sales Operations Analyst · Retail Sales Associate · Sales Director |
| `marketing` | Demand generation, brand, communications | Digital Marketing Specialist · Content Marketing Manager · SEO Specialist · PPC / SEM Specialist · Social Media Manager · Brand Manager · Product Marketing Manager · Marketing Analyst · Email Marketing Specialist · Communications Manager · Growth Marketer |
| `accounting` | Financial recording, reporting, compliance | Accountant · Staff Accountant · Senior Accountant · Accounts Payable Clerk · Accounts Receivable Specialist · Payroll Specialist · Financial Analyst · Cost Accountant · Internal Auditor · Tax Accountant · Financial Controller · Finance Manager · Bookkeeper |
| `management` | Cross-functional business leadership and project/product management **only** | General Manager · Business Unit Director · Project Manager · Program Manager · Product Manager · Chief of Staff · Country Manager · Regional Manager · Strategy Manager · Branch Manager |
| `administrators` | **Office and business administration — NOT system administration** | Administrative Assistant · Executive Assistant · Office Manager · Receptionist · Data Entry Clerk · HR Administrator · Records Officer · Document Controller · Front Desk Coordinator · Personal Assistant · Scheduling Coordinator |
| `maintenance` | Physical upkeep of equipment, facilities, plant | Maintenance Technician · Electrical Technician · Mechanical Technician · HVAC Technician · Facilities Technician · Industrial Electrician · Plumber · Millwright · Maintenance Planner · Equipment Technician · Maintenance Supervisor |
| `operations` | Running the physical/process business — supply chain, logistics, production | Operations Coordinator · Operations Analyst · Supply Chain Analyst · Logistics Coordinator · Warehouse Supervisor · Inventory Controller · Procurement Officer · Production Planner · Quality Control Inspector · Shift Supervisor · Distribution Manager |

⚠️ **`administrators` means office administration.** A Systems Administrator, Database
Administrator or Network Administrator is `engineering`. This is the single easiest mistake to
make here.

### Consistency rules — these are what make the dataset professional

**1. Seniority ↔ experience must agree.**

| `seniority_level` | `min_experience_years` | `max_experience_years` |
|---|---|---|
| `entry` | 0–1 | 2–3 |
| `mid` | 2–4 | 5–7 |
| `senior` | 5–8 | 9–12 |
| `lead` | 8–10 | 12–15 |
| `manager` | 8–12 | 15–18 |
| `executive` | 12–18 | 20–25 |

**2. `remote_type` must be physically possible.**

| Category | Allowed |
|---|---|
| `maintenance` | `on-site` **only** — you cannot fix an HVAC unit remotely |
| `operations` | `on-site` mostly; `hybrid` only for analyst/planner desk roles |
| `administrators` | `on-site` or `hybrid`; `remote` only for data entry and scheduling |
| `engineering`, `marketing`, `sales`, `accounting`, `management` | any of the three |

Overall mix across the corpus: roughly 45% on-site, 30% hybrid, 25% remote.

**3. `education_level` must suit the role.** Trades and entry admin → `High School` or
`Diploma`. Accounting, engineering, marketing → `Bachelor's` typically. `Master's` only for
senior/executive or specialist roles. `PhD` rare (under 1%), and only for research-flavoured
engineering or data roles.

**4. Every skill must exist in File B, spelled as its canonical name.** Not an alias, not a
variant. This is the hard invariant of the whole dataset.

**5. Skills must belong to the category.** A Maintenance Technician does not require
`Kubernetes`. An Accountant does not require `React`. Cross-category skills are fine where
genuinely shared — `Excel`, `Communication`, `Project Management`, `SAP`.

**6. No duplicate `(title, company_name)` pairs** anywhere in the corpus. The old one had 486.

**7. Distribution targets per category:** seniority roughly 15% entry, 35% mid, 25% senior,
10% lead, 12% manager, 3% executive. Employment type roughly 85% full-time, 7% contract, 5%
part-time, 3% internship — with internships only at `entry`.

### Description format — exact

Structured **plain text**, not Markdown, not HTML. Four sections, these exact headings, in
this order, separated by blank lines. Bullets use `• ` (U+2022 + space). **900–1,400
characters total.**

```
About the role
<2–3 sentences: what the team does, what this person owns. Company- and
context-specific — not a restatement of the title.>

Responsibilities
• <verb-first, concrete, 8–16 words>
• <4–6 bullets total>

Requirements
• <4–6 bullets — experience, qualifications, core competencies>

Nice to have
• <2–3 bullets>
```

Critical rule: **the description must never be a template with the skills list pasted into
it.** The old corpus generated every description from one sentence pattern with
`required_skills` interpolated, which made keyword scoring against the description
circular — it measured the skill list twice. Write genuine prose per role. Skills may be
*mentioned* naturally where relevant, but the description must carry information the skill
arrays do not.

### Output

Return complete, valid JSON — UTF-8, 2-space indent, LF line endings, no trailing commas, no
placeholder or `...` values.

**Generate in three passes, in this order. Do not emit descriptions before pass 3.**

Rules 6 and 7 are corpus-*wide*: no duplicate `(title, company_name)` anywhere, ~60 companies
reused naturally, a 45/30/25 remote mix, a 15/35/25/10/12/3 seniority split. Emitting eight
independent batches of 100 cannot satisfy those — batch 7 cannot check a pair against 600
records written earlier, and eight independent samples do not land on a global percentage.
Splitting the work by *stage* rather than by *category* fixes that, and costs far less,
because the invariants get locked in the cheap pass before any prose is written.

**Pass 1 — names.** Emit ~60 company names and ~130 job titles mapped to categories. One
small response.

**Pass 2 — skeleton.** Emit all 800 records with every field *except* `description`:
`job_id`, `category`, `title`, `company_name`, `location_city`, `location_country`,
`remote_type`, `employment_type`, `seniority_level`, `min_experience_years`,
`max_experience_years`, `required_skills`, `preferred_skills`, `posted_date`,
`education_level`, `salary_range`, `is_active`. Compact enough for one or two responses, and
**every global invariant is verifiable here**, mechanically, before any prose exists. Run
`python scripts/validate_corpus.py` at this point — description checks will fail, everything
else must pass.

**Pass 3 — prose.** Fill in `description` in batches, taking the finished skeleton row as
input. Cross-batch consistency no longer matters, because nothing global depends on the
descriptions.

### Self-check before returning

A model confirming its own output is not verification. **`scripts/validate_corpus.py` turns
every item below into an assertion** — run it, and treat its exit code as the answer:

```bash
python scripts/validate_corpus.py
```

The list is kept here so the generator knows what it is aiming at:

1. Exactly 800 jobs, exactly 100 per category.
2. Every `job_id` unique and matching its category prefix.
3. Every `required_skills` and `preferred_skills` entry appears as a canonical name in File B.
4. No job has a skill from an implausible category.
5. Every `min_experience_years` / `max_experience_years` pair fits its seniority band.
6. No `maintenance` job is `hybrid` or `remote`.
7. No duplicate `(title, company_name)` pair.
8. Every description is 900–1,400 characters with all four headings in order.
9. Every `posted_date` falls within 90 days before `generated_at`.
10. No `company`, `location`, `job_type` or `created_at` keys anywhere.

---

# END OF PROMPT

---

## After the files land

1. Drop them at `data/json/jobs.json` and `data/dictionaries/skills.json`.
2. Update `load_jobs()` to read `payload["jobs"]`; delete the legacy-shape branch.
3. Delete the `jobs = jobs[:4000]` cap (`api.py:114`).
4. Point `config.skills_database_path` at the new vocabulary if the name changed.
5. **Add the invariant as a test** — this is the guard the old corpus never had:

```python
def test_every_job_skill_is_in_the_vocabulary():
    vocab = {c.lower() for c in canonical_names(load_skills())}
    unknown = {s for job in load_jobs() for s in job.required_skills
               if s.lower() not in vocab}
    assert not unknown, f"{len(unknown)} skills absent from vocabulary: {sorted(unknown)[:10]}"
```

6. Re-measure coverage. The old corpus scored 2.3% of distinct skills and 21.2% of mentions,
   with 60.9% of jobs unmatchable. **This design should give 100% by construction** — if it
   does not, the generation did not honour rule 4, and that is worth catching immediately.
7. Frontend: `description` now carries newlines. Add `whitespace-pre-line` to the description
   element in `jobs/page.tsx` or the sections render as one run-on paragraph.
8. **Expect education scores to move for every job at once.** `_score_education` already
   reads `job.education_level`, and it is `None` on all 6,146 archived records — verified —
   so `job_level` has always fallen through to the default of `3` (Associate) universally.
   Populating real values makes that scorer meaningful for the first time, which is a genuine
   improvement this spec unlocks. But it is a scoring change with no code change to point at,
   so note it in the PR's "scoring impact" section and pin two known CV/job pairs in a test.
9. **Keyword scoring is now weak by design, and that is a choice worth making knowingly.**
   Rule: descriptions must not restate the skills list — correct, because it removes the
   circularity where `_score_keywords` measured the same skills twice. The consequence is
   that keyword scoring matches CV text against 20 words of ordinary prose. At 5% weight it
   distorts little, but if you want it to mean something, rank keywords by rarity rather than
   raw frequency and let genuine domain terms surface naturally in the prose.
