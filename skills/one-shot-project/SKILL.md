---
name: one-shot-project
description: >-
  Multi-agent software project builder. Spawns 3 parallel implementer agents
  (each with a dedicated reviewer), iterated until a tester/runner confirms
  correctness, then validated by a project manager — looping until truly done.
  TRIGGER on: "one-shot project", "build this project", "implement X from scratch",
  "create a complete app/tool/service", "build a working version of", any request
  for a full working implementation where quality matters and multiple solution
  approaches are worth exploring in parallel.
  SKIP on: single-file edits, small bug fixes, code explanations, questions
  about existing code, simple refactors, tasks with one obvious solution path.
license: MIT
metadata:
  author: iamky1e
  version: 1.0.0
  category: meta
  tags:
    - multi-agent
    - orchestration
    - project-builder
    - parallel
    - iterative
---

# One-Shot Project

Runs a fleet of 8 specialized agents to implement any software project from
scratch. Three implementers explore different design angles, each reviewed by
a dedicated critic, tested by a runner, and validated by a project manager.
The PM loops until it is satisfied.

```
Phase 1:  Impl-A ─┐
          Impl-B ─┤ (parallel)
          Impl-C ─┘
                   ↓
Phase 2:  Rev-A ─┐
          Rev-B ─┤ (parallel) → revisions → re-review (max 3 rounds)
          Rev-C ─┘
                   ↓
Phase 3:  Tester/Runner
                   ↓
Phase 4:  Project Manager
              ├── DONE → deliver winner
              └── ITERATE → targeted revision → Phase 3 (max 5 PM rounds)
```

---

## Phase 0: Setup

Before spawning any agents:

1. **Parse the request** into a clear one-paragraph spec. Identify:
   - What the code must DO (observable behavior)
   - What success looks like (acceptance criteria)
   - Language/stack if specified; otherwise pick what fits best

2. **Create output directories — determine appropriate location first:**
   Check if the current working directory appears to be a project root (look for `README.md`, `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `Makefile`, `*.sln`, `BUILD.bazel`).
   - If **yes** (project directory): use `./one-shot-output/` as the root
   - If **no** (empty dir, skills repo, etc.): use `/tmp/one-shot-output/` as the root
   
   Let `OUTPUT_ROOT` be whichever path was chosen. Then:
   ```bash
   mkdir -p "$OUTPUT_ROOT"/{impl-a,impl-b,impl-c,reviews,test-results,pm-decisions}
   ```
   
   All implementer prompts reference `./one-shot-output/` — when running from a non-project directory (OUTPUT_ROOT is `/tmp/one-shot-output/`), substitute `$OUTPUT_ROOT` in place of `./one-shot-output/` in every subagent prompt. Reviewers, tester, and PM reference the same root.

3. **Initialize state:** `PM_ROUND=1`, `MAX_PM_ROUNDS=5`

---

## Phase 1: Parallel Implementation

Spawn all 3 implementers **in a single message** (3 Agent tool calls at once).
Each gets a distinct design philosophy to guarantee diverse approaches.

### Implementer A — Minimal/Elegant

Prompt:
```
You are Implementer A in a one-shot project build.

TASK:
{paste the full user request here}

PHILOSOPHY: Minimal and elegant. Fewest files, fewest lines, cleanest design.
Prioritize simplicity and readability over features. If in doubt, leave it out.

OUTPUT DIRECTORY: $OUTPUT_ROOT/impl-a/

Deliver ALL of the following inside $OUTPUT_ROOT/impl-a/ only:
1. Full working implementation
2. README.md — what it does, how to run it, dependencies
3. IMPLEMENTATION_SUMMARY.md — approach, key decisions, trade-offs
4. run.sh (or equivalent) that demonstrates the implementation working

Do NOT modify anything outside $OUTPUT_ROOT/impl-a/.
End your final message with exactly: IMPLEMENTER_A_DONE
```

### Implementer B — Robust/Defensive

Prompt:
```
You are Implementer B in a one-shot project build.

TASK:
{paste the full user request here}

PHILOSOPHY: Robust and defensive. Comprehensive error handling, input
validation, edge cases covered, logging, graceful failure. Production-ready
reliability over elegance.

OUTPUT DIRECTORY: $OUTPUT_ROOT/impl-b/

Deliver ALL of the following inside $OUTPUT_ROOT/impl-b/ only:
1. Full working implementation
2. README.md — what it does, how to run it, dependencies
3. IMPLEMENTATION_SUMMARY.md — approach, key decisions, trade-offs
4. run.sh (or equivalent) that demonstrates the implementation working

Do NOT modify anything outside $OUTPUT_ROOT/impl-b/.
End your final message with exactly: IMPLEMENTER_B_DONE
```

### Implementer C — Feature-Complete

Prompt:
```
You are Implementer C in a one-shot project build.

TASK:
{paste the full user request here}

PHILOSOPHY: Feature-complete and extensible. Most fully-featured, anticipates
likely follow-on needs. Good abstractions, extensible design, tests included.

OUTPUT DIRECTORY: $OUTPUT_ROOT/impl-c/

Deliver ALL of the following inside $OUTPUT_ROOT/impl-c/ only:
1. Full working implementation
2. README.md — what it does, how to run it, dependencies
3. IMPLEMENTATION_SUMMARY.md — approach, key decisions, trade-offs
4. run.sh (or equivalent) that demonstrates the implementation working
5. tests/ directory with at least basic test cases

Do NOT modify anything outside $OUTPUT_ROOT/impl-c/.
End your final message with exactly: IMPLEMENTER_C_DONE
```

Wait for all 3 completion signals before moving to Phase 2.

---

## Phase 2: Parallel Review

Set `REVIEW_ROUND=1`. Spawn all 3 reviewers **in a single message**.

### Reviewer prompt template

Use this for each of A, B, C — substituting the slot letter and round number:

```
You are Reviewer for Implementer {A/B/C} in a one-shot project build.

ORIGINAL TASK:
{paste the full user request here}

IMPLEMENTATION TO REVIEW: $OUTPUT_ROOT/impl-{a/b/c}/

Read every file in that directory thoroughly, then write a structured review:

1. CORRECTNESS — Does it actually solve the task? List any gaps.
2. CRITICAL ISSUES — Bugs, crashes, wrong logic (must fix)
3. MAJOR ISSUES — Missing error handling, flawed structure, likely failures
4. MINOR ISSUES — Style, naming, clarity
5. STRENGTHS — What's done well
6. QUALITY SCORE — 0–10
7. VERDICT — NEEDS_WORK | READY

For each issue provide: file path + line range, what's wrong, specific fix.

Write your review to:
$OUTPUT_ROOT/reviews/review-{a/b/c}-r{REVIEW_ROUND}.md

End your final message with exactly:
REVIEW_{A/B/C}_DONE: {VERDICT} {SCORE}/10
```

### After reviews complete

For each implementation where VERDICT=NEEDS_WORK **or** score < 7:

Spawn a **revision agent** for that implementer (revisions for different
implementers can run in parallel):

```
You are Implementer {A/B/C} revising your implementation based on reviewer feedback.

ORIGINAL TASK:
{paste the full user request here}

YOUR IMPLEMENTATION: $OUTPUT_ROOT/impl-{a/b/c}/
REVIEW FEEDBACK:     $OUTPUT_ROOT/reviews/review-{a/b/c}-r{REVIEW_ROUND}.md

Read your implementation and the review. Apply ALL critical and major fixes.
Apply minor fixes where practical.

Edit files in-place within $OUTPUT_ROOT/impl-{a/b/c}/ only.
Do NOT modify anything outside that directory.
End your final message with exactly: REVISION_{A/B/C}_DONE
```

After all revisions complete, increment REVIEW_ROUND and run another review
pass for the revised implementations (same reviewer prompt, updated round number).

**Repeat up to 3 review rounds per implementer.** After 3 rounds, proceed to
Phase 3 regardless of verdict — the tester is the final judge of correctness.

---

## Phase 3: Tester/Runner

Spawn a **single tester agent**:

```
You are the Tester/Runner for a one-shot project build. PM round: {PM_ROUND}.

ORIGINAL TASK:
{paste the full user request here}

Test all three implementations:
  $OUTPUT_ROOT/impl-a/
  $OUTPUT_ROOT/impl-b/
  $OUTPUT_ROOT/impl-c/

For EACH implementation:
1. Read README.md to understand how to run it
2. Install dependencies per README instructions
3. Execute run.sh (or equivalent)
4. Capture stdout/stderr verbatim
5. Run tests/ if present and capture results
6. Judge: does the output correctly solve the original task?

Write results to: $OUTPUT_ROOT/test-results/run-{PM_ROUND}.json

Use exactly this JSON schema:
{
  "round": {PM_ROUND},
  "impl_a": {
    "status": "pass" | "fail" | "error",
    "stdout_summary": "<first 500 chars of stdout>",
    "stderr_summary": "<errors if any>",
    "tests_passed": 0,
    "tests_total": 0,
    "score": 0,
    "notes": "<what worked, what didn't>"
  },
  "impl_b": { ... },
  "impl_c": { ... },
  "recommended": "impl_a" | "impl_b" | "impl_c" | "none",
  "overall_done": true | false,
  "summary": "<one paragraph>"
}

End your final message with exactly:
TESTER_DONE: overall_done={true|false} recommended={impl_a|impl_b|impl_c|none}
```

---

## Phase 4: Project Manager Decision

Spawn a **single PM agent**:

```
You are the Project Manager for a one-shot project build. PM round: {PM_ROUND}.

ORIGINAL TASK:
{paste the full user request here}

Review all available information:
  Test results:     $OUTPUT_ROOT/test-results/run-{PM_ROUND}.json
  Implementations:  $OUTPUT_ROOT/impl-{a,b,c}/IMPLEMENTATION_SUMMARY.md
  Latest reviews:   $OUTPUT_ROOT/reviews/ (read the highest round numbers)
  Prior decisions:  $OUTPUT_ROOT/pm-decisions/ (if any)

Decide: is any implementation truly finished and correct for the user's task?

DONE criteria (all must hold):
  - Tester reports status=pass with score >= 7
  - No critical issues remain in the latest review
  - Output actually solves the original task

Write your decision to: $OUTPUT_ROOT/pm-decisions/decision-{PM_ROUND}.md

Use EXACTLY this format (the orchestrator parses these fields):
---
STATUS: DONE | ITERATE
WINNER: impl_a | impl_b | impl_c | none
TARGET: impl_a | impl_b | impl_c
GUIDANCE: |
  <specific, actionable instructions for the targeted implementer>
  <what to fix, why it's wrong, what correct behavior looks like>
  <be concrete — name files, functions, expected outputs>
RATIONALE: <why you made this decision>
---

End your final message with exactly:
PM_DONE: STATUS={DONE|ITERATE} WINNER={impl_x|none} TARGET={impl_x|none}
```

---

## Phase 5: Loop Control

Parse the PM completion signal and route:

### If STATUS=DONE

1. Note the WINNER directory (`$OUTPUT_ROOT/impl-{winner}/`)
2. Copy the winner to the project root (or user's specified output path)
3. Proceed to the Completion Report

### If STATUS=ITERATE and PM_ROUND < MAX_PM_ROUNDS

1. Increment `PM_ROUND`
2. Read TARGET and GUIDANCE from the latest PM decision file
3. Spawn a **targeted revision agent** for TARGET:

   ```
   You are Implementer {A/B/C} applying targeted fixes from the project manager.

   ORIGINAL TASK:
   {paste the full user request here}

   YOUR IMPLEMENTATION: $OUTPUT_ROOT/impl-{target}/
   PM GUIDANCE (Round {PM_ROUND}):
   {paste the GUIDANCE block from the PM decision verbatim}

   Apply exactly what the PM asks. Fix only what's specified — do not refactor
   or rewrite beyond the guidance scope.

   Edit files in-place within $OUTPUT_ROOT/impl-{target}/ only.
   End your final message with exactly: PM_REVISION_DONE
   ```

4. After revision, run **one review round** for the revised implementation only
   (same reviewer prompt, set REVIEW_ROUND to latest + 1)
5. Return to **Phase 3** with the updated PM_ROUND

### If STATUS=ITERATE and PM_ROUND >= MAX_PM_ROUNDS

1. Read all test results, pick the implementation with the highest score
2. Copy it to the project root
3. Tell the user: max rounds reached, here's the best available, here's what
   remains unresolved, here's what manual work is still needed

---

## Completion Report

Present this to the user:

```
## One-Shot Project Complete

Winner:      Implementer {A/B/C} — {Minimal/Robust/Feature-Complete}
PM Rounds:   {PM_ROUND}
Final Score: {score}/10

What was built:
{one paragraph from the winner's IMPLEMENTATION_SUMMARY.md}

Location: $OUTPUT_ROOT/impl-{winner}/ (copied to project root)

Why this implementation won:
{PM RATIONALE from final decision}

Approaches compared:
- A (Minimal/Elegant):     {one line from IMPLEMENTATION_SUMMARY.md}
- B (Robust/Defensive):    {one line from IMPLEMENTATION_SUMMARY.md}
- C (Feature-Complete):    {one line from IMPLEMENTATION_SUMMARY.md}
```

---

## Orchestration Notes

**Parallelism:** Make 3 Agent tool calls in a single message to run implementers
or reviewers in parallel. Never run them sequentially — that defeats the purpose.

**State tracking:** Keep PM_ROUND and REVIEW_ROUND as simple variables in your
working context. If the conversation compresses, re-read the pm-decisions/
directory to reconstruct state.

**Agent failures:** If an agent returns without the expected completion signal,
re-spawn it with a note: "Previous attempt did not complete. Resume from where
you left off, reading $OUTPUT_ROOT/impl-{x}/ to see what exists."

**PM authority:** The PM is the final arbiter. Trust its DONE verdict even if
the tester score is borderline — it reads the full picture.

**Philosophy diversity:** The three implementer angles (minimal, robust,
feature-complete) are intentional. Do not collapse them. The tension between
approaches surfaces the best final solution and the PM should weigh which
philosophy fits the task when selecting the winner.

**Output directory as shared memory:** All agent communication flows through
`$OUTPUT_ROOT/`. It is the single source of truth. Never pass large blobs
of code between agents through prompts — always write to disk and tell the next
agent where to read from.
