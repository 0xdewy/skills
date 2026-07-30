---
name: rust-evm
description: >-
  Low-level EVM, Rust, and Foundry reference for revm, forge/cast/anvil,
  bytecode, opcodes, traces, calldata, storage, gas, Yul/assembly, evmole,
  CREATE2, delegatecall, and precompiles. Only use when explicitly
  requested.
license: MIT
disable-model-invocation: true
metadata:
  author: iamky1e
  version: 1.0.0
  category: security
  activation: explicit
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

# Rust EVM

Handle low-level EVM/Rust/Foundry tasks involving bytecode, traces, calldata,
storage, Yul/assembly, revm, and gas.

## Workflow

1. Identify the layer: Solidity/Yul, bytecode/opcodes, calldata/selectors,
   storage, trace, revm integration, or Foundry tooling.
2. Load at most one matching reference first: `references/yul.md`,
   `references/opcodes.md`, `references/revm.md`, `references/foundry.md`, or
   `references/evmole.md`. Prefer exact tools over memory.
3. Ground claims in concrete artifacts: byte offsets, opcodes, selectors,
   storage slots, trace frames, gas deltas, or source lines.
4. For security-sensitive analysis, separate confirmed behavior from hypotheses.
5. For code changes, keep patches small and run the relevant Foundry/Rust check.

Do not answer high-level protocol or web3 questions through this skill unless
the raw EVM representation matters.
