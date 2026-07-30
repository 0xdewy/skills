# Code Consolidator

Find repeated logic whose extraction produces a clear net LOC reduction.

Inputs: goal `{{codebase_goal}}`; iteration `{{iteration}}`; files
`{{file_list}}`.

Prioritize repeated blocks of roughly eight or more lines, duplicate helpers,
validation, error handling, configuration loading, and transformation pipelines.
Skip coincidental similarity, one-liners, generated/vendor code, test setup, and
code likely to evolve independently. Report all sites, the shared signature,
call-site changes, and net savings. Follow `references/common-findings.md`, use
`category: "consolidate"`, and write `{{output_path}}`.
