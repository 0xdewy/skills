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
  version: 2.0.0
  category: meta
  tags:
    - refactoring
    - code-quality
    - bugs
    - optimization
    - multi-agent
---

## What This Does

Load `skills/common/patterns/orchestration.md` and
`skills/common/patterns/activation.md` for cross-skill patterns.
See `skills/common/episodic-memory-guide.md` for the full memory design.

Four subagents run in parallel, each with a specific mandate:

| Agent | Finds |
|-------|-------|
| **Bug Hunter** | Crashes, incorrect logic, unhandled errors, type errors, security issues |
| **Code Minimizer** | Dead code, duplication, verbosity, unused imports, redundant abstractions |
| **Architecture Optimizer** | Inefficient algorithms, N+1 queries, bad data structures, missing caching |
| **Security Auditor** | Dependency CVEs, hardcoded secrets, insecure function usage, missing input sanitization |

### Key Improvements (v2.0)

1. **Tool-verified dead code** — a static analysis pre-pass (Python AST + JS/TS export analysis)
   feeds the minimizer with high-confidence deletion targets, so it doesn't guess.
2. **Cross-file duplication detection** — line-hashing finds identical code blocks
   across files that the minimizer and architect can consolidate.
3. **Diff-patch output** — subagents produce unified diff patches, eliminating
   orchestrator misinterpretation of fix descriptions.
4. **Type-check, lint, and format gates** — the type checker and linter run _before_ the
   test suite on every iteration. The formatter runs after to condense formatting.
5. **STAGED_CHANGES.md review** — all planned changes are written to a review file
   before any edit is applied, so the user can inspect and abort.
6. **Quarantine** — any change category (bugs/simplify/arch/security) that exceeds
   50% revert rate is skipped for the rest of the run.
7. **Second minimizer pass** — after architectural changes are applied in Phase 3,
   the minimizer runs again on the modified files to catch new simplification
   opportunities created by the restructuring.
8. **Conflict resolution bias toward simplification** — when Bug Hunter and Minimizer
   disagree about dead code, the Minimizer wins unless the Bug Hunter can cite a
   specific caller or test that exercises the code.
9. **Dependency CVE scan in orchestrator** — `npm audit`, `pip-audit`, `cargo audit`
   are run in Phase 0 and results fed to the Security Auditor as pre-computed data.
10. **`.stinkyignore` support** — exclude files/dirs with `.gitignore` syntax so
    the skill never touches known-fragile or auto-generated code.
11. **Zero commits** — this skill never commits. All changes stay in the working
    tree. Review with `git diff` and commit yourself when ready.
12. **`git apply -R` revert flow** — changes are tracked by patch file. Reverting
    is O(1): just apply the patch in reverse. No binary search needed.

After all four report, changes are applied, type-checked, linted, formatted, and tested.
The loop repeats until nothing meaningful remains — or 5 iterations, or quarantine
halts a category — whichever comes first.

**This skill never runs `git commit`.** All changes stay in the working tree.
Review with `git diff` and commit when ready. The skill uses `git apply` to stage
changes and `git apply -R` to revert them — no commits are created.

## Prerequisites

- Python 3 (for helper scripts)
- A test suite is strongly preferred. Without tests, correctness is unverifiable.
- The project should be in a git repository so changes are reversible.

---

## Phase 0: Discovery & Static Analysis

**If `/tmp/stinky-output/` already exists**, archive it first:
```bash
mv /tmp/stinky-output /tmp/stinky-output.prev 2>/dev/null || true
mkdir -p /tmp/stinky-output
```

### 0.1 Project Discovery

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

### 0.2 Load .stinkyignore (File Exclusions)

Check for a `.stinkyignore` file in the project root. If it exists, read it.
It uses `.gitignore` syntax. Files matching these patterns will be excluded from
all subagent review and all edits. If no `.stinkyignore` exists, all source files
are in scope.

Write the parsed patterns to `/tmp/stinky-output/exclusions.txt` (one pattern per line,
with `!` negations preserved).

### 0.3 Static Analysis (Dead Code + Duplication + CVE + Formatter)

Run the static analysis pre-pass to generate tool-verified data for the subagents:
```bash
python3 $SKILL_DIR/scripts/static_analysis.py . /tmp/stinky-output
```

This produces:
- `dead_code.json` — unused functions, classes, imports (Python AST verified),
  plus potentially dead JS/TS exports
- `dupes.json` — cross-file duplicate code blocks (5+ identical lines)
- `tools.json` — detected type checker, linter, formatter, and CVE scanner commands

**Security note:** the orchestrator runs the CVE/dependency scan here in Phase 0
(not delegated to the security-auditor subagent, which is read-only). If a
dependency scanner is detected, run it now and save output to
`/tmp/stinky-output/dep-audit-raw.json`.

Print a summary:
```
Static analysis: N dead code items found, M duplicate blocks across files
Type checker: mypy | tsc | cargo | none
Linter: ruff | eslint | clippy | none
Formatter: black | prettier | gofmt | none
CVE scanner: npm audit | pip-audit | cargo audit | none
Excluded files: N patterns loaded from .stinkyignore (or "none")
```

### 0.4 Baseline & Initial Test

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

### 0.5 Initialize Session

Create `/tmp/stinky-output/session.json`:
```json
{
  "iteration": 0,
  "codebase_goal": "<one sentence>",
  "baseline_loc": <number>,
  "baseline_tests": "<pass_rate or 'no tests'>",
  "runner_command": "<command or null>",
  "typecheck_cmd": "<command or null>",
  "lint_cmd": "<command or null>",
  "format_cmd": "<command or null>",
  "dep_audit_cmd": "<command or null>",
  "dead_code_count": <number>,
  "dupe_block_count": <number>,
  "has_stinkyignore": false,
  "quarantine": { "bug": false, "simplify": false, "arch": false, "security": false },
  "category_stats": {
    "bug":     { "attempted": 0, "reverted": 0 },
    "simplify":{ "attempted": 0, "reverted": 0 },
    "arch":    { "attempted": 0, "reverted": 0 },
    "security":{ "attempted": 0, "reverted": 0 }
  },
  "history": []
}
```

**Phase 0 outputs:** `runner.json`, `exclusions.txt`, `dead_code.json`, `dupes.json`, `tools.json`, `dep-audit-raw.json` (if CVE scanner found), `baseline_loc.json`, `session.json` — all in `/tmp/stinky-output/`
**Phase 1 reads:** `session.json`, `exclusions.txt`, `dead_code.json`, `dupes.json`, `dep-audit-raw.json`

---

## Phase 1: Dispatch Subagents in Parallel

Read `references/subagent-prompts.md` for the full prompt templates.

Fill in the template variables:
- `{{codebase_goal}}` — from session.json
- `{{file_list}}` — all source files, excluding:
  `.git/`, `node_modules/`, `__pycache__/`, `dist/`, `build/`, `target/`,
  `.venv/`, `coverage/`, `stinky-output/`, AND any patterns from `.stinkyignore`.
  Read `/tmp/stinky-output/exclusions.txt` for the ignore patterns.
- `{{iteration}}` — current iteration number
- `{{dead_code_path}}` — `/tmp/stinky-output/dead_code.json`
- `{{dupes_path}}` — `/tmp/stinky-output/dupes.json`
- `{{dep_audit_path}}` — `/tmp/stinky-output/dep-audit-raw.json` (for Security Auditor only)

Spawn all four agents **simultaneously**. Each receives a read-only mandate
and pre-computed dead-code/dupe data. Each writes one JSON file to
`/tmp/stinky-output/` with findings that include unified diff patches:

```
/tmp/stinky-output/findings-bugs.json
/tmp/stinky-output/findings-simplify.json
/tmp/stinky-output/findings-arch.json
/tmp/stinky-output/security-audit.json
```

The Security Auditor receives the pre-computed `dep-audit-raw.json` (CVE scan
run by the orchestrator in Phase 0) as input. It does NOT run its own commands.

**Each finding entry now includes a `patch` field** — a unified diff hunk that
can be applied with `git apply`. This eliminates the orchestrator having to
interpret fix descriptions, which was a major source of breakage.

**Critical:** agents READ and REPORT only. No file changes in Phase 1.

Wait for all four to complete before moving to Phase 2.

**Phase 1 outputs:** `findings-bugs.json`, `findings-simplify.json`, `findings-arch.json`, `security-audit.json` — all in `/tmp/stinky-output/`
**Phase 2 reads:** all four findings files

---

## Phase 2: Triage & Review

### 2.1 Read Findings

Read all four findings files and build a unified, prioritized action list.

### 2.2 Conflict Resolution

Conflicts are resolved with a bias toward simplification:

| Scenario | Resolution |
|----------|-----------|
| Bug Hunter says "keep this code" and Minimizer says "delete it" | **Minimizer wins** — unless Bug Hunter cites a *specific* caller, test, or dynamic reference that exercises the code. Vague "might be needed" objections are ignored. |
| Two agents touch the same lines | Apply the higher-severity finding first; skip the other |
| Finding requires business context you don't have | Skip it, log as "needs human review" |
| A patch in findings doesn't have a `patch` field | Apply manually using the `fix`/`approach` description |

### 2.3 Priority & Quarantine

**Priority rules:**
- CRITICAL security findings → apply first, and verify immediately (typecheck + tests)
  before applying any other changes from the same iteration
- HIGH severity → apply this iteration (unless category is quarantined)
- MEDIUM severity → apply unless the change is risky (touches public API, shared
  utility, or complex logic — flag those for human review instead)
- LOW severity → apply only if no HIGH/MEDIUM remain

**Quarantine check:**
Before scheduling any change, check `session.json → quarantine[category]`.
If the category is `true`, skip ALL findings from that category this iteration.
A category enters quarantine when its cumulative revert rate exceeds 50%
(tracked via `category_stats`). Print a warning:
```
⚠ Category "simplify" is quarantined (3/5 changes reverted in prior iterations).
  Skipping 4 simplify findings this iteration.
```

### 2.4 Write STAGED_CHANGES.md

Write all planned changes to `/tmp/stinky-output/STAGED_CHANGES.md` BEFORE
applying any edits. The file should list:
- Iteration number
- Each change: category, file, line range, severity, 1-line description
- Total planned changes, estimated LOC delta
- Which categories are quarantined (if any)

Print the triage summary:
```
=== Iteration N Triage ===
  Bugs found:         3 high, 2 medium, 1 low
  Simplifications:    5 high, 3 medium, 2 low   ← includes dead_code.json hits
  Architecture:       1 high, 2 medium, 0 low
  Security:           1 critical, 0 high, 2 medium
  Quarantined:        none   (or: "simplify" if applicable)
  Applying this round: 11 changes
  Skipping (risky/conflict): 3 changes
  STAGED_CHANGES.md written to /tmp/stinky-output/
```

**If all findings are LOW or zero across all four agents: skip to Phase 6.**

**Phase 2 outputs:** `STAGED_CHANGES.md` in `/tmp/stinky-output/`
**Phase 3 reads:** `STAGED_CHANGES.md`, `session.json`

---

## Phase 3: Apply Changes

**Before any edits**, save a checkpoint of the working tree so we can always
return to the pre-iteration state if things go wrong:
```bash
git diff > /tmp/stinky-output/pre-iter-N.diff
```

### 3.1 Apply Security Fixes First

CRITICAL security findings (CVE with known exploit, hardcoded secret in a
file) MUST be applied first and verified before any other changes.

1. Apply each security patch with `git apply --check && git apply`
2. Run the type checker: `<typecheck_cmd> 2>&1`
3. Run tests: `<runner_command>`
4. If both pass → keep them. Log as `"change_type": "security_fix"`.
5. If either fails → `git apply -R` each patch to revert, skip them.

### 3.2 Apply Remaining Changes

Work in dependency order:
1. Bug fixes that affect shared utilities (these changes affect many callers)
2. Bug fixes in individual files
3. Architectural changes (restructuring may create opportunities for simplification)
4. Simplifications (easiest to apply once bugs and structure are fixed)

**Per-change patch application:**
1. If the finding has a `patch` field:
   - Write the patch to a temp file `/tmp/stinky-output/patch-N.diff`
   - Run `git apply --check /tmp/stinky-output/patch-N.diff`
   - If `--check` succeeds: `git apply /tmp/stinky-output/patch-N.diff`
   - If `--check` fails: the file may have changed since the subagent read it.
     Fall back to manual edit using the `fix`/`approach` description.
2. If the finding has no `patch` field: apply manually using the `fix`/`approach` text.

**After each individual change**, run the type checker:
```bash
<typecheck_cmd from session.json> 2>&1
```
If the type checker reports new errors:
- `git apply -R /tmp/stinky-output/patch-N.diff` to revert just that change
- Mark it `"reverted": true` and skip it
- This catches regressions immediately instead of in a batch

**Batch fallback:** If the type checker is unavailable, revert to batching
3-5 changes and run the test suite after each batch to isolate failures.

### 3.3 Second Minimizer Pass (Post-Architecture)

After all architectural changes have been applied, re-run the Code Minimizer
**only on the files modified by the architect**. Use the second-pass prompt
template from `references/subagent-prompts.md` (under "Agent 2b: Post-Arch
Minimizer"). Provide only the architect-touched files as `{{file_list}}`.

This catches new dead-code and simplification opportunities created by the
restructuring (e.g. extracted utilities making old copies safe to delete).

```
Second-pass minimizer: reviewing N files for post-arch cleanup...
```

Apply any new findings from this pass before proceeding to Phase 4.

### 3.4 Log Changes

Log each change in `/tmp/stinky-output/session.json` under `history`:
```json
{
  "iteration": N,
  "change_type": "bug_fix|simplify|arch|security_fix",
  "file": "path/to/file",
  "description": "what changed and why",
  "applied_via_patch": true,
  "patch_file": "/tmp/stinky-output/patch-N.diff",
  "reverted": false
}
```
Store the patch file path so it can be reverted with `git apply -R` during Phase 4
if needed.

**Phase 3 outputs:** `pre-iter-N.diff`, `patch-N.diff` files, updated `session.json` history — all in `/tmp/stinky-output/`
**Phase 4 reads:** `session.json` (for tool commands + patch paths)

---

## Phase 4: Verify

### 4.1 Type Check Gate

Run the type checker (regardless of whether it was run in Phase 3):
```bash
<typecheck_cmd from session.json> 2>&1
```
If the type checker is not available, skip this step.

**If new type errors appear:**
1. Revert patches in reverse application order with `git apply -R` (use the
   `patch_file` paths logged in session.json history) until typecheck passes.
2. Mark each reverted change `"reverted": true`.
3. Update `category_stats[change_type].reverted += 1` for each.

### 4.2 Lint Gate

Run the linter (if available):
```bash
<lint_cmd from session.json> 2>&1
```
If the linter reports new issues that were introduced by our changes, fix them.
If they're pre-existing, note them but don't block.

### 4.3 Formatter Gate

Run the formatter (if available):
```bash
<format_cmd from session.json> 2>&1
```
The formatter may produce additional LOC reduction on top of our changes
(formatters condense verbose line breaks, trailing whitespace, inconsistent
indentation). If the formatter changes files, those count as part of this
iteration's LOC delta.

If no formatter is available, skip this step.

### 4.4 Test Suite

Run the full test suite:
```bash
<runner_command from session.json>
```

#### Tests pass
- Measure new LOC:
  ```bash
  python3 $SKILL_DIR/scripts/measure_loc.py . > /tmp/stinky-output/iter_N_loc.json
  ```
- Compute delta: `baseline_loc - current_loc` lines removed
- Print iteration summary:
  ```
  Iteration N complete: 9 changes applied, 3 bugs fixed, 47 lines removed
  Tests: 42/42 passing  |  Type check: clean  |  Lint: clean  |  Format: applied
  ```
- **All changes are in the working tree only.** Review with `git diff` and
  commit when ready. No commits have been made by this skill.

#### Tests fail
1. Revert patches in reverse application order with `git apply -R` until tests pass.
   (Use the `patch_file` paths logged in session.json history.)
2. Mark each reverted change `"reverted": true`.
3. Update `category_stats[change_type].reverted += 1` for each reverted change.
4. Re-run tests to confirm green.
5. Note what the failing changes were — they may need manual attention.

**Fallback:** If `git apply -R` fails on a patch (file changed by a later patch),
restore from the pre-iteration checkpoint:
```bash
git checkout . && git apply /tmp/stinky-output/pre-iter-N.diff
```
Then re-apply only the changes that passed.

If reverting leaves you with fewer than 2 successful changes this iteration,
that counts as a plateau (see Phase 5).

**Phase 4 outputs:** `iter_N_loc.json`, updated `session.json` (reverted flags, pass/fail) — in `/tmp/stinky-output/`
**Phase 5 reads:** `session.json` (category_stats, iteration count)

#### No tests exist
Verify core functionality manually:
- Run the main entry point or example from the README
- Confirm it produces the expected output
- Note in session.json: "verified: manual run, no test suite"

---

## Phase 5: Convergence Decision

### 5.1 Update Category Stats

After Phase 4, update `category_stats` for each category:
```json
"bug": { "attempted": 5, "reverted": 1 }
```
If any category's revert rate exceeds 50% (reverted / attempted > 0.5 and
attempted ≥ 4 to avoid flukes on small samples), set `quarantine[category] = true`.
Mark it in the history:
```json
{ "event": "quarantine", "category": "arch", "reason": "3/4 changes reverted" }
```

### 5.2 Check Stopping Conditions

Check in order:

1. **Clean** — re-run the four subagents (same as Phase 1) and check if all
   four return zero HIGH/MEDIUM findings → emit final report and stop
2. **Plateau** — fewer than 2 changes were successfully applied this iteration → stop
3. **Limit** — iteration count has reached 5 → stop
4. **Unstable** — more than 40% of changes this iteration were reverted → stop
   and flag: "Codebase may be too tightly coupled for safe automatic refactoring
   in this area. Remaining issues flagged for human review."
5. **Full quarantine** — all four categories are quarantined → stop and report:
   "All change categories have been quarantined. The codebase may need manual review."

If none apply: increment `session.json iteration` and return to Phase 1.

**Phase 5 outputs:** updated `session.json` (quarantine flags, incremented iteration)
→ Loop to Phase 1, or proceed to Phase 6

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
Type check           : clean | N issues | not available
Lint                 : clean | not available
Format               : applied | not available
Note                 : All changes are in the working tree. Review with `git diff` and commit when ready.

Changes applied:
  Bugs fixed                  : N
  Lines removed (simplify)    : N
  Architecture improvements   : N
  Security issues fixed       : N  (CVEs patched, secrets removed)
  Total changes               : N

Changes reverted (broke typecheck/tests): N
Quarantined categories:   <none | bug, arch, simplify, security>

Remaining items (not applied):
  [medium] path/to/file — description
  [low]    path/to/file — description

Recommendation:
  <"Code is clean." | "N items require human review." | specific advice>
```

Emit: `DONE: /tmp/stinky-output/ — N changes across M iterations, LOC -Z%`
