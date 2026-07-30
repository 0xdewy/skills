---
title: HyperEVM
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm.md
section: hyperevm-dev
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm.md).

# HyperEVM

The HyperEVM consists of EVM blocks built as part of Hyperliquid's execution, inheriting all security from HyperBFT consensus. HYPE is the native gas token on the HyperEVM. To move HYPE from HyperCore to HyperEVM, send HYPE to `0x2222222222222222222222222222222222222222`. See the instructions in [Native Transfers](/hyperliquid-docs/for-developers/hyperevm/hypercore-less-than-greater-than-hyperevm-transfers.md) for more details on how this works.

Note that there are currently no official frontend components of the EVM. Users can build their own frontends or port over existing EVM applications. All interaction with the EVM happens through the JSON-RPC. For example, users can add the chain to their wallets by entering the RPC URL and chain ID. There is currently no websocket JSON-RPC support for the RPC at `rpc.hyperliquid.xyz/evm`but other RPC implementations may support it.

The HyperEVM uses the Cancun hardfork without blobs. In particular, EIP-1559 is enabled on the HyperEVM. Base fees are burned as usual, implemented in the standard way where the burned fees are removed from the total EVM supply. Unlike most other EVM chains, priority fees are also burned because the HyperEVM uses HyperBFT consensus. The burned priority fees are sent to the zero address's EVM balance.&#x20;

On both mainnet and testnet, HYPE on the HyperEVM has 18 decimals. A few differences between testnet and mainnet HyperEVM are highlighted below:

### Mainnet

Chain ID: 999

JSON-RPC endpoint: `https://rpc.hyperliquid.xyz/evm` for mainnet&#x20;

### Testnet

Chain ID: 998&#x20;

JSON-RPC endpoint: `https://rpc.hyperliquid-testnet.xyz/evm`


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
