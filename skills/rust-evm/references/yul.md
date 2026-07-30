# Yul Reference

Source: https://docs.soliditylang.org/en/v0.8.35/yul.html

Yul is a low-level language that compiles to EVM bytecode (and can target
other backends). It's used as Solidity's intermediate representation (`--via-ir`)
and as inline assembly (`assembly { ... }` blocks in Solidity).

---

## Inline Assembly in Solidity

```solidity
assembly {
    // Yul code here — direct access to EVM
    let x := mload(0x40)       // read free memory pointer
    mstore(0x40, add(x, 0x20)) // advance free memory pointer
}
```

**Scope rules:** Solidity variables are accessible inside assembly by name (as
their slot/pointer). Storage variables are NOT directly accessible by name —
you must use `.slot` and `.offset` suffixes:

```solidity
uint256 public myVar;    // at storage slot 0

assembly {
    let slot := myVar.slot      // → 0
    let val := sload(slot)
}

// For packed variables:
assembly {
    let s := packedVar.slot
    let o := packedVar.offset   // byte offset within slot
    let val := byte(sub(31, o), sload(s))  // extract byte
}
```

**Memory layout (Solidity conventions):**
- `0x00–0x3f`: Scratch space (safe to use without saving)
- `0x40`: Free memory pointer — ALWAYS update if you allocate
- `0x60`: Zero slot — must always be zero, never write here
- `0x80+`: Heap starts here (after `new` / `abi.encode` etc.)

**Accessing function parameters in assembly:**
```solidity
function foo(uint256 x) external returns (uint256) {
    assembly {
        // x is on the stack as a local variable:
        let result := mul(x, 2)
        mstore(0x00, result)
        return(0x00, 0x20)
    }
}
```

---

## Yul Syntax

### Variable declaration and assignment

```yul
let x := 5
let y := add(x, 3)
x := mul(y, 2)    // reassign (no 'let')
```

### Functions

```yul
function myFunc(a, b) -> result {
    result := add(a, b)
}

// Multiple return values:
function divmod(a, b) -> quot, rem {
    quot := div(a, b)
    rem := mod(a, b)
}
let q, r := divmod(10, 3)
```

### Control flow

```yul
// if (no else in Yul — use switch for else)
if iszero(x) {
    revert(0, 0)
}

// switch
switch x
case 0 { /* x == 0 */ }
case 1 { /* x == 1 */ }
default { /* everything else */ }

// for loop (init; condition; post)
for { let i := 0 } lt(i, 10) { i := add(i, 1) }
{
    // loop body
}

// leave (return from function)
function foo() -> result {
    if eq(result, 0) { leave }  // early return
}

// break / continue (inside for)
for { let i := 0 } lt(i, 100) { i := add(i, 1) } {
    if eq(i, 50) { break }
    if eq(mod(i, 2), 0) { continue }
}
```

---

## All Yul Built-in Functions

### Arithmetic

| Function | Description | Notes |
|----------|-------------|-------|
| `add(a, b)` | a + b mod 2^256 | |
| `sub(a, b)` | a - b mod 2^256 | |
| `mul(a, b)` | a * b mod 2^256 | |
| `div(a, b)` | a / b (unsigned) | 0 if b=0 |
| `sdiv(a, b)` | a / b (signed, two's complement) | 0 if b=0 |
| `mod(a, b)` | a % b (unsigned) | 0 if b=0 |
| `smod(a, b)` | a % b (signed) | 0 if b=0 |
| `exp(a, b)` | a ** b mod 2^256 | gas: 10 + 50*bytes(b) |
| `addmod(a, b, N)` | (a+b) % N | |
| `mulmod(a, b, N)` | (a*b) % N | |
| `signextend(b, x)` | sign extend x from bit (b*8+7) | |

### Comparison (return 0 or 1)

| Function | Description |
|----------|-------------|
| `lt(a, b)` | 1 if a < b (unsigned) |
| `gt(a, b)` | 1 if a > b (unsigned) |
| `slt(a, b)` | 1 if a < b (signed) |
| `sgt(a, b)` | 1 if a > b (signed) |
| `eq(a, b)` | 1 if a == b |
| `iszero(a)` | 1 if a == 0 |

### Bitwise

| Function | Description |
|----------|-------------|
| `and(a, b)` | bitwise AND |
| `or(a, b)` | bitwise OR |
| `xor(a, b)` | bitwise XOR |
| `not(a)` | bitwise NOT (~a) |
| `byte(i, x)` | i-th byte of x from left (byte 0 = most significant) |
| `shl(shift, val)` | val << shift (logical, EIP-145) |
| `shr(shift, val)` | val >> shift (logical) |
| `sar(shift, val)` | val >> shift (arithmetic, sign-preserving) |

### Memory

| Function | Description | Gas |
|----------|-------------|-----|
| `mload(p)` | read 32 bytes at memory[p..p+32] | 3 + expansion |
| `mstore(p, v)` | write 32 bytes v to memory[p..p+32] | 3 + expansion |
| `mstore8(p, v)` | write 1 byte (low byte of v) to memory[p] | 3 + expansion |
| `msize()` | current memory size in bytes (multiple of 32) | 2 |
| `mcopy(dst, src, len)` | copy memory (EIP-5656, ≥Cancun) | 3 + 3*ceil(len/32) |

Memory expansion cost: 3*words + words²/512 (cumulative, pays for new words only)

### Storage

| Function | Description | Gas |
|----------|-------------|-----|
| `sload(slot)` | read storage slot | 100 warm / 2100 cold |
| `sstore(slot, val)` | write storage slot | 100→20000 (EIP-2200 rules) |
| `tload(slot)` | read transient storage (EIP-1153, ≥Cancun) | 100 |
| `tstore(slot, val)` | write transient storage (EIP-1153, ≥Cancun) | 100 |

**SSTORE gas rules (EIP-2200):**
- No-op (val == current): 100
- Clean slot → nonzero: 20000
- Clean slot → zero: 20000 (but refund 19900 at end)
- Dirty slot (previously written this tx): 100

### Calldata

| Function | Description |
|----------|-------------|
| `calldataload(p)` | read 32 bytes at calldata[p] |
| `calldatasize()` | total calldata length in bytes |
| `calldatacopy(dst, src, len)` | copy calldata to memory |

### Code

| Function | Description |
|----------|-------------|
| `codesize()` | size of current contract's code in bytes |
| `codecopy(dst, src, len)` | copy contract code to memory |
| `extcodesize(addr)` | code size at address (0 if EOA) |
| `extcodecopy(addr, dst, src, len)` | copy external code to memory |
| `extcodehash(addr)` | keccak256 of external code (0 if empty account) |

### Return data

| Function | Description |
|----------|-------------|
| `returndatasize()` | size of last sub-call's return data |
| `returndatacopy(dst, src, len)` | copy return data to memory |

### Block / transaction environment

| Function | Description |
|----------|-------------|
| `address()` | current contract address |
| `caller()` | msg.sender |
| `callvalue()` | msg.value in wei |
| `origin()` | tx.origin |
| `gasprice()` | tx.gasprice |
| `gas()` | gasleft() |
| `balance(addr)` | ETH balance of addr |
| `selfbalance()` | this.balance (cheaper than balance(address())) |
| `chainid()` | EIP-155 chain ID |
| `blockhash(n)` | block hash of block n (only last 256 blocks) |
| `coinbase()` | block.coinbase |
| `timestamp()` | block.timestamp |
| `number()` | block.number |
| `prevrandao()` | block.prevrandao (post-Merge) |
| `gaslimit()` | block.gaslimit |
| `basefee()` | block.basefee (EIP-1559, ≥London) |
| `blobhash(i)` | versioned blob hash at index i (EIP-4844, ≥Cancun) |
| `blobbasefee()` | blob base fee (EIP-7516, ≥Cancun) |

### Calls

```yul
// CALL: gas, to, value, argsOffset, argsLen, retOffset, retLen → success
let ok := call(gas(), addr, value, argPtr, argLen, retPtr, retLen)

// STATICCALL: no value, read-only
let ok := staticcall(gas(), addr, argPtr, argLen, retPtr, retLen)

// DELEGATECALL: preserves caller and value, uses caller's storage
let ok := delegatecall(gas(), impl, argPtr, argLen, retPtr, retLen)

// All return 1 on success, 0 on failure
// After call: returndatasize() has the return data size
```

### Creation

```yul
// CREATE: value, offset, len → address (0 on failure)
let addr := create(value, codeOffset, codeLen)

// CREATE2: deterministic address
// address = keccak256(0xff ++ this ++ salt ++ keccak256(initcode))[12:]
let addr := create2(value, codeOffset, codeLen, salt)
```

### Termination

```yul
return(p, s)           // return memory[p..p+s], stop execution
revert(p, s)           // revert with memory[p..p+s] as error data
stop()                 // STOP (like return with no data)
invalid()              // INVALID opcode, consumes all gas
selfdestruct(addr)     // SELFDESTRUCT (deprecated, behavior changed in Cancun)
```

### Logging

```yul
log0(p, s)                           // emit event, no topics
log1(p, s, t0)                       // 1 topic
log2(p, s, t0, t1)                   // 2 topics
log3(p, s, t0, t1, t2)              // 3 topics
log4(p, s, t0, t1, t2, t3)         // 4 topics (max)
// p = memory offset of data, s = data length
// t0..t3 = 32-byte topic values (keccak256 of event signature is t0 for indexed)
```

### Cryptography

```yul
keccak256(p, s)    // keccak256(memory[p..p+s])
```

---

## Common Assembly Patterns

### Efficient function selector dispatch

```solidity
assembly {
    let sel := shr(224, calldataload(0))  // top 4 bytes of calldata
    switch sel
    case 0xa9059cbb { /* transfer */ }
    case 0x70a08231 { /* balanceOf */ }
    default { revert(0, 0) }
}
```

### Tight memory allocation (without Solidity allocator)

```solidity
assembly {
    // Use scratch space (0x00–0x3f) for temporary hashes
    mstore(0x00, key)
    mstore(0x20, slot)
    let mappingSlot := keccak256(0x00, 0x40)

    // Allocate from heap properly:
    let ptr := mload(0x40)
    mstore(ptr, value)
    mstore(0x40, add(ptr, 0x20))  // advance free ptr
}
```

### Read a packed storage value

```solidity
// For variable `uint128 b` packed at offset 16 in a slot:
assembly {
    let raw := sload(b.slot)
    let val := and(shr(mul(b.offset, 8), raw), 0xffffffffffffffffffffffffffffffff)
}
```

### Efficient calldata parsing (avoiding abi.decode overhead)

```solidity
// For (address to, uint256 amount) calldata (after 4-byte selector):
assembly {
    let to     := shr(96, calldataload(4))   // address: right-shift 12 bytes
    let amount := calldataload(36)           // uint256: no shift needed
}
```

### Return a uint256 from assembly

```solidity
assembly {
    mstore(0x00, result)
    return(0x00, 0x20)
}
```

### Revert with a custom error (without Solidity overhead)

```solidity
// CustomError() → selector = bytes4(keccak256("CustomError()"))
assembly {
    mstore(0x00, 0xCustomErrSelector00000000000000000000000000000000000000000000)
    revert(0x00, 0x04)
}
```

### Optimal ERC20 transfer (gas-optimized)

```solidity
function _transfer(address token, address to, uint256 amount) internal {
    assembly {
        let ptr := mload(0x40)
        // transfer(address,uint256) selector: 0xa9059cbb
        mstore(ptr, 0xa9059cbb00000000000000000000000000000000000000000000000000000000)
        mstore(add(ptr, 0x04), and(to, 0xffffffffffffffffffffffffffffffffffffffff))
        mstore(add(ptr, 0x24), amount)
        let ok := call(gas(), token, 0, ptr, 0x44, 0x00, 0x20)
        // handle returndata: some tokens return nothing, some return bool
        if iszero(ok) { revert(0, 0) }
    }
}
```

### Checking contract existence

```solidity
assembly {
    if iszero(extcodesize(addr)) { revert(0, 0) }
    // Note: returns 0 during construction (before deploy completes)
    // Use extcodehash for more reliable check:
    if iszero(extcodehash(addr)) { revert(0, 0) }
}
```
