# Orchestration Patterns

Loaded by skills in the Orchestration category and any skill that spawns
sub-agents: implementer, one-shot-project, code-smellz, brainstormers,
startup-ideation, researcher, student-counsel, shrinkray.

Read this at activation. Also load
`skills/common/patterns/execution-contract.md`; this file records discovered
patterns, while the execution contract is the reusable checklist. Append
discovered patterns at completion.

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

### Shared Orchestration Contract
- **Discovered by:** skills review, 2026-06-17
- **Tags:** parallel, filesystem, validation, resumability
- **Pattern:** Before spawning agents, create all output directories, assign each
  agent exactly one owned output file or directory, require a parseable `DONE:`
  line naming that artifact, then validate expected artifacts before advancing.
- **Why:** Parallel agents are reliable only when ownership, write locations, and
  phase gates are explicit; otherwise missing files and partial outputs masquerade
  as completed work.

### Single-writer Workspace
- **Discovered by:** researcher, 2026-06-17
- **Tags:** parallel, workspace, clobber-prevention
- **Pattern:** Mutable coordination files have one owner; parallel agents write
  proposals to separate files, and the orchestrator merges them.
- **Why:** Markdown and JSON workspaces have no locking, so concurrent edits to a
  shared status board, queue, or decision log silently overwrite each other.

### Patch-only Rollback
- **Discovered by:** skills review, 2026-06-17
- **Tags:** rollback, dirty-worktree, safety
- **Pattern:** Revert only patches or snapshots created by the skill; never use
  whole-tree checkout/reset as a fallback in a user worktree.
- **Why:** Skills commonly run in dirty repos. Whole-tree rollback can erase user
  edits that existed before the skill started or were made concurrently.

### Artifact Validation Gate
- **Discovered by:** skills review, 2026-06-17
- **Tags:** validation, phase-gate, schema
- **Pattern:** At every phase boundary, check that each expected file exists,
  parses if structured, and contains the required completion/verdict fields.
- **Why:** The next phase should consume facts, not trust conversational claims
  that a sub-agent finished correctly.
