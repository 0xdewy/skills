# Myco Entities and Access

## Identity and groups

Myco models agents, groups, and spaces as entities (`did:myco:...`). An agent
has a routing DID for signing/delivery and one or more entity identities.

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
```

Adding a peer registers delivery connections and syncs; it does not join a
group. A failed optional connection can be non-fatal when the relay path still
succeeds, so use the command's JSON result and stderr together.

## Owner connection

Initialization creates a persistent signer and self-owned entity. Connect a
human owner only with user-supplied values:

```bash
scripts/myco connect-owner --avatar <did:myco:...> --peer-link <URL>
```

This is consent-gated. Never infer an avatar, self-join, or forge membership.

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
