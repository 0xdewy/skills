---
name: myco
description: >-
  Operate a Myco device identity through the bundled CLI: connect it to a
  person's identity, accept invitations, inspect groups, peers, messages and
  ACLs, post, and manage Kanban boards. TRIGGER on Myco identity or group
  inspection, connecting this machine or the local LLMs to a Myco identity,
  peer sync, posting, invitations, or board/card management. SKIP generic
  Kanban, non-Myco messaging, UI automation, and unrelated Myco development.
---

# Myco

Act as a Myco device: one device key that joins a person's identity and then
acts as it. Keep semantic judgment in the agent and use `scripts/myco` for
identity, protocol, read, and reconciliation mechanics. Resolve the script
relative to this `SKILL.md`; never automate the Myco UI.

Load only the reference needed for the request:

- Devices, identities, connecting, peers, membership, posts, or ACLs:
  `references/entities-and-access.md`.
- Project snapshots, desired-state reconciliation, moving, or closing cards:
  `references/board-workflows.md`.
- Desired-state JSON schema: `references/manifest.md`.

## Establish context

1. Run `scripts/myco doctor`. If `agentDeps` is false, run `pnpm install` in
   `myco-agent`.
2. Run `scripts/myco identity --json`. If uninitialized and the request needs
   a device, run `scripts/myco init`.
3. `identities` lists what this device can act as. If it is empty, the device
   has not joined an identity yet: connecting needs the person's device DID
   (see the reference).
4. Before board mutations, run
   `scripts/myco snapshot --entity <did:myco:...> --repo <root> --json`.

`MYCO_ROOT` overrides the Myco checkout (default `/home/user/code/myco`, on the
branch the person runs). `MYCO_DATA_DIR` selects another device's data;
`MYCO_RELAY_URL` another relay (default `https://relay.myco.network`).

## Acting as a person

A device that belongs to someone's identity posts, invites and edits **as that
person**. Treat every write as speaking in their name: do it only when they
asked for it, preview with `--dry-run`, and report the identity used (`as`).

For a visible or permission-changing operation:

1. Confirm it is within the user's request.
2. Run it with `--dry-run`.
3. Check membership and ACL state.
4. Apply the same command without `--dry-run`.
5. Read fresh state and report identifiers plus the observed result.

Prefer the read-only `identity`, `groups`, `entity`, `messages`, `peers`, and
`snapshot` commands. Absence after sync means an entity is not present
locally; report that instead of guessing or self-joining.

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
- Never print or read the keyring files or private keys. Device DIDs, entity
  and project ids, task ids, rosters, and peer links are reportable.
- Never regenerate a missing device or create a second one to get around a
  failure.
- Connect only to a device DID the person supplies; never pick one from the
  network.
- Membership is two-step: a Join, then the nominee's Accept. Never report an
  invitation or a sent connect request as membership.
