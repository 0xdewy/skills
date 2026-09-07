---
name: shrinkray
description: >-
  Shrinks repositories while preserving behavior by removing dead code,
  duplication, and verbosity with measured verification. Only use when
  explicitly requested.
license: MIT
disable-model-invocation: true
metadata:
  author: iamky1e
  version: 2.2.0
  category: meta
  tags:
    - refactoring
    - code-size
    - dead-code
    - multi-agent
    - optimization
---

# Shrinkray

Reduce repo size while preserving behavior. Before any agent is dispatched, a
deterministic pass and two pre-pass scripts turn the repo into evidence and,
where possible, an already-smaller repo — so agents spend tokens verifying
and implementing rather than discovering (the LLM weak spot per SmellBench
arXiv:2606.05574 and CodeTaste arXiv:2603.04177):

0. `scripts/less_code_pass.py` — for Python, JavaScript, TypeScript, and
   Rust, runs `less-code` (`lc`), which does not just find candidates but
   applies and verifies them itself (own frozen-suite/API/doc gate, self-
   reverting per layer): dead internal code, loop-to-comprehension folds,
   redundant temporaries, guard/conditional collapses, import packing, and
   (Python) cross-function duplicate-window outlining. Zero agent budget.
   Optional: skips cleanly when a language is unsupported or `lc` is not
   installed (see the script's docstring for how it is found).
1. `scripts/deadcode_scan.py` — wraps vulture/knip/deadcode/cargo-udeps + type
   checker into one unified findings JSON.
2. `scripts/dependency_index.py` — caller counts, importer counts,
   single-caller symbols, single-importer files, single-implementor interfaces.

Run pass 0 first: it needs no dispatch, and it shrinks the tree before passes
1/2 scan it, so they do not re-propose what `lc` already applied and
verified.

Dead Code Hunter and Ghost File Hunter **verify-and-apply** tool-flagged
candidates. Structural roles run **propose-then-implement**: they propose
candidates from the index, the orchestrator selects, then they implement.
`less_code_pass.py` needs neither pattern — it is its own verify-and-apply,
upstream of both.

Prefer direct edits for small targets; use agents only when independent bloat
categories can run in parallel.

Load `../common/patterns/execution-contract.md`,
`../common/patterns/quarantine-loop.md`, and `../common/patterns/scaling.md`.
Use `../common/scripts/detect_runner.py` and `measure_loc.py`, plus
shrinkray's own `scripts/less_code_pass.py`, `scripts/deadcode_scan.py`, and
`scripts/dependency_index.py` for the deterministic pass and the two
pre-passes. At dispatch, use `references/subagent-prompts.md` to load only
the active role prompt.

## Activation

Second gate: confirm via `../common/ROUTING.md` that the task is size/dead
code reduction, not bug/security/architecture cleanup, docs, or build
minification.

## Modes

All three run `less_code_pass.py` first — it costs no budget regardless of
mode.

- `--quick`: `less_code_pass.py`, then a direct dead-code/verbosity pass.
  Budget: 0. Still runs `deadcode_scan.py` and applies clear-cut findings
  directly.
- `--standard`: dispatch the 2-3 primary roles justified by pre-pass
  evidence, once. Budget: 3.
- `--thorough`: primary roles + the five structural roles, with
  propose-then-implement (Phase 1.5), repeat shared loop to convergence, cap 5.

Default for non-interactive dispatch is `--standard`; for obvious tiny targets,
use `--quick`.

## Agents

**Primary** (verify-and-apply, always available):

- Dead Code Hunter — consumes `{{deadcode_scan_path}}`.
- Ghost File Hunter — consumes `{{deadcode_scan_path}}`.
- Verbosity Reducer — direct scan.
- Code Consolidator — consumes `{{dependency_index_path}}`.

**Structural** (propose-then-implement, thorough mode only):

- Stdlib Replacer — hand-rolled → stdlib/library.
- Indirection Inliner — single-caller symbols & single-implementor interfaces
  from `{{dependency_index_path}}`.
- Table-Drive Converter — switch/if-else ladders → dispatch table.
- Flag Pruner — shipped feature flags & one-shot migrations → collapse.
- Module Merger — single-importer files from `{{dependency_index_path}}`.

Each agent is read-only and writes one findings JSON file (and one proposal
JSON during the propose pass for structural roles).

## Workflow

Run `../common/patterns/quarantine-loop.md` under the selected mode, with one
addition before it starts: **Phase 0.4 — deterministic pass.** Immediately
after Phase 0's baseline LOC/test capture and before Phase 0.5's pre-pass
scripts, run `scripts/less_code_pass.py <WORKSPACE> <WORKSPACE>` (pass
`--test-command` with the Phase 0 detected runner's command when confidence
is `high`, so this pass and Phase 4's verify run the identical suite). It
writes directly to the tree and is already gated by its own frozen-suite/
API/doc checks — nothing here goes through Phase 2's triage or Phase 3's
`git apply`, and a per-layer failure inside it is not a run failure, `lc`
already reverted that layer. Record its `total_loc_removed` and per-language
`tests_ok` from `less_code_pass.json` for Phase 6; when `ran: false`, note
the one-line reason and continue — this phase is optional, never a blocker.
Then run Phase 0.5's pre-pass scripts on the now-smaller tree, so they do not
re-propose what this pass already applied.

shrinkray opts into: **the deterministic pass** (Phase 0.4:
`less_code_pass.py`, before dispatch), **two pre-pass scripts** (Phase 0.5:
`deadcode_scan.py` + `dependency_index.py`), **type-check gate** (Phase 4),
**propose-then-implement decomposition** (Phase 1.5, structural roles only),
and **second-minimizer pass** (Phase 3.3).

Finding schema (agent-produced findings only; Phase 0.4 is exempt, see
above): `{id, category, file, lines, description, estimated_loc_saved,
confidence, source_tool, patch}`; ghost files use `lines: "all"`.
Categories: `dead_code | ghost_file | consolidate | verbosity`. Apply in
order: ghost files, dead code, consolidations, verbosity. `source_tool`
records which pre-pass tool certified the candidate so the reviewer weights
tool-certified findings above LLM-discovered ones.

Final line:

```text
DONE: <WORKSPACE> — <lines> lines removed across <iterations> iterations (-<pct>% LOC)
```
