---
name: one-shot-project
description: >-
  Multi-agent software project builder. Spawns 3 parallel implementer agents
  (each with a dedicated reviewer), iterated until a tester/runner confirms
  correctness, then validated by a project manager — looping until truly done.
  TRIGGER on: "one-shot project", "build three competing implementations",
  "create a complete app/tool/service from scratch with parallel approaches",
  "full project from scratch with multiple solution paths", "compare competing
  implementations", or explicit requests for a multi-agent project build.
  SKIP on: single-file edits, small bug fixes, code explanations, questions
  about existing code, simple refactors, user-provided implementation plans that
  should be executed directly, incremental feature work, tasks with one obvious
  solution path.
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

Load `skills/common/patterns/orchestration.md`,
`skills/common/patterns/execution-contract.md`, and
`skills/common/parallel-agents-guide.md` before starting. Follow the shared
contract: create directories before dispatch, assign disjoint write roots,
validate every expected artifact before the next phase, and end the overall run
with a parseable `DONE:` line.

If subagents are unavailable, run the implementer/reviewer/tester/PM roles
sequentially into the same directories and state that the run was serialized.

Load `skills/common/patterns/scaling.md` for the effort-scaling gate below.

## Effort Scaling

This skill's default tier is **full** (competing approaches is its purpose).
Pick a tier before Phase 0 and state it in one line:

- **lite** — a single small component or a one-step build: implement directly
  with one implementer and one self-check; no critic, no PM loop.
- **standard** — a normal multi-file project: 3 implementers + critics, one PM round.
- **full** — large/ambitious project, or an explicit "compare approaches" request:
  the full fleet and PM loop.

Escalate down when the task is clearly small — current models (Opus 4.5+)
over-spawn, and you should not stand up 3 competing builds for a one-screen task.

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
                   ↓
Phase 5:  Orchestrator Verification
              ├── PASS → deliver winner
              └── FAIL → targeted revision → Phase 3 (max 5 PM rounds)
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
2. Run the **Orchestrator Verification Gate** below. Do not copy or deliver the
   winner until this gate passes.
3. Copy the winner to `$OUTPUT_ROOT/final/` by default only after verification.
4. If the user explicitly requested a project-root or existing output path,
   produce a conflict list and ask before overwriting any existing file.
5. Proceed to the Completion Report

### Orchestrator Verification Gate

The PM is an advisor, not an authority. The top-level orchestrator must
independently verify the chosen implementation before delivery:

1. Read the original acceptance criteria from Phase 0.
2. Read `$OUTPUT_ROOT/test-results/run-{PM_ROUND}.json` and confirm the winner
   has `status=pass`, `score >= 7`, and no unresolved critical review findings.
3. Run the winner's documented demo command (`run.sh` or README command) yourself.
4. Run its tests if a `tests/` directory or test command exists.
5. Inspect the produced output against the original task. If the output does not
   actually satisfy the task, treat verification as failed even if the PM said
   DONE.
6. Write `$OUTPUT_ROOT/pm-decisions/orchestrator-verification-{PM_ROUND}.md`:
   ```
   STATUS: PASS | FAIL
   WINNER: impl_a | impl_b | impl_c
   COMMANDS_RUN:
     - <command> -> <pass|fail>
   ACCEPTANCE_CHECK:
     - <criterion> -> <pass|fail>
   BLOCKERS:
     - <specific blocker, or "none">
   ```

If verification fails and `PM_ROUND < MAX_PM_ROUNDS`, convert the failure into
targeted guidance for the same winner and follow the `STATUS=ITERATE` path. If
verification fails at the round cap, deliver `PARTIAL` and clearly list the
remaining blockers.

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

1. Read all test results, pick the implementation with the highest score.
2. Run the Orchestrator Verification Gate. If it fails, still copy the best
   available implementation to `$OUTPUT_ROOT/final/`, but mark the run `PARTIAL`.
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

Location: $OUTPUT_ROOT/final/ (winner copied from $OUTPUT_ROOT/impl-{winner}/)

Why this implementation won:
{PM RATIONALE from final decision}

Approaches compared:
- A (Minimal/Elegant):     {one line from IMPLEMENTATION_SUMMARY.md}
- B (Robust/Defensive):    {one line from IMPLEMENTATION_SUMMARY.md}
- C (Feature-Complete):    {one line from IMPLEMENTATION_SUMMARY.md}

Verification:
{PASS/PARTIAL plus one sentence from orchestrator-verification-{PM_ROUND}.md}

DONE: $OUTPUT_ROOT/final/ — winner impl_{a|b|c}, PM rounds {PM_ROUND}, verification {PASS|FAIL}, status {DONE|PARTIAL}
```

---

## Orchestration Notes

The shared contract (`orchestration.md`, `execution-contract.md`) governs
resumability, re-spawning agents that omit their completion signal, and the
orchestrator owning final verification over the PM. The notes below are
specific to this skill:

**Parallelism:** Make 3 Agent tool calls in a single message to run implementers
or reviewers in parallel. Never run them sequentially — that defeats the purpose.

**Philosophy diversity:** The three implementer angles (minimal, robust,
feature-complete) are intentional. Do not collapse them. The tension between
approaches surfaces the best final solution, and the PM should weigh which
philosophy fits the task when selecting the winner.

**Output directory as shared memory:** All agent communication flows through
`$OUTPUT_ROOT/`. Never pass large blobs of code between agents through prompts —
write to disk and tell the next agent where to read from.
