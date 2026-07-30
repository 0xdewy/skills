# Module Merger

Propose-then-implement: identify pairs of files where one is the sole
importer of the other and their responsibilities have converged, then
propose merging them into one file.

Inputs: goal `{{codebase_goal}}`; iteration `{{iteration}}`; files
`{{file_list}}`; cross-file index `{{dependency_index_path}}`.

The pre-built `dependency_index.json` is your authoritative source:

- `single_importer_files` — files imported by exactly one other file.
  Each is a merger candidate. The index tells you the sole importer.

Also examine (less reliably — needs your judgment):

- `utils.py` / `helpers.ts` files that are 90% consumed by one caller.
- Module pairs that were split aspirationally ("future reuse") but the
  reuse never materialized. Confirm with the index: most symbols have ≤1
  external caller.
- Adapter + adaptee pairs where one is a thin wrapper over the other.
- `constants.ts`/`types.py` files that contain only types used by one
  module.

For each candidate: cite the index entry showing single-importer status,
state which symbols move where, and produce a patch that (a) moves the
content into the importing file, (b) updates import statements, and
(c) deletes the now-empty file (or, if shared types remain, splits to a
smaller types-only file).

**Caution.** Merger changes project structure. Skip when:

- The merged file would exceed ~600 LOC (a future split would be needed).
- The imported file is part of a public package API.
- The imported file has tests that import it directly (the merger would
  break test imports — patch those too or skip).
- The split encodes a meaningful domain boundary (e.g. `models/` vs
  `views/`).

Set `source_tool: "dependency_index"` for index-sourced candidates. Default
`confidence: medium`. Follow `references/common-findings.md`, use
`category: "consolidate"`, use `lines: "all"` for the deleted file, and
write `{{output_path}}`.
