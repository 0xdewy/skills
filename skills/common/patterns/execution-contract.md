# Execution Contract

Shared contract for skills that run phases, spawn subagents, write files, or
modify a user worktree. Load this alongside the domain-specific pattern file.

## Activation Gate

Before doing heavyweight work, confirm the situation still matches the skill:

1. The user asked for this workflow, not just a word that appears in the trigger.
2. Required inputs are present or can be inferred safely.
3. Required tools are available, or there is a documented fallback.
4. The expected side effects are acceptable for the current directory.

If any condition fails, ask one focused question or use the documented fallback.

## Workspace

Do not hardcode `/tmp/<skill>-output/` in skill bodies; the temp directory
differs across runtimes. Resolve `WORKSPACE` once, in this order, and reuse it:

1. **Caller-supplied path.** An explicit `OUTPUT_DIR` / `WORKSPACE` parameter
   or env var from the user or a parent orchestrator, used verbatim. A parent
   dispatching sub-agents always sets this so children write into its run dir.
2. **Temp dir.** `${TMPDIR:-/tmp}/<skill>-<slug>/`, with `<slug>` derived from
   the task.
3. **Project-local fallback.** `./.<skill>-workspace/` when no temp dir is
   writable.

Use a path inside the target repo only when the user explicitly asked for
durable output there. Cleanup skills that edit the repo still keep their review
artifacts (staged-change lists, patches, session log) in `WORKSPACE`.

If `WORKSPACE` already exists from a prior run, archive it
(`mv "$WORKSPACE" "$WORKSPACE.prev"`) rather than deleting, unless the skill's
resume rules say to continue it.

## Phase Setup

At the start of a run:

1. Write down the observable acceptance criteria.
2. State the resolved `WORKSPACE` in one line so the run is auditable.
3. Create every output directory before dispatching agents or scripts.
4. Record the phase state in one place: `status.json`, `README.md`, or a clearly
   named status section.

## Subagent Contract

Every subagent gets:

- One role, one objective, and one owned output file or directory.
- Read/write scope and boundaries stated explicitly.
- Input files listed by path, plus any tool or source guidance.
- Output schema or Markdown structure.
- A required final line naming its artifact:
  `DONE: <artifact-path> — <summary>`

Missing any of these means the task is not ready to delegate.

`WORKSPACE` is owned by the orchestrator. Parallel agents never write the same
file; each gets its own subdir or owned file. Coordination files
(`status.json`, `session.json`, staged-change lists, debate logs) have exactly
one writer, normally the orchestrator.

## Artifact Validation Gate

At every phase boundary, validate artifacts before consuming them:

1. Expected file or directory exists.
2. Structured data parses.
3. Required fields, headings, or verdict lines are present.
4. Completion signal names the same artifact.
5. Empty output is explicit (`[]`, `none`, or `NO_FINDINGS`) rather than missing.

If validation fails, re-run only the failed role with the same output path and a
short description of the contract failure. Do not infer missing findings from a
chat transcript.

## Tool and Subagent Fallbacks

If subagents are unavailable, run the same roles sequentially inline and write
the same artifacts. State that execution was serialized.

If a nonessential tool is unavailable, skip only the affected check and record
the reduced confidence. If an essential tool is unavailable, stop with a clear
blocker instead of pretending the phase passed.

## Worktree Safety

Before modifying files:

1. Check `git status --short` when inside a git repo.
2. Treat existing changes as user-owned.
3. Keep edits scoped to files required by the task.
4. For reversible automated edits, save the patch or per-file snapshot before
   applying the change.
5. Revert only the patch/snapshot created by this skill.

Never use `git reset --hard`, `git checkout .`, broad `git restore .`, or
whole-tree cleanup as a fallback in a dirty worktree.

## Verification Gate

A reviewer, PM, or subagent can recommend completion, but the top-level
orchestrator owns final verification.

Before emitting the final `DONE:` line:

1. Run the documented tests or checks when available.
2. Check outputs against the acceptance criteria.
3. Record commands run and any checks skipped.
4. Mark the result `DONE` only if required criteria passed.
5. Use `PARTIAL` when useful artifacts exist but blockers remain.

## Completion Line

End with a parseable line:

```text
DONE: <primary-output-path> — <what changed or was produced>
```

For incomplete runs:

```text
DONE: <primary-output-path> — PARTIAL, <what works>, blockers: <summary>
```

The completion line is the final line. Do not emit it before verification.

**Scope.** The completion line is mandatory for orchestrator-invoked skills —
anything another agent, a loop, a cron, or a pipeline might dispatch and wait
on. It is optional for pure reference or voice skills that answer a human
directly and are never consumed by an orchestrator (e.g. a Q&A reference skill,
a voice/persona skill). If a skill can be spawned by another skill, it emits
`DONE:`; if it only ever talks back to a human, the line is encouraged but not
required.
