---
name: goal
description: >-
  A goal-driven iterative agent. Given a GOAL (and optional success criteria or a
  verify command), it loops — plan, attempt, verify against the goal, diagnose
  the gap, refine — until the goal is met or the iteration cap is reached. The
  verifier is an executable check command if one is supplied (exit 0 = goal met);
  otherwise it self-judges each success criterion PASS/FAIL with cited evidence.
  Domain-agnostic: does the work directly for most goals, and delegates code
  goals to the `coders` skill. TRIGGER on: "iterate until", "keep going until X",
  "loop until the tests pass", "drive this to a goal", "don't stop until",
  "make this goal happen", "achieve X", "iterate toward", "get X to Y", "goal
  loop", "refine until it meets the bar". SKIP on: single-step tasks with no loop
  needed (just do them directly), a one-shot fix you can make in one edit, tasks
  that need an adversarial review loop (use `implementer`), greenfield projects
  wanting competing approaches (use `one-shot-project`), and asking what a goal
  is.
license: MIT
metadata:
  author: user
  version: 1.0.0
  category: meta
  tags:
    - goal
    - iteration
    - verifier
    - self-refinement
    - loop
    - composable
    - multi-agent
---

# Goal

Iterate toward a verifiable goal until it is met or the cap is reached. The
defining trait is the **verify→diagnose→refine** loop: every iteration produces
an objective verdict against the goal, and the next attempt is driven by the
specific gap that remains — not by a generic retry.

Load `skills/common/patterns/execution-contract.md` for the binding sub-agent
contract (owned output, worktree safety, `DONE:` signal) and
`skills/common/patterns/scaling.md` for the effort gate. This skill follows
those contracts; it does not restate them.

## Activation Gate

Confirm before looping: (1) the task actually needs iteration — there is no
known single edit that achieves it; (2) the goal is stated concretely enough to
judge "met" objectively; (3) you have a place to write output. If one obvious
action achieves the goal, do it directly and emit `DONE:` — do not loop to look
busy. If the goal cannot be judged objectively and the user gave no verify
command, ask them for either a check command or measurable criteria before
starting; a loop with no verifier thrashes.

## Effort Scaling

Load `skills/common/patterns/scaling.md`. Pick a tier and state it in one line:

- **lite** — one tight goal with 1–2 clear criteria (e.g. "make this test
  pass"): work directly, cap at 3 iterations, no delegation.
- **standard** — a goal with a few independent success criteria, or a code goal
  needing real implementation: delegate code work to `coders`, cap at 8
  iterations.
- **full** — large/open-ended goal with many criteria or parallel sub-goals:
  full crew, parallel verification, cap at 15 iterations.

Escalate down by default. Current models over-spawn, so prefer direct action
over delegating whenever a sub-task is faster done yourself.

## Inputs

Accept these from the invocation prompt (or infer from the user's words):

- **GOAL** — the goal, in the user's words. The source of truth.
- **CRITERIA** *(optional)* — observable success criteria. If absent, derive
  them in Phase 0.
- **VERIFY** *(optional)* — a shell command whose exit code is authoritative:
  exit 0 = goal met, non-zero = not met. When supplied, this is the primary
  gate; self-judged criteria are secondary evidence.
- **MAX_ITERS** *(optional)* — override the tier cap.
- **OUTPUT_DIR** — the workspace. Default `/tmp/goal-<slug>/`.

## Phase 0 — Decompose

Before any attempt, turn the goal into something you can judge objectively.

1. Derive **3–7 success criteria** (use the user's CRITERIA verbatim if given).
   Each criterion must be independently checkable and observable: "the function
   returns X for input Y", "the doc has an example in every section",
   "`pytest tests/` exits 0". Avoid subjective criteria like "reads well"; if the
   goal is subjective, find the observable proxy.
2. Pick the **verifier**: if VERIFY is supplied, it is authoritative for the
   "command passes" criterion. For every other criterion (and for all criteria
   when no VERIFY is given), self-judge PASS/FAIL citing concrete evidence — a
   `path:line`, a quoted output, or a command result. A self-judged PASS with no
   cited evidence is invalid; treat it as FAIL.
3. Write the workspace:

   ```
   /tmp/goal-<slug>/{goal.md, criteria.md, iterations/, status.json}
   ```

   `criteria.md` holds the numbered criteria. `status.json` holds `{slug, tier,
   max_iters, iteration: 0, criteria: [{id, status}], verdict: "PENDING"}`.

## Phase 1 — The Loop

Each iteration runs the four steps below, then writes
`iterations/iteration-N.md`.

**1. Plan.** Read the previous iteration's gap diagnosis (skip on iteration 1).
State, in 2–4 lines, what *this* attempt will change to close the remaining
gaps. The plan must target specific failing criteria — not "try harder".

**2. Execute.** Make the attempt.
- For **code** goals at `standard`/`full`: delegate the implementation to the
  `coders` skill (one `coders` sub-agent per disjoint slice, dispatched
  together). Give each coder the relevant failing criterion as its ACCEPTANCE.
- For everything else (prose, config, data, research artifacts): do the work
  directly.
Write outputs into `OUTPUT_DIR` (or the target repo with worktree safety).

**3. Verify.** Run the verifier and produce a per-criterion table:
- If VERIFY is set: run it; capture exit code + last lines. Exit 0 → the
  "command passes" criterion is PASS; non-zero → FAIL (authoritative — a
  self-judged PASS cannot override a failing VERIFY command).
- Then judge **every** remaining criterion PASS/FAIL, each with cited evidence.
  Record the actual command outputs / file evidence; never infer a result.

**4. Decide.**
- All criteria PASS (and VERIFY exits 0 if set) → **goal met**, go to Phase 2
  with verdict `DONE`.
- Otherwise → write a **gap diagnosis**: which criteria failed, the root cause
  of each, and the specific change the next iteration will try. Increment
  `status.json`. Loop to iteration N+1.

**Iteration record** (`iteration-N.md`) has exactly these sections: `## Plan`,
`## Attempt` (what was done + files touched), `## Verification` (the criterion
table with evidence), `## Verdict` (MET | NOT_MET) and, if not met, `## Gap
Diagnosis`. Resumability: on resume, read `status.json` and the latest
`iteration-*.md`; never re-run a completed iteration.

## Anti-Degeneration Rules

These rules are the real value of the loop. A naive retry loop will thrash on
the same failure forever.

- **No identical retries.** Each iteration's attempt must be materially
  different from the last. If you cannot state how it differs, you do not have a
  plan — go back to diagnosis.
- **Escalate strategy, not effort.** If the same criterion FAILs with the same
  root cause for **2 consecutive iterations**, change *strategy* (different
  approach, different tool, re-read the goal/inputs for a missed constraint),
  and state the change explicitly. Doing the same thing louder is not a strategy
  change.
- **Stop when stuck.** If the same set of criteria has failed for **3
  consecutive iterations** with no net progress, stop early — do not burn the
  whole cap. Go to Phase 2 with verdict `BLOCKED` and report what's stuck.
- **Evidence or it didn't happen.** No self-judged PASS without cited evidence.
  A VERIFY command's exit code is final.
- **Don't move the goalposts.** Criteria are fixed in Phase 0. If mid-loop you
  discover the goal itself was mis-specified, stop and surface that to the user
  rather than silently redefining success.

## Phase 2 — Terminate

End with a parseable completion line as the very last line of your message.

If the goal was met:

```
DONE: goal/<slug> — goal met in <N> iterations, all <M> criteria PASS (<evidence pointer>)
```

If the cap was reached or the loop is blocked:

```
DONE: goal/<slug> — PARTIAL|BLOCKED after <N> iterations, <X>/<M> criteria met, remaining: <failing criteria summary>, root cause: <one line>
```

Never emit `DONE:` claiming success when criteria are unmet. `PARTIAL` is a
legitimate outcome — the iteration record lets the user (or a follow-up run)
resume exactly where it stopped.

## Composition

- **As executor:** delegate code goals to `coders`. For non-code or `lite`-tier
  work, execute directly.
- **As a step inside a larger workflow:** a parent orchestrator (e.g.
  `project-manager`, or a `schedule` agent) can invoke `goal` to drive one
  sub-goal to completion. Accept GOAL/VERIFY/MAX_ITERS as parameters; emit the
  `DONE:` line as the completion signal a caller can detect.
- **Agent depth:** `goal → coders` and stops there. Coders never spawn
  sub-agents. Do not nest further; if you need another capability, do it
  yourself as the orchestrator.

## Worktree Safety

Patch-scoped edits only. `git status --short` before touching a real repo; treat
existing uncommitted changes as user-owned. Save a per-file snapshot before
applying, revert only your own patches. Never `git reset --hard`,
`git checkout .`, broad `git restore .`. Never `git commit` — leave changes for
the user to review with `git diff`.

## See Also

- `coders` — the executor this skill delegates code goals to.
- `implementer` — a single-task implement→review→fix loop driven by *reviewer
  verdicts*. Use it when the gate is "does it pass review", not "does it meet an
  external goal".
- `one-shot-project` — competing greenfield builds judged by a PM. Use it when
  you want multiple approaches, not when you have one goal to converge on.
- `project-manager` — coordinated multi-coder builds with PM-owned review.
