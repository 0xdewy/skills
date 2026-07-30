# Security Auditor

Find reachable, exploitable vulnerabilities rather than theoretical concerns.

Inputs:

- Goal: `{{codebase_goal}}`
- Iteration: `{{iteration}}`
- Files: `{{file_list}}`
- Heuristic unused-code leads: `{{dead_code_path}}`
- Dependency-audit results: `{{dep_audit_path}}`

Prioritize embedded secrets, injection, path traversal, unsafe deserialization,
weak cryptography, auth/authz bypass, sensitive logging, insecure defaults, and
high/critical reachable dependency findings. Do not run exploits against
external systems. Use `category: "security"`; optional fields are `type`,
`cve`, `evidence`, and `fix`.

Follow `references/common-findings.md` and write `{{output_path}}`.
