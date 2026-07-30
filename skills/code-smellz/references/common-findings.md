# Common Findings Contract

Fill `{{codebase_goal}}`, `{{iteration}}`, `{{file_list}}`, and
`{{output_path}}`. Static-analysis files are heuristic leads, never proof.

Rules for every role:

- Read and report only; never edit the target.
- Verify claims with repository-wide search, tests, or a focused command.
- Check framework, reflection, plugin, generated, public API, and external-call
  surfaces before calling code dead or unsafe.
- Report only actionable findings. Use `[]` when none exist.
- Write one JSON array to `{{output_path}}`, with no prose in the file.
- End the response with `DONE: {{output_path}} — <summary>`.

Each finding uses this common shape; role files define `category` and optional
evidence fields:

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

When present, `patch` must be a valid repo-relative unified diff. Use `null`
when business logic is unknown or the change spans a risky structural rewrite.
