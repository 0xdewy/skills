# Workspace Resolution

Shared rule for any skill that writes intermediate artifacts or coordinates
workers.

Do not hardcode `/tmp/<skill>-output/` in skill bodies. The filesystem layout
and the temp directory differ across runtimes (Linux `/tmp`, macOS `/var/tmp`
symlink, containers with no writable `/tmp`, sandboxes that only allow writes
under the project dir). Resolve the workspace once and reuse the variable.

## Resolution order

A skill resolves `WORKSPACE` in this order, taking the first that applies:

1. **Caller-supplied path.** If the invocation (user prompt or a parent
   orchestrator) provides an explicit output dir — e.g. an `OUTPUT_DIR` /
   `WORKSPACE` parameter or env var — use it verbatim. A parent orchestrator
   dispatching sub-agents should always set this so children write into the
   parent's run directory.
2. **Temp dir.** `${TMPDIR:-/tmp}/<skill>-<slug>/`, where `<slug>` is a kebab-case
   slug derived from the task or mandate. Use this for scratch artifacts the user
   does not need to keep.
3. **Project-local fallback.** If no writable temp dir is available (a read-only
   `/tmp`, a sandbox, or `$TMPDIR` unset and `/tmp` non-writable), fall back to
   `./.<skill>-workspace/` inside the project. This keeps artifacts discoverable
   without polluting the top level.

State the resolved `WORKSPACE` in one line at setup so the run is auditable, and
use it everywhere a hardcoded `/tmp/...` path would have appeared.

## Single-writer rule

`WORKSPACE` is owned by the orchestrator. Parallel sub-agents never write to the
same file; each gets its own subdir or owned file under `WORKSPACE`. Coordination
files (`session.json`, `status.json`, `STAGED_CHANGES.md`, the debate log) have
exactly one writer — the orchestrator. See `orchestration.md` → Single-writer
Workspace.

## When to use a repo dir instead

Use a path **inside** the target repo only when the user explicitly asked for
durable output there (e.g. "write the report to `docs/`", "apply the changes to
my source tree"). Otherwise keep scratch in `WORKSPACE` and leave the caller's
working directory clean. Cleanup skills that edit the repo still keep their
review artifacts (`STAGED_CHANGES.md`, patches, session log) in `WORKSPACE`, not
alongside the source.

## Archival

If `WORKSPACE` already exists from a prior run, archive it
(`mv "$WORKSPACE" "$WORKSPACE.prev"`) before recreating, rather than deleting, so
the previous run remains inspectable. This preserves the audit trail.
