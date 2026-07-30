# Code Minimizer

Find code that can be safely deleted or simplified without changing observable
behavior.

Inputs:

- Goal: `{{codebase_goal}}`
- Iteration: `{{iteration}}`
- Files: `{{file_list}}`
- Heuristic unused-code leads: `{{dead_code_path}}`
- Duplicate-block leads: `{{dupes_path}}`

Verify every candidate with repository-wide search. Skip public APIs, dynamic
callers, framework hooks, behavior changes, and uncertain equivalence. Focus on
dead code/imports, meaningful duplication, redundant conditions, unused test
helpers, and verbose constructs with an objectively smaller equivalent. Use
`category: "simplify"`; optional fields are `type`, `current_loc`,
`estimated_savings`, and `approach`.

Follow `references/common-findings.md` and write `{{output_path}}`.
