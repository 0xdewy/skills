# Worker Slice Contract

Load only when dispatching an implementation worker.

Provide: slice ID, objective, acceptance criteria, dependencies, input paths,
allowed write paths, output directory, and verification command.

The worker must:

1. Read repository guidance and stay within its owned paths.
2. Implement only the slice; report scope conflicts instead of expanding.
3. Avoid subagents, commits, and questions in non-interactive dispatch mode.
4. Run the supplied check or the narrowest relevant fallback.
5. Write `SUMMARY.md` with changed files, verification evidence, assumptions,
   deviations, and blockers.
6. End with `DONE: <output>/SUMMARY.md — <implemented|blocked>, verification=<result>`.

The coordinator validates the artifact and worktree; a worker's `DONE` is not
acceptance.
