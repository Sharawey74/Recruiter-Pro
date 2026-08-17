<!--
Branch and commit conventions: CONTRIBUTING.md
Backlog item IDs: docs/adr/README.md#backlog-ids
Keep this filled in — a squash-merged PR body is the permanent record of the change.
-->

## What and why

<!-- One or two sentences. What changes, and what problem it solves. -->

**Backlog item(s):** <!-- e.g. A0, A0b — or "none" for unplanned work, with a reason -->

**Type:** <!-- feat | fix | perf | refactor | test | chore | docs | ci -->

## Root cause

<!--
For `fix` and `perf` PRs only; delete this section otherwise.
What was actually wrong, not what the symptom was. If there is no root cause, the
change is a workaround and should say so.
-->

## How this was verified

<!--
Be specific. "Tests pass" on its own is not verification.
Delete the lines that do not apply.
-->

- [ ] New test added, and confirmed **failing before** the fix (paste the failure)
- [ ] `pytest` passes locally — <!-- N passed, M skipped -->
- [ ] `next build` passes (frontend changes)
- [ ] Exercised manually — <!-- what you clicked / what request you sent, and what you saw -->
- [ ] Benchmark before/after (perf PRs) — <!-- before: Xs, after: Ys, method -->

```
<!-- paste the relevant command output -->
```

## Scoring impact

<!--
Required if this PR touches Agent 3, the skill vocabulary, scoring weights, the ML
model, or feature engineering. Otherwise write "none".

Scores are the product's output. A change that moves them silently is the failure mode
this project already had once (A0) — say what moved and whether that was intended.
-->

- Does this change the score any candidate receives? <!-- yes / no -->
- If yes: intended or a side effect, and what was compared to confirm it.

## Risk and rollback

<!-- Delete what does not apply. -->

- **Blast radius:** <!-- e.g. scoring path only / API contract / frontend only / build only -->
- **Rollback:** <!-- revert is clean / requires re-running X / migration involved -->
- **Config or env changes:** <!-- new keys, defaults, whether `.env.example` was updated -->

## Checklist

- [ ] Branch name follows `<type>/<scope>-<slug>`
- [ ] Commits follow `type(scope): subject`, no `WIP`, no AI attribution trailers
- [ ] Single concern — this PR does one thing
- [ ] No secrets, keys, or `.env` contents in the diff or in logs
- [ ] No new abstraction without ≥2 real implementations today
- [ ] Dead code removed rather than commented out
- [ ] Backlog item ticked, or a follow-up item added for what was deliberately left out
- [ ] ADR added or updated if this changes a decision recorded in `docs/adr/`

## Deliberately not in this PR

<!--
Anything you noticed and chose not to fix here. Keeps scope honest and stops the
reviewer from re-reporting it. Add it to the backlog and reference the ID.
-->
