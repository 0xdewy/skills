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
  version: 2.1.0
  category: meta
  activation: explicit
  tags:
    - refactoring
    - code-size
    - dead-code
    - multi-agent
    - optimization
---

# Shrinkray

Reduce repo size while preserving behavior. Two pre-pass scripts feed agents
cross-file evidence as data, so they spend tokens verifying and implementing
rather than discovering (the LLM weak spot per SmellBench arXiv:2606.05574 and
CodeTaste arXiv:2603.04177):

1. `scripts/deadcode_scan.py` — wraps vulture/knip/deadcode/cargo-udeps + type
   checker into one unified findings JSON.
2. `scripts/dependency_index.py` — caller counts, importer counts,
   single-caller symbols, single-importer files, single-implementor interfaces.

Dead Code Hunter and Ghost File Hunter **verify-and-apply** tool-flagged
candidates. Structural roles run **propose-then-implement**: they propose
candidates from the index, the orchestrator selects, then they implement.

Prefer direct edits for small targets; use agents only when independent bloat
categories can run in parallel.

Load `../common/patterns/execution-contract.md`,
`../common/patterns/quarantine-loop.md`, and `../common/patterns/scaling.md`.
Use `../common/scripts/detect_runner.py` and `measure_loc.py`, plus
shrinkray's own `scripts/deadcode_scan.py` and `scripts/dependency_index.py`
for the two pre-passes. At dispatch, use `references/subagent-prompts.md` to
load only the active role prompt.

## Activation

Second gate: confirm via `../common/ROUTING.md` that the task is size/dead
code reduction, not bug/security/architecture cleanup, docs, or build
minification.

## Modes

- `--quick`: direct dead-code/verbosity pass. Budget: 0. Still runs
  `deadcode_scan.py` and applies clear-cut findings directly.
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

Run `../common/patterns/quarantine-loop.md` under the selected mode. shrinkray
opts into: **two pre-pass scripts** (Phase 0.5: `deadcode_scan.py` +
`dependency_index.py`), **type-check gate** (Phase 4), **propose-then-implement
decomposition** (Phase 1.5, structural roles only), and **second-minimizer
pass** (Phase 3.3).

Finding schema:
`{id, category, file, lines, description, estimated_loc_saved, confidence,
source_tool, patch}`; ghost files use `lines: "all"`. Categories:
`dead_code | ghost_file | consolidate | verbosity`. Apply in order: ghost
files, dead code, consolidations, verbosity. `source_tool` records which
pre-pass tool certified the candidate so the reviewer weights tool-certified
findings above LLM-discovered ones.

Final line:

```text
DONE: <WORKSPACE> — <lines> lines removed across <iterations> iterations (-<pct>% LOC)
```
