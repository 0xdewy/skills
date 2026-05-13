# Orchestration Patterns

Loaded by skills in the Orchestration category and any skill that spawns
sub-agents: implementer, one-shot-project, code-smellz, brainstormers,
dialectic-council.

Read this at activation. Append discovered patterns at completion.

## Contribution Format

```
### <Pattern Name>
- **Discovered by:** <skill>, <date>
- **Tags:** <tag1>, <tag2>
- **Pattern:** <one sentence>
- **Why:** <one sentence>
```

---

### Output Directory Guard
- **Discovered by:** code-smellz, 2026-05-11
- **Tags:** parallel, sub-agent, filesystem
- **Pattern:** Create the output directory before spawning sub-agents, not during.
- **Why:** Sub-agents that start before the directory exists produce silent
  failures — they write to a non-existent path, no error, output lost.

### Sub-agent Completion Signal
- **Discovered by:** implementer, 2026-05-11
- **Tags:** sub-agent, orchestration, validation
- **Pattern:** Require each sub-agent to emit a parseable completion signal
  (e.g., `IMPLEMENTER_DONE: ...`) and validate it before proceeding.
- **Why:** Sub-agents can produce output but fail silently on later steps.
  The signal confirms the sub-agent reached its intended termination point.
