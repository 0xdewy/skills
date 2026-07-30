---
title: Uniswap perpetuals
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/uniswap-perpetuals.md
section: trading
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/uniswap-perpetuals.md).

# Uniswap perpetuals

Some perpetual contracts on Hyperliquid use Uniswap V2 or V3 AMM price as the underlying spot asset. These contracts are restricted to be isolated-only, which means that cross margin is not allowed and margin cannot be manually removed from an open position. Instead, the position must be partially or fully closed to partially or fully return isolated margin.

Uniswap pool prices are always converted to USDT prices based on the robust CEX oracle prices.

The current contract addresses for the Uniswap pools used as oracles:

RLB: `0x510100d5143e011db24e2aa38abe85d73d5b2177`


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/trading/uniswap-perpetuals.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
