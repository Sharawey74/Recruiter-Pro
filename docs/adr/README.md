# Architecture Decision Records

Decisions with consequences that outlive the commit that implemented them. Each record
states the situation, the choice, the options rejected and why, and what the choice makes
harder — not only what it makes easier.

Read the relevant ADR before changing the area it covers. These three are decided; reopening
one means writing a new ADR that supersedes it, not editing it in place.

| ADR | Title | Status | Covers |
|---|---|---|---|
| [001](001-llm-allocation.md) | LLM allocation across the four-agent pipeline | Accepted | Which agents may call an LLM, and why Agents 1 and 3 may not |
| [002](002-llm-provider-abstraction.md) | An `LLMProvider` protocol for Agent 4 | Accepted | Provider selection, rule-based as a first-class default, statelessness |
| [003](003-unified-skill-vocabulary.md) | One unified skill vocabulary | Accepted | Merging four skill sources; the alias index behind the scoring bug |

## Conventions

- Filename: `NNN-kebab-case-title.md`, numbered sequentially, never renumbered.
- Status: `Proposed` → `Accepted` → `Deprecated` | `Superseded by ADR-NNN`.
- An accepted ADR is not edited to change its decision. Write the next one and mark this one
  superseded; the record of what was believed at the time is the point.
- Name the backlog items that implement it in the header. Cite the IDs; never link to the
  file. See [Backlog IDs](#backlog-ids) below.

## Backlog IDs

Comments, commit footers and ADR headers in this repository cite short IDs — `A0`, `N18`,
`5.9`, `7.2.3`. **They refer to a local engineering log that is deliberately not published**;
it holds raw findings and superseded conclusions rather than documentation.

Read them as issue numbers. They exist so a change can be traced back to the finding that
caused it, and they are stable, which is why they are worth keeping even though the file
is not here. **You never need the log to understand the code**: anything from it that
matters to a reader was written into the README, into these ADRs, or into a comment at the
site it concerns. A comment reading `See backlog 5.9` is naming a finding whose substance
the sentences above it already state.

## Open

**ADR-4 — hosted demo default explanation mode**, blocked until Phase 4. Rule-based by
default with an OpenRouter opt-in, or OpenRouter by default behind the quota guards.

> Note: `.gitignore` ignores `docs/` as a whole and re-includes only `docs/adr/`. Documentation
> added elsewhere under `docs/` will not be tracked.
