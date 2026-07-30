# Architecture Optimizer

Find localized structural changes that improve reliability, complexity, or
changeability without demanding a speculative rewrite.

Inputs:

- Goal: `{{codebase_goal}}`
- Iteration: `{{iteration}}`
- Files: `{{file_list}}`
- Heuristic unused-code leads: `{{dead_code_path}}`
- Duplicate-block leads: `{{dupes_path}}`

Prioritize asymptotic improvements, N+1 calls, wrong data structures, repeated
expensive work, failure isolation, blocking work that is safely parallelizable,
shared-state hazards, and high-cost coupling. Require concrete evidence and a
measurable expected improvement. Use `category: "architecture"`; optional
fields are `scope`, `type`, `current_approach`, `suggested_approach`, and
`expected_improvement`.

Follow `references/common-findings.md` and write `{{output_path}}`.
