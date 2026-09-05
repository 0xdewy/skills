# Myco Entities and Access

## Identity and groups

Myco models agents, groups, and spaces as entities (`did:myco:...`). Each
identity data directory has one routing DID for signing/delivery and one agent
entity identity. Multiple data directories allow separate identities on the
same computer.

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

ACL values are permission arrays such as `["creator","members"]`. The command
may edit only when the current entity is already allowed by the `edit` slot.
Public and private tiers may differ; inspect both. If permission is absent,
report the required grant and stop for human authorization.
