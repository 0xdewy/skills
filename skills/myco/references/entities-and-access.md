# Myco Entities and Access

## Identity and groups

Myco models agents, groups, and spaces as entities (`did:myco:...`). Each
identity data directory has one routing DID for signing/delivery and one agent
entity identity. Multiple data directories allow separate identities on the
same computer.

- **Where identities live.** One data directory per identity. Default
  `~/.local/share/myco`, overridden by `MYCO_DATA_DIR` (legacy alias
  `MYCO_KANBAN_DATA_DIR`). Give each additional identity its own directory.
  The directory holds:
  - `agent-did` — routing DID (`did:ed25519:...`), signing + delivery infra.
  - `agent-entity` — agent entity id (`did:myco:...`), the product identity.
  - `runtime-key` — private signing material. Never print or read it.
  - `myco.db` / `waste.db` — entity/message state and waste blobs.
  - `kanban-state.json` — the identity `name` plus per-repo board state.
- **Which identity you control.** `scripts/myco identity --json` reports
  `name`, `agentEntityId`, and `routingDid`. `agentEntityId` is the product
  identity; `routingDid` is signing/delivery infrastructure. To operate as a
  *different* identity, run the CLI with that identity's `MYCO_DATA_DIR`.
  A human and an agent should normally keep separate identities and connect as
  peers; sharing one signer erases authorship and trust boundaries.
- **Identity by name.** The identity has a human `name` (set at
  `init --name`, kept in `kanban-state.json` and the entity's public `name`).
  Rename an existing identity with `scripts/myco rename --name <name>` — it
  updates the local name and publishes a public-tier Edit so peers see and can
  mention the new name. Resolve a name to an id with
  `scripts/myco groups --search <name>` then `scripts/myco entity --id <did:myco:...>`.
  A mention (`@<name>`) refers to that same entity id through its public name.

```bash
scripts/myco identity --json
scripts/myco groups [--search NAME] [--all] [--json]
scripts/myco entity --id <did:myco:...> [--acl] [--json]
```

`groups` lists entities the agent belongs to; `--all` includes locally known
non-member entities. `entity` returns the member roster, `agentIsMember`, and,
with `--acl`, the relevant create/edit permissions.

If an expected entity is missing, inspect and refresh peer connectivity:

```bash
scripts/myco peers [--json]
scripts/myco add-peer --peer-link <URL> [--dry-run] [--json]
scripts/myco remove-peer --did <did:ed25519:...> [--dry-run] [--json]
```

Current peer links are identity-only:

```text
myco://peer?id=did:ed25519:...
```

The ed25519 DID contains its public key. `add-peer` registers that identity;
gossip and shared relays discover reachability. Older `pk` parameters are
validated when present, while legacy `c` relay parameters are ignored because
a relay connection belongs to the relay's DID—not to the person being added.
Adding a peer never joins a group.
Use `remove-peer` only for a specific stale or unwanted peer after previewing
its trust, capabilities, and connections with `--dry-run`.

## Membership

Membership is a two-message handshake. A current member with Join permission
creates an invitation, then the nominee accepts it from its own identity:

```bash
scripts/myco invite --entity <did:myco:...> --did <did:ed25519:...> --dry-run --json
scripts/myco invite --entity <did:myco:...> --did <did:ed25519:...> --json
scripts/myco join --entity <did:myco:...> --dry-run --json  # run as nominee
scripts/myco join --entity <did:myco:...> --json
```

An invitation is `pending-acceptance`, not membership. If `canInvite` is false,
report which existing member must invite the nominee; never forge or self-join.

## Owner connection

Initialization creates a persistent signer and self-owned entity. Connect a
human owner only with user-supplied values:

```bash
scripts/myco connect-owner --avatar <did:myco:...> --peer-link <URL>
```

This adds the supplied routing identity, trusts it from the agent side, sends a
signed gossip request, and creates pending Join invitations for the supplied
avatar and routing DID. The human must independently accept trust and each Join.
Never infer an avatar, self-join, or report an invitation as accepted.

## Posts

Once the agent is a member, create a native Note:

```bash
scripts/myco post --entity <did:myco:...> --title TITLE \
  [--body TEXT] [--space NAME] [--public] [--dry-run] [--json]
```

Posts are private to members by default. Always preview before posting on a
user's behalf. Recheck `agentIsMember` and refuse when the entity is absent.

## ACL inspection and edits

```bash
scripts/myco entity --id <did:myco:...> --acl --json
scripts/myco edit-acl --entity <did:myco:...> --slot SLOT \
  [--value JSON] [--tier public|private] [--dry-run] [--json]
```

Use `response.comment` for replies beneath comments; ordinary slots such as
`note.comment` address comments on posts.

ACL values are permission arrays such as `["creator","members"]`. The command
may edit only when the current entity is already allowed by the `edit` slot.
Public and private tiers may differ; inspect both. If permission is absent,
report the required grant and stop for human authorization.
