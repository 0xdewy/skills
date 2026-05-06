# EVM Opcode Reference

Complete opcode table with hex values, stack effects, gas costs, and descriptions.
Gas costs reflect post-Berlin/London/Cancun rules where applicable.

## Arithmetic (0x00–0x0B)

| Hex | Mnemonic | Gas | Stack (in → out) | Description |
|-----|----------|-----|-------------------|-------------|
| 0x00 | STOP | 0 | → | Halt execution |
| 0x01 | ADD | 3 | a,b → a+b | Modulo 2^256 addition |
| 0x02 | MUL | 5 | a,b → a*b | Modulo 2^256 multiplication |
| 0x03 | SUB | 3 | a,b → a-b | Modulo 2^256 subtraction |
| 0x04 | DIV | 5 | a,b → ⌊a/b⌋ | Unsigned integer division (0 if b=0) |
| 0x05 | SDIV | 5 | a,b → a÷b | Signed integer division (0 if b=0) |
| 0x06 | MOD | 5 | a,b → a%b | Unsigned modulus (0 if b=0) |
| 0x07 | SMOD | 5 | a,b → a%b | Signed modulus (0 if b=0) |
| 0x08 | ADDMOD | 8 | a,b,N → (a+b)%N | Addition modulo N (0 if N=0) |
| 0x09 | MULMOD | 8 | a,b,N → (a*b)%N | Multiplication modulo N (0 if N=0) |
| 0x0A | EXP | 10+50*B | a,b → a**b | Exponentiation (B = bytes in exponent) |
| 0x0B | SIGNEXTEND | 5 | b,x → y | Sign extend x from bit (b*8+7) upward |

## Comparison & Bitwise (0x10–0x1D)

| Hex | Mnemonic | Gas | Stack | Description |
|-----|----------|-----|-------|-------------|
| 0x10 | LT | 3 | a,b → a<b | Unsigned less-than (1 or 0) |
| 0x11 | GT | 3 | a,b → a>b | Unsigned greater-than |
| 0x12 | SLT | 3 | a,b → a<b | Signed less-than |
| 0x13 | SGT | 3 | a,b → a>b | Signed greater-than |
| 0x14 | EQ | 3 | a,b → a==b | Equality |
| 0x15 | ISZERO | 3 | a → !a | 1 if a=0, else 0 |
| 0x16 | AND | 3 | a,b → a&b | Bitwise AND |
| 0x17 | OR | 3 | a,b → a\|b | Bitwise OR |
| 0x18 | XOR | 3 | a,b → a^b | Bitwise XOR |
| 0x19 | NOT | 3 | a → ~a | Bitwise NOT |
| 0x1A | BYTE | 3 | i,x → y | i-th byte of x (from left, 0=MSB) |
| 0x1B | SHL | 3 | shift,val → val<<shift | Left shift (EIP-145) |
| 0x1C | SHR | 3 | shift,val → val>>shift | Logical right shift |
| 0x1D | SAR | 3 | shift,val → val>>shift | Arithmetic (sign-preserving) right shift |

## SHA3 (0x20)

| Hex | Mnemonic | Gas | Stack | Description |
|-----|----------|-----|-------|-------------|
| 0x20 | KECCAK256 | 30+6*⌈len/32⌉+mem | offset,len → hash | keccak256(mem[offset..offset+len]) |

## Environment (0x30–0x4A)

| Hex | Mnemonic | Gas | Stack | Description |
|-----|----------|-----|-------|-------------|
| 0x30 | ADDRESS | 2 | → addr | Address of currently executing account |
| 0x31 | BALANCE | 100/2600 | addr → bal | ETH balance (100 warm, 2600 cold) |
| 0x32 | ORIGIN | 2 | → addr | tx.origin |
| 0x33 | CALLER | 2 | → addr | msg.sender |
| 0x34 | CALLVALUE | 2 | → val | msg.value in wei |
| 0x35 | CALLDATALOAD | 3 | i → x | calldata[i..i+32] (0-padded) |
| 0x36 | CALLDATASIZE | 2 | → len | calldata byte length |
| 0x37 | CALLDATACOPY | 3+3*⌈len/32⌉+mem | dstOff,srcOff,len → | copy calldata to memory |
| 0x38 | CODESIZE | 2 | → len | current code byte length |
| 0x39 | CODECOPY | 3+3*⌈len/32⌉+mem | dstOff,srcOff,len → | copy code to memory |
| 0x3A | GASPRICE | 2 | → price | tx gas price in wei |
| 0x3B | EXTCODESIZE | 100/2600 | addr → len | code size at addr |
| 0x3C | EXTCODECOPY | 100/2600+copy | addr,dstOff,srcOff,len → | copy external code to memory |
| 0x3D | RETURNDATASIZE | 2 | → len | return data buffer size |
| 0x3E | RETURNDATACOPY | 3+3*⌈len/32⌉+mem | dstOff,srcOff,len → | copy return data to memory |
| 0x3F | EXTCODEHASH | 100/2600 | addr → hash | keccak256 of code at addr (0 for empty) |
| 0x40 | BLOCKHASH | 20 | blocknum → hash | hash of block N (only last 256) |
| 0x41 | COINBASE | 2 | → addr | block.coinbase |
| 0x42 | TIMESTAMP | 2 | → ts | block.timestamp (unix) |
| 0x43 | NUMBER | 2 | → n | block.number |
| 0x44 | PREVRANDAO | 2 | → rand | block.prevrandao (post-Merge) / block.difficulty (pre-Merge) |
| 0x45 | GASLIMIT | 2 | → lim | block.gaslimit |
| 0x46 | CHAINID | 2 | → id | EIP-155 chain ID |
| 0x47 | SELFBALANCE | 5 | → bal | this.balance (cheaper than BALANCE(ADDRESS())) |
| 0x48 | BASEFEE | 2 | → fee | block.basefee (EIP-1559, ≥London) |
| 0x49 | BLOBHASH | 3 | i → hash | blob versioned hash at index i (EIP-4844, ≥Cancun) |
| 0x4A | BLOBBASEFEE | 2 | → fee | blob base fee (EIP-7516, ≥Cancun) |

## Stack, Memory, Storage (0x50–0x5F)

| Hex | Mnemonic | Gas | Stack | Description |
|-----|----------|-----|-------|-------------|
| 0x50 | POP | 2 | x → | Discard top of stack |
| 0x51 | MLOAD | 3+mem | offset → val | Load 32 bytes from memory |
| 0x52 | MSTORE | 3+mem | offset,val → | Store 32 bytes to memory |
| 0x53 | MSTORE8 | 3+mem | offset,val → | Store 1 byte (low byte of val) to memory |
| 0x54 | SLOAD | 100/2100 | slot → val | Load from storage (100 warm, 2100 cold) |
| 0x55 | SSTORE | complex | slot,val → | Store to storage (see EIP-2200 gas rules) |
| 0x56 | JUMP | 8 | dest → | Unconditional jump (dest must be JUMPDEST) |
| 0x57 | JUMPI | 10 | dest,cond → | Jump if cond ≠ 0 |
| 0x58 | PC | 2 | → pc | Program counter value |
| 0x59 | MSIZE | 2 | → size | Active memory size in bytes |
| 0x5A | GAS | 2 | → gas | Remaining gas |
| 0x5B | JUMPDEST | 1 | → | Valid jump target marker (no-op) |
| 0x5C | TLOAD | 100 | slot → val | Transient storage load (EIP-1153, ≥Cancun) |
| 0x5D | TSTORE | 100 | slot,val → | Transient storage store (EIP-1153, ≥Cancun) |
| 0x5E | MCOPY | 3+3*⌈len/32⌉+mem | dst,src,len → | Memory copy (EIP-5656, ≥Cancun) |
| 0x5F | PUSH0 | 2 | → 0 | Push zero (EIP-3855, ≥Shanghai) |

## Push Operations (0x60–0x7F)

| Hex | Mnemonic | Gas | Stack | Description |
|-----|----------|-----|-------|-------------|
| 0x60 | PUSH1 | 3 | → val | Push 1-byte immediate |
| 0x61 | PUSH2 | 3 | → val | Push 2-byte immediate |
| ... | ... | 3 | → val | ... |
| 0x7F | PUSH32 | 3 | → val | Push 32-byte immediate (full word) |

## Duplication (0x80–0x8F)

| Hex | Mnemonic | Gas | Description |
|-----|----------|-----|-------------|
| 0x80 | DUP1 | 3 | Duplicate 1st stack item (top) |
| 0x81 | DUP2 | 3 | Duplicate 2nd stack item |
| ... | ... | 3 | ... |
| 0x8F | DUP16 | 3 | Duplicate 16th stack item |

## Exchange (0x90–0x9F)

| Hex | Mnemonic | Gas | Description |
|-----|----------|-----|-------------|
| 0x90 | SWAP1 | 3 | Swap top with 2nd item |
| 0x91 | SWAP2 | 3 | Swap top with 3rd item |
| ... | ... | 3 | ... |
| 0x9F | SWAP16 | 3 | Swap top with 17th item |

## Logging (0xA0–0xA4)

| Hex | Mnemonic | Gas | Stack | Description |
|-----|----------|-----|-------|-------------|
| 0xA0 | LOG0 | 375+8*len+mem | offset,len → | Emit event, no topics |
| 0xA1 | LOG1 | 375+8*len+375*1+mem | offset,len,t0 → | 1 topic |
| 0xA2 | LOG2 | 375+8*len+375*2+mem | offset,len,t0,t1 → | 2 topics |
| 0xA3 | LOG3 | 375+8*len+375*3+mem | offset,len,t0,t1,t2 → | 3 topics |
| 0xA4 | LOG4 | 375+8*len+375*4+mem | offset,len,t0,t1,t2,t3 → | 4 topics |

## System (0xF0–0xFF)

| Hex | Mnemonic | Gas | Stack | Description |
|-----|----------|-----|-------|-------------|
| 0xF0 | CREATE | 32000+ | val,off,len → addr | Deploy contract (addr=0 on failure) |
| 0xF1 | CALL | complex | gas,addr,val,aOff,aLen,rOff,rLen → ok | Call external contract |
| 0xF2 | CALLCODE | complex | gas,addr,val,aOff,aLen,rOff,rLen → ok | Call with external code, own storage (deprecated) |
| 0xF3 | RETURN | 0+mem | offset,len → | Return mem[offset..offset+len] and halt |
| 0xF4 | DELEGATECALL | complex | gas,addr,aOff,aLen,rOff,rLen → ok | Call preserving msg.sender/msg.value, own storage |
| 0xF5 | CREATE2 | 32000+ | val,off,len,salt → addr | CREATE with deterministic address |
| 0xFA | STATICCALL | complex | gas,addr,aOff,aLen,rOff,rLen → ok | Read-only external call (no state changes) |
| 0xFD | REVERT | 0+mem | offset,len → | Revert with mem[offset..offset+len] |
| 0xFE | INVALID | all gas | → | Invalid instruction (EIP-141), consumes all gas |
| 0xFF | SELFDESTRUCT | 5000/25000+ | addr → | Destroy contract, send balance to addr |

---

## Gas Cost Quick Reference

### Call gas (post-Berlin, EIP-2929)

| Scenario | Cost |
|----------|------|
| Cold address access | +2600 |
| Warm address access | 100 |
| Value transfer (non-zero) | +9000 |
| New account creation | +25000 |
| Memory expansion | 3*words + words²/512 (cumulative) |

### SSTORE gas (EIP-2200, post-Istanbul)

| Scenario | Cost | Refund |
|----------|------|--------|
| No-op (current == new) | 100 | — |
| Zero → nonzero (clean) | 20000 | — |
| Nonzero → zero (clean) | 5000 | +19900 |
| Any dirty write | 100 | depends |
| Reset to original zero | 100 | +19900 |
| Reset to original nonzero | 100 | +2800 |

### Precompile addresses & costs

| Address | Name | Gas |
|---------|------|-----|
| 0x01 | ecRecover | 3000 |
| 0x02 | SHA2-256 | 60 + 12*⌈len/32⌉ |
| 0x03 | RIPEMD-160 | 600 + 120*⌈len/32⌉ |
| 0x04 | Identity (datacopy) | 15 + 3*⌈len/32⌉ |
| 0x05 | modexp | complex (EIP-2565) |
| 0x06 | bn128Add | 150 |
| 0x07 | bn128Mul | 6000 |
| 0x08 | bn128Pairing | 45000 + 34000*k |
| 0x09 | blake2f | rounds * 1 |
| 0x0A | point eval (KZG) | 50000 (EIP-4844) |

---

## Calldata ABI Encoding Reference

**Function selector:** `bytes4(keccak256("funcName(type1,type2)"))`

**Static types** (encoded in-place, each 32 bytes):
- `uint<N>`, `int<N>`: right-aligned, zero/sign padded
- `bool`: 0 or 1 in 32 bytes
- `address`: 20-byte address, 12 zero bytes on left
- `bytes<N>` (fixed size): right-padded to 32 bytes

**Dynamic types** (encoded as offset + length + data):
- `bytes`, `string`: pointer (32 bytes) + length (32 bytes) + data (padded to 32)
- `T[]`, `T[N]`: pointer + length (for dynamic) + each element

**`abi.encodePacked`**: no padding, no selector, elements packed tightly —
**NOT** safe for hashing tuples (collision risk), OK for single arguments.

**Selector computation:**
```bash
cast sig "transfer(address,uint256)"  # → 0xa9059cbb
cast keccak "transfer(address,uint256)" | cut -c1-10  # same
```

**Common selectors:**
```
0xa9059cbb  transfer(address,uint256)
0x23b872dd  transferFrom(address,address,uint256)
0x095ea7b3  approve(address,uint256)
0x70a08231  balanceOf(address)
0x18160ddd  totalSupply()
0xdd62ed3e  allowance(address,address)
0x06fdde03  name()
0x95d89b41  symbol()
0x313ce567  decimals()
0xd0e30db0  deposit()        (WETH)
0x2e1a7d4d  withdraw(uint256) (WETH)
```
