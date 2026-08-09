# Contributing to Recruiter-Pro

This is a solo portfolio repository, but it is worked on as if it were not. Every change
flows through a branch and a pull request, so the PR list reads as a narrative of how the
project was built and refactored.

The conventions below are deliberately proportional: trunk-based development with
short-lived branches and Conventional Commits. There is no `develop` branch, no
`release/*`, no `hotfix/*`. That ceremony exists to coordinate versioned releases across
multiple teams, and adding it here would be exactly the kind of over-engineering this
refactor is meant to avoid.

---

## 1. Branching model

`main` is always green and always deployable. Nothing is committed directly to `main`.

```
main
  ├── feat/<scope>-<slug>       feat/agent3-alias-index
  ├── fix/<scope>-<slug>        fix/agent3-skill-category-collapse
  ├── perf/<scope>-<slug>       perf/pipeline-batch-persistence
  ├── refactor/<scope>-<slug>   refactor/agent4-provider-abstraction
  ├── test/<scope>-<slug>       test/agent3-normalization-regression
  ├── chore/<slug>              chore/remove-dead-utils
  ├── docs/<slug>               docs/adr-llm-allocation
  └── ci/<slug>                 ci/pytest-and-lint-workflow
```

### Rules

| Rule | Detail |
|---|---|
| Format | `<type>/<scope>-<slug>`, or `<type>/<slug>` for `chore`, `docs`, `ci` |
| Characters | lowercase `a–z`, digits, and `-` only. No `_`, no `/` beyond the first, no uppercase |
| Length | keep the whole name under 50 characters |
| Lifetime | short-lived — open, merge, delete. A branch older than a few days should be split |
| Scope | one backlog item per branch. If a PR needs two summary lines, it is two PRs |
| Base | always branch from an up-to-date `main` |

### Types

| Type | Use for | Example |
|---|---|---|
| `feat` | new user-visible capability | `feat/api-jobs-search-filter` |
| `fix` | a defect in existing behaviour | `fix/api-cors-wildcard-credentials` |
| `perf` | same behaviour, measurably faster | `perf/agent3-vectorized-ml-scoring` |
| `refactor` | internal restructuring, no behaviour change | `refactor/agent1-remove-init-side-effects` |
| `test` | tests added or restructured with no production change | `test/pipeline-topk-persistence` |
| `chore` | dependencies, cleanup, tooling, repo hygiene | `chore/split-requirements-files` |
| `docs` | documentation, ADRs, README | `docs/known-limitations-leakage` |
| `ci` | workflow and pipeline configuration | `ci/add-github-actions` |

### Scopes

Use the part of the system the change lives in. The current set:

`agent1` · `agent2` · `agent3` · `agent4` · `pipeline` · `api` · `ml` · `storage` ·
`config` · `frontend` · `data` · `deps` · `repo`

Add a scope when a genuinely new area appears; do not invent one per file.

---

## 2. Commit format

[Conventional Commits](https://www.conventionalcommits.org/). This keeps history readable
and makes an auto-generated changelog possible later without retrofitting anything.

```
<type>(<scope>): <subject>

<body — optional, wrapped at 72 columns>

<footer — optional>
```

### The subject line

- Same `type` vocabulary as branches, plus `style` (formatting only) and `build`.
- `scope` is required for `feat`, `fix`, `perf`, `refactor`; optional for `chore`, `docs`, `ci`.
- Imperative mood: `add`, not `added` or `adds`.
- Lowercase first word, no trailing period.
- 72 characters maximum.

```
fix(agent3): flatten canonical skill index to alias→canonical map
perf(pipeline): persist only top-K matches via single executemany
refactor(agent4): extract LLMProvider protocol from Ollama client
chore(deps): split requirements into runtime, ml and dev files
docs(adr): record LLM allocation decision for the 4-agent pipeline
test(agent3): assert normalize("python") != normalize("java")
```

### The body

Optional for mechanical changes, expected for anything with reasoning behind it.
Explain **why**, not what — the diff already says what. Reference the backlog item ID
from [`TASKS.md`](TASKS.md) so a commit can be traced back to the finding that caused it.

```
fix(agent3): flatten canonical skill index to alias→canonical map

_get_canonical_skill iterated a dict that is nested by category, so the
alias comparison ran against the inner dict's keys and the function
returned the category name. Every programming language normalized to
"programming_languages", making unrelated skills match at 100%.

Skills are 50% of the rule-based score, which is 60% of the hybrid
score, so roughly a third of every reported match was noise.

Refs: A0
```

### Footers

- `Refs: A0, A0b` — backlog items this commit addresses.
- `Closes #12` — GitHub issue, if one exists.
- `BREAKING CHANGE: <what broke and what to do>` — API shape or config key changes.
  Also allowed as `feat(api)!: …` on the subject line.

### Do not

- Do not add AI co-author or generated-by trailers.
- Do not commit `WIP`, `fixes`, `update`, or `asdf`. Amend or rebase before opening the PR.
- Do not mix unrelated changes. A cleanup that rides along inside a bug fix hides the fix.

A commit message template is provided. Enable it once per clone:

```bash
git config commit.template .gitmessage
```

---

## 3. Pull requests

One PR per branch, even solo. Squash-merge so `main` stays one commit per unit of work,
and the squash subject follows the commit format above.

- The PR template at [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md)
  is filled in, not deleted.
- Every PR states how it was verified. "It builds" is not verification.
- Behaviour changes ship with a test in the same PR. Correctness fixes ship with a
  regression test that fails without the fix — confirm it fails first.
- Delete the branch after merge.
- Once CI exists, a red pipeline blocks the merge. No exceptions, including for docs-only
  PRs — a docs PR that fails CI means CI is wrong and that is worth knowing.

---

## 4. Working order

The backlog in [`TASKS.md`](TASKS.md) is in dependency order and grouped into six phases.
Work top-down within the current phase. Two orderings must not be broken:

1. **A0 (skill normalization) before B2/B4 (skill-path performance).** They rewrite the
   same function; doing performance first means writing it twice.
2. **Agent redesign before the OpenRouter provider.** The provider abstraction slots into
   a stateless Agent 4. Adding it to today's per-request-mutated singleton bakes in the
   A7 race.

Architecture decisions with lasting consequences are recorded in [`docs/adr/`](docs/adr/).
Read them before changing the LLM boundary, the provider abstraction, or the skill
vocabulary — those three are already decided and the reasoning is written down.
