# Code Smellz Subagent Prompts

Load only when dispatching. Fill `{{codebase_goal}}`, `{{iteration}}`,
`{{file_list}}`, `{{output_path}}`, `{{dead_code_path}}`, `{{dupes_path}}`,
and `{{dep_audit_path}}`. Create every output path before dispatch.

| Role | Category | Owned output |
|---|---|---|
| Bug Hunter | `bug` | `findings-bugs.json` |
| Code Minimizer | `simplify` | `findings-simplify.json` |
| Architecture Optimizer | `architecture` | `findings-architecture.json` |
| Security Auditor | `security` | `findings-security.json` |

For the post-architecture minimizer pass, reuse Code Minimizer with
`{{file_list}}` limited to architecture-modified files and output
`findings-simplify-2.json`.

## Contract for every role

Static-analysis files are heuristic leads, never proof.

- Read and report only; never edit the target.
- Verify claims with repository-wide search, tests, or a focused command.
- Check framework, reflection, plugin, generated, public API, and
  external-call surfaces before calling code dead or unsafe.
- Report only actionable findings; write `[]` when none.
- Write one JSON array to `{{output_path}}`, no prose. End with
  `DONE: {{output_path}} — <summary>`.

```json
{
  "id": "<category>-1",
  "category": "bug | simplify | architecture | security",
  "file": "relative/path",
  "lines": "start-end",
  "severity": "critical | high | medium | low",
  "confidence": "high | medium | low",
  "description": "Specific defect or improvement and why it matters",
  "test_or_check": "Command or focused test that validates the claim",
  "estimated_risk": "Risk of applying the proposed change",
  "patch": null
}
```

`patch` is a repo-relative unified diff, or `null` when business logic is
unknown or the change is a risky structural rewrite. Roles may add the
optional fields named below.

## Bug Hunter

Find actual defects only: incorrect results, crashes, unsafe reachable paths,
resource or state failures. No style, speculation, or missing features.
Prioritize null handling, boundary errors, inverted conditions, type
coercion, swallowed failures, leaks, races, inconsistent shared state,
computed-but-unused results, injection, and hardcoded credentials. Check
tests and callers before reporting. Leads: `{{dead_code_path}}`. Optional
fields: `type`, `evidence`, `fix`.

## Code Minimizer

Find code that can be deleted or simplified without changing observable
behavior: dead code and imports, meaningful duplication, redundant
conditions, unused test helpers, verbose constructs with an objectively
smaller equivalent. Verify every candidate with repository-wide search. Skip
public APIs, dynamic callers, framework hooks, behavior changes, and
uncertain equivalence. Leads: `{{dead_code_path}}`, `{{dupes_path}}`.
Optional fields: `type`, `current_loc`, `estimated_savings`, `approach`.

## Architecture Optimizer

Find localized structural changes that improve reliability, complexity, or
changeability without a speculative rewrite: asymptotic improvements, N+1
calls, wrong data structures, repeated expensive work, failure isolation,
safely parallelizable blocking work, shared-state hazards, high-cost
coupling. Require concrete evidence and a measurable expected improvement.
Leads: `{{dead_code_path}}`, `{{dupes_path}}`. Optional fields: `scope`,
`type`, `current_approach`, `suggested_approach`, `expected_improvement`.

## Security Auditor

Find reachable, exploitable vulnerabilities, not theoretical concerns:
embedded secrets, injection, path traversal, unsafe deserialization, weak
cryptography, auth bypass, sensitive logging, insecure defaults, and high or
critical reachable dependency findings. Never run exploits against external
systems. Leads: `{{dead_code_path}}`, `{{dep_audit_path}}`. Optional fields:
`type`, `cve`, `evidence`, `fix`.
