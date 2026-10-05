# Myco Entities and Access

## Devices and identities

A person's Myco identity is an entity (`did:myco:...`) whose members are their
devices. Any member device can act as the identity: post, invite, edit. This
CLI is one such device.

- **Where the device lives.** One data directory per device. Default
  `~/.local/share/myco-llm`, overridden by `MYCO_DATA_DIR`. It holds:
  - `device-did` — the device DID (`did:key:...`).
  - `keyring.json` / `keyring.key` — the keyring sealing every store and the
    key row. Never print or read them.
  - `myco.db` / `waste.db` — encrypted entity/message and transport state.
  - `kanban-state.json` — per-repository board state.
- **What it can act as.** `scripts/myco identity --json` reports `deviceDid`
  and `identities` — the entities this device is a member of. Writes are
  authored as the single identity, or the one named with `--as <did:myco:...>`.
  `--as device` authors as the bare device key.
- **Separate devices.** Run another data directory for another device; never
  share one directory or its keyring between devices.

```bash
scripts/myco identity --json
scripts/myco groups [--search NAME] [--all] [--json]
scripts/myco entity --id <did:myco:...> [--acl] [--as DID] [--json]
```

`groups` lists entities this device or its identities belong to; `--all`
includes locally known non-member entities. `entity` returns the roster and,
with `--acl`, the tier ACLs and what the acting identity can create.

## Joining a person's identity

Use only the device DID the person supplies (their app shows it):

```bash
scripts/myco connect --device <did:key:...> --dry-run --json
scripts/myco connect --device <did:key:...> --json
```

This peers with and trusts that device and sends the app's identity-connect
request. Give the person the `pairingCode`; they accept "Add to Identity" on
their device after matching it, which creates a Join for this device. Then:

```bash
scripts/myco join --dry-run --json
scripts/myco join --json
```

`join` accepts pending Joins naming this device or its identities and reports
the `identities` it can now act as. Before the person accepts, `join` finds
nothing — report that as waiting, never as membership.

## Peers

```bash
scripts/myco peers [--json]
scripts/myco add-peer --peer-link <URL> [--dry-run] [--json]
scripts/myco remove-peer --did <DID> [--dry-run] [--json]
```

Inbound connection requests are journaled, never auto-answered:

```bash
scripts/myco requests --json                 # origin, message, pairingCode
scripts/myco trust --did <DID> --dry-run --json
scripts/myco trust --did <DID> --json
```

Trust only a request the person says they sent, matching the origin DID (or
pairing code) they confirm.

Peer links are identity-only (`myco://peer?id=<DID>`); relays are learned, not
carried in links. Adding a peer never joins a group. Use `remove-peer` only for
a specific stale or unwanted peer, after a `--dry-run`.

## Membership in groups

A member with Join permission invites; the nominee accepts from its own side:

```bash
scripts/myco invite --entity <did:myco:...> --did <DID> --dry-run --json
scripts/myco invite --entity <did:myco:...> --did <DID> --json
```

An invitation is `pending-acceptance`, not membership. If `status` is
`denied`, report which member must invite; never forge or self-join.

## Posts

```bash
scripts/myco post --entity <did:myco:...> --title TITLE \
  [--body TEXT] [--space NAME] [--public] [--as DID] [--dry-run] [--json]
```

Posts are private to members by default and appear as the acting identity —
the person's own name. Always preview before posting on their behalf.

## ACL inspection and edits

```bash
scripts/myco entity --id <did:myco:...> --acl --json
scripts/myco edit-acl --entity <did:myco:...> --slot SLOT --value JSON \
  [--tier public|private] [--as DID] [--dry-run] [--json]
```

Use `response.comment` for replies beneath comments; ordinary slots such as
`note.comment` address comments on posts. Values are permission arrays such as
`["creator","members"]`. Public and private tiers may differ; inspect both. If
`canEdit` is false, report the required grant and stop for human authorization.

## Groups and hosted agents

```bash
scripts/myco create-group --name NAME [--description TEXT] [--template Company] --dry-run --json
scripts/myco create-agent --entity <group> --name NAME --manager <factory DID> \
  --keys minimax,deepseek [--description TEXT] [--instructions-file F] --dry-run --json
scripts/myco share-key --provider minimax --to <factory DID> --json
scripts/myco sync --json
```

`create-group` registers a group as the acting identity, which takes every role
the template names. An agent is a child of a group run by a hosted factory
(`--manager`); pair with the factory first (`connect --device <factory> --peer`).
`--keys` lists providers in priority order: the first is used, the rest are
fallbacks when a provider is out of quota. Each key is read from the desktop
keyring (`secret-tool store --label='Myco minimax' myco llm-minimax`, stored by
the person) and shared with `share-key`; the value is never printed or posted.
The manager collects a key by asking this device for it, so after `share-key`
run `sync` until the manager has it (its agents stop logging "waiting for
secrets"); this device must be reachable when the manager first asks.
For a working team, two more steps are required:

- **Invite the factory into the group** (`invite --entity <group> --did <factory DID>`).
  The factory accepts automatically; agents only scan groups the factory is a
  member of, so without this they never see a mention.
- **Name the agents in the ACL.** Agents cannot be roster members, so grant
  standing by naming their ids in slots (`edit-acl`), including
  `response.comment`: a reply to a post is a comment, and without it every
  reply fails as `not_permitted`.
