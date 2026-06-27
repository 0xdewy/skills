---
name: rust-evm
description: >-
  Expert EVM/Rust/Foundry skill for revm, forge/cast/anvil/chisel, evmole,
  bytecode analysis, Yul/inline assembly, opcodes, gas, calldata, memory, storage,
  selectors, dispatchers, traces, CREATE2, delegatecall, transient storage,
  EIP-1153/EIP-4844, and custom precompiles. TRIGGER on: "revm", "foundry",
  "forge", "cast", "anvil", "evm bytecode", "evm opcodes", "yul",
  "inline assembly", "evm storage layout", "evm trace", "revm inspector",
  "evmole", "calldata", "function selector", "solidity assembly", "decompile",
  "gas optimization assembly". SKIP on: high-level Solidity without bytecode or
  assembly angle, generic Rust unrelated to EVM, and ethers/web3 questions unless
  raw calldata, bytecode, or traces are involved.
license: MIT
metadata:
  author: iamky1e
  version: 1.0.0
  category: security
  tags:
    - evm
    - rust
    - revm
    - foundry
    - forge
    - cast
    - yul
    - bytecode
    - solidity
    - evmole
    - opcodes
    - assembly
---

# rust-evm

Expert-level EVM engineering skill. Covers the full stack from opcode semantics
through bytecode analysis, Yul/assembly authoring, revm integration in Rust,

Ground every claim in the reference files or the actual code/bytecode — never
speculate about gas costs, opcodes, or revm APIs you have not checked. Open the
relevant file (or run `cast`/`forge`) before asserting how something behaves.
and Foundry tooling.

## Freshness & Source Discipline

Load `skills/common/patterns/knowledge.md` for source hierarchy, freshness, and
inference-labeling rules.

EVM details change at fork boundaries and tool APIs change across releases. For
answers that depend on current gas costs, opcode availability, revm types,
Foundry flags, or evmole APIs:

1. Load the relevant local reference first.
2. State the assumed fork or tool version when it affects correctness.
3. If the task asks for current behavior and the local reference does not name a
   verification date or version, verify against primary sources before giving
   production guidance: Ethereum EIPs/specs for protocol behavior, Solidity docs
   for compiler/Yul semantics, and official crate/tool documentation for APIs.
4. Never present guessed gas costs or unstable tool APIs as certain. If you are
   inferring from known EVM rules, say that explicitly.

---

## Routing: Which Reference to Load

| Task type | Load reference |
|-----------|---------------|
| Working with revm in Rust (types, Inspector, Database, builder) | `references/revm.md` |
| forge / cast / anvil / chisel commands and patterns | `references/foundry.md` |
| Bytecode analysis, evmole API | `references/evmole.md` |
| Yul / inline assembly authoring or reading | `references/yul.md` |
| Opcode semantics, gas costs, stack effects | `references/opcodes.md` |

Load only the reference relevant to the current task. For cross-cutting tasks
(e.g. "write a revm inspector that traces Yul-level opcodes"), load both.

---

## Core EVM Mental Model

The EVM is a **stack machine** with 256-bit words, running inside an isolated
context defined by:

- **Stack** — max 1024 items, 32-byte words; every opcode consumes/produces here
- **Memory** — byte-addressable, zero-initialized, expands in 32-byte chunks;
  expansion costs gas quadratically (cheap until ~700 bytes, expensive after)
- **Storage** — persistent 32→32 word mapping per contract address; cold/warm
  access model (EIP-2929: cold SLOAD=2100, warm SLOAD=100)
- **Transient storage** — EIP-1153, cleared after each transaction; TLOAD/TSTORE
  cost 100 gas; useful for reentrancy locks without SSTORE overhead
- **Calldata** — read-only input; CALLDATALOAD(offset) loads 32 bytes; the
  first 4 bytes are the function selector (keccak256 of signature, big-endian)
- **Return data** — set by RETURN or REVERT from sub-calls; accessed via
  RETURNDATASIZE / RETURNDATACOPY

**Call types and context preservation:**

| Opcode | msg.sender | msg.value | storage context |
|--------|-----------|-----------|-----------------|
| CALL | callee | forwarded | callee's storage |
| DELEGATECALL | preserved (caller's caller) | preserved | **caller's storage** |
| STATICCALL | callee | 0 | callee's storage (read-only) |
| CALLCODE | callee | forwarded | **caller's storage** (deprecated) |

**Contract creation:**
- `CREATE` — address = keccak256(rlp([sender, nonce]))[12:]
- `CREATE2` — address = keccak256(0xff ++ sender ++ salt ++ keccak256(initcode))[12:]
- Initcode runs, its RETURN value becomes the deployed bytecode

**ABI encoding (essential):**
- Selector: `keccak256("funcName(type1,type2)")[0:4]`
- Static types (uint, bool, address, bytesN) — encoded in-place, 32-byte padded
- Dynamic types (bytes, string, arrays) — encoded as offset pointer + length + data
- `abi.encode` pads everything; `abi.encodePacked` strips padding (no selector)

---

## Key Patterns by Task

### Bytecode analysis workflow
1. Fetch bytecode: `cast code <addr> --rpc-url $RPC`
2. Extract selectors: `cast selectors <bytecode>` (uses evmole under the hood)
3. Resolve signatures: `cast 4byte <selector>` → openchain.xyz lookup
4. Deep analysis: use evmole `contract_info()` for full ABI + storage layout
5. Trace a tx: `cast run <txhash> --rpc-url $RPC` for full opcode trace
6. For custom analysis: load `references/evmole.md` and `references/revm.md`

### Gas optimization (assembly path)
1. Profile first: `forge test --gas-report`
2. Identify hot paths; write tight Yul with `assembly { ... }`
3. Key wins: replace mapping reads with direct SLOAD, pack storage slots,
   use `calldataload` instead of `abi.decode` for simple inputs, avoid
   memory allocation with scratch space (0x00–0x3f free memory pointer)
4. Load `references/yul.md` for builtins and idioms

### Writing a revm Inspector (tracing / fuzzing harness)
Load `references/revm.md` — covers the full Inspector trait and builder.

### Running a Foundry test with fork
```bash
forge test --fork-url $RPC --fork-block-number 20000000 -vvvv --match-test testFoo
```
Load `references/foundry.md` for full cheatcode reference.

---

## Solidity Storage Layout Rules (critical for assembly)

Slot assignment (Solidity compiler):
- State variables packed sequentially, starting at slot 0
- Values < 32 bytes packed into the same slot if they fit (right-aligned)
- `mapping(K => V)`: slot of value at key `k` = `keccak256(k ++ slot_index)`
- `mapping` nested: `keccak256(k2 ++ keccak256(k1 ++ outer_slot))`
- Dynamic arrays: length at `slot_index`, element `i` at `keccak256(slot_index) + i`
- Fixed arrays: element `i` at `slot_index + i` (if element ≤ 32 bytes)
- `bytes`/`string` < 32 bytes: stored in the slot itself (length * 2 in low byte)
- `bytes`/`string` ≥ 32 bytes: length * 2 + 1 in slot, data at `keccak256(slot)`

Read any slot with: `cast storage <addr> <slot> --rpc-url $RPC`
Inspect storage layout: `forge inspect <Contract> storageLayout`

---

## Common Gotchas

- **Memory safety in Yul**: Solidity reserves 0x00–0x3f as scratch, 0x40 as
  free memory pointer, 0x60 as zero slot. Writing below `mload(0x40)` without
  updating it corrupts Solidity's allocator. Use scratch (0x00–0x3f) only for
  hash intermediates that don't persist across calls.
- **delegatecall storage collisions**: Proxy and implementation must share
  identical storage layouts. Use ERC-1967 slots (keccak256 - 1) to avoid
  collision with implementation variables.
- **PUSH0 (EIP-3855)** introduced in Shanghai — produces `0x5F`. Code compiled
  with `--evm-version paris` or earlier won't emit PUSH0; important for chains
  that haven't upgraded.
- **dirty revert data**: After a failed sub-call, RETURNDATASIZE is still the
  size of the revert data — copy it before making another call.
- **gas forwarding**: `call{gas: X}(...)` — use `gasleft() - 2300` pattern or
  explicit gas stipend. EIP-150 means only 63/64 of remaining gas can be
  forwarded per call frame.
- **cold/warm accounts (EIP-2929)**: First access to an address in a tx costs
  2600 extra gas. Use `access_list` to pre-warm slots: `cast access-list`.
