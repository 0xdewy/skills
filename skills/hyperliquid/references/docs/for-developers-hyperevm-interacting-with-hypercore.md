---
title: Interacting with HyperCore
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/interacting-with-hypercore.md
section: hyperevm-dev
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/interacting-with-hypercore.md).

# Interacting with HyperCore

### Read precompiles

The testnet EVM provides read precompiles that allows querying HyperCore information. The precompile addresses start at  0x0000000000000000000000000000000000000800 and have methods for querying information such as perps positions, spot balances, vault equity, staking delegations, oracle prices, and the L1 block number.

The values are guaranteed to match the latest HyperCore state at the time the EVM block is constructed.

Attached is a Solidity file `L1Read.sol` describing the read precompiles. As an example, this call queries the third perp oracle price on testnet:

```
cast call 0x0000000000000000000000000000000000000807 0x0000000000000000000000000000000000000000000000000000000000000003 --rpc-url https://rpc.hyperliquid-testnet.xyz/evm
```

To convert to floating point numbers, divide the returned price by `10^(6 - szDecimals)`for perps and `10^(8 - base asset szDecimals)` for spot.

Precompiles called on invalid inputs such as invalid assets or vault address will return an error and consume all gas passed into the precompile call frame. Precompiles have a gas cost of `2000 + 65 * (input_len + output_len)`.

### CoreWriter contract

A system contract is available at 0x3333333333333333333333333333333333333333 for sending transactions from the HyperEVM to HyperCore. It burns \~25,000 gas before emitting a log to be processed by HyperCore as an action. In practice the gas usage for a basic call will be \~47000. A solidity file `CoreWriter.sol` for the write system contract is attached.

#### Action encoding details

* Byte 1: Encoding version
  * Currently, only version `1` is supported, but enables future upgrades while maintaining backward compatibility.
* Bytes 2-4: Action ID
  * These three bytes, when decoded as a big-endian unsigned integer, represent the unique identifier for the action.
* Remaining bytes: Action encoding
  * The rest of the bytes constitue the action-specific data. It is always the raw ABI encoding of a sequence of Solidity types

To prevent any potential latency advantages for using HyperEVM to bypass the L1 mempool, order actions and vault transfers sent from CoreWriter are delayed onchain for a few seconds. This has no noticeable effect on UX because the end user has to wait for at least one small block confirmation. These onchain-delayed actions appear twice in the L1 explorer: first as an enqueuing and second as a HyperCore execution.

| Action ID | Action                | Fields                                                               | Solidity Type                                        | Notes                                                                                                                                                                                                     |
| --------- | --------------------- | -------------------------------------------------------------------- | ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1         | Limit order           | (asset, isBuy, limitPx, sz, reduceOnly, encodedTif, cloid)           | (uint32, bool, uint64, uint64, bool, uint8, uint128) | Tif encoding: `1` for `Alo` , `2` for `Gtc` , `3` for `Ioc` . Cloid encoding: 0 means no cloid, otherwise uses the number as the cloid. limitPx and sz should be sent as 10^8 \* the human readable value |
| 2         | Vault transfer        | (vault, isDeposit, usd)                                              | (address, bool, uint64)                              |                                                                                                                                                                                                           |
| 3         | Token delegate        | (validator, wei, isUndelegate)                                       | (address, uint64, bool)                              |                                                                                                                                                                                                           |
| 4         | Staking deposit       | wei                                                                  | uint64                                               |                                                                                                                                                                                                           |
| 5         | Staking withdraw      | wei                                                                  | uint64                                               |                                                                                                                                                                                                           |
| 6         | Spot send             | (destination, token, wei)                                            | (address, uint64, uint64)                            |                                                                                                                                                                                                           |
| 7         | USD class transfer    | (ntl, toPerp)                                                        | (uint64, bool)                                       |                                                                                                                                                                                                           |
| 8         | Finalize EVM Contract | (token, encodedFinalizeEvmContractVariant, createNonce)              | (uint64, uint8, uint64)                              | encodedFinalizeEvmContractVariant `1` for `Create`, `2` for `FirstStorageSlot` , `3` for `CustomStorageSlot` . If `Create` variant, then `createNonce` input argument is used.                            |
| 9         | Add API wallet        | (API wallet address, API wallet name)                                | (address, string)                                    | If the API wallet name is empty then this becomes the main API wallet / agent                                                                                                                             |
| 10        | Cancel order by oid   | (asset, oid)                                                         | (uint32, uint64)                                     |                                                                                                                                                                                                           |
| 11        | Cancel order by cloid | (asset, cloid)                                                       | (uint32, uint128)                                    |                                                                                                                                                                                                           |
| 12        | Approve builder fee   | (maxFeeRate, builder address)                                        | (uint64, address)                                    | maxFeeRate is in decibps. To approve a builder fee of 0.01% maxFreeRate should be 10.                                                                                                                     |
| 13        | Send asset            | (destination, subAccount, source\_dex, destination\_dex, token, wei) | (address, address, uint32, uint32, uint64, uint64)   | If subAccount is not the zero address, then transfer from subAccount. Specify uint32::MAX for the source\_dex or destination\_dex for spot.                                                               |
| 15        | Borrow lend operation | (encodedOperation, token, wei)                                       | (uint8, uint64, uint64)                              | encodedOperation `0` for `Supply`, `1` for `Withdraw` . If `wei` is 0 then maximally apply the operation, e.g. withdraw full balance from reserve.                                                        |
| 16        | Set abstraction       | (user, abstraction)                                                  | (address, uint8)                                     | abstraction `1` for `disabled`, `2` for `unifiedAccount` , `3` for `portfolioMargin` . `user` can either be the master user or a sub-account.                                                             |

Below is an example contract that would send an action on behalf of its own contract address on HyperCore, which also demonstrates one way to construct the encoded action in Solidity.

```
contract CoreWriterCaller {
    function sendUsdClassTransfer(uint64 ntl, bool toPerp) external {
        bytes memory encodedAction = abi.encode(ntl, toPerp);
        bytes memory data = new bytes(4 + encodedAction.length);
        data[0] = 0x01;
        data[1] = 0x00;
        data[2] = 0x00;
        data[3] = 0x07;
        for (uint256 i = 0; i < encodedAction.length; i++) {
            data[4 + i] = encodedAction[i];
        }
        CoreWriter(0x3333333333333333333333333333333333333333).sendRawAction(data);
    }
}
```

\
Happy building. Any feedback is appreciated.

{% file src="/files/Z8SxemCYCsCtTvMkJNIX" %}

{% file src="/files/KtkofGhs7hIjy2DsiYOR" %}


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/interacting-with-hypercore.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
