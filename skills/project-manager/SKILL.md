---
name: project-manager
description: >-
  Runs resumable long-horizon builds by decomposing dependency-aware slices,
  dispatching isolated workers, reviewing and integrating checkpoints, and
  verifying the result; supports explicit competing candidates. Only use when
  explicitly requested.
license: MIT
disable-model-invocation: true
metadata:
  author: user
  version: 2.0.0
  category: meta
  activation: explicit
  tags:
    - coordination
    - long-running
    - resumable
    - integration
    - multi-agent
---

# Project Manager

Own a long-running mandate from decomposition through verified integration.

Load `../common/patterns/execution-contract.md` and
`../common/patterns/scaling.md`. Consult
`../common/ROUTING.md`. Load `../common/patterns/worker-slice.md` and
`references/subagent-prompts.md` only when dispatching or reviewing workers.
Validate state with `../common/scripts/validate_state.py`.

## Modes

- `--quick`: direct work or one worker; one review checkpoint.
- `--standard`: 2-4 dependency-aware slices; one revision per failing slice.
- `--thorough`: multiple bounded waves with explicit worker/wave budget.
- `--compete`: orthogonal flag; dispatch 2-3 isolated candidates against the
  same acceptance criteria, test all, and select by evidence.

Use this only when workstreams are independent or the task must persist across
sessions. A single verifier loop is `goal`; one direct action needs no skill.

## Durable State

Use the emitted schema (`validate_state.py project-manager --print-template`)
for the single-writer `status.json`. Record mandate, mode, state,
current wave, acceptance criteria, integration checks, `next_action`, and each
slice's ID, dependencies, owner, state, attempt count, artifact, and evidence.
Slice states: `pending`, `ready`, `in_progress`, `review`, `accepted`, `blocked`.

If an unfinished workspace matches the mandate, validate artifacts and resume
from `next_action`; never redo accepted slices. Archive only completed or
mismatched runs. Checkpoint after planning, each wave, integration, and final
verification so interruption loses no accepted work.

## Workflow

1. State mode/workspace and create `PLAN.md` plus validated `status.json`. Define slices,
   dependencies, owned paths, acceptance, integration order, and checks.
2. Mark dependency-satisfied slices `ready`; dispatch only disjoint ready work
   in parallel under `workers/<id>/`.
3. Validate each worker artifact, inspect its diff, run slice checks, and record
   `ACCEPT` or one targeted revision. Never accept conversational claims alone.
4. Advance the dependency graph; validate and checkpoint after every wave.
5. Integrate accepted slices in declared order. Preserve user-owned worktree
   changes and resolve cross-slice conflicts centrally.
6. Under `--compete`, keep candidates isolated and reject any not run through
   the same checks; document the selection and discarded tradeoffs.
7. Run integration checks. Optional `red-team` is report-only and only when
   explicitly requested; map accepted findings back to criteria before fixes.
8. Write final evidence and `next_action: null`. Never commit unless separately
   requested.

```text
DONE: <WORKSPACE> — <accepted>/<total> slices accepted, waves=<N>, verification=<passed|partial|blocked>
```
