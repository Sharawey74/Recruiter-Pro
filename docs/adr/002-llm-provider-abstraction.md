# ADR-2: An `LLMProvider` protocol for Agent 4

**Status:** Accepted
**Date:** 2026-08-09
**Deciders:** Repository owner (solo project)
**Related:** [ADR-1](001-llm-allocation.md) · [ADR-3](003-unified-skill-vocabulary.md)
**Backlog:** [`TASKS.md`](../../TASKS.md) — 4.6, 4.7, 4.9

---

## Context

[ADR-1](001-llm-allocation.md) puts an LLM in exactly two places, one of which is Agent 4,
the Explainer. Agent 4 now has to run in three environments that cannot share a client:

| Environment | Needs |
|---|---|
| Local development | Ollama on `localhost:11434`, no key, no quota |
| Hosted demo (Render free tier) | A remote API — a 3B model needs several GB of RAM, so Ollama is impossible there |
| CI, tests, and any offline run | No network at all |

The current implementation cannot serve any two of those, and the codebase already contains
the *shape* of a solution that was never wired up. Verified against the clone:

- `config.py:89` declares `provider: str = "ollama"  # ollama, openai, anthropic`. **Nothing
  in the repository ever reads this field.**
- `agent4_llm_explainer.py` (406 LOC) pings `/api/tags` and POSTs `/api/generate` with
  Ollama's payload shape — hardcoded.
- `agent4_langchain_explainer.py` (247 LOC) instantiates `ChatOllama` directly — also
  hardcoded.
- `agent4_factory.py` (61 LOC) selects between those two on a `use_langchain` boolean. Both
  branches lead to Ollama, so the factory chooses between two spellings of the same
  destination.
- `requirements.txt` pins `openai==1.51.0` with the comment `# For OpenRouter/GPT-OSS-20B
  access`. **`openai` is imported nowhere in the repository.** The OpenRouter intent exists
  only as that comment.

So "switch to OpenRouter" is not a config change, despite a config field that looks like it
would do it. It is a refactor of Agent 4.

There is a second, worse problem entangled with this one. `api.py:335–362` reaches into a
module-level singleton to reconfigure Agent 4 per request:

```python
original_agent = pipeline.agent4
pipeline.agent4 = get_explainer_agent(use_langchain=True, config=pipeline.config)
original_llm_enabled = pipeline.agent4.llm_available
pipeline.agent4.llm_available = False          # ...restored in a finally
```

With two concurrent requests, request B's toggle leaks into request A. Under uvicorn with
more than one worker that is a live race, and the restore is skipped on some raise paths.
This is `TASKS.md` item 4.6, and it exists **because** provider selection has no home other
than mutable instance state on a shared object.

One further constraint, self-imposed and recorded in `TASKS.md`: *no new abstraction unless
it has ≥2 real implementations today.* This ADR has to clear that bar rather than assume it.

---

## Decision

Introduce one small protocol, and make provider selection a **constructor argument** rather
than a mutable attribute.

```python
class LLMProvider(Protocol):
    def is_available(self) -> bool: ...
    def explain(self, batch: list[ExplanationContext]) -> list[Explanation]: ...
```

Two methods. No base class, no registry, no plugin discovery — a `typing.Protocol`, so
implementations are related by shape rather than inheritance and each stays independently
testable.

Four implementations, all of which exist as working code today or as a pinned dependency
with declared intent:

| Implementation | Role | Status today |
|---|---|---|
| `RuleBasedProvider` | **Production default.** Always available, zero network | Working fallback logic inside `agent4_llm_explainer.py` |
| `OllamaProvider` | Local development | `agent4_llm_explainer.py`, 406 LOC |
| `LangChainProvider` | Optional fourth path | `agent4_langchain_explainer.py`, 247 LOC |
| `OpenRouterProvider` | Hosted demo | To build — via the already-pinned `openai` SDK pointed at `https://openrouter.ai/api/v1` |

Selected by `config.llm.provider` — the field at `config.py:89` that finally gets read.

**`RuleBasedProvider` is a first-class provider, not an error path.** This is the design's
load-bearing claim. It satisfies the same protocol, is selectable by config, is tested like
the others, and is what CI runs against. The rule-based logic already works; what changes is
that it stops being reachable only through a failure.

Agent 4 becomes stateless: the provider is injected once at construction, and `explain()`
takes everything it needs as arguments. Nothing mutates `pipeline.agent4` at request time.
That resolves `TASKS.md` 4.6 as a consequence of the design rather than as a separate patch —
which is why **4.9 must land before 4.7**. Adding a provider to today's mutated singleton
would bake the race into the new abstraction.

### Failure behaviour

Quota exceeded, timeout, malformed JSON, or `is_available()` returning `False` → fall back to
`RuleBasedProvider`, tag the response `explanation_source: "rule_based"`, and surface a quiet
note in the UI. **The user always gets an explanation.** Falling back is normal operation,
not an incident.

---

## Options considered

### Option A — keep the current factory, add an `if` branch for OpenRouter

| Dimension | Assessment |
|---|---|
| Complexity | Low today, compounding — the fourth branch is where it stops being readable |
| Cost | None |
| Testability | Poor — no seam to substitute a fake, so tests need a live Ollama or heavy mocks |
| Concurrency | **Unsafe** — provider selection stays mutable instance state; A7 race persists |

**Pros:** smallest diff; nothing new to learn.
**Cons:** does not address the race, which is the more serious of the two problems. The
factory's `use_langchain` boolean does not extend to four options — it becomes
`use_langchain`, `use_openrouter`, `use_rules`, and then the combinations are ambiguous.
Rule-based stays an error path rather than a selectable mode, so CI still cannot exercise
Agent 4 without a network.

### Option B — `LLMProvider` protocol, constructor-injected *(chosen)*

| Dimension | Assessment |
|---|---|
| Complexity | Low — two methods, four implementations, no framework |
| Cost | None; enables the free-tier hosted demo |
| Testability | Good — a fake provider is ~5 lines; CI runs the rule-based path with no network |
| Concurrency | **Safe** — immutable after construction; the A7 race is structurally impossible |

**Pros:** clears the ≥2-implementations bar decisively (four, three of them already written);
makes `config.llm.provider` honest; local, hosted and offline environments each get a real
configuration; fixes the race as a property of the design.
**Cons:** the four implementations must genuinely agree on a return type, which means
normalizing four different response shapes into one `Explanation` — real work, and the place
bugs will appear.

### Option C — adopt LangChain as the single abstraction layer

LangChain already abstracts over providers, and `agent4_langchain_explainer.py` plus four
`langchain*` pins are already in the tree.

| Dimension | Assessment |
|---|---|
| Complexity | Deceptively high — a large dependency surface for two method calls |
| Cost | Adds ~4 packages and their transitive tree to a 512 MB deployment target |
| Testability | Moderate — testing means mocking LangChain's abstractions rather than ours |
| Concurrency | Neutral — does not address the singleton mutation |

**Pros:** no bespoke abstraction to maintain; provider integrations already written.
**Cons:** the deployment target is a 512 MB free tier, and `TASKS.md` 1.2 is actively
*removing* unused heavy dependencies to fit it. Taking a hard dependency on a large framework
to obtain two methods inverts that work. It also does not give a rule-based provider, which
is the one that must always work — that would still have to be hand-written and bolted on
outside the abstraction. Keep LangChain as *one* provider; do not promote it to *the*
abstraction.

### Option D — no abstraction; support only OpenRouter

| Dimension | Assessment |
|---|---|
| Complexity | Lowest |
| Cost | Quota consumed during every local development run |
| Testability | Poor — CI needs a live key |
| Offline | Broken |

**Pros:** one code path.
**Cons:** burns a 50/day quota on local iteration, requires a secret in CI, and deletes 653
lines of working Ollama and rule-based code that solve real problems. Rejected.

---

## Trade-off analysis

**The ≥2-implementations bar, checked honestly.** This is the guardrail that keeps the
refactor from sprawling, so it deserves to be applied rather than waved at. Three
implementations exist as working code *right now* (rule-based, Ollama, LangChain) and are
already reached through a factory — the abstraction is being **recognized**, not invented.
Contrast with a `ScoringStrategy` interface, which was rejected precisely because there is one
scoring approach and an interface would be speculative generality. Same rule, opposite
answer, which is what makes it a usable rule.

**Two methods, not five.** The protocol is deliberately minimal. Streaming, token counting,
retry policy and model selection stay inside implementations, where they differ. A protocol
that grows to accommodate every provider's features becomes the union of all of them and
constrains nothing.

**Constructor injection is doing more work than the protocol is.** The protocol makes
OpenRouter possible; injection makes the concurrency bug impossible. If only one of the two
could ship, injection would be the one — a mutable `llm_available` attribute on a shared
singleton is a defect regardless of how many providers exist.

**Normalizing four response shapes is where the real cost sits.** Ollama returns its own JSON,
LangChain returns message objects, OpenRouter returns OpenAI-shaped completions, and
rule-based returns a constructed string. All four must produce the same `Explanation`, and
malformed model output must be caught at the boundary rather than propagating a half-parsed
object into the API response. Budget test coverage for this specifically.

**What is given up:** provider-specific capabilities are not exposed. Streaming responses,
per-provider tuning parameters and function calling are unavailable through the protocol. For
a batched call that returns ≤3 explanations, none of that is currently wanted, and any of it
can be added later by extending a single implementation without touching the others.

---

## Consequences

**Easier**
- The hosted demo becomes possible at all — Ollama cannot run on the target free tier.
- CI exercises Agent 4 end-to-end with no network and no secret, using `RuleBasedProvider`.
- `TASKS.md` 4.6 (the A7 race) is fixed by construction rather than by a `finally` block.
- Adding a fifth provider is a new file plus a config value, touching nothing else.
- `config.py:89` stops being a lie.

**Harder**
- Four implementations must agree on one return type; response normalization needs its own
  tests, including malformed-output cases.
- Provider-specific features are out of reach without extending the protocol — accepted
  deliberately.
- One more layer between the API handler and the model when debugging a bad explanation;
  mitigated by tagging every response with `explanation_source`.

**To revisit**
- If `LangChainProvider` is never selected in practice, delete it and its four `langchain*`
  pins — that removes real weight from the deployment image. Keep it only while it is
  genuinely a fourth option.
- If the hosted demo defaults to OpenRouter rather than rule-based, that is a separate
  decision with cost and abuse implications → ADR-4.
- If a second agent ever needs an LLM, this protocol is the reuse point; check that its call
  shape actually fits `explain(batch) -> list` before assuming it does.

---

## Action items

1. [ ] Define `LLMProvider` protocol, `ExplanationContext` and `Explanation` types (`TASKS.md` 4.9)
2. [ ] Extract `RuleBasedProvider` from the fallback path inside `agent4_llm_explainer.py` —
       first, since it is the default and everything else falls back to it
3. [ ] Extract `OllamaProvider`; delete the hardcoded endpoint construction
4. [ ] Adapt `agent4_langchain_explainer.py` to the protocol as `LangChainProvider`
5. [ ] Replace `agent4_factory.py`'s `use_langchain` boolean with `config.llm.provider`
       dispatch
6. [ ] Make Agent 4 stateless; remove the singleton mutation at `api.py:335–362` and pass
       `use_llm` down as an argument (`TASKS.md` 4.6)
7. [ ] Build `OpenRouterProvider` on the `openai` SDK against `https://openrouter.ai/api/v1`;
       re-add `openai` to `requirements.txt` in the same PR that first imports it (`TASKS.md` 4.7)
8. [ ] Fallback chain: any provider failure → `RuleBasedProvider`, tagged
       `explanation_source: "rule_based"`, surfaced in the UI
9. [ ] Tests: a fake provider for the fallback chain; a malformed-response test per
       implementation; assert no provider state is mutated during a request
