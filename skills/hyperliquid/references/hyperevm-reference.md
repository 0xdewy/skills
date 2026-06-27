# HyperEVM Reference

Use this guide for HyperEVM, CoreWriter, precompiles, transfers, and JSON-RPC.
Open exact mirrored pages before coding.

## Entry Points

- HyperEVM overview: `references/docs/hyperevm.md`
- Builder tools: `references/docs/hyperevm-tools-for-hyperevm-builders.md`
- Developer HyperEVM overview:
  `references/docs/for-developers-hyperevm.md`
- Dual-block architecture:
  `references/docs/for-developers-hyperevm-dual-block-architecture.md`
- Raw HyperEVM block data:
  `references/docs/for-developers-hyperevm-raw-hyperevm-block-data.md`
- Interaction timings:
  `references/docs/for-developers-hyperevm-interaction-timings.md`
- Wrapped HYPE: `references/docs/for-developers-hyperevm-wrapped-hype.md`
- JSON-RPC: `references/docs/for-developers-hyperevm-json-rpc.md`

## JSON-RPC

The default HyperEVM JSON-RPC supports common Ethereum methods such as:

- `eth_blockNumber`
- `eth_call` and `eth_estimateGas` for latest state
- `eth_chainId`
- `eth_feeHistory`
- `eth_gasPrice`
- `eth_getBalance`, `eth_getCode`, `eth_getStorageAt` for latest state
- block, receipt, transaction, and log lookups
- `eth_maxPriorityFeePerGas`, currently always zero per docs

Custom endpoints:

- `eth_bigBlockGasPrice`
- `eth_usingBigBlocks`
- `eth_getSystemTxsByBlockHash`
- `eth_getSystemTxsByBlockNumber`

Important limitations:

- Requests requiring historical state are not supported by the default RPC.
- `eth_getLogs` is limited to up to 4 topics and a 50-block query range.
- RPC rate limits follow the API server IP-based limits.

## Read Precompiles

Exact page:
`references/docs/for-developers-hyperevm-interacting-with-hypercore.md`.

Read precompiles start at:

```text
0x0000000000000000000000000000000000000800
```

They query HyperCore state such as perp positions, spot balances, vault equity,
staking delegations, oracle prices, and the L1 block number. Returned values
match latest HyperCore state when the EVM block is constructed.

Numeric conversion:

- Perp oracle price: divide by `10^(6 - szDecimals)`.
- Spot price: divide by `10^(8 - base asset szDecimals)`.

Invalid precompile inputs, such as invalid assets or vault addresses, return an
error and consume all gas passed into that precompile call frame. Gas cost is
`2000 + 65 * (input_len + output_len)`.

## CoreWriter

CoreWriter system contract:

```text
0x3333333333333333333333333333333333333333
```

It sends transactions from HyperEVM to HyperCore by burning roughly 25000 gas
before emitting a log processed as a HyperCore action. A basic call is roughly
47000 gas in practice.

Raw action encoding:

- Byte 1: encoding version. Currently `1`.
- Bytes 2-4: action ID as big-endian unsigned integer.
- Remaining bytes: raw ABI encoding of the action-specific Solidity types.

CoreWriter actions include:

- 1: limit order
- 2: vault transfer
- 3: token delegate
- 4: staking deposit
- 5: staking withdraw
- 6: spot send
- 7: USD class transfer
- 8: finalize EVM contract
- 9: add API wallet
- 10: cancel order by oid
- 11: cancel order by cloid
- 12: approve builder fee
- 13: send asset
- 15: borrow/lend operation
- 16: set abstraction

Latency note: order actions and vault transfers sent through CoreWriter are
delayed onchain for a few seconds to avoid bypassing the L1 mempool. They can
appear twice in the L1 explorer: enqueue and HyperCore execution.

## HyperCore <> HyperEVM Transfers

Exact page:
`references/docs/for-developers-hyperevm-hypercore-less-than-greater-than-hyperevm-transfers.md`.

Terminology:

- `Core spot`: spot assets on HyperCore.
- `EVM spot`: linked assets on HyperEVM.
- HYPE links to the native HyperEVM balance, not an ERC20 contract.

System address rules:

- Every token has a Core system address with first byte `0x20`; remaining bytes
  are zero except the token index encoded big-endian.
- Example token index 200:
  `0x20000000000000000000000000000000000000c8`.
- HYPE exception:
  `0x2222222222222222222222222222222222222222`.

Transfer directions:

- HyperCore to HyperEVM: use a `sendAsset` action or frontend transfer with the
  token system address as destination.
- HyperEVM to HyperCore: ERC20 transfer to the corresponding system address.
- HYPE back to HyperCore: send native HYPE as transaction value to the
  `0x222...2` system contract.

Core to EVM transfer gas: docs state it costs 200k gas at the base gas price of
the next HyperEVM block.

Caveats:

- Only linked tokens can move between Core and EVM.
- There are no universal guarantees that a linked contract is a correct ERC20.
  Verify source, bytecode behavior, total balance, and system-address supply.
- Extra EVM wei decimals can burn non-round dust amounts.

## Nodes

- Nodes overview: `references/docs/for-developers-nodes.md`
- L1 data schemas: `references/docs/for-developers-nodes-l1-data-schemas.md`
- Foundation non-validating node:
  `references/docs/for-developers-nodes-foundation-non-validating-node.md`
