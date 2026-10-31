# Shrinkray Subagent Prompts

Load only when dispatching. Fill `{{codebase_goal}}`, `{{file_list}}`,
`{{output_path}}`, `{{deadcode_scan_path}}`, and `{{dependency_index_path}}`.
Create every output path before dispatch.

| Focus | Role | Category |
|---|---|---|
| size | Dead Code Hunter | `dead_code` |
| size | Ghost File Hunter | `ghost_file` |
| size | Verbosity Reducer | `verbosity` |
| size | Code Consolidator | `consolidate` |
| size, `--thorough` | Stdlib Replacer | `verbosity` |
| size, `--thorough` | Indirection Inliner | `consolidate` |
| size, `--thorough` | Table-Drive Converter | `consolidate` |
| size, `--thorough` | Flag Pruner | `dead_code` |
| size, `--thorough` | Module Merger | `consolidate` |
| correctness | Bug Hunter | `bug` |
| correctness | Architecture Optimizer | `architecture` |
| security | Security Auditor | `security` |

Output file: `findings-<role-slug>.json`. Dispatch Indirection Inliner or
Module Merger without `--thorough` when the index shows many single-caller
symbols or single-importer files.

## Contract for every role

- Read and report only; never edit the target.
- Pre-pass files are leads, not proof. Verify every claim with a
  repository-wide search (`rg -w`), a test, or a focused command, including
  string references, `getattr`/`importlib`, and dynamic imports.
- Skip generated, vendor, cache, build, and untracked files. Preserve public
  APIs, entry points, framework hooks, plugins, and observable behavior.
- Report only high or medium confidence findings; write `[]` when none.
- Write one JSON array to `{{output_path}}`, no prose. End with
  `DONE: {{output_path}} — <summary>`.

```json
{
  "id": "<category>-1",
  "category": "dead_code | ghost_file | consolidate | verbosity | bug | architecture | security",
  "file": "relative/path",
  "lines": "start-end | all",
  "description": "What to change and why it is safe",
  "evidence": "Search, test, or command output that proves it",
  "confidence": "high | medium | low",
  "source_tool": "vulture | knip | deadcode | cargo-udeps | tsc | mypy | rustc | go-vet | dependency_index | null",
  "estimated_loc_saved": 0
}
```

`source_tool` comes from the pre-pass finding; `null` means model-found.
`confidence: high` needs a tool and a clean search to agree. The orchestrator
drops structural findings under 5 net LOC.

## Dead Code Hunter

Confirm each `{{deadcode_scan_path}}` candidate has no remaining reference
and is not an export, entry point, decorator target, magic method, or plugin
interface. Include cascading edits such as removed parameters. Add
unflagged dead code only when met while verifying.

## Ghost File Hunter

Confirm each `kind: "file"` or `kind: "dependency"` candidate in
`{{deadcode_scan_path}}` has no inbound import or path reference and is not
an entry point, package export, script, config, migration, or README
example. Use `lines: "all"`. knip is authoritative for JS/TS.

## Verbosity Reducer

Find constructs with a shorter, equally readable equivalent: redundant
temporaries, boilerplate the standard library covers, repeated guards,
disabled code. Skip style-only changes, dense one-liners, comments, and zero
net savings. Show before and after in `description`.

## Code Consolidator

Find repeated logic, roughly eight or more lines, whose extraction gives a
clear net reduction. Skip coincidental similarity, test setup, and code
likely to diverge. List every site, the shared signature, and net savings.
Use `{{dependency_index_path}}` for callers.

## Stdlib Replacer

Find hand-rolled versions of stdlib or already-imported library functions
and classes that only namespace static methods. Name the exact replacement.

## Indirection Inliner

Use `single_caller_symbols` and `single_implementor_interfaces` from
`{{dependency_index_path}}`: inline at the sole call site or collapse the
abstraction. Also pass-through wrappers. Skip plugin interfaces, injection
boundaries, and public API.

## Table-Drive Converter

Find `switch`/`if-elif` ladders with near-identical branches and families
of near-identical functions. Replace with a table plus one dispatch only when
clearly smaller.

## Flag Pruner

Find branches behind shipped flags, finished migration guards, debug blocks
pinned off, and shims with no caller. State which branch is live and how that
was confirmed (git log, config, coverage).

## Module Merger

Use `single_importer_files` from `{{dependency_index_path}}`: move the
content into its importer and delete the file. Skip when the result exceeds
about 600 LOC, the file is public API, tests import it, or it marks a real
domain boundary.

## Bug Hunter

Find real defects: wrong results, crashes, boundary errors, inverted
conditions, swallowed failures, leaks, races, computed-but-unused results.
No style or speculation. Check tests and callers. `evidence` names the
failing input or the test that would catch it.

## Architecture Optimizer

Find localized structural fixes with measurable gain: asymptotic
improvements, N+1 calls, wrong data structures, repeated expensive work,
missing failure isolation. No speculative rewrites. State the expected
improvement.

## Security Auditor

Find reachable, exploitable issues: secrets, injection, path traversal,
unsafe deserialization, weak cryptography, auth bypass, sensitive logging,
insecure defaults, and high or critical reachable dependency advisories.
Never run exploits against external systems. `evidence` shows the reachable
path.
