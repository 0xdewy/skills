# Bug Hunter

Find actual defects only: incorrect results, crashes, unsafe reachable paths, or
resource/state failures. Do not report style, speculative improvements, or
missing features.

Inputs:

- Goal: `{{codebase_goal}}`
- Iteration: `{{iteration}}`
- Files: `{{file_list}}`
- Heuristic dead-code leads: `{{dead_code_path}}`

Prioritize null/None handling, boundary errors, inverted conditions, type
coercion, swallowed failures, leaks, races, inconsistent shared state,
computed-but-unused results, injection, and hardcoded credentials. Check tests
and callers before reporting. Use `category: "bug"`; optional fields are
`type`, `evidence`, and `fix`.

Follow `references/common-findings.md` and write `{{output_path}}`.
