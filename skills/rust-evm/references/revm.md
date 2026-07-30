# revm Reference

Source: https://github.com/bluealloy/revm

## Crate Layout

| Crate | Purpose |
|-------|---------|
| `revm` | Top-level re-exports, `Context`, `Evm`, `EvmBuilder` |
| `revm-interpreter` | Opcode dispatch loop, `Interpreter`, stack/memory |
| `revm-primitives` | `TxEnv`, `BlockEnv`, `CfgEnv`, `ExecutionResult`, `Address`, `U256`, `Bytes`, `Bytecode` |
| `revm-precompile` | Built-in precompiles (sha2, ripemd, ecrecover, bn128, etc.) |
| `revm-database` | `CacheDB`, `EmptyDB`, `WrapDatabaseRef` helpers |

Add to `Cargo.toml`:
```toml
revm = { version = "19", features = ["std", "serde"] }
# optional: alloy types integration
revm = { version = "19", features = ["std", "alloy-primitives"] }
```

---

## Core Types

### Context / Evm

```rust
use revm::{
    Context, MainContext, Evm,
    primitives::{TxEnv, BlockEnv, CfgEnv, SpecId, U256, Address, Bytes},
    db::{CacheDB, EmptyDB},
};

// Simplest mainnet context
let mut evm = Context::mainnet()
    .with_db(CacheDB::new(EmptyDB::default()))
    .with_block(block_env)      // BlockEnv
    .with_tx(tx_env)            // TxEnv
    .build_mainnet();

let result = evm.transact().unwrap();
// or with inspector:
let result = evm.inspect_tx(tx, &mut my_inspector).unwrap();
```

### TxEnv

```rust
TxEnv {
    caller: Address,           // msg.sender / tx.origin
    gas_limit: u64,
    gas_price: U256,           // in wei per gas unit
    transact_to: TxKind,       // TxKind::Call(address) or TxKind::Create
    value: U256,               // wei sent
    data: Bytes,               // calldata (encoded ABI)
    nonce: u64,
    chain_id: Option<u64>,
    access_list: Vec<(Address, Vec<U256>)>,
    gas_priority_fee: Option<U256>,  // EIP-1559 tip
    blob_hashes: Vec<B256>,          // EIP-4844
    max_fee_per_blob_gas: Option<U256>,
    ..Default::default()
}
```

### BlockEnv

```rust
BlockEnv {
    number: U256,
    coinbase: Address,
    timestamp: U256,
    gas_limit: U256,
    basefee: U256,          // EIP-1559 base fee
    difficulty: U256,
    prevrandao: Option<B256>,
    blob_excess_gas_and_price: Option<BlobExcessGasAndPrice>,  // EIP-4844
    ..Default::default()
}
```

### CfgEnv

```rust
CfgEnv {
    chain_id: u64,
    spec: SpecId,    // Hardfork: SpecId::CANCUN, SHANGHAI, MERGE, etc.
    limit_contract_code_size: Option<usize>,
    disable_nonce_check: bool,
    disable_base_fee: bool,
    ..Default::default()
}
```

**SpecId variants (in order):**
`FRONTIER → HOMESTEAD → DAO_FORK → TANGERINE → SPURIOUS_DRAGON → BYZANTIUM → CONSTANTINOPLE → PETERSBURG → ISTANBUL → MUIR_GLACIER → BERLIN → LONDON → ARROW_GLACIER → GRAY_GLACIER → MERGE → SHANGHAI → CANCUN → PRAGUE → LATEST`

---

## ExecutionResult

```rust
match result {
    ExecutionResult::Success { reason, gas_used, gas_refunded, logs, output } => {
        match output {
            Output::Call(bytes) => { /* return data */ }
            Output::Create(bytes, Some(address)) => { /* deployed contract address */ }
        }
        // reason: Eval::Stop | Return | SelfDestruct | EofReturnContract
    }
    ExecutionResult::Revert { gas_used, output } => {
        // output contains ABI-encoded revert reason if any
        // decode: abi.decode(output[4:], (string)) for require/revert("msg")
    }
    ExecutionResult::Halt { reason, gas_used } => {
        // reason: HaltReason::OutOfGas | InvalidJump | OpcodeNotFound | etc.
    }
}
```

---

## Database Trait

Implement to connect revm to any state backend (live node, custom trie, etc.):

```rust
use revm::database::{Database, DatabaseRef};
use revm::primitives::{AccountInfo, Bytecode, Address, B256, U256};

pub trait Database {
    type Error;

    // Load basic account info (nonce, balance, code_hash)
    fn basic(&mut self, address: Address) -> Result<Option<AccountInfo>, Self::Error>;

    // Load bytecode by its keccak256 hash
    fn code_by_hash(&mut self, code_hash: B256) -> Result<Bytecode, Self::Error>;

    // Load a storage slot value
    fn storage(&mut self, address: Address, index: U256) -> Result<U256, Self::Error>;

    // Get a block hash by number
    fn block_hash(&mut self, number: u64) -> Result<B256, Self::Error>;
}
```

**CacheDB** wraps any `DatabaseRef` and caches all reads + tracks writes:
```rust
use revm::db::{CacheDB, EthersDB};  // or alloy provider variant

let mut cache = CacheDB::new(EmptyDB::default());
// Pre-insert account for testing:
cache.insert_account_info(addr, AccountInfo {
    balance: U256::from(1e18 as u64),
    nonce: 0,
    code_hash: KECCAK_EMPTY,
    code: None,
});
// Insert a storage slot:
cache.insert_account_storage(addr, U256::from(slot), U256::from(value)).unwrap();
```

---

## Inspector Trait

The Inspector intercepts every step of execution. Use it for tracing, coverage,
fuzzing invariant checks, custom gas metering, or exploit detection.

```rust
use revm::{
    Inspector,
    interpreter::{
        Interpreter, InterpreterTypes,
        CallInputs, CallOutcome,
        CreateInputs, CreateOutcome,
    },
    primitives::Log,
};

pub struct MyInspector {
    pub call_depth: u64,
    pub opcode_counts: HashMap<u8, u64>,
}

impl<CTX, INTR: InterpreterTypes> Inspector<CTX, INTR> for MyInspector {
    // Called BEFORE each opcode executes
    fn step(&mut self, interp: &mut Interpreter<INTR>, _ctx: &mut CTX) {
        let opcode = interp.current_opcode();
        *self.opcode_counts.entry(opcode).or_default() += 1;
        // Read stack: interp.stack.peek(0) → top of stack
        // Read PC: interp.program_counter()
        // Read memory: interp.shared_memory.slice(offset, len)
    }

    // Called AFTER each opcode executes
    fn step_end(&mut self, interp: &mut Interpreter<INTR>, _ctx: &mut CTX) {}

    // Called before a CALL/CALLCODE/DELEGATECALL/STATICCALL
    // Return Some(outcome) to SHORT-CIRCUIT execution (override the call)
    // Return None to proceed normally
    fn call(&mut self, _ctx: &mut CTX, inputs: &mut CallInputs) -> Option<CallOutcome> {
        self.call_depth += 1;
        println!("CALL to {:?} value={}", inputs.target_address, inputs.call_value());
        None
    }

    fn call_end(&mut self, _ctx: &mut CTX, _inputs: &CallInputs, outcome: &mut CallOutcome) {
        self.call_depth -= 1;
    }

    // Called before CREATE/CREATE2; return Some to override
    fn create(&mut self, _ctx: &mut CTX, inputs: &mut CreateInputs) -> Option<CreateOutcome> {
        None
    }

    fn create_end(&mut self, _ctx: &mut CTX, _inputs: &CreateInputs, outcome: &mut CreateOutcome) {}

    // Called when LOG0–LOG4 executes
    fn log(&mut self, _ctx: &mut CTX, log: Log) {
        println!("LOG: {:?}", log.topics());
    }

    // Called when SELFDESTRUCT executes
    fn selfdestruct(&mut self, contract: Address, target: Address, value: U256) {}
}
```

Wiring the inspector:
```rust
let mut evm = Context::mainnet()
    .with_db(db)
    .with_block(block)
    .build_mainnet();

let mut inspector = MyInspector::default();
let result = evm.inspect_tx(tx, &mut inspector).unwrap();
```

---

## Common revm Patterns

### Fork mainnet state (using alloy provider)

```rust
use revm::db::AlloyDB;  // revm feature: "alloy"
use alloy::providers::ProviderBuilder;

let provider = ProviderBuilder::new().on_http(rpc_url);
let block_id = BlockId::Number(BlockNumberOrTag::Latest);
let db = AlloyDB::new(provider, block_id);
let mut cache = CacheDB::new(db);

let mut evm = Context::mainnet()
    .with_db(&mut cache)
    .modify_cfg_chained(|cfg| cfg.disable_base_fee = true)
    .build_mainnet();
```

### Simulate a transaction against live state

```rust
let tx = TxEnv {
    caller: from_address,
    transact_to: TxKind::Call(contract_address),
    data: calldata.into(),
    value: U256::ZERO,
    gas_limit: 1_000_000,
    gas_price: U256::from(1_000_000_000u64),
    ..Default::default()
};
evm.context.modify_tx(|t| *t = tx);
let result = evm.transact_commit().unwrap();  // commits state changes to CacheDB
// vs transact() which doesn't commit (read-only simulation)
```

### Deploy a contract

```rust
let tx = TxEnv {
    caller: deployer,
    transact_to: TxKind::Create,
    data: initcode.into(),  // ABI-encoded constructor args appended to bytecode
    value: U256::ZERO,
    gas_limit: 5_000_000,
    ..Default::default()
};
if let ExecutionResult::Success { output: Output::Create(_, Some(addr)), .. } = result {
    println!("Deployed at {:?}", addr);
}
```

### Bytecode from hex string

```rust
use revm::primitives::Bytecode;
let bytecode = Bytecode::new_raw(Bytes::from(hex::decode("60806040...").unwrap()));
// Insert into account:
let code_hash = bytecode.hash_slow();
cache.insert_account_info(addr, AccountInfo {
    code_hash,
    code: Some(bytecode),
    balance: U256::ZERO,
    nonce: 1,
});
```
