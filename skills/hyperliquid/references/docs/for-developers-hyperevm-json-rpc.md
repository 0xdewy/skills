---
title: JSON-RPC
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/json-rpc.md
section: hyperevm-dev
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/json-rpc.md).

# JSON-RPC

The following RPC endpoints are available

* `net_version`
* `web3_clientVersion`
* `eth_blockNumber`
* `eth_call`
  * only the latest block is supported
* `eth_chainId`
* `eth_estimateGas`
  * only the latest block is supported
* `eth_feeHistory`
* `eth_gasPrice`
  * returns the base fee for the next small block
* `eth_getBalance`
  * only the latest block is supported
* `eth_getBlockByHash`
* `eth_getBlockByNumber`
* `eth_getBlockReceipts`
* `eth_getBlockTransactionCountByHash`
* `eth_getBlockTransactionCountByNumber`
* `eth_getCode`
  * only the latest block is supported
* `eth_getLogs`
  * up to 4 topics
  * up to 50 blocks in query range
* `eth_getStorageAt`
  * only the latest block is supported
* `eth_getTransactionByBlockHashAndIndex`
* `eth_getTransactionByBlockNumberAndIndex`
* `eth_getTransactionByHash`
* `eth_getTransactionCount`
  * only the latest block is supported
* `eth_getTransactionReceipt`
* `eth_maxPriorityFeePerGas`
  * always returns zero currently
* `eth_syncing`
  * always returns false

The following custom endpoints are available

* `eth_bigBlockGasPrice`
  * returns the base fee for the next big block
* `eth_usingBigBlocks`
  * returns whether the address is using big blocks
* `eth_getSystemTxsByBlockHash`  and `eth_getSystemTxsByBlockNumber`

  * similar to the "getTransaction" analogs but returns the system transactions that originate from HyperCore

Unsupported requests

* Requests that require historical state are not supported at this time on the default RPC implementation. However, independent archive node implementations are available for use, and the GitHub repository has examples on how to get started indexing historical data locally. Note that read precompiles are only recorded for the calls actually made on each block. Hypothetical read precompile results could be obtained from a full L1 replay.

Rate limits: IP based rate limits are the same as the API server.&#x20;


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/json-rpc.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
