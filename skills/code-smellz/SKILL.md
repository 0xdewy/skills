---
name: code-smellz
description: >-
  Deep-cleans a codebase using four parallel subagents — one hunting bugs, one
  finding code to simplify or delete, one spotting architectural and logical
  improvements, one auditing security vulnerabilities and CVEs. Applies
  findings, runs tests to verify correctness, and iterates until the code is
  as clean and optimal as it can get. TRIGGER on: "stinky code", "clean up
  this codebase", "improve this code", "find bugs and fix them", "code quality
  pass", "refactor this project", "remove dead code", "optimize this codebase",
  "code smells", "make this code better", "run code-smellz". SKIP on:
  explaining what code does without changing it, single-file reviews that don't
  require subagents, security-only audits (use security-review instead),
  documentation-only requests.
license: MIT
metadata:
  author: iamky1e
  version: 1.0.0
  category: meta
  tags:
    - refactoring
    - code-quality
    - bugs
    - optimization
    - multi-agent
---

## What This Does

Four subagents run in parallel, each with a specific mandate:

| Agent | Finds |
|-------|-------|
| **Bug Hunter** | Crashes, incorrect logic, unhandled errors, type errors, security issues |
| **Code Minimizer** | Dead code, duplication, verbosity, unused imports, redundant abstractions |
| **Architecture Optimizer** | Inefficient algorithms, N+1 queries, bad data structures, missing caching |
| **Security Auditor** | Dependency CVEs, hardcoded secrets, insecure function usage, missing input sanitization |

After all three report, changes are applied, tests run, and the loop repeats
until nothing meaningful remains — or 5 iterations, whichever comes first.

## Prerequisites

- Python 3 (for helper scripts)
- A test suite is strongly preferred. Without tests, correctness is unverifiable.
- The project should be in a git repository so changes are reversible.

---

## Phase 0: Codebase Discovery

**If `/tmp/stinky-output/` already exists**, archive it first:
```bash
mv /tmp/stinky-output /tmp/stinky-output.prev 2>/dev/null || true
mkdir -p /tmp/stinky-output
```

**Read the project's stated goal** from (in priority order):
- `CLAUDE.md` — project notes
- `README.md` — first 30 lines
- `package.json` → `description` field
- `pyproject.toml` → `[project] description`
- If nothing: "goal unknown — inferred from code structure"

**Detect the test runner:**
```bash
python3 $SKILL_DIR/scripts/detect_runner.py . > /tmp/stinky-output/runner.json
cat /tmp/stinky-output/runner.json
```

**Establish baseline LOC:**
```bash
python3 $SKILL_DIR/scripts/measure_loc.py . > /tmp/stinky-output/baseline_loc.json
```

**Run the test suite once** using the command from `runner.json`. Record whether
tests pass and the total count. If no test runner is found, note that and
proceed — changes will need manual verification.

**Check git status.** If the project is not a git repository, warn the user:
> "This project is not tracked by git. Changes cannot be easily reverted.
> Continue? (y/n)"
If confirmed, proceed. If no git repo and no confirmation, stop.

**Save session state:**
```json
// stinky-output/session.json
{
  "iteration": 0,
  "codebase_goal": "<one sentence>",
  "baseline_loc": <number>,
  "baseline_tests": "<pass_rate or 'no tests'>",
  "runner_command": "<command or null>",
  "history": []
}
```

---

## Phase 1: Dispatch Three Subagents in Parallel

Read `references/subagent-prompts.md` for the full prompt templates.

Fill in the template variables:
- `{{codebase_goal}}` — from session.json
- `{{file_list}}` — all source files (exclude: `.git/`, `node_modules/`,
  `__pycache__/`, `dist/`, `build/`, `target/`, `.venv/`, `coverage/`)
- `{{iteration}}` — current iteration number

Spawn all four agents **simultaneously**. Each receives a read-only mandate
and writes one JSON file to `/tmp/stinky-output/`:

  ```
  /tmp/stinky-output/findings-bugs.json
  /tmp/stinky-output/findings-simplify.json
  /tmp/stinky-output/findings-arch.json
  /tmp/stinky-output/security-audit.json
  ```

for the full step-by-step mandate. Write output to `/tmp/stinky-output/security-audit.json`
and raw dependency scanner output to `/tmp/stinky-output/dep-audit-raw.json`.

**Critical:** agents READ and REPORT only. No file changes in Phase 1.

Wait for all four to complete before moving to Phase 2.

---

## Phase 2: Triage and Plan

Read all three findings files and build a unified, prioritized action list.

**Priority rules:**
- HIGH severity findings → apply this iteration
- MEDIUM severity → apply unless the change is risky (touches public API, shared
  utility, or complex logic — flag those for human review instead)
- LOW severity → apply only if no HIGH/MEDIUM remain

**Conflict resolution:**
- If Bug Hunter says "keep this code" and Minimizer says "delete it" → keep it
- If two agents touch the same lines → apply the higher-severity finding first,
  skip the other
- If a finding requires business context you don't have → skip it, log as
  "needs human review"

Print the triage summary before applying anything:
```
=== Iteration N Triage ===
  Bugs found:         3 high, 2 medium, 1 low
  Simplifications:    0 high, 5 medium, 3 low
  Architecture:       1 high, 2 medium, 0 low
  Security:           N critical, N high, N medium
  Applying this round: 9 changes
  Skipping (conflicts/risky): 2 changes
```

**CRITICAL security findings** (CVE with known exploit, hardcoded secret in a
committed file) apply first in a standalone commit before any other changes:
`git commit -am "security: fix critical CVE / remove hardcoded secret"`.
Log with `"change_type": "security_fix"`.

**If all findings are LOW or zero across all four agents: skip to Phase 6.**

---

## Phase 3: Apply Changes

Apply each planned change using file edits. Work in dependency order:
1. Bug fixes that affect shared utilities (these changes affect many callers)
2. Bug fixes in individual files
3. Architectural changes (restructuring may create opportunities for simplification)
4. Simplifications (easiest to apply once bugs and structure are fixed)

Log each change in `/tmp/stinky-output/session.json` under `history`:
```json
{
  "iteration": N,
  "change_type": "bug_fix|simplify|arch",
  "file": "path/to/file",
  "description": "what changed and why",
  "reverted": false
}
```

Do not run tests between every individual change — batch them for Phase 4.
However, if a change is large or touches a core module, commit what you have
first, then apply the risky change alone so a test failure is easy to isolate.

---

## Phase 4: Verify

Run the full test suite:
```bash
<runner_command from session.json>
```

### Tests pass
- Measure new LOC:
  ```bash
  python3 $SKILL_DIR/scripts/measure_loc.py . > /tmp/stinky-output/iter_N_loc.json
  ```
- Compute delta: `baseline_loc - current_loc` lines removed
- Print iteration summary:
  ```
  Iteration N complete: 9 changes applied, 3 bugs fixed, 47 lines removed
  Tests: 42/42 passing
  ```
- Optionally commit: `git commit -am "code-smellz: iteration N — N fixes, N lines removed"`

### Tests fail
1. Identify which change broke the test (use `git diff` or binary search by reverting changes one at a time)
2. Revert that specific change
3. Mark it `"reverted": true` in session.json
4. Re-run tests to confirm green
5. Note what the failing change was — it may need manual attention

If reverting leaves you with fewer than 2 successful changes this iteration,
that counts as a plateau (see Phase 5).

### No tests exist
Verify core functionality manually:
- Run the main entry point or example from the README
- Confirm it produces the expected output
- Note in session.json: "verified: manual run, no test suite"

---

## Phase 5: Convergence Decision

Check in order:

1. **Clean** — re-run the three subagents (same as Phase 1) and check if all
   three return zero HIGH/MEDIUM findings → emit final report and stop
2. **Plateau** — fewer than 2 changes were successfully applied this iteration → stop
3. **Limit** — iteration count has reached 5 → stop
4. **Unstable** — more than 40% of changes this iteration were reverted → stop
   and flag: "Codebase may be too tightly coupled for safe automatic refactoring
   in this area. Remaining issues flagged for human review."

If none apply: increment `session.json iteration` and return to Phase 1.

---

## Phase 6: Final Report

Read `/tmp/stinky-output/session.json` and all `iter_*_loc.json` files. Print:

```
╔══════════════════════════════════╗
║       STINKY-CODE REPORT         ║
╚══════════════════════════════════╝
Iterations completed : N
Starting LOC         : XXXX
Final LOC            : YYYY  (-ZZ%)
Tests                : NN/NN passing  (was: NN/NN)

Changes applied:
  Bugs fixed                  : N
  Lines removed (simplify)    : N
  Architecture improvements   : N
  Security issues fixed       : N  (CVEs patched, secrets removed)
  Total changes               : N

Changes reverted (broke tests): N

Remaining items (not applied):
  [medium] path/to/file — description
  [low]    path/to/file — description

Recommendation:
  <"Code is clean." | "N items require human review." | specific advice>
```

Emit: `DONE: /tmp/stinky-output/ — N changes across M iterations, LOC -Z%`
