---
title: HIP-4: Outcome markets
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/hyperliquid-improvement-proposals-hips/hip-4-outcome-markets.md
section: hips
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/hyperliquid-improvement-proposals-hips/hip-4-outcome-markets.md).

# HIP-4: Outcome markets

### Overview

Outcomes are fully collateralized contracts that settle within a fixed range. HIP-4 is a general-purpose primitive that is useful for applications such as prediction markets and bounded options-like instruments.&#x20;

Outcomes bring non-linearity, dated contracts, and an alternative form of derivative trading that does not involve leverage or liquidations. The outcome primitive expands the expressivity of HyperCore, while composing with other primitives such as portfolio margin and the HyperEVM.

The first market is a recurring binary outcome that settles daily at 06:00 UTC to the BTC mark price on HyperCore mark prices. See the spec [here](/hyperliquid-docs/trading/contract-specifications.md#recurring-outcomes). Multi-outcome markets will be supported but are not part of the initial mainnet release. Additional features and markets will be rolled out in stages.

The outcome trading API is similar to spot, with key differences highlighted here: <https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/asset-ids>.

### Mechanics

Each outcome market consists of two sides, each with a token. The tokens are labeled by `sideSpecs` in the `outcomeMeta` info endpoint, often `Yes` and `No`. Settlement automatically converts either Yes to `settleFraction` quote tokens and No to `1 - settleFraction` quote tokens. In particular, `settleFraction = 1` for "binary yes" and `settleFraction = 0` for "binary no" settlement.

The order books of Yes and No tokens for the same outcome are merged to share liquidity. For example, an order to buy Yes at price `p` is equivalent to an order to sell No at price `1-p`. Under the merged book, price-time priority generalizes to price-side-time priority. In other words, *for orders at the same merged price level*, the resting sell orders are sorted before all resting buy dual orders. Advanced users may also manually split and merge outcomes to convert between primary and dual balances. See [here](/hyperliquid-docs/for-developers/api/exchange-endpoint.md#split-outcome) for API examples.

Most operations abstract the dual book's liquidity from the user's perspective. However, there are a few examples whose ergonomics will be improved on a future network upgrade. For example, historical orders can return the primary and dual orders separately if a user sends an order that both matches and rests on the book.

*Questions* are collections of outcomes where exactly one outcome will settle to Yes, and all others will settle to No. Each outcome trades on a separate order book, but is linked by `negate` and `merge` operations. See [here](/hyperliquid-docs/for-developers/api/exchange-endpoint.md#negate-outcome) for API examples. In other words, users with No shares on different outcomes of the same question can redeem quote tokens before the underlying outcomes settle.

Fees are currently zero for outcome markets for initial testing. However, builder codes do work the same as normal spot trading, where builders earn builder fees on sell orders that specify their builder code.&#x20;


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/hyperliquid-improvement-proposals-hips/hip-4-outcome-markets.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
