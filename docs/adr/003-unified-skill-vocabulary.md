# ADR-3: One unified skill vocabulary

**Status:** Accepted
**Date:** 2026-08-09
**Deciders:** Repository owner (solo project)
**Related:** [ADR-1](001-llm-allocation.md) · [ADR-2](002-llm-provider-abstraction.md)
**Backlog:** [`TASKS.md`](../../TASKS.md) — 2.1, 2.2, 2.4, 2.6, 3.2, 3.4

---

## Context

Skill matching is 50% of the rule-based score, which is 60% of the hybrid score. Roughly a
third of every number this product reports comes from deciding whether two strings refer to
the same skill. [ADR-1](001-llm-allocation.md) keeps an LLM out of the scoring path, so that
decision rests entirely on a lexical vocabulary — which raises the stakes on getting the
vocabulary right.

There are currently four of them. Verified against the clone:

| Location | Size | Used for | Owner |
|---|---|---|---|
| `Agent2.SKILLS_DATABASE` (class constant) | 178 skills | extraction | Agent 2, private |
| `Agent3._find_skill_matches` local `synonyms` dict | 45 groups | matching | Agent 3, function-local |
| `data/dictionaries/skills_canonical.json` | 8 categories, nested | normalization | loaded by Agent 3 — **broken** |
| `src/utils/skill_extraction.py` | 6 functions | nothing | **never imported** |

Four sources of truth that disagree with each other. Adding a skill in one place leaves the
other three unaware, and the disagreement is not theoretical: Agent 2 can extract a skill that
Agent 3's synonym table has never heard of, so the extraction succeeds and the match silently
does not.

### The bug this arrangement produced

`agent3_scorer.py:510–526` assumes `skills_canonical.json` is flat — `{canonical: [aliases]}`.
It is nested by category:

```json
{ "comment": "...",
  "programming_languages": { "Python": ["python","py"], "Java": ["java","jdk"] },
  "frameworks":            { "React": ["react"], "Django": ["django"] } }
```

So `for canonical, aliases in self.skills_database.items()` binds `canonical` to
`"programming_languages"` and `aliases` to the **inner dict**. `[a.lower() for a in aliases]`
then iterates that dict's *keys* — `["python", "java", …]` — the membership test passes, and
the function returns the **category name**.

| CV / job skill | normalizes to |
|---|---|
| `python`, `java`, `javascript` | `programming_languages` |
| `react`, `django` | `frameworks` |
| `mysql` | `databases` |
| `docker` | `devops` |

Both `cv.skills` and `job.required_skills` pass through `_normalize_skills`, so **a Python
developer scores a perfect skill match against a Java job.** No exception, no log line, and a
score that looks entirely plausible. It is the highest-severity item in the backlog
(`TASKS.md` 2.2).

The four-vocabulary arrangement is not incidental to that bug — it is the reason it survived.
With one vocabulary, one owner and one loader, a normalization function returning
`"programming_languages"` is obviously wrong the first time anyone looks at it. Spread across
four half-used sources where three others still produce plausible matches, the failure had
somewhere to hide.

### Additional forces

- **Performance.** `_get_canonical_skill` linearly scans the vocabulary per skill, and the
  45-key synonym dict is rebuilt on every call to `_find_skill_matches` — which
  `_has_skill_match` re-enters for every missing skill. Measured: ~80,000 rebuilds and 3.26 s
  wasted per upload. Whatever replaces this has to be built once and looked up in O(1).
- **Sequencing.** `TASKS.md` 2.2 (fix normalization) and 3.2/3.4 (the performance work)
  rewrite the same function. The alias index is the fix for both. Doing performance first
  means writing it twice.
- **Deployment.** The vocabulary loads into a 512 MB free tier alongside pandas, numpy and
  scikit-learn. Its resident size is a real constraint.

---

## Decision

**One vocabulary file, one loader, one in-memory index, injected into both agents that need
it.**

Merge all four sources into a single `data/skills.json`, keeping the human-authored nested
structure — categories are genuinely useful for grouping and for future UI facets, and
editing a flat 400-entry map by hand is unpleasant.

At load time, flatten it once into an alias index:

```python
def _build_alias_index(raw: dict) -> dict[str, str]:
    """Flatten the category-nested vocabulary into {alias_lower: Canonical}."""
    index: dict[str, str] = {}
    for category, entries in raw.items():
        if not isinstance(entries, dict):      # skips the "comment" key
            continue
        for canonical, aliases in entries.items():
            index[canonical.lower()] = canonical
            for alias in aliases:
                index[alias.lower()] = canonical
    return index
```

Two properties, both load-bearing:

1. **Nested on disk, flat in memory.** Humans edit the readable form; the hot path gets a
   single dict.
2. **Lookup is one dict access.** `_get_canonical_skill` stops being a linear scan, which is
   most of the fix for `TASKS.md` 3.2 and 3.4 at the same time.

The index is wrapped in a `SkillVocabulary` object built once at startup and
**constructor-injected** into Agents 2 and 3 — the same rule [ADR-2](002-llm-provider-abstraction.md)
applies to providers. Neither agent owns a private copy, neither reads the file, and neither
builds a dict inside a loop.

The `comment` key stays in the file (it is useful documentation) and is skipped by the
`isinstance` guard — the same guard whose absence caused the original bug, now explicit.

### The regression test is part of the decision

```python
assert vocab.normalize("python") != vocab.normalize("java")
```

Written **before** the fix and confirmed failing against the current code. This is the guard
that should have existed, and it is cheap enough that its absence was the real defect.

---

## Options considered

### Option A — leave four vocabularies, fix only the nested-dict bug

| Dimension | Assessment |
|---|---|
| Complexity | Lowest — a five-line change |
| Correctness | Fixes the reported bug, leaves the condition that produced it |
| Performance | No improvement; the linear scan and per-call rebuilds remain |
| Maintenance | Four places to update per skill, indefinitely |

**Pros:** smallest possible diff; unblocks Phase 3 immediately.
**Cons:** the four sources still disagree, so Agent 2 continues extracting skills Agent 3
cannot match. Solves the instance and preserves the class. And since the performance work
rewrites the same function anyway, the saved effort is recovered a week later at higher cost.

### Option B — one vocabulary file, flattened alias index, injected *(chosen)*

| Dimension | Assessment |
|---|---|
| Complexity | Low — one JSON file, one ~15-line loader, one injected object |
| Correctness | Fixes the bug and removes the conditions that hid it |
| Performance | O(1) lookup, built once — subsumes `TASKS.md` 3.2 and 3.4 |
| Memory | ~400 entries as a flat `dict[str, str]` — trivial against a 512 MB budget |
| Maintenance | One file to edit; both agents see every change |

**Pros:** single source of truth; both agents provably agree because they hold the same
object; the hot path gets fast as a side effect; trivially unit-testable in isolation;
`src/utils/skill_extraction.py` finally has a destination instead of being deleted outright.
**Cons:** a one-time merge of four overlapping sources, which requires resolving genuine
conflicts (Agent 3's synonyms map `sql → mysql, postgresql`, while `skills_canonical.json`
treats those as distinct canonical entries — a real modelling decision, not a mechanical
merge).

### Option C — fuzzy string matching (Levenshtein / `rapidfuzz`)

| Dimension | Assessment |
|---|---|
| Complexity | Medium — a threshold to tune, plus a new dependency |
| Correctness | **Introduces false positives** on short technical tokens |
| Performance | Considerably worse — pairwise comparison per skill pair |
| Determinism | Preserved, but sensitive to threshold changes |

**Pros:** handles typos and unseen variants without vocabulary maintenance.
**Cons:** short technical skill names are exactly where edit distance fails. `R` and `Go`
are one or two characters; `Java`/`JavaScript` and `C`/`C#`/`C++` are the canonical
counterexamples. A threshold loose enough to catch `postgres`/`postgresql` also matches
things that are not the same skill, and the fan-out (every CV skill × every job skill × 4,000
jobs) makes it the slowest option. The current code already contains a
substring-based fuzzy fallback (`agent3_scorer.py:266–269`) that matches any pair sharing a
4-character substring — a milder version of the same failure mode, which should be tightened
or removed as part of this work.

Rejected. A curated vocabulary with explicit aliases is both faster and more correct here.

### Option D — embedding-based semantic matching

| Dimension | Assessment |
|---|---|
| Complexity | High — embedding model, vector store, index build |
| Correctness | Best recall; `"K8s orchestration"` ↔ `"container orchestration"` works |
| Performance | Acceptable if precomputed; the model itself is heavy |
| Deployment | **Does not fit** a 512 MB free tier |

**Pros:** genuinely solves the class of problem a lexical vocabulary can only approximate,
and respects [ADR-1](001-llm-allocation.md)'s fan-out constraint since embeddings are
precomputed rather than called per job.
**Cons:** crosses the project's explicit over-engineering line, and does not fit the
deployment target that `TASKS.md` 1.2 and 3.3 are actively working toward.

**Deferred, not dismissed** — the same disposition as in ADR-1. Revisit if lexical matching
proves to be the accuracy ceiling once the vocabulary is unified. Record it in the README as
considered-and-deferred.

---

## Trade-off analysis

**Nested on disk versus flat in memory is not a compromise — both forms are optimal for their
consumer.** The failure was never the nesting; it was code reading the on-disk shape as
though it were the in-memory shape. A single explicit conversion at load time, with the
`isinstance` guard that skips non-dict values, is the whole fix. It is worth noting that the
guard exists specifically because the original code assumed every value was a list.

**Curation cost versus correctness.** Options C and D both promise fewer entries to maintain;
both trade that for a failure mode that is harder to see. A missing alias in a curated
vocabulary is a visible gap — the skill simply does not match, and a test can assert it should
have. A false positive from fuzzy or semantic matching is an invisible wrong answer, which is
the exact category of bug this ADR exists to eliminate. **For a screening tool, predictable
gaps beat unpredictable matches.**

**The merge conflicts are the real work, and they are modelling decisions.** Agent 3's synonym
table treats `sql` as a parent of `mysql` and `postgresql`; `skills_canonical.json` treats
each as its own canonical skill. Both are defensible — a job requiring "SQL" probably is
satisfied by a Postgres developer, while a job requiring "PostgreSQL" specifically is not
satisfied by "some SQL". The merge has to decide this deliberately per case rather than let
whichever file is read last win, which is the status quo.

**Removing a dependency rather than adding one.** Option B needs no new packages. Option C
adds `rapidfuzz`; Option D adds an embedding model and a vector store, against a deployment
target the backlog is already trimming dependencies to reach.

**What is given up:** unseen skill variants will not match until someone adds the alias. That
is an accepted and *visible* cost — and it is partially recovered from a direction that does
not compromise the scoring path: ADR-1 puts an LLM in Agent 2's extraction, which can surface
phrasings the dictionary misses at *extraction* time, without ever entering Agent 3's
deterministic loop.

---

## Consequences

**Easier**
- One file to edit when a skill is added; both agents see it immediately.
- The vocabulary is testable in isolation, with no agent involved.
- `_get_canonical_skill` becomes O(1), which is most of `TASKS.md` 3.2 and 3.4.
- `src/utils/skill_extraction.py` gets a destination for its useful parts before deletion
  (`TASKS.md` 2.6).
- Scoring becomes genuinely reproducible: the vocabulary is data, so a score can be
  reproduced by pinning the vocabulary version alongside the code.

**Harder**
- The one-time merge requires real decisions about skill hierarchy, not a mechanical union.
- The vocabulary becomes a versioned artifact — changing it changes scores. It belongs in the
  PR template's "scoring impact" section, and a vocabulary change deserves the same scrutiny
  as a scoring-weight change.
- Two agents now share mutable-looking state. It must be genuinely immutable after
  construction — a frozen mapping, not a dict two agents can write to.

**To revisit**
- If curation becomes a burden as the corpus grows → reconsider Option D, now that a clean
  seam exists to put it behind.
- If Agent 2's LLM extraction consistently surfaces skills absent from the vocabulary, that is
  a signal to add them; consider logging unmatched skills to build the backlog empirically
  rather than by guesswork.
- Tighten or remove the 4-character substring fuzzy fallback at `agent3_scorer.py:266–269`
  once the alias index covers the cases it was compensating for.

---

## Action items

1. [ ] Write the regression test first; confirm it **fails** against current code and paste
       the failure into the PR (`TASKS.md` 2.1)
2. [ ] Implement `_build_alias_index` and the `SkillVocabulary` wrapper; fix
       `_get_canonical_skill` to use it (`TASKS.md` 2.2)
3. [ ] Merge the four sources into `data/skills.json`, resolving hierarchy conflicts
       explicitly (`sql`/`mysql`/`postgresql` first) and recording the rule chosen (`TASKS.md` 2.4)
4. [ ] Inject `SkillVocabulary` into Agents 2 and 3; delete `Agent2.SKILLS_DATABASE` and
       Agent 3's function-local `synonyms` dict (`TASKS.md` 2.4)
5. [ ] Salvage the useful parts of `src/utils/skill_extraction.py` into the vocabulary module,
       then delete the original along with the other three dead `src/utils/` files (`TASKS.md` 2.6)
6. [ ] Confirm the index is immutable after construction
7. [ ] Tighten or remove the substring fuzzy fallback; assert the tightening does not regress
       the matches it was compensating for
8. [ ] Add a `version` field to `data/skills.json` and record it on every stored match, so a
       historical score can be traced to the vocabulary that produced it
9. [ ] Log skills that fail to normalize, at DEBUG — an empirical backlog of missing aliases
