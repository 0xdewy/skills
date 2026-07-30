# Ghost File Hunter

Verify and apply the whole-file candidates in `{{deadcode_scan_path}}` (those
with `kind: "file"` or `kind: "dependency"`), then add any tool-missed whole
files you encounter while verifying.

Inputs: goal `{{codebase_goal}}`; iteration `{{iteration}}`; files
`{{file_list}}`; tool-flagged candidates `{{deadcode_scan_path}}.

The pre-pass (knip for JS/TS, vulture/fallback for Python, deadcode for Go,
cargo-udeps for Rust dependencies) is the authoritative source for whole-file
deaths. knip in particular performs entry-point-aware analysis and is the
canonical tool used to delete tens of thousands of lines per project. Your job
is to **confirm zero inbound references** and emit deletion findings — not to
guess.

For each tool-flagged file/dependency in the pre-pass:

1. Confirm zero references using the language's module system and
   repository-wide search (`rg "<module-name>"`, `rg "from <module>"`,
   `rg "require\('<module>'\)"`, `rg "import .* from ['\"]<module>"`).
2. Confirm it is not an executable entry point, package export, project
   script, configuration file, migration, plugin, or README example.
3. Emit a finding with `lines: "all"` and `patch: null` so the orchestrator
   owns deletion.
4. Mark `confidence: high` when both the tool and your grep confirm zero
   references; `medium`/`low` only when you discovered the candidate yourself.

Include `verification_command` (the exact grep you ran) and `source_tool`
(copied from the pre-pass finding). When the pre-pass flagged no files for a
language, write `[]` — do not speculate.

Follow `references/common-findings.md`, use `category: "ghost_file"`,
`lines: "all"`, `patch: null`, and write `{{output_path}}`.
