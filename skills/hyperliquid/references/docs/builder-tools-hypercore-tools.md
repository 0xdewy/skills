---
title: HyperCore Tools
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/builder-tools/hypercore-tools.md
section: builder-tools
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/builder-tools/hypercore-tools.md).

# HyperCore Tools

### Analytics - perps and order book data

* ASXN (most comprehensive): <https://hyperscreener.asxn.xyz/home>
* Artemis: <https://app.artemis.xyz/project/hyperliquid>
* Blockliquidity: [https://blockliquidity.xyz/](< https://blockliquidity.xyz/>)
* Coinalyze: <https://coinalyze.net/markets/?exchange=H>
* DefiLlama (note that TVL is tracked differently on order books and AMMs): <https://defillama.com/perps/chains/hyperliquid>
* Flowscan: <https://www.flowscan.xyz/>
* HyperDash: <https://legacy.hyperdash.com/>
* HyperTracker: <https://app.coinmarketman.com/hypertracker>
* Laevitas: <https://app.laevitas.ch/exchanges/perpswaps/HYPERLIQUID/screener>
* Velo: <https://velo.xyz/futures/>

### Analytics - USDC Arbitrum bridge

* Dune dashboards by community members: [Mogie](https://dune.com/mogie/hyperliquid-flows), [KamBenbrik](https://dune.com/kambenbrik/hyperliquid), [Hashed](https://dune.com/hashed_official/usdc-on-hyperliquid), and [X3Research](https://dune.com/x3research/hyperliquid)
* Parsec: <https://parsec.fi/arb/address/0x2df1c51e09aecf9cacb7bc98cb1742757f163df7>

### APIs

* API Docs: <https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api>
* SDKs:&#x20;
  * Python SDK: <https://github.com/hyperliquid-dex/hyperliquid-python-sdk>
  * Rust SDK by community member, Infinite Field: <https://github.com/infinitefield/hypersdk>
  * Typescript SDKs by community members: <https://github.com/nktkas/hyperliquid>, <https://github.com/nomeida/hyperliquid>
* CCXT integrations in multiple languages that conform with the standard CCXT API: <https://docs.ccxt.com/#/exchanges/hyperliquid>
* Dwellir (gRPC): <https://www.dwellir.com/docs/hyperliquid/grpc/>
* Dwellir (websocket): <https://www.dwellir.com/docs/hyperliquid/websocket-api>
* Hydromancer (non-rate-limited APIs and indexing): <https://docs.hydromancer.xyz/>

### Explorers

* Hyperliquid.xyz: <https://app.hyperliquid.xyz/explorer>
* Flowscan: [flowscan.xyz](https://flowscan.xyz)
* HypurrScan: [https://hypurrscan.io](https://hypurrscan.io/)

### Indexing

* Allium: <https://docs.allium.so/historical-chains/supported-blockchains/hyperliquid>
* Hydromancer historical data: <https://docs.hydromancer.xyz/reservoir>
* HypeDexer by Enigma: <https://www.hypedexer.com/>
* SonarX: <https://docs.sonarx.com/datasets/HYPERLIQUID/Hyperliquid>

### Multisig, MPC, and qualified custodians

* Anchorage Digital (custodian): <https://www.anchorage.com/insights/anchorage-digital-offers-support-hype-custody-staking-full-support-across-hypeevm-hypercore>
* FalconX (custodian): <https://www.falconx.io/>
* HyperSig (multisig): <https://www.hypersig.xyz/>
* Komainu (custodian): <https://komainu.com/komainu-announces-institutional-grade-custody-and-staking-support-for-hyperliquid-hype/>
* Tholos (MPC): <https://www.tholos.app/>&#x20;


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/builder-tools/hypercore-tools.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
