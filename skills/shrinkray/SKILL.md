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
  version: 2.2.1
  category: meta
  tags:
    - refactoring
    - code-size
    - dead-code
    - multi-agent
    - optimization
---

# Shrinkray

Reduce repository size while preserving behavior. Prefer direct edits for a
small target; use agents only when evidence identifies independent bloat
categories that benefit from parallel work.

Load `../common/ROUTING.md` to confirm this is a size or dead-code task rather
than bug, security, architecture, documentation, or build-minification work.
Then load `../common/patterns/execution-contract.md`,
`../common/patterns/quarantine-loop.md`, and
`../common/patterns/scaling.md`. Use `references/subagent-prompts.md` only when
dispatching a role.

## Modes

- `--quick`: deterministic pass, then directly apply clear dead-code and
  verbosity findings. No agent budget.
- `--standard`: dispatch the 2-3 primary roles justified by evidence once.
  Budget: 3.
- `--thorough`: add structural roles, use propose-then-implement, and repeat
  the shared loop to convergence. Budget cap: 5.

Default non-interactive runs to `--standard`; use `--quick` for an obviously
small target.

## Evidence passes

After Phase 0 captures baseline LOC and tests, run these before dispatch:

1. **Phase 0.4:** run
   `scripts/less_code_pass.py <WORKSPACE> <WORKSPACE>`. For Python,
   JavaScript, TypeScript, and Rust it invokes `less-code` (`lc`), which applies
   and verifies transformations with its own frozen-suite/API/doc gates and
   reverts a failing layer. Pass `--test-command` when runner detection has
   high confidence so it uses the Phase 4 suite. The tool and supported
   language are optional; record a skip reason and continue when `ran` is
   false. Record `total_loc_removed` and per-language `tests_ok` from
   `less_code_pass.json`. Do not send its already-applied changes through agent
   triage or `git apply`.
2. **Phase 0.5:** run `scripts/deadcode_scan.py` and
   `scripts/dependency_index.py` on the resulting tree. The first combines
   language dead-code tools and type checking. The second records caller and
   importer counts, including single-caller symbols, single-importer files,
   and single-implementor interfaces.

Use `../common/scripts/detect_runner.py` and `measure_loc.py` for runner and
measurement support. The deterministic pass runs in every mode because it
spends no agent budget.

## Roles and application

Primary roles verify and apply evidence-backed candidates: Dead Code Hunter,
Ghost File Hunter, Verbosity Reducer, and Code Consolidator. Thorough mode may
also use structural roles for standard-library replacement, indirection
inlining, table-driven conversion, shipped-flag removal, and module merging.
Structural roles first propose candidates from the dependency index; the
orchestrator selects proposals before implementation.

Each agent is read-only and writes one findings JSON file; structural roles
also write one proposal JSON. Findings use:

```text
{id, category, file, lines, description, estimated_loc_saved, confidence, source_tool, patch}
```

Use `lines: "all"` for ghost files and categories `dead_code`, `ghost_file`,
`consolidate`, or `verbosity`. Apply ghost files, dead code, consolidation,
then verbosity. Weight tool-certified findings above model-only findings.
Phase 0.4 output is exempt because `lc` applies and verifies its own changes.

Run the shared type-check and test gates after edits, including the second
minimizer pass. Finish with:

```text
DONE: <WORKSPACE> — <lines> lines removed across <iterations> iterations (-<pct>% LOC)
```
