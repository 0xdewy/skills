# Myco Board Workflows

## Inspect the codebase

Read repository-local instructions first. Inspect tracked source, manifests,
tests, README/docs/issues, `git status --short`, and targeted
`TODO|FIXME|HACK|XXX` searches. Exclude generated and vendor directories.

Create cards only from concrete evidence:

- an explicit TODO or issue with a source location;
- a failing test or build with a reproducible command;
- unfinished work visible in the current diff;
- a documented milestone with an observable acceptance condition.

Do not create speculative work. Absence of a TODO is not proof of completion.

## Snapshot and reconcile

Use durable keys such as `path#symbol:slug`, issue id, or test id. Put source
locations and verification commands in `evidence`. Unless the board defines a
different workflow, use `Backlog`, `Ready`, `In Progress`, `Review`, `Done`.

Write desired state using `references/manifest.md`, then:

```bash
scripts/myco snapshot --repo <root> --json
scripts/myco reconcile --repo <root> --file <manifest> --dry-run --json
scripts/myco reconcile --repo <root> --file <manifest> --json
```

Inspect the preview for duplicate keys, unsupported statuses, and accidental
closures. After applying, read a fresh snapshot and report created, updated,
unchanged, and closed cards.

By default the project belongs to the agent entity. Pass
`--entity <did:myco:...>` for a group project. The agent must be a member with
project/task creation permission; if not, report the required ACL grant and
stop.

Reconciliation is additive and key-based. Omitted cards remain untouched.
Close only with `"closed": true` plus resolution evidence or an explicit
request. Never delete cards or the identity.

## Focused changes

After a snapshot confirms the stable key:

```bash
scripts/myco move --repo <root> --key <task-key> \
  --status "Review" [--dry-run]
scripts/myco close --repo <root> --key <task-key> [--dry-run]
```

A move must use a configured workflow column. Closing archives a card; it is
not the same as moving it to `Done`. Preview ambiguous changes.
