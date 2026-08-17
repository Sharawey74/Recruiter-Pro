# ADR-1: LLM allocation across the four-agent pipeline

**Status:** Accepted
**Date:** 2026-08-09
**Deciders:** Repository owner (solo project)
**Related:** [ADR-2](002-llm-provider-abstraction.md) · [ADR-3](003-unified-skill-vocabulary.md)
**Backlog:** items 2.5, 2.7, 4.4 ([what these are](README.md#backlog-ids))

---

## Context

Recruiter-Pro runs a four-agent pipeline: **Parser** (file → text) → **Extractor** (text →
structured profile) → **Scorer** (profile × N jobs → ranked matches) → **Explainer**
(matches → recruiter-readable prose). The question is which of the four may call an LLM.

The default instinct on a project labelled "AI agents" is to put a model in every stage.
Three forces make that the wrong answer here, and only one of them is about cost.

**1. Fan-out.** Agents 1, 2 and 4 run once per upload. Agent 3 runs **once per job**, against
a corpus of roughly 4,000 postings. That is not a difference of degree.

**2. Quota is a fixed ceiling, not a budget.** The intended hosted provider is OpenRouter's
free tier:

| | Limit |
|---|---|
| Requests/day, free account | **50** |
| Requests/day, after a one-time $10 credit (permanent) | **1,000** |
| Requests/**minute**, both | **20** — credits do *not* raise this |
| Token cost on `:free` models | $0 |

The per-minute cap cannot be bought out of. One LLM call per job means ~4,000 requests for a
single CV: 80× the entire daily budget, and 200 minutes of wall time at 20 req/min. That is
not a cost problem to optimize; it is arithmetic that does not close.

**3. Auditability is the product.** This is a screening tool. A score that rejects a
candidate has to be reproducible, explainable, and regression-testable. Those properties are
not achievable if a sampled language model sits in the decision path.

There is also a live lesson in the codebase arguing for determinism. `TASKS.md` item 2.2
documents a bug where skill normalization silently collapsed every skill into its category
name, so a Python developer matched a Java job perfectly. It was found by reading the code
and is fixable with a five-line index build and a unit test. **The equivalent bug inside an
LLM-scored pipeline would have been invisible and untestable** — no stack trace, no failing
assertion, just plausible-looking numbers.

---

## Decision

**LLMs run at the edges of the pipeline — understanding the input and explaining the output.
Never in the middle, where the decision is made.**

| Agent | LLM? | Calls per upload | Rationale |
|---|---|---|---|
| **1 — Parser** | ❌ No | 0 | File→text is deterministic and solved. An LLM adds latency and can hallucinate text that is not in the document — catastrophic for a resume screener |
| **2 — Extractor** | ✅ Hybrid | **1** | Regex is brittle across free-form CV layouts. This is where a model earns its place |
| **3 — Scorer** | ❌ **No — hard architectural boundary** | 0 | O(n) per job, and scoring must be deterministic, reproducible and auditable |
| **4 — Explainer** | ✅ Yes | **1**, batched | Natural-language generation is its literal purpose. Runs on top-K only |

**Total: 2 LLM calls per CV upload.**

| Account | Uploads/day |
|---|---|
| Free (50 req/day) | ~25 |
| After the one-time $10 (1,000 req/day) | ~500 |

Twenty-five per day is sufficient for a portfolio demo. The $10 unlock is worth it if the
link is shared widely, and it stays genuinely optional — a good place to be.

### Agent 2 — the hybrid split

"Hybrid" is load-bearing. The deterministic pass runs **first and always**; the LLM enriches
and never overrides a confident regex result.

| Field | Method | Why |
|---|---|---|
| `email`, `phone`, URLs | **Regex only** | ~100% reliable, free, instant. An LLM here is strictly worse |
| `skills` | **Vocabulary match, LLM-augmented** | The dictionary catches known skills; the model catches phrasing it misses |
| `name` | **LLM** | Currently guarded by a hardcoded blocklist of Cairo neighbourhoods (`maadi`, `zamalek`, `heliopolis`, `dokki`) — heuristics overfit to a handful of test CVs that will not generalize |
| `experience_years` | **LLM + validation** | Needs reasoning over date ranges and overlapping roles. Clamp to 0–50; anything outside is a hallucination → fall back to the regex value |
| `education`, `seniority` | **LLM** | Free-form phrasing, normalized to an enum |

Prompt rule, non-negotiable: *"Return null for any field not present in the text. Do not
infer or guess."* A hallucinated skill on a resume screener is a correctness bug, not a
cosmetic one. Output is validated against a Pydantic schema; on schema failure, retry once,
then fall back to deterministic-only with `degraded=True`. The request still succeeds.

### Agent 4 — grounded, batched, capped

Runs on top-K only, hard cap **K ≤ 3**, **all K batched into one call**. Batching is why the
budget is 2 calls per upload rather than 4+, and it halves latency as well as quota. The
prompt receives the computed scores and the matched/missing skills and explains *those*: it
never produces a score, a decision, or a hiring recommendation. Prompt rule: *"Do not state
facts not present in the provided breakdown."*

---

## Options considered

### Option A — LLM in every agent

| Dimension | Assessment |
|---|---|
| Complexity | High — four prompt surfaces, four failure modes, four fallbacks |
| Cost / quota | **Infeasible** — ~4,000 requests per upload against a 50–1,000/day cap |
| Latency | ~200 minutes per upload at the fixed 20 req/min ceiling |
| Auditability | None — scores unreproducible, bias untestable |

**Pros:** demos as maximally "AI-powered"; no hand-written scoring logic to maintain.
**Cons:** does not run at all on the target quota. Even with unlimited paid quota, it fails
the reproducibility and auditability requirements, which are the product's actual value.

Rejected on arithmetic before philosophy.

### Option B — LLM at the edges only *(chosen)*

| Dimension | Assessment |
|---|---|
| Complexity | Low — two prompt surfaces, both with working deterministic fallbacks |
| Cost / quota | 2 requests per upload; ~25 uploads/day free, ~500 after a one-time $10 |
| Latency | <200 ms parse + <3 s extract + <2 s score + <5 s explain |
| Auditability | Full — the entire decision path is deterministic and unit-testable |

**Pros:** fits the quota with room to spare; the core works when the LLM does not; scoring is
regression-testable; each LLM stage degrades to a working deterministic path instead of an
error.
**Cons:** name and experience extraction stay heuristic whenever the provider is unavailable;
skill matching remains lexical rather than semantic.

### Option C — no LLM at all

| Dimension | Assessment |
|---|---|
| Complexity | Lowest |
| Cost / quota | Zero |
| Latency | Best |
| Auditability | Full |

**Pros:** nothing to rate-limit, nothing to fall back from, no key to manage.
**Cons:** Agent 2's extraction quality stays capped by the regex heuristics — including that
neighbourhood blocklist. Explanations stay templated. And on a project whose premise is an
agentic pipeline, having no model anywhere is a weaker demonstration than having one placed
deliberately.

Rejected, but note it is the **fallback configuration**, not a discarded branch: with
`provider = rule_based` the system runs exactly this way, and that path must keep working
(see [ADR-2](002-llm-provider-abstraction.md)).

### Option D — semantic scoring via embeddings (LLM-adjacent, no LLM in the hot path)

Embed CV skills and job requirements once; score by cosine similarity. This would genuinely
improve Agent 3 without a model in the loop, and it respects the fan-out constraint since
embeddings are precomputed.

**Rejected — deferred, not dismissed.** It requires a vector store, an embedding model and an
index build, which crosses the project's explicit over-engineering line and does not fit the
512 MB deployment target. Worth revisiting if Agent 3's lexical matching turns out to be the
accuracy ceiling after `TASKS.md` 2.2 and 2.4 land. Recorded in the README as
considered-and-deferred, which reads better than not having considered it.

---

## Trade-off analysis

**Fan-out is the decisive axis.** Agents 1, 2 and 4 are O(1) per upload; Agent 3 is O(n) per
job. That single fact separates "an LLM is affordable here" from "an LLM is impossible here",
and it is why the allocation is not a matter of preference.

**The quota does not change the answer — it changes the guardrails.** If the API were free and
unmetered, Agent 3 would *still* not use an LLM: 4,000 sequential calls fails on latency and
determinism regardless of price. What the fixed 20 req/min ceiling does change is that the
guards below become mandatory rather than nice-to-have. But they are simpler than cost guards
— a counter and a graceful degrade, not budget tracking.

**Determinism in Agent 3 is a feature, not a limitation,** and it should be stated plainly in
the README:

> *Scoring is deterministic by design. The same CV and job always produce the same score, the
> breakdown is fully auditable, and the LLM is confined to explaining decisions it did not
> make. An LLM-scored ATS cannot be audited for bias, cannot be regression-tested, and cannot
> justify a rejection to a candidate.*

That is a defensible engineering position rather than an apology for a constraint. Most
portfolio "AI agent" projects put a model in the scoring path precisely because they have not
worked through this.

**What is given up:** semantic skill matching (`"K8s orchestration"` will not match
`"container orchestration"` unless the vocabulary says so), and heuristic-quality extraction
whenever the provider is down. Both are acceptable; the second is bounded by the `degraded`
flag being surfaced rather than hidden.

---

## Consequences

**Easier**
- Agent 3 is a pure function of its inputs — unit-testable, benchmarkable, and safe to
  optimize aggressively (the entire Phase 3 performance work depends on this).
- The product works with zero network access. `provider = rule_based` is a first-class
  configuration, not an error path.
- Quota exhaustion degrades the demo instead of breaking it.
- Two prompt surfaces to maintain instead of four.

**Harder**
- Extraction quality when the LLM is unavailable is bounded by the regex heuristics; the
  `degraded` flag must be surfaced in the API response and the UI rather than swallowed.
- Skill matching quality now rests entirely on the vocabulary, which raises the stakes on
  [ADR-3](003-unified-skill-vocabulary.md).
- Two extraction paths (deterministic and LLM-enriched) means both need test coverage.

**To revisit**
- If Agent 3's lexical matching proves to be the accuracy ceiling → reconsider Option D.
- If the hosted demo defaults to OpenRouter → the guardrails below move from advisable to
  load-bearing, and the decision gets its own ADR-4.

### Guardrails required by this decision

| Guard | Setting | Protects |
|---|---|---|
| Endpoint rate limit (`slowapi`) | `/match` 5/min/IP, `/upload` 10/min/IP | the instance on a public URL |
| LLM concurrency semaphore | ≤2 in flight | stays under the fixed 20 req/min |
| Top-K explanation cap | **K ≤ 3, hard** | the quota, at its source |
| Daily request counter (SQLite) | auto-switch to rule-based at 90% | **degrade, do not break** |
| Per-call timeout | 30 s, then fall back | latency |

The top-K cap is the one that actually protects the quota — today `explain=true` generates an
explanation for *every* job scoring ≥ 0.6, which on a public URL is unbounded. The rate
limiter is the backstop, not the primary defence.

---

## Action items

1. [ ] Enforce the boundary in code: no network client is constructed anywhere inside Agent 3
       (`TASKS.md` 2.7)
2. [ ] Determinism test — same inputs produce a byte-identical `ScoreBreakdown` (`TASKS.md` 2.5)
3. [ ] Agent 2 hybrid split: regex-first pass, one Pydantic-validated LLM call, `degraded`
       flag, `extraction_method` recorded per field (`TASKS.md` 2.7)
4. [ ] Delete the `ADDRESS_TOKENS` neighbourhood blocklist once the LLM handles names
5. [ ] Agent 4: batch top-K into a single call, hard-cap K ≤ 3 (`TASKS.md` 4.4)
6. [ ] Implement all five guardrails above (`TASKS.md` 4.4)
7. [ ] Surface `degraded` and `explanation_source` in the API response and the UI
8. [ ] Add the determinism paragraph to the README (`TASKS.md` 6.5)

---

*Rate limits sourced from OpenRouter free-tier documentation, August 2026. Re-verify before
relying on the 1,000/day figure.*
