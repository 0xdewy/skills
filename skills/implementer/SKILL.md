---
name: implementer
description: >-
  Iteratively implements a plan and validates the result through an
  Implementer → Reviewer → Fixer loop until the work reaches 10/10 quality.
  TRIGGER on: "implement this plan", "build it", "write the code", "start
  implementation", "implement the feature", "implement it", "begin build",
  "start building", "carry out the plan", "execute the plan".
  SKIP on: casual mentions of implementation, questions about how to implement
  without a plan to execute, single-line code generation requests.
license: MIT
metadata:
  author: opencode
  version: 1.1.0
  category: productivity
  tags:
    - implementation
    - iterative
    - review
    - quality
    - subagent
    - orchestration
---

# Implementer Skill

An iterative, subagent-driven implementation skill. The loop runs until a
reviewer confirms the work is 10/10 ready for the user.

## Loop Architecture

```
IMPLEMENTER → REVIEWER → [if not 10/10] → FIXER → IMPLEMENTER → REVIEWER → ...
                                                              ↑
                                              (loop until verdict = DONE or MAX_LOOPS)
```

- **Implementer**: Executes the plan, writes code, produces artifacts
- **Reviewer**: Analyzes, runs tests, runs code, renders verdict
- **Fixer** (only spawned on non-DONE verdict): Analyzes failures, produces a
  targeted fix plan, then yields back to Implementer

---

## Phase 1: Understand the Ask

Read whatever the user has provided. Capture:
- The plan or task description
- Any existing files, specs, or context
- Output location expectations

If no plan exists, ask the user to provide one before proceeding.

---

## Phase 2: Initialize

Create working directory and set loop state:

```bash
mkdir -p /tmp/implementer-loop/{implementer,reviewer,fixer,outputs}
```

Set `LOOP_COUNT=1`, `MAX_LOOPS=8`.

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

## Phase 3: Implementer

Spawn a subagent:

```
You are the Implementer for this iteration. Loop: {LOOP_COUNT}.

ORIGINAL TASK:
{the user's request / plan description}

WORKING DIRECTORY: /tmp/implementer-loop/

Read any existing context files in /tmp/implementer-loop/ before starting.

Your job is to implement the plan fully. Produce:

1. All source code, scripts, configs needed
2. A README.md explaining how to build and run
3. TEST_RESULTS.md documenting what you tested manually
4. An IMPLEMENTATION_NOTES.md covering key decisions and why

If this is loop > 1, also read /tmp/implementer-loop/fixer/fix-plan.md to
understand what the fixer identified and address those specific issues.
Do NOT re-implement from scratch — fix only what was broken.

Output everything to /tmp/implementer-loop/implementer/

IMPORTANT: Before declaring done, verify:
- The code compiles or runs without errors
- README instructions are accurate and complete
- All promised features are present

End your final message with exactly: IMPLEMENTER_DONE
```

If the subagent returns without `IMPLEMENTER_DONE`, re-spawn it with:
"Previous attempt did not complete. Resume from where you left off, reading
/tmp/implementer-loop/implementer/ to see what exists."

---

## Phase 4: Reviewer

Spawn a subagent:

```
You are the Reviewer for this iteration. Loop: {LOOP_COUNT}.

ORIGINAL TASK:
{the user's request / plan description}

WORKING DIRECTORY: /tmp/implementer-loop/

Read everything in /tmp/implementer-loop/implementer/ thoroughly.

Your job is to critically analyze the implementation and determine if it is
10/10 ready for the user.

MANDATORY CHECKS — execute all of these, not just code inspection:
1. CORRECTNESS — Does it actually solve the stated task?
2. COMPLETENESS — Are all features from the plan present?
3. RUNS WITHOUT ERROR — Execute the code. Does it start and run without crashes?
4. TESTS PASS — Run any tests. Do they pass?
5. EDGE CASES — Try broken inputs. Does it fail gracefully?
6. CODE QUALITY — Are there bugs, anti-patterns, or security issues?
7. DOCUMENTATION — Is it clear how to run and use?

For each check: rate 0–10 with a one-sentence justification.
Compute overall score as the weighted average (correctness 30%, completeness 20%,
runs without error 20%, tests pass 10%, edge cases 10%, code quality 5%, docs 5%).

Write your full assessment to:
/tmp/implementer-loop/reviewer/assessment-loop{LOOP_COUNT}.md

Format requirements:
- Rate every dimension explicitly
- For any dimension rated below 7, explain why
- If overall score < 10, list specific gaps in order of severity

End your final message with exactly:
REVIEWER_DONE: VERDICT={DONE|NEEDS_WORK} SCORE={X}/10
```

If the subagent returns without `REVIEWER_DONE: VERDICT=... SCORE=...`,
re-spawn it with the same prompt.

---

## Phase 5: Loop Control

Read `/tmp/implementer-loop/reviewer/assessment-loop{LOOP_COUNT}.md`.

Extract the VERDICT and SCORE lines.

### If VERDICT = DONE

Write to `outputs/summary.json`:
- Set `verdict` to "DONE"
- Set `score` to the reported score
- Set `summary` to a one-paragraph description of what was built
- Set `files` to the list of files in /tmp/implementer-loop/implementer/

Print:
```
Implementation complete. Loops: {LOOP_COUNT}. Score: {X}/10.
Files at: /tmp/implementer-loop/implementer/
```

Output the parseable completion signal:
```
DONE: implementer delivered after {LOOP_COUNT} loop(s), score {X}/10, files at /tmp/implementer-loop/implementer/
```

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

After Fixer completes, loop back to **Phase 3: Implementer**.

---

## Composition

This skill orchestrates subagents. It composes naturally with:

**Before Review** (optional pre-flight quality pass):
Invoke `code-smellz` to catch bugs, dead code, and security issues before the
reviewer runs. Call it like:
```
Before spawning the reviewer, run code-smellz on /tmp/implementer-loop/implementer/
```

**After DONE** (optional post-delivery validation):
For UI work, invoke `frontend-twerkin` to exhaustively test every feature with
Playwright, auto-fixing any failures:
```
After delivery, run frontend-twerkin on the delivered UI
```

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