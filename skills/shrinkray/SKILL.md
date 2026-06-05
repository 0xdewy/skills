---
name: shrinkray
description: >-
  Reduces a codebase to its smallest correct form using four parallel subagents,
  each targeting a different source of bloat. Removes dead code, deletes unused
  files, consolidates duplicated logic into shared utilities, and shrinks verbose
  constructs — all without breaking functionality or test coverage. Runs the test
  suite before and after every iteration; reverts any change that causes a
  failure. Never commits. TRIGGER on: "shrink this codebase", "reduce codebase
  size", "make this codebase smaller", "minimize lines of code", "remove all
  bloat", "compress the code", "shrink the repo", "remove dead code and files",
  "run shrinkray", "/shrinkray". SKIP on: code quality passes focused on bugs or
  security (use code-smellz instead), single-file refactors, documentation-only
  changes, build artifact minification (JS/CSS bundler minify is not this).
license: MIT
metadata:
  author: iamky1e
  version: 1.0.0
  category: meta
  tags:
    - refactoring
    - code-size
    - dead-code
    - multi-agent
    - optimization
---

## What This Does

Four subagents run in parallel, each holding a laser on a specific source of
bloat. They read — never write. The orchestrator collects their reports, applies
changes in safe batches, runs the test suite, and reverts anything that breaks.

| Agent | Mandate |
|---|---|
| **Dead Code Hunter** | Functions, methods, classes, variables, and imports never reached at runtime |
| **Ghost File Hunter** | Entire source files never imported, required, or referenced anywhere |
| **Code Consolidator** | Duplicate or near-duplicate logic that can be extracted into one shared utility |
| **Verbosity Reducer** | Verbose constructs that can be expressed in fewer lines without sacrificing clarity |

The loop repeats until nothing meaningful remains, a plateau is hit, or 5
iterations elapse — whichever comes first.

**This skill never runs `git commit`.** All changes stay in the working tree.
Review with `git diff` and commit when ready.

---

## Prerequisites

- Python 3
- A git repository (so changes are reversible with `git apply -R`)
- A test suite is strongly preferred. Without tests, correctness is unverifiable
  and the skill will warn you.

---

## Phase 0: Setup & Baseline

### 0.1 Initialize Output Directory

```bash
mv /tmp/shrinkray-output /tmp/shrinkray-output.prev 2>/dev/null || true
mkdir -p /tmp/shrinkray-output
```

### 0.2 Read Project Goal

Find the one-sentence project purpose from (in priority order):
- `CLAUDE.md` — project notes
- `README.md` — first 30 lines
- `package.json` → `description`
- `pyproject.toml` → `[project] description`
- Fallback: "goal unknown — inferred from code structure"

### 0.3 Detect Test Runner

```bash
python3 $SKILL_DIR/scripts/detect_runner.py . > /tmp/shrinkray-output/runner.json
cat /tmp/shrinkray-output/runner.json
```

### 0.4 Check Git Repo

Run `git status`. If not a git repo, warn:
> "This project is not tracked by git. Changes cannot be easily reverted.
> Continue? (y/n)"
Stop if not confirmed.

### 0.5 Load .shrinkignore

Check for `.shrinkignore` in the project root. It uses `.gitignore` syntax.
Files matching these patterns are excluded from all subagent review and all edits.
Write parsed patterns to `/tmp/shrinkray-output/exclusions.txt`.
If absent, all source files are in scope.

### 0.6 Baseline LOC

```bash
python3 $SKILL_DIR/scripts/measure_loc.py . > /tmp/shrinkray-output/baseline_loc.json
cat /tmp/shrinkray-output/baseline_loc.json
```

### 0.7 Baseline Tests

Run the test suite using the command from `runner.json`. Record pass rate.
If no runner is found, note it and warn the user — changes will need manual
verification.

Print:
```
Baseline: XXXX LOC | Tests: NN/NN passing | Runner: <command or "none found">
```

### 0.8 Initialize Session

Create `/tmp/shrinkray-output/session.json`:
```json
{
  "iteration": 0,
  "codebase_goal": "<one sentence>",
  "baseline_loc": 0,
  "baseline_tests": "<pass_rate or 'no tests'>",
  "runner_command": "<command or null>",
  "history": [],
  "stats": {
    "dead_code":   { "removed": 0, "skipped": 0 },
    "ghost_files": { "removed": 0, "skipped": 0 },
    "consolidate": { "removed": 0, "skipped": 0 },
    "verbosity":   { "removed": 0, "skipped": 0 }
  }
}
```

**Phase 0 outputs:** `runner.json`, `exclusions.txt`, `baseline_loc.json`, `session.json` — all in `/tmp/shrinkray-output/`
**Phase 1 reads:** `session.json`, `exclusions.txt`

---

## Phase 1: Dispatch Subagents in Parallel

Read `references/subagent-prompts.md` for the four prompt templates.

Fill in template variables:
- `{{codebase_goal}}` — from session.json
- `{{file_list}}` — all source files, excluding:
  `.git/`, `node_modules/`, `__pycache__/`, `dist/`, `build/`, `target/`,
  `.venv/`, `coverage/`, and any patterns from `.shrinkignore`
- `{{iteration}}` — current iteration number

**Spawn all four agents simultaneously** (run_in_background: true).
Each is read-only — no file changes. Each writes one JSON file:

```
/tmp/shrinkray-output/findings-dead-code.json
/tmp/shrinkray-output/findings-ghost-files.json
/tmp/shrinkray-output/findings-consolidate.json
/tmp/shrinkray-output/findings-verbosity.json
```

**Wait for all four to complete before proceeding.**

**Phase 1 outputs:** `findings-dead-code.json`, `findings-ghost-files.json`, `findings-consolidate.json`, `findings-verbosity.json` — all in `/tmp/shrinkray-output/`
**Phase 2 reads:** all four findings files

Each finding entry format:
```json
{
  "id": "unique-string",
  "category": "dead_code | ghost_file | consolidate | verbosity",
  "file": "relative/path/to/file.py",
  "lines": "10-45",
  "description": "What this is and why it is safe to remove/shrink",
  "estimated_loc_saved": 12,
  "confidence": "high | medium | low",
  "patch": "<unified diff hunk, or null if too complex for a patch>"
}
```

Ghost file findings use `"file"` for the full file path and `"lines": "all"`.

---

## Phase 2: Triage

### 2.1 Merge & Sort

Merge all four findings files into one sorted list:
- High confidence first, then medium, then low
- Within same confidence: most LOC saved first

### 2.2 Conflict Detection

Before any edit, check: do two findings touch the same lines?
- If yes: apply the finding that saves more LOC; skip the other.

### 2.3 Safety Filters

**Skip a finding if:**
- Confidence is `low` AND estimated LOC saved < 10 (not worth the risk)
- The file matches a `.shrinkignore` pattern
- The finding touches a public API surface (exported symbol, REST endpoint, CLI flag)
  without a replacement — flag it as "needs human review"

### 2.4 Write STAGED_CHANGES.md

Write `/tmp/shrinkray-output/STAGED_CHANGES.md` before any edit:
```markdown
# Shrinkray — Iteration N Staged Changes

| # | Category | File | Lines | LOC Saved | Confidence | Description |
|---|---|---|---|---|---|---|
| 1 | dead_code | foo.py | 45-78 | 34 | high | unused `_parse_legacy()` |
...

Total planned: N changes, ~M LOC saved
```

Print:
```
=== Iteration N Triage ===
  Dead code findings:    N (high: X, medium: Y, low: Z)
  Ghost files:           N
  Consolidation:         N (high: X, medium: Y, low: Z)
  Verbosity:             N (high: X, medium: Y, low: Z)
  Applying this round:   N changes (~M LOC)
  Skipping (safety):     N changes
  STAGED_CHANGES.md written → /tmp/shrinkray-output/
```

**If zero HIGH/MEDIUM findings remain across all four agents: skip to Phase 6.**

**Phase 2 outputs:** `STAGED_CHANGES.md` in `/tmp/shrinkray-output/`
**Phase 3 reads:** `STAGED_CHANGES.md`, `session.json`

---

## Phase 3: Apply Changes

### 3.1 Save Checkpoint

```bash
git diff > /tmp/shrinkray-output/pre-iter-N.diff
```

### 3.2 Apply in Order

Apply changes in this order:
1. Ghost file deletions (whole-file removals — lowest risk of conflict)
2. Dead code removals (removing code from files)
3. Consolidations (creating new shared utilities + updating callers)
4. Verbosity reductions (in-place rewrites)

**Per-change:**
1. If the finding has a `patch` field:
   ```bash
   git apply --check /tmp/shrinkray-output/patch-N.diff && git apply /tmp/shrinkray-output/patch-N.diff
   ```
   If `--check` fails (file changed since subagent read it), apply manually
   using the `description`.
2. If no `patch` field: apply manually using the `description`.

**After each individual change**, run a quick syntax check if available
(e.g. `python3 -m py_compile <file>` for Python). If it fails, revert that
single change immediately:
```bash
git checkout -- <file>
```
Mark it `"reverted": true` and continue.

### 3.3 Log Changes

Append each applied change to `session.json → history`:
```json
{
  "iteration": 1,
  "category": "dead_code",
  "file": "path/to/file.py",
  "lines": "45-78",
  "description": "removed unused _parse_legacy()",
  "loc_saved": 34,
  "patch_file": "/tmp/shrinkray-output/patch-1.diff",
  "reverted": false
}
```

**Phase 3 outputs:** `pre-iter-N.diff`, `patch-N.diff` files, updated `session.json` history — all in `/tmp/shrinkray-output/`
**Phase 4 reads:** `session.json` (runner command + patch paths)

---

## Phase 4: Verify

### 4.1 Run Tests

```bash
<runner_command from session.json>
```

#### Tests pass ✓
- Measure new LOC:
  ```bash
  python3 $SKILL_DIR/scripts/measure_loc.py . > /tmp/shrinkray-output/iter_N_loc.json
  ```
- Compute delta: `baseline_loc - current_loc`
- Print:
  ```
  Iteration N complete: N changes applied, N LOC removed (-X.X%)
  Tests: NN/NN passing
  ```

#### Tests fail ✗
1. Revert in reverse order using `git apply -R /tmp/shrinkray-output/patch-N.diff`
   for each patched change, or `git checkout -- <file>` for manual edits.
2. Mark each reverted change `"reverted": true`.
3. Update `stats[category].skipped += 1`.
4. Re-run tests to confirm green.
5. Log what failed for the final report.

**Fallback:** If granular revert fails, restore from checkpoint:
```bash
git checkout . && git apply /tmp/shrinkray-output/pre-iter-N.diff
```

#### No tests
Manually verify: run the main entry point (from README or `package.json → scripts.start`).
Confirm it produces expected output. Note in session.json: "verified: manual run".

**Phase 4 outputs:** `iter_N_loc.json`, updated `session.json` (reverted flags) — in `/tmp/shrinkray-output/`
**Phase 5 reads:** `session.json` (iteration count, stats)

---

## Phase 5: Convergence

Check stopping conditions in order:

1. **Clean** — all four subagents return zero HIGH/MEDIUM findings → stop
2. **Plateau** — fewer than 2 changes successfully applied this iteration → stop
3. **Limit** — iteration count reached 5 → stop

If none apply: increment iteration in session.json and return to Phase 1.

**Phase 5 outputs:** updated `session.json` (incremented iteration)
→ Loop to Phase 1, or proceed to Phase 6

---

## Phase 6: Final Report

Read `session.json` and all `iter_*_loc.json` files. Print:

```
╔══════════════════════════════════════╗
║         SHRINKRAY REPORT             ║
╚══════════════════════════════════════╝
Iterations completed : N
Starting LOC         : XXXX
Final LOC            : YYYY  (-ZZ% / -NN lines)
Tests                : NN/NN passing  (was NN/NN)
Note: All changes are in the working tree. Review with `git diff` and commit when ready.

Lines removed by category:
  Dead code removed   : N lines (N items)
  Ghost files deleted : N files (N lines)
  Code consolidated   : N lines (N deduplication sites)
  Verbosity reduced   : N lines (N rewrites)
  ─────────────────────────────────────
  Total               : N lines removed

Reverted (broke tests): N changes
Skipped (safety):       N changes

Remaining (not applied, needs human review):
  [medium] path/to/file — description
  [low]    path/to/file — description

Recommendation:
  <"Codebase is minimal." | "N items require human review." | specific advice>
```

Emit: `DONE: shrinkray — N lines removed across M iterations (-Z% LOC reduction)`
