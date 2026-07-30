# Flag Pruner

Propose-then-implement: identify code branches gated by shipped feature
flags, one-shot migrations, or "in case we need it later" guards, and
propose collapsing to the live branch.

Inputs: goal `{{codebase_goal}}`; iteration `{{iteration}}`; files
`{{file_list}}`; cross-file index `{{dependency_index_path}}`.

Hunt for:

- Feature-flag branches (`if feature_flags.X:`, `if config.USE_NEW_...:`,
  `process.env.X`, `LD_FLAGS.X`) where the flag value has been pinned to one
  branch in production for a meaningful period. Confirm via git history or
  the config files; collapse to the winning branch and delete the losing one.
- One-shot migration guards (`if migrated:`, `if user.version >= 2:`) that
  have run their course. Confirm the migration is complete (all entities
  past the gate) and collapse.
- Debug-only blocks gated by constants pinned to false (`if DEBUG:`, guarded
  by `if False:`) — delete outright.
- A/B experiment branches whose experiment has concluded.
- Backwards-compat shims for entry points that no longer ship the old shape
  (confirm via git blame: no caller of the old shape exists).

**Safety bar is high.** For each candidate, the description must include:
which branch is live, how you confirmed it (git log, config snapshot, test
coverage), and what gets deleted. If you cannot prove the losing branch is
dead, downgrade to `confidence: low` and flag for human review.

Set `source_tool: null` (LLM-discovered). Follow
`references/common-findings.md`, use `category: "dead_code"` (it is
behaviorally dead even if syntactically live), and write `{{output_path}}`.
