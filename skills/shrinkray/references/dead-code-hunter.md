# Dead Code Hunter

Verify and apply the dead-code candidates in `{{deadcode_scan_path}}`, then add
any tool-missed dead code you encounter while verifying.

Inputs: goal `{{codebase_goal}}`; iteration `{{iteration}}`; files
`{{file_list}}`; tool-flagged candidates `{{deadcode_scan_path}}`.

The pre-pass already ran a language-native dead-code tool (vulture for Python,
knip for JS/TS, deadcode for Go, cargo-udeps/rustc for Rust) plus the type
checker. Your job is to **confirm reachability** and **emit deletion patches**,
not to discover dead code from scratch. Most of your output should come from
the pre-pass file.

For each tool-flagged candidate in the file:

1. Confirm no remaining references with `rg --type <lang> -w '<name>'` or the
   language's equivalent (cross-file). For Python: also grep string literals
   and `getattr`/`importlib` patterns. For JS/TS: also check dynamic imports
   and string-referenced exports.
2. Confirm it is not a public/exported API, entry point, framework hook,
   decorator, magic method, generated code, or plugin interface.
3. Emit a unified-diff deletion patch in `patch`. If deletion requires
   cascading edits (e.g. removing parameters from callers), include them in the
   same patch.
4. Mark `confidence: high` when a tool certified the candidate and your grep
   confirmed zero references; `medium` when you discovered additional dead code
   yourself with strong evidence; `low` only when reachability is uncertain and
   flag it for human review in the description.

When the pre-pass flagged nothing for a file you scan, write no findings for
that file. Do not pad the report with speculative removals. Optional fields:
`verification_command` (the exact grep you ran), `kind`, and `source_tool`
(set to the `source` field of the pre-pass finding you applied).

Follow `references/common-findings.md`, use `category: "dead_code"`, and write
`{{output_path}}`.
