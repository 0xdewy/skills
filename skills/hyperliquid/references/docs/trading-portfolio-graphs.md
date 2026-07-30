---
title: Portfolio graphs
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/portfolio-graphs.md
section: trading
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/portfolio-graphs.md).

# Portfolio graphs

The portfolio page shows account value and P\&L graphs on 24 hour, 7 day, and 30 day time horizons.&#x20;

`Account value` includes unrealized pnl from cross and isolated margin positions, as well as vault balances.&#x20;

Pnl is defined as `account value` plus net deposits, i.e. `account value + deposits - withdrawals`.

Note that these graphs are samples on deposits and withdrawals and also every 15 minutes. Therefore, they are not recommended to precise accounting purposes, as the interpolation between samples may not reflect the actual change in unrealized pnl in between two consecutive samples.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/trading/portfolio-graphs.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
