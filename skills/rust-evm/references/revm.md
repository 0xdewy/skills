# revm Reference

Source: https://github.com/bluealloy/revm
Last verified: 2026-07-10 (revm 40.0.2)

`revm` changes quickly and tracks current stable Rust. Treat project types and
examples as authoritative when the installed version differs from this marker.

## Start Here

```toml
[dependencies]
revm = "40.0.2"
```

Use `cargo tree -i revm` in an existing project before changing its version or
features. Read the matching release's rustdoc or source for exact generic bounds.

The current execution API centers on a context, transaction, database, and
hardfork configuration:

```rust
use revm::{Context, MainContext};

let mut evm = Context::mainnet()
    .with_block(block)
    .build_mainnet();

let result = evm.transact(tx)?;
```

For inspection, attach an inspector and execute the same transaction:

```rust
let mut evm = evm.with_inspector(tracer);
let result = evm.inspect_tx(tx)?;
```

These snippets mirror the upstream README. Copy complete imports and type
construction from the examples shipped with the exact dependency version.

## Choose the API Layer

- **Execution API:** configure Ethereum state and execute transactions.
- **Inspector API:** observe or override steps, calls, creates, logs, and
  self-destructs for traces, coverage, or custom analysis.
- **Framework API:** extend handlers, context types, instructions, or EVM
  variants. Use only when the execution and inspector APIs cannot express the
  requirement.

Primary crates include `revm`, `revm-interpreter`, `revm-precompile`,
`revm-database`, and context/handler/state crates. Confirm names in the current
workspace because the crate split is not a stable compatibility boundary.

## Database Contract

A database supplies account basics, code by hash, storage slots, and block
hashes. Prefer the database traits re-exported by the installed `revm` version.
Common patterns:

- an empty database for isolated execution;
- a cache over a read-only backend for repeated reads and state changes;
- a provider-backed database for forked state;
- a custom database for snapshots, proofs, or deterministic fixtures.

Distinguish read-only execution from state-committing execution. Never assume a
method commits merely because the returned result is successful; verify the
method contract for the pinned version.

## Transaction and Block Inputs

Build inputs with the types and defaults exported by the pinned version. Check:

- caller, call/create kind, calldata, value, nonce, and chain ID;
- gas limit, fee fields, access list, authorization list, and blob fields;
- block number, timestamp, beneficiary, gas limit, base fee, randomness, and
  blob gas fields;
- configured hardfork/spec ID.

Avoid reproducing struct layouts from memory. They are version-sensitive and
new forks add fields.

## Result Handling

Keep these states distinct:

- success with call output or created-contract output;
- EVM revert with return bytes;
- exceptional halt such as out-of-gas or invalid instruction;
- host/database/configuration error.

Always report the configured hardfork and whether state was committed. Decode
revert bytes only after checking their length and selector.

## Verification

For integration code:

```bash
cargo check
cargo test
cargo tree -i revm
```

For semantic changes, add a small transaction fixture and assert result class,
output, gas behavior where relevant, logs, and post-state. Pin the hardfork so a
future default change cannot silently alter the test.
