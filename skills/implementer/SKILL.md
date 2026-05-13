---
name: implementer
description: >-
  Iteratively implements and refines work through an adversarial quality loop.
  Runs Implementer → Reviewer → Fixer until the work passes. The Reviewer does
  two passes: a blind Skeptic pass (sees only the output, finds the single
  strongest flaw — adapted from implement-with-review) and, for code tasks, a
  scored 0–10 pass against the original plan. Halted when the Reviewer can find
  no remaining flaws or the loop cap is reached. TRIGGER on: "implement this
  plan", "build it", "write the code", "start implementation", "implement the
  feature", "implement it", "begin build", "start building", "carry out the
  plan", "execute the plan", "stress-test this answer", "find flaws until none
  remain", "adversarial refinement", "refine until right", "best possible
  answer", "make this bulletproof", "keep iterating until solid",
  "implement-with-review", "oracle-skeptic", "oracle skeptic".
  SKIP on: casual mentions of implementation, questions about how to implement
  without a plan to execute, single-line code generation requests, simple
  factual lookups, direct code edits, formatting tasks, file reads, or anything
  where one-shot answers are clearly sufficient.
license: MIT
metadata:
  author: opencode (Skeptic pass adapted from iamky1e's implement-with-review)
  version: 2.0.0
  category: productivity
  tags:
    - implementation
    - iterative
    - review
    - quality
    - adversarial
    - refinement
    - subagent
    - orchestration
    - multi-agent
---

# Implementer Skill

An iterative, subagent-driven refinement loop. Work is produced, reviewed
(including a blind adversarial pass), fixed, and re-reviewed — repeating until
the reviewer finds nothing left to fix.

## Loop Architecture

```
              ┌─────────────────────────────────────────────┐
              │                                             │
              v                                             │
IMPLEMENTER → REVIEWER → [if not 10/10] → FIXER → IMPLEMENTER → ...
                    ↑                                   │
                    └── (loop until verdict = DONE or MAX_LOOPS)
```

- **Implementer**: Executes the plan, writes code or produces the answer
- **Reviewer**: Runs two passes — a blind Skeptic pass (sees only the output) to
  find the strongest flaw, then a scored pass against the original plan (for
  code tasks). Renders verdict.
- **Fixer** (only spawned on non-DONE verdict): Analyzes failures, produces a
  targeted fix plan, then yields back to Implementer

The blind Skeptic pass is adapted from implement-with-review: the reviewer sees
only the output, not the original question. A truly robust answer should be
defensible on its own terms. This catches unsupported claims, internal
contradictions, and hidden assumptions that context-aware review would excuse.

---

## Phase 1: Understand the Ask

Read whatever the user has provided. Capture:
- The plan, question, or task description
- Any existing files, specs, or context
- Whether this is a code task (produces files, has a build/run step) or a text
  task (produces an answer/argument/plan)

If no plan or question exists, ask the user to provide one before proceeding.
Set `MAX_LOOPS=8` for code tasks, `MAX_LOOPS=6` for text tasks.

---

## Phase 2: Initialize

Create working directory and set loop state:

```bash
mkdir -p /tmp/implementer-loop/{implementer,reviewer,fixer,outputs}
```

Set `LOOP_COUNT=1`.

Initialize `outputs/summary.json`:
```json
{
  "loop_count": 1,
  "max_loops": 8,
  "verdict": "IN_PROGRESS",
  "score": null,
  "files": [],
  "gaps": [],
  "summary": null
}
```

---

## Phase 3: Implementation

Spawn a subagent:

```
You are the Implementer for this iteration. Loop: {LOOP_COUNT}.

ORIGINAL TASK:
{the user's request / plan description}

WORKING DIRECTORY: /tmp/implementer-loop/

Read any existing context files in /tmp/implementer-loop/ before starting.

Your job is to produce the best possible version of what was asked for.

FOR CODE TASKS — produce:
1. All source code, scripts, configs needed
2. A README.md explaining how to build and run
3. A TEST_RESULTS.md documenting what was tested manually
4. An IMPLEMENTATION_NOTES.md covering key decisions and why

FOR TEXT TASKS — produce:
1. The answer, argument, or plan — thorough, well-structured, no hedging
2. Make claims only when you can support them. Acknowledge genuine uncertainty.
3. Avoid unstated assumptions.

If this is loop > 1, also read /tmp/implementer-loop/fixer/fix-plan.md to
understand what the fixer identified and address those specific issues.
Do NOT rewrite from scratch — fix only what was identified as broken.

Output everything to /tmp/implementer-loop/implementer/

IMPORTANT: Before declaring done, verify:
- For code: the code compiles or runs without errors, all promised features are
  present, README instructions are accurate
- For text: the answer is consistent, non-circular, and addresses the core
  question directly

End your final message with exactly: IMPLEMENTER_DONE
```

If the subagent returns without `IMPLEMENTER_DONE`, re-spawn it with:
"Previous attempt did not complete. Resume from where you left off, reading
/tmp/implementer-loop/implementer/ to see what exists."

---

## Phase 4: Review

Spawn a subagent:

```
You are the Reviewer for this iteration. Loop: {LOOP_COUNT}.

ORIGINAL TASK:
{the user's request / plan description}

WORKING DIRECTORY: /tmp/implementer-loop/

Read everything in /tmp/implementer-loop/implementer/ thoroughly.

MANDATORY CHECKS — execute all applicable ones:

SKEPTIC PASS (always run first — read only the implementation, not the
original task above):
0. Find the single strongest flaw, gap, internal contradiction, unsupported
   claim, or dangerous unstated assumption in this output. Quote the exact
   phrase. Explain why it is flawed in one sentence. If — after genuinely
   trying — you cannot find a remaining flaw worth raising, output exactly:
   Skeptic: I cannot find a remaining flaw.
   If you do find a flaw, output as:
   Skeptic: FLAW: "[exact quote]" REASON: [one sentence]

CONTEXT-AWARE PASS (for code tasks with a spec):
1. CORRECTNESS — Does it actually solve the stated task?
2. COMPLETENESS — Are all features from the plan present?
3. RUNS WITHOUT ERROR — Execute the code. Does it start and run without crashes?
4. TESTS PASS — Run any tests. Do they pass?
5. EDGE CASES — Try broken inputs. Does it fail gracefully?
6. CODE QUALITY — Are there bugs, anti-patterns, or security issues?
7. DOCUMENTATION — Is it clear how to run and use?

For text tasks, skip checks 3-4 (no code to execute). Instead add:
3T. COHERENCE — Do the claims connect logically? Any contradictions?
4T. COMPLETENESS — Does it address the full scope of the question?

For each applicable check: rate 0–10 with a one-sentence justification.
Compute overall score as weighted average (correctness 30%, completeness 20%,
runs 20%, tests 10%, edge cases 10%, code quality 5%, docs 5%).
For text tasks use: coherence 30%, completeness 20%, correctness 25%,
edge cases 10%, quality 15%.

Write your full assessment to:
/tmp/implementer-loop/reviewer/assessment-loop{LOOP_COUNT}.md

Format requirements:
- Skeptic pass result first
- Rate every applicable dimension explicitly
- For any dimension rated below 7, explain why
- If overall score < 10, list specific gaps in order of severity

End your final message with exactly:
REVIEWER_DONE: SKEPTIC={FLAW|CLEAN} VERDICT={DONE|NEEDS_WORK} SCORE={X}/10
```

If the subagent returns without `REVIEWER_DONE: ... VERDICT=... SCORE=...`,
re-spawn it with the same prompt.

---

## Phase 5: Loop Control

Read `/tmp/implementer-loop/reviewer/assessment-loop{LOOP_COUNT}.md`.

Extract the SKEPTIC, VERDICT, and SCORE fields.

**The Skeptic result overrides:** if the Skeptic pass found a flaw (SKEPTIC=FLAW),
the Reviewer MUST report VERDICT=NEEDS_WORK regardless of other scores. Only
when SKEPTIC=CLEAN AND all dimensions score ≥ 7 can VERDICT=DONE.

### If VERDICT = DONE

Write to `outputs/summary.json`:
- Set `verdict` to "DONE"
- Set `score` to the reported score
- Set `summary` to a one-paragraph description of what was built/produced
- Set `files` to the list of files in /tmp/implementer-loop/implementer/

Print:
```
Implementation complete. Loops: {LOOP_COUNT}. Score: {X}/10. Skeptic: {CLEAN|FLAW}.
Files at: /tmp/implementer-loop/implementer/
```

Output the parseable completion signal:
```
DONE: implementer delivered after {LOOP_COUNT} loop(s), score {X}/10, files at /tmp/implementer-loop/implementer/
```

For text tasks without files, print the final answer from
`/tmp/implementer-loop/implementer/` directly to the conversation and include
it in the DONE signal payload.

### If VERDICT = NEEDS_WORK

Increment `LOOP_COUNT`.

**If LOOP_COUNT > MAX_LOOPS**: write partial summary with `verdict: PARTIAL`
and `gaps` listing all unresolved issues from the last reviewer assessment.
Print the completion signal with `PARTIAL` flag:
```
DONE: implementer stopped after {MAX_LOOPS} loops (cap), score {last_score}/10, partial — gaps remain
```
Include the partial summary.json path in the output.

**Otherwise**: spawn Fixer:

```
You are the Fixer for this iteration. Loop: {LOOP_COUNT}.

ORIGINAL TASK:
{the user's request / plan description}

WORKING DIRECTORY: /tmp/implementer-loop/

Read /tmp/implementer-loop/reviewer/assessment-loop{LOOP_COUNT}.md to
understand what failed. Read any prior fix-plan.md files to avoid repeating fixes.

Your job is to analyze the failures and produce a targeted fix plan.

Write to: /tmp/implementer-loop/fixer/fix-plan.md

Format requirements — be exact:
## Problems Identified
1. [problem description — file:line or specific area]
   Why it fails: [one sentence]
   Fix needed: [specific change, not a vague direction]

## Fix Plan
For each problem above:
- Area: [file or module]
- Change: [the exact change needed]
- Why: [how this addresses the problem]

## Priority
Fix in this order: [1, 2, 3...]

The implementer must read your plan and make exactly the right changes without
guesswork. If a problem is "function X doesn't handle null", the fix is not
"add null handling" — it is "add null check before line Y, return error message Z".

End your final message with exactly: FIXER_DONE
```

After Fixer completes, loop back to **Phase 3: Implementation**.

---

## Composition

This skill orchestrates subagents. It composes naturally with:

**Before Review** (optional pre-flight quality pass):
Invoke `code-smellz` to catch bugs, dead code, and security issues before the
reviewer runs.

**After DONE** (optional post-delivery validation):
For UI work, invoke `frontend-twerkin` to exhaustively test every feature with
Playwright, auto-fixing any failures.

These are optional enhancements. The core loop works without them.

---

## Output Structure

All loop artifacts live under `/tmp/implementer-loop/`:

```
/tmp/implementer-loop/
├── implementer/          ← Implementer's output
│   ├── README.md
│   ├── TEST_RESULTS.md
│   ├── IMPLEMENTATION_NOTES.md
│   └── [source files]
├── reviewer/             ← Reviewer's assessments
│   ├── assessment-loop1.md
│   └── assessment-loop{N}.md
├── fixer/                ← Fixer's plans
│   └── fix-plan.md
└── outputs/              ← Structured summary (written on completion)
    └── summary.json
```

---

## Key Principles

**The reviewer is the gate.** No implementation is delivered until the reviewer
explicitly returns DONE. "Mostly works" is not done.

**Blind pass catches what context excuses.** The Skeptic pass sees only the
output — not the original question. A flaw that only context-aware review
catches is a good catch. A flaw that blind review catches is an *necessary*
catch. The output must stand on its own.

**Fixer writes actionable plans.** "Improve error handling" is not a fix.
"In handle_user_input() at line 47, add try/catch that returns 'Invalid input'
on Exception" is a fix.

**Resumable phases.** Each phase reads prior output. If context compresses,
re-read /tmp/implementer-loop/ to reconstruct state.

**Subagent completion signals are enforced.** If a subagent returns without
its expected signal, re-spawn it with the same prompt. Do not continue without
the signal.

**One fix per loop.** The implementer addresses exactly what the fixer
identified. Re-implementing from scratch wastes prior work.

---

## Completion Signal

When the loop exits (DONE or PARTIAL), the last line of output is always:
```
DONE: implementer delivered after {N} loop(s), score {S}/10, status {DONE|PARTIAL}, files at /tmp/implementer-loop/implementer/
```

Orchestrators can parse this line to determine outcome without reading files.

DONE: implementer skill loaded.
