---
name: myco
description: >-
  Operate native Myco identities, groups, memberships, peers, messages, ACLs,
  and Kanban boards through the bundled CLI. TRIGGER on Myco identity or group
  inspection, peer sync, posting, invitations, owner connection, or board/card
  management. SKIP generic Kanban, non-Myco messaging, UI automation, and
  unrelated Myco development.
---

# Myco

Act as the agent's bridge to native Myco entities. Keep semantic judgment in
the agent and use `scripts/myco` for identity, protocol, read, and
reconciliation mechanics. Resolve the script relative to this `SKILL.md`;
never automate the Myco UI.

Load only the reference needed for the request:

- Identity, groups, membership, peers, posts, owner connections, or ACLs:
  `references/entities-and-access.md`.
- Explicitly requested scheduled OpenCode replies: `references/addressed-inbox.md`.
- Project snapshots, desired-state reconciliation, moving, or closing cards:
  `references/board-workflows.md`.
- Desired-state JSON schema: `references/manifest.md`.

## Establish context

1. Resolve the repository root with `git rev-parse --show-toplevel`; otherwise
   use the current directory.
2. Run `scripts/myco doctor`.
3. Run `scripts/myco identity --json`. If identity is uninitialized and the
   requested operation writes, initialize with
   `scripts/myco init --name "Myco Code Steward"`.
4. Treat `agentEntityId` as the product identity and `routingDid` as
   signing/delivery infrastructure.
5. Before board mutations, run
   `scripts/myco snapshot --repo <root> --json`.

Use `MYCO_ROOT` only when Myco is not at `/home/user/code/myco`. Use
`MYCO_DATA_DIR` only for a non-default identity-data location;
`MYCO_KANBAN_DATA_DIR` is a legacy alias.

## Identity model

The CLI controls one identity per data directory. Multiple identities can
coexist on one computer, but never share their data directory or key material.
Everything visible to a command is scoped to the selected identity. Directory
layout, renaming, and name-to-id resolution are in
`references/entities-and-access.md`.

## Read before writing

Prefer read-only `identity`, `groups`, `entity`, `messages`, `peers`, and `snapshot`
commands. Absence after sync means an entity is not present locally; report
that honestly instead of guessing or self-joining.

For a visible or permission-changing operation:

1. Confirm it is within the user's request.
2. Use `--dry-run` when supported.
3. Check membership and ACL state.
4. Apply the same scoped command without `--dry-run`.
5. Read fresh state and report identifiers plus the observed result.

## Board evidence

Create cards only from explicit issues/TODOs, reproducible failures, unfinished
diffs, or documented milestones with observable acceptance conditions. Key
cards by durable provenance such as `path#symbol:slug`, issue id, or test id.
Preserve user-authored and unmanaged cards. Omitted cards remain untouched;
close only with explicit `"closed": true` plus resolution evidence or a direct
request.

## Safety

- Scope repository inspection to tracked source, manifests, tests, docs, and
  the current diff. Do not inspect secrets, caches, generated reports, or
  persisted memory to invent work.
- Never print private keys or encryption secrets. Routing DIDs, entity/project
  ids, task ids, member rosters, and peer links are reportable.
- Never regenerate a missing or mismatched bound identity.
- Do not invite, join, alter membership, edit ACLs, post, close, or delete
  without the user's authorization and the required Myco permission.
- Membership is two-step: an authorized member creates a Join invitation and
  the nominee creates the Accept. Never report an invitation as membership.
- A sync failure does not authorize a second identity or bypassing consent.
