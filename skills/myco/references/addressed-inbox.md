# Threadripper addressed-message responder

The user systemd timer polls Myco once a minute. Polling does not invoke a model.
An OpenCode session using `deepseek/deepseek-v4-flash` starts only for a validated,
new Myco message signed by a device in a local inbox config and either:

- containing an explicit `@threadripper`, `@<threadripper routing DID>`, or
  `@<threadripper entity DID>` mention outside quotes, code and URLs; or
- a comment directly replying to a message signed and authored by threadripper.

Names or DIDs without `@`, ordinary group activity, assignments alone, edits,
reactions, blocked/deleted messages, third-party signers and self-replies do not
launch a worker. The host checks reply permissions before spending.

OpenCode has no tools, runs at most one agent step, has a three-minute deadline,
and returns text. The host replies beneath the triggering message when permitted. If nested comments
are disabled, it posts in the same thread and visibility tier, explicitly addressing
the sender and referencing the triggering message. It never changes group ACLs. Provider
credentials remain in OpenCode's existing credential store, outside this repo.
This is a conversational responder; it cannot execute requested machine work.

## Spending and recovery

The journal is fsynced before launching OpenCode. Each message can launch once;
failures and interrupted claims do not automatically retry paid inference.
Generated replies are saved before posting; posting retries reuse that response
and a deterministic nonce. The worker permits one session per poll, six per
rolling hour, and twenty per rolling day. These are session caps, not dollar
caps. Messages older than activation or 24 hours are ignored.

The first initialization marks all existing messages seen. A missing, corrupt,
or mismatched journal fails closed; it must never silently reset on restart.
Do not delete the journal to retry a failed message: send a new explicit reply
or mention instead. `--check` never invokes OpenCode or changes the journal.

## Operation

This is an optional skill-side OpenCode bridge, separate from the native
`myco-agent` hosted factory. It reuses the skill's existing identity bootstrap
and installed Myco dependencies; it does not alter the hosted agent runtime.
Enable it only when the user explicitly requests automatic paid replies.

Keep configuration and systemd units outside source control. Create a config
with `routingDid`, `agentEntityId` (from `scripts/myco identity --json`), an
explicit `allowedSigners` list, and absolute `stateDir` and `opencode` paths.
Only add a device when the user has identified it. Group membership alone is
not permission to spend. Never put API keys in this config.

Initialize once and preview without spending:

```sh
scripts/myco inbox --config /absolute/path/inbox.json --initialize
scripts/myco inbox --config /absolute/path/inbox.json --check
```

Schedule `scripts/myco inbox --config /absolute/path/inbox.json` in a user
systemd oneshot service with a one-minute timer. Use absolute paths and a PATH
containing Node and OpenCode. Set `UMask=0077`, `TimeoutStartSec=240`,
`KillMode=control-group` and `NoNewPrivileges=yes`. Initialization must not be
part of the scheduled command. The wrapper serializes polling and normal CLI
operations with flock; bespoke processes using this identity must share
`<Myco data directory>/threadripper-inbox.lock` too.

The journal lives at `<stateDir>/journal.json` (mode 0600). Stop the timer and
wait for its service to finish before moving code or state. Keep the journal
and bound identity intact when upgrading. Inspect service logs for `launch`,
`launched`, `responded` and `pending`; message bodies and provider diagnostics
are not printed. OpenCode retains its normal session history.

On the original host the unit is named `threadripper-inbox` and user lingering
keeps it running after logout. Its machine-specific config is under
`~/.config/myco/`, with units under `~/.config/systemd/user/`.

Run regression tests without calling any provider:

```sh
node --import /path/to/myco-agent/node_modules/tsx/dist/loader.mjs --test scripts/addressed-inbox.test.ts
```

Implementation references: [OpenCode CLI](https://opencode.ai/docs/cli/) and
[agent permissions/steps](https://opencode.ai/docs/agents/).
