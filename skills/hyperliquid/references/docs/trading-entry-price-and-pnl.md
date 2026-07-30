---
title: Entry price and pnl
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/entry-price-and-pnl.md
section: trading
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/entry-price-and-pnl.md).

# Entry price and pnl

On the Hyperliquid DEX, entry price, unrealized pnl, and closed pnl are purely frontend components provided for user convenience. The fundamental accounting is based on margin (balance for spot) and trades.&#x20;

### Perps

Perp trades are considered `opening` when the absolute value of the position increases. In other words, longing when already long or shorting when already short.

For opening trades, the entry price is updated to an average of current entry price and trade price weighted by size.

For closing trades, the entry price is kept the same.

Unrealized pnl is defined as `side * (mark_price - entry_price) * position_size` where `side = 1` for a long position and `side = -1` for a short position

Closed pnl is `fee + side * (mark_price - entry_price) * position_size` for a closing trade and only the fee for an opening trade.

### Spot

Spot trades use the same formulas as perps with the following modifications: Spot trades are considered `opening` for buys and `closing` for sells. Transfers are treated as buys or sells at mark price, and genesis distributions are treated as having entry price at `10000 USDC` market cap. Note that while 0 is the correct answer as genesis distributions are not bought, it leads to undefined return on equity.&#x20;

Pre-existing spot balances are assigned an entry price equal to the first trade or send after the feature was enabled around July 3 08:00 UTC.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/trading/entry-price-and-pnl.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
