# EVMole Reference

Source: https://github.com/cdump/evmole
Last verified: 2026-07-10 (evmole 0.8.5)

EVMole symbolically follows calldata through EVM bytecode to recover function
selectors, argument types, state mutability, storage layout, CBOR metadata, and
control-flow information. Results are inference, not a substitute for a verified
ABI or source.

## Prefer the Existing Tool

Foundry's `cast selectors` uses EVMole internally:

```bash
BYTECODE=$(cast code "$ADDRESS" --rpc-url "$RPC_URL")
cast selectors "$BYTECODE"
cast selectors --resolve "$BYTECODE"
```

Use the library API only when structured integration or additional analyses are
required.

## Rust

```toml
[dependencies]
evmole = "0.8.5"
hex = "0.4"
```

```rust
let code = hex::decode(bytecode.trim_start_matches("0x"))?;
let info = evmole::contract_info(
    evmole::ContractInfoArgs::new(&code)
        .with_selectors()
        .with_arguments()
        .with_state_mutability(),
);
println!("{info:?}");
```

Confirm the exact builder methods in the pinned crate's rustdoc before adding
less common analyses such as storage layout or CFG extraction.

## Python

```bash
python -m pip install --upgrade evmole
```

```python
from evmole import contract_info

info = contract_info(
    bytecode,
    selectors=True,
    arguments=True,
    state_mutability=True,
)
```

## Go and JavaScript

The official repository maintains Go and JavaScript bindings. Follow its current
README for installation and signatures; do not translate the Rust types by hand.

## Interpretation Rules

1. Strip an optional `0x` prefix and reject malformed hex.
2. Confirm whether the bytecode is creation or deployed runtime code.
3. For proxies, analyze the implementation bytecode as well as the proxy shell.
4. Keep selector, argument, mutability, storage, and CFG confidence separate.
5. Resolve selectors against a signature database only as candidate names;
   four-byte collisions are possible.
6. Compare inferred output with verified ABI/source when available.

Compiler versions, handcrafted dispatchers, unreachable code, metadata, and
proxy patterns can change inference quality. Report uncertainty instead of
inventing an ABI.

## Minimal Output

For each recovered function, retain:

- selector and bytecode offset;
- inferred argument types and mutability;
- resolved signature candidate, if any;
- source of corroboration;
- uncertainty or ambiguity.

For security work, pair EVMole with concrete disassembly/trace evidence before
claiming reachability or exploitability.
