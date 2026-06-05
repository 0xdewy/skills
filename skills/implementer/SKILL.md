---
name: implementer
description: >-
  Iteratively implements and refines work through an adversarial quality loop.
  Runs Implementer → Correctness Reviewer → Succinctness Reviewer → Fixer until
  the work passes. The Correctness Reviewer does a blind Skeptic pass plus a
  scored correctness pass. The Succinctness Reviewer hunts duplication, dead
  code, over-abstraction, and verbosity. Halted when both reviewers find no
  remaining flaws or the loop cap is reached. TRIGGER on: "implement this
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
  version: 3.0.0
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
    - succinctness
---

# Implementer Skill

An iterative, subagent-driven refinement loop. Work is produced, reviewed
by two independent reviewers (correctness then succinctness), fixed, and
re-reviewed — repeating until both reviewers find nothing left to fix.

## Loop Architecture

```
                                          ┌─────────────────────────────────┐
                                          │                                 │
                                          v                                 │
IMPLEMENTER → CORRECTNESS-REVIEWER → SUCCINCTNESS-REVIEWER → FIXER → IMPLEMENTER → ...
                  │                         │
                  └── [both must return DONE to exit]
```

- **Implementer**: Executes the plan, writes code.
- **Correctness Reviewer**: Two passes — a blind Skeptic pass (sees only the
  output) to find the single strongest flaw, then a scored pass against the
  original plan covering correctness, completeness, runability, tests, edge
  cases, code quality, and documentation.
- **Succinctness Reviewer** (runs sequentially after Correctness Reviewer):
  Hunts duplication, dead code, over-abstraction, verbose idioms, and file
  bloat. Reads the correctness assessment to avoid re-flagging the same issues.
- **Fixer** (only spawned when either reviewer returns NEEDS_WORK): Reads both
  assessments, produces one unified fix plan, then yields back to Implementer.

The blind Skeptic pass is adapted from implement-with-review: the reviewer sees
only the output, not the original question. A truly robust answer should be
defensible on its own terms. This catches unsupported claims, internal
contradictions, and hidden assumptions that context-aware review would excuse.

---

## Phase 1: Understand the Ask

Read whatever the user has provided. Capture:
- The plan, question, or task description
- Any existing files, specs, or context

If no plan or question exists, ask the user to provide one before proceeding.
Set `MAX_LOOPS=8`.

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
  "correctness_score": null,
  "succinctness_score": null,
  "skeptic_result": null,
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

Produce:
1. All source code, scripts, configs needed
2. A README.md explaining how to build and run
3. A TEST_RESULTS.md documenting what was tested manually
4. An IMPLEMENTATION_NOTES.md covering key decisions and why

If this is loop > 1, also read /tmp/implementer-loop/fixer/fix-plan.md to
understand what the fixer identified and address those specific issues.
Do NOT rewrite from scratch — fix only what was identified as broken.

Output everything to /tmp/implementer-loop/implementer/

IMPORTANT: Before declaring done, verify:
- The code compiles or runs without errors
- All promised features are present
- README instructions are accurate

End your final message with exactly: IMPLEMENTER_DONE
```

If the subagent returns without `IMPLEMENTER_DONE`, re-spawn it with:
"Previous attempt did not complete. Resume from where you left off, reading
/tmp/implementer-loop/implementer/ to see what exists."

---

## Phase 4a: Correctness Review

Spawn a subagent:

```
You are the Correctness Reviewer for this iteration. Loop: {LOOP_COUNT}.

ORIGINAL TASK:
{the user's request / plan description}

WORKING DIRECTORY: /tmp/implementer-loop/

Read everything in /tmp/implementer-loop/implementer/ thoroughly.

MANDATORY CHECKS — execute all of them:

SKEPTIC PASS (always run first — read only the implementation output in
/tmp/implementer-loop/implementer/, NOT the original task above):
0. Find the single strongest flaw, gap, internal contradiction, unsupported
   claim, or dangerous unstated assumption in this output. Quote the exact
   phrase. Explain why it is flawed in one sentence. If — after genuinely
   trying — you cannot find a remaining flaw worth raising, output exactly:
   Skeptic: CLEAN
   If you do find a flaw, output as:
   Skeptic: FLAW: "[exact quote]" REASON: [one sentence]

CONTEXT-AWARE PASS:
1. CORRECTNESS — Does it actually solve the stated task?
2. COMPLETENESS — Are all features from the plan present?
3. RUNS WITHOUT ERROR — Execute the code. Does it start and run without crashes?
4. TESTS PASS — Run any tests. Do they pass?
5. EDGE CASES — Try broken inputs. Does it fail gracefully?
6. CODE QUALITY — Are there bugs, anti-patterns, or security issues?
7. DOCUMENTATION — Is it clear how to run and use?

For each applicable check: rate 0–10 with a one-sentence justification.
Compute overall score as weighted average (correctness 30%, completeness 20%,
runs 20%, tests 10%, edge cases 10%, code quality 5%, docs 5%).

THE SKEPTIC PASS OVERRIDES: if Skeptic found a flaw (SKEPTIC=FLAW), your
VERDICT MUST be NEEDS_WORK regardless of other scores. Only when
SKEPTIC=CLEAN AND all dimensions score >= 7 can VERDICT=DONE.

Write your full assessment to:
/tmp/implementer-loop/reviewer/assessment-loop{LOOP_COUNT}.md

Format requirements:
- Skeptic pass result first (Skeptic: CLEAN or Skeptic: FLAW: "..." REASON: ...)
- Rate every applicable dimension explicitly
- For any dimension rated below 7, explain why
- If overall score < 10, list specific gaps in order of severity

End your final message with exactly:
CORRECTNESS_DONE: SKEPTIC={FLAW|CLEAN} VERDICT={DONE|NEEDS_WORK} SCORE={X}/10
```

If the subagent returns without `CORRECTNESS_DONE: ... VERDICT=... SCORE=...`,
re-spawn it with the same prompt.

---

## Phase 4b: Succinctness Review

Spawn a subagent:

```
You are the Succinctness Reviewer for this iteration. Loop: {LOOP_COUNT}.

WORKING DIRECTORY: /tmp/implementer-loop/

Read everything in /tmp/implementer-loop/implementer/ thoroughly.
Also read /tmp/implementer-loop/reviewer/assessment-loop{LOOP_COUNT}.md
to avoid re-flagging issues the Correctness Reviewer already found.

Your job: make this code as minimal as possible without losing functionality.

MANDATORY CHECKS:
1. DUPLICATION — Is the same logic expressed in two or more places? Flag each
   instance with file:line pairs.
2. DEAD CODE — Unused imports, unreachable branches, commented-out blocks,
   variables assigned but never read, functions never called.
3. OVER-ABSTRACTION — Factories that produce a single class, interfaces with
   only one implementation, wrappers that add no value, classes with one
   method that could be a function.
4. VERBOSE IDIOMS — Multi-line boilerplate that a builtin or library function
   already provides. Redundant variable assignments. Unnecessary intermediate
   variables.
5. FILE BLoat — Can any file be merged into another? Can any file be deleted
   entirely without loss?

For each check: rate 0–10 with a one-sentence justification.
If you find nothing to flag on a check, score it 10 and write "Nothing found."

Score is the simple average of the five dimensions.
If any dimension scores below 7, VERDICT=NEEDS_WORK.
If all dimensions score 7+, VERDICT=DONE.

Write your full assessment to:
/tmp/implementer-loop/reviewer/succinctness-loop{LOOP_COUNT}.md

Format requirements:
- Score each dimension (Duplication: X/10 — justification)
- List every DRY violation, dead code block, or over-abstraction with file:line
- For each finding, state what to delete or merge

End your final message with exactly:
SUCCINCTNESS_DONE: VERDICT={DONE|NEEDS_WORK} SCORE={X}/10
```

If the subagent returns without `SUCCINCTNESS_DONE: ... VERDICT=... SCORE=...`,
re-spawn it with the same prompt.

---

## Phase 5: Loop Control

Read both assessment files:
- `/tmp/implementer-loop/reviewer/assessment-loop{LOOP_COUNT}.md`
- `/tmp/implementer-loop/reviewer/succinctness-loop{LOOP_COUNT}.md`

Extract SKEPTIC, VERDICT, SCORE from each.

**Exit condition:** Both reviewers must return VERDICT=DONE.

**If both reviewers return VERDICT=DONE**, the loop exits successfully. Even if
the Succinctness Reviewer returned DONE first and the Correctness Reviewer said
DONE second, both must agree.

### If VERDICT = DONE (both)

Write to `outputs/summary.json`:
- Set `verdict` to "DONE"
- Set `correctness_score` to the correctness reviewer's score
- Set `succinctness_score` to the succinctness reviewer's score
- Set `summary` to a one-paragraph description of what was built
- Set `files` to the list of files in /tmp/implementer-loop/implementer/

Print:
```
Implementation complete. Loops: {LOOP_COUNT}. Correctness: {X}/10. Succinctness: {Y}/10.
Files at: /tmp/implementer-loop/implementer/
```

Output the parseable completion signal:
```
DONE: implementer delivered after {LOOP_COUNT} loop(s), correctness {CX}/10, succinctness {SX}/10, status DONE, files at /tmp/implementer-loop/implementer/
```

### If VERDICT = NEEDS_WORK (either reviewer)

Increment `LOOP_COUNT`.

**If LOOP_COUNT > MAX_LOOPS**: write partial summary with `verdict: PARTIAL`
and `gaps` listing all unresolved issues from both reviewer assessments.
Print the completion signal with `PARTIAL` flag:
```
DONE: implementer stopped after {MAX_LOOPS} loops (cap), correctness {CX}/10, succinctness {SX}/10, status PARTIAL, gaps remain
```
Include the partial summary.json path in the output.

**Otherwise**: spawn Fixer:

```
You are the Fixer for this iteration. Loop: {LOOP_COUNT}.

ORIGINAL TASK:
{the user's request / plan description}

WORKING DIRECTORY: /tmp/implementer-loop/

Read BOTH review files:
- /tmp/implementer-loop/reviewer/assessment-loop{LOOP_COUNT}.md
- /tmp/implementer-loop/reviewer/succinctness-loop{LOOP_COUNT}.md

Also read any prior fix-plan.md files to avoid repeating fixes.

Your job is to analyze all failures from both reviewers and produce ONE
unified fix plan. Address correctness issues and succinctness issues together.

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

## Output Structure

All loop artifacts live under `/tmp/implementer-loop/`:

```
/tmp/implementer-loop/
├── implementer/              ← Implementer's output
│   ├── README.md
│   ├── TEST_RESULTS.md
│   ├── IMPLEMENTATION_NOTES.md
│   └── [source files]
├── reviewer/                 ← Both reviewers' assessments
│   ├── assessment-loop1.md
│   ├── assessment-loop{N}.md
│   ├── succinctness-loop1.md
│   └── succinctness-loop{N}.md
├── fixer/                    ← Fixer's plans
│   └── fix-plan.md
└── outputs/                  ← Structured summary (updated each loop)
    └── summary.json
```

---

## Key Principles

**The reviewers are the gates.** No implementation is delivered until both the
Correctness Reviewer and the Succinctness Reviewer explicitly return DONE.
"Mostly works" or "mostly minimal" is not done.

**Blind pass catches what context excuses.** The Skeptic pass sees only the
output — not the original question. A flaw that only context-aware review
catches is a good catch. A flaw that blind review catches is a *necessary*
catch. The output must stand on its own.

**Correctness first, then succinctness.** The Succinctness Reviewer runs after
and reads the correctness assessment. This prevents duplicate flagging and
ensures minimalism is applied to already-correct code.

**Fixer writes actionable plans.** "Improve error handling" is not a fix.
"In handle_user_input() at line 47, add try/catch that returns 'Invalid input'
on Exception" is a fix. The Fixer reads both reviews and produces one plan.

**Resumable phases.** Each phase reads prior output. If context compresses,
re-read /tmp/implementer-loop/ to reconstruct state.

**Subagent completion signals are enforced.** If a subagent returns without
its expected signal, re-spawn it with the same prompt. Do not continue without
the signal.

**Minimalism is a correctness concern.** Bloated code is harder to review,
harder to maintain, and hides bugs. The Succinctness Reviewer is not optional —
it runs every loop alongside the Correctness Reviewer.

---

## Completion Signal

When the loop exits (DONE or PARTIAL), the last line of output is always:
```
DONE: implementer delivered after {N} loop(s), correctness {CX}/10, succinctness {SX}/10, status {DONE|PARTIAL}, files at /tmp/implementer-loop/implementer/
```

Orchestrators can parse this line to determine outcome without reading files.
