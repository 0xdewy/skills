---
name: goal
description: >-
  Runs a bounded attempt-verify-diagnose loop until executable,
  observable, or explicit reviewer gates pass, with durable resume state
  and evidence per criterion. Only use when explicitly requested.
license: MIT
disable-model-invocation: true
metadata:
  author: user
  version: 2.0.0
  category: meta
  activation: explicit
  tags:
    - goal
    - iteration
    - verifier
    - review
    - resumable
---

# Goal

Iterate against fixed gates until they pass, progress stalls, or the cap is
reached.

Load `../common/patterns/execution-contract.md`,
`../common/patterns/workspace.md`, and `../common/patterns/scaling.md`. Consult
`../common/ROUTING.md`. Load `../common/patterns/worker-slice.md` only when
dispatching an independent implementation slice. Validate state with
`../common/scripts/validate_state.py`.

## Gates

- `command`: exit 0 is authoritative.
- `observable`: cite an artifact, output, or `path:line` for each criterion.
- `review`: an independent reviewer returns concrete defects against stated
  criteria; the orchestrator still runs objective checks.

Fix criteria before iteration. Reviewer approval cannot override a failed
command or observable criterion.

## Modes

- `lite`: direct work, max 3 iterations, zero workers.
- `standard`: one workstream, optional worker/reviewer, max 8 iterations.
- `full`: several criteria or a long-running task, bounded workers, max 15.

## Durable State

Use the emitted schema (`validate_state.py goal --print-template`) for
`status.json`: goal, mode, state, cap, gate type,
criteria states, current iteration, attempts, last evidence, blockers, and
`next_action`. If an unfinished workspace matches the goal, validate its
artifacts and resume; do not restart or repeat passed criteria. Archive only a
mismatched or completed prior run.

## Loop

1. State mode/workspace. Write fixed criteria and validate initial status.
2. Plan only against failing criteria. Record each iteration under
   `iterations/<N>.md`: attempt, evidence, verdict, and gap diagnosis.
3. Work directly unless an independent slice justifies a worker. For a review
   gate, give the reviewer only the task, criteria, diff/artifact, and evidence.
4. Run the authoritative command, then judge every remaining criterion.
5. On failure, update and validate `status.json` before continuing.
6. Never retry an identical strategy. Change approach after two same-root-cause
   failures; stop `BLOCKED` after three failures without material progress.
7. Finish only when all gates pass. Never commit or call another coordinator.

```text
DONE: goal/<slug> — PASS|PARTIAL|BLOCKED after <N> iterations, <X>/<M> criteria passed, evidence=<pointer>
```
