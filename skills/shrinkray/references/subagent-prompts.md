# Shrinkray Role Index

Load `references/common-findings.md` plus only the active role prompt:

| Role | Category | Prompt | Owned output | Reads pre-pass? |
|---|---|---|---|---|
| Dead Code Hunter | `dead_code` | `references/dead-code-hunter.md` | `findings-dead-code.json` | `{{deadcode_scan_path}}` |
| Ghost File Hunter | `ghost_file` | `references/ghost-file-hunter.md` | `findings-ghost-files.json` | `{{deadcode_scan_path}}` |
| Verbosity Reducer | `verbosity` | `references/verbosity-reducer.md` | `findings-verbosity.json` | optional |
| Code Consolidator | `consolidate` | `references/code-consolidator.md` | `findings-consolidate.json` | `{{dependency_index_path}}` |
| Stdlib Replacer | `verbosity` | `references/stdlib-replacer.md` | `findings-stdlib.json` | optional |
| Indirection Inliner | `consolidate` | `references/indirection-inliner.md` | `findings-inline.json` | `{{dependency_index_path}}` |
| Table-Drive Converter | `consolidate` | `references/table-drive-converter.md` | `findings-table.json` | optional |
| Flag Pruner | `dead_code` | `references/flag-pruner.md` | `findings-flag.json` | optional |
| Module Merger | `consolidate` | `references/module-merger.md` | `findings-merge.json` | `{{dependency_index_path}}` |

The first four are the **primary roles**. The last five are **structural
roles** and run only when `--thorough` is set, or when the pre-pass surfaces
evidence that justifies one (e.g. `dependency_index.json` shows many
single-caller symbols → dispatch Indirection Inliner; many single-importer
files → dispatch Module Merger).

## Deterministic pass, then two pre-pass scripts

The orchestrator runs the deterministic pass in Phase 0.4, before any agent
exists to consume its output — it applies and verifies its own changes, it
does not produce findings:

0. `scripts/less_code_pass.py <project> <workspace> [--test-command CMD]`
   → `less_code_pass.json` (per-language `loc_start`/`loc_final`/`tests_ok`
   from `less-code`). No consumer; read `total_loc_removed` for Phase 6 and
   move on. Optional — see the script's docstring for how `lc` is found and
   what happens when it or the language is unsupported.

Then it runs both of these in Phase 0.5 and writes them to the workspace:

1. `scripts/deadcode_scan.py <project> <workspace>` → `deadcode_scan.json`
   (vulture/knip/deadcode/cargo-udeps + type-checker diagnostics, unified).
   Consumed by Dead Code Hunter and Ghost File Hunter.
2. `scripts/dependency_index.py <project> <workspace>` → `dependency_index.json`
   (caller counts, importer counts, single-caller symbols, single-importer
   files, single-implementor interfaces). Consumed by Code Consolidator,
   Indirection Inliner, and Module Merger.

## Dispatch

Create output paths before dispatch and pass each resolved path as
`{{output_path}}`. Pass `{{deadcode_scan_path}}` to the roles that read it;
pass `{{dependency_index_path}}` to the roles that read it. Standard mode
dispatches 2-3 roles justified by pre-pass evidence; thorough mode adds the
five structural roles.
