# Pass 3 — write the 800 job descriptions

**Run this in a new Claude Code session with `C:\Users\DELL\Desktop\Recruiter-Pro` as the
working directory.** Both input files are already staged in the repo.

Copy everything below the rule into that session.

---

You are completing pass 3 of a job-corpus build for **Recruiter-Pro**. Passes 1 and 2 are
done and verified; only the `description` field is missing.

## Input (already in this repo)

- `data/json/jobs.skeleton.json` — 800 records, every field except `description`
- `data/dictionaries/skills.json` — the controlled vocabulary those skills came from
- `JOBS_DATASET_SPEC.md` — the full spec. Read the "Description format" section.

## Output

`data/json/jobs.json` — the identical envelope and the identical 800 records, with
`description` added to each.

## Absolute rules

1. **Change nothing except `description`.** Every other field, and the top-level envelope,
   must survive byte-identical. The skeleton passed 16/19 validator checks — the only
   failures were the missing descriptions. Do not "improve" anything else. Do not reorder
   records or keys.
2. **Never restate the skills list.** The old corpus generated every description from one
   template with `required_skills` interpolated, which made keyword scoring circular — it
   measured the same skills twice. Skills may be *mentioned* naturally where they fit, but
   the description must carry information the skill arrays do not.
3. **Descriptions must differ from each other.** Two records with the same `title` at
   different companies must not share text. Vary the opening, the responsibilities and the
   emphasis.

## Format — exact

Plain text. Not Markdown, not HTML. Four sections, these exact headings, in this order,
separated by blank lines. Bullets use `• ` (U+2022 + space). **900–1,400 characters total.**

```
About the role
<2-3 sentences: what the team does and what this person owns. Specific to the
company, category and seniority - not a restatement of the title.>

Responsibilities
• <verb-first, concrete, 8-16 words>
• <4-6 bullets total>

Requirements
• <4-6 bullets: experience, qualifications, core competencies>

Nice to have
• <2-3 bullets>
```

Write to the record in front of you. A `maintenance` `entry` role at a facilities company
and an `engineering` `lead` role at a software company should read nothing alike — different
vocabulary, different concerns, different seniority of language. Use `category`,
`seniority_level`, `title`, `company_name`, `employment_type` and the experience range to
decide tone and content.

## How to work — batch and save as you go

Do **not** try to emit 800 descriptions in one response. Work in batches of 50 and write
each batch to disk before starting the next, so nothing is lost if the session ends.

1. Read `data/json/jobs.skeleton.json`.
2. Copy it to `data/json/jobs.json` once, at the start.
3. For each batch of 50 records: write the descriptions, then update those 50 records in
   `data/json/jobs.json` in place (load, patch by `job_id`, dump).
4. Report progress after each batch: `batch N/16 done — X of 800 have descriptions`.
5. Repeat until all 800 are filled.

Preserve UTF-8 (no BOM), 2-space indent, and LF line endings on every write.

## Verify before you finish

```bash
python scripts/validate_corpus.py --jobs data/json/jobs.json --skills data/dictionaries/skills.json
```

**All checks must pass.** The three that currently fail — description length, the four
headings, and `JobPosting` construction — exist precisely because descriptions were missing,
so they are the ones your work has to turn green. If anything *else* starts failing, you
changed a field you should not have; revert and redo that batch.

Also confirm before declaring done:

```bash
python -c "
import json
d=json.load(open('data/json/jobs.json',encoding='utf-8'))
js=d['jobs']
print('records            :', len(js))
print('with descriptions  :', sum(1 for j in js if (j.get('description') or '').strip()))
print('distinct texts     :', len({j['description'] for j in js}))
L=[len(j['description']) for j in js]
print('length min/max     :', min(L), max(L))
"
```

Expected: 800 records, 800 with descriptions, **800 distinct texts**, lengths within
900–1,400.

## If it becomes a slog

There is a documented fallback: write one description per **title** (145 unique) rather than
per record, shared across employers. It is roughly 18% of the work. The cost is that jobs
sharing a title score identically against a CV, which weakens the matching demo. Take it only
if the full run stalls, and say so explicitly if you do — it is a quality trade-off the
project owner should know was made.

---

# END OF PROMPT

## After it finishes, come back to the main session for:

- `load_jobs()` reading `payload["jobs"]` from the envelope (C.5)
- Deleting the `jobs = jobs[:4000]` cap (C.6)
- Pointing `config.skills_database_path` at the new vocabulary (C.7)
- The vocabulary-coverage test (C.8) and re-measurement (C.9)
- `whitespace-pre-line` on the frontend description element (C.10)
