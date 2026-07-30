# Common Findings Contract

Fill `{{codebase_goal}}`, `{{iteration}}`, `{{file_list}}`, and
`{{output_path}}`.

- Read and report only; never edit the target.
- Verify every candidate with repository-wide search or a focused command.
- Exclude ignored, generated, vendor, cache, and build output.
- Preserve public APIs and observable behavior.
- Report only high/medium-confidence net reductions; write `[]` when none.
- Write one JSON array to `{{output_path}}`, with no prose in the file.
- End with `DONE: {{output_path}} — <summary>`.

```json
{
  "id": "<category>-1",
  "category": "dead_code | ghost_file | consolidate | verbosity",
  "file": "relative/path",
  "lines": "start-end | all",
  "description": "Why removal or replacement is safe",
  "estimated_loc_saved": 1,
  "confidence": "high | medium | low",
  "source_tool": "vulture | knip | deadcode | cargo-udeps | tsc | mypy | rustc | go-vet | fallback-ast | null",
  "patch": null
}
```

Use a valid repo-relative unified diff when practical. Ghost files always use
`lines: "all"` and `patch: null` so the orchestrator owns deletion. Set
`source_tool` to the pre-pass tool that certified the candidate (copied from
the finding's `source` field) when the candidate came from `deadcode_scan.json`;
leave `null` for LLM-discovered candidates so the reviewer can weight
tool-certified findings above model-only ones.
