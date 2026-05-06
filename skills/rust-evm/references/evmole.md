# evmole Reference

Source: https://github.com/cdump/evmole

evmole extracts structured information from EVM bytecode using **symbolic
execution** — it actually traces CALLDATA flow through the dispatcher rather
than static pattern matching. Works on unverified contracts, handles complex
dispatchers, proxy patterns, and Vyper/Solidity differences.

**foundry integration:** `cast selectors <bytecode>` calls evmole internally.

---

## What it extracts

| Feature | Accuracy (1000 largest contracts) |
|---------|----------------------------------|
| Function selectors (4-byte) | 0 false negatives |
| Function state mutability | 0% error rate |
| Function arguments | 14% error rate (best-in-class) |
| Storage layout | Supported via `contract_info()` |

Speed: 18ms for 24,427 functions across 1,000 contracts.

---

## Rust API

```toml
# Cargo.toml
evmole = "0.6"
```

```rust
use evmole::{contract_info, ContractInfoArgs, ContractInfo, Function, StorageRecord};

// Full analysis in one call
let bytecode: Vec<u8> = hex::decode("608060405260...").unwrap();
let info: ContractInfo = contract_info(ContractInfoArgs::new(&bytecode)
    .with_selectors()
    .with_arguments()
    .with_state_mutability()
    .with_storage()
);

for func in &info.functions {
    println!(
        "selector={} args={:?} mutability={:?}",
        hex::encode(func.selector),  // [u8; 4]
        func.arguments,              // Option<String> e.g. "uint256,address"
        func.state_mutability,       // Option<StateMutability>
    );
}

for record in &info.storage {
    println!("slot={} offset={} type={:?}", record.slot, record.offset, record.type_);
}
```

**StateMutability variants:**
```rust
pub enum StateMutability {
    Pure,       // no state read or write
    View,       // reads state, no write
    NonPayable, // writes state, no ETH accepted
    Payable,    // writes state, accepts ETH (CALLVALUE check present)
}
```

**StorageRecord fields:**
```rust
pub struct StorageRecord {
    pub slot: U256,          // storage slot number
    pub offset: u8,          // byte offset within slot (for packed values)
    pub type_: StorageType,  // Uint(bits), Bool, Address, Bytes(n), etc.
    pub reads: Vec<[u8;4]>,  // selectors that read this slot
    pub writes: Vec<[u8;4]>, // selectors that write this slot
}
```

---

## Python API

```bash
pip install evmole
```

```python
from evmole import contract_info, ContractInfoArgs

bytecode = bytes.fromhex("608060405260...")

info = contract_info(
    ContractInfoArgs(bytecode)
    .with_selectors()
    .with_arguments()
    .with_state_mutability()
    .with_storage()
)

for func in info.functions:
    print(f"0x{func.selector.hex()} ({func.arguments}) [{func.state_mutability}]")

for record in info.storage:
    print(f"slot={record.slot} offset={record.offset} type={record.type_}")
```

---

## CLI usage

```bash
# Install
pip install evmole   # or: cargo install evmole

# Analyze bytecode from hex string
evmole selectors 0x608060405260...
evmole arguments 0x608060405260... a9059cbb  # args for one selector
evmole state-mutability 0x608060405260...
evmole all 0x608060405260...    # full report

# From file
evmole all --file contract.bin  # raw binary
evmole all --hex-file contract.hex

# JSON output
evmole all 0x... --json
```

---

## Integration patterns

### Fetch + analyze a deployed contract

```bash
# Get bytecode
BYTECODE=$(cast code 0xUniswapV2Router --rpc-url $RPC)
# Extract selectors
cast selectors $BYTECODE
# Resolve to signatures
cast selectors $BYTECODE | awk '{print $1}' | xargs -I{} cast 4byte {}
```

```python
import subprocess, json
from evmole import contract_info, ContractInfoArgs

# Get bytecode via cast
result = subprocess.run(
    ["cast", "code", addr, "--rpc-url", rpc],
    capture_output=True, text=True
)
bytecode = bytes.fromhex(result.stdout.strip().removeprefix("0x"))
info = contract_info(ContractInfoArgs(bytecode).with_selectors().with_arguments())
```

### Reconstruct ABI from unverified contract

```python
from evmole import contract_info, ContractInfoArgs

def reconstruct_abi(bytecode_hex: str) -> list[dict]:
    bytecode = bytes.fromhex(bytecode_hex.removeprefix("0x"))
    info = contract_info(
        ContractInfoArgs(bytecode)
        .with_selectors()
        .with_arguments()
        .with_state_mutability()
    )
    abi = []
    for func in info.functions:
        sel = func.selector.hex()
        args = func.arguments or ""
        arg_list = [{"type": t.strip()} for t in args.split(",") if t.strip()]
        mut = {
            "pure": "pure", "view": "view",
            "nonpayable": "nonpayable", "payable": "payable"
        }.get(str(func.state_mutability).lower(), "nonpayable")
        abi.append({
            "type": "function",
            "selector": f"0x{sel}",
            "inputs": arg_list,
            "stateMutability": mut,
        })
    return abi
```

---

## How it works (internals)

evmole implements a custom EVM interpreter that runs in "symbolic mode":
- CALLDATA bytes are represented as **symbolic variables** rather than concrete values
- The interpreter traces which symbolic calldata bytes flow into which comparison operations
- By tracking how `CALLDATALOAD(0)` is shifted and compared, it identifies the 4-byte selector
- Argument extraction follows the same approach: tracks how remaining calldata offsets map to ABI types
- State mutability: presence of SSTORE or CALLVALUE check determines write/payable status

This beats regex/pattern matching approaches on:
- Non-standard dispatchers (binary search, jump tables)
- Proxy contracts that forward selectors
- Compiler versions that generate unusual dispatcher patterns
- Vyper contracts (different dispatch structure than Solidity)
