---
title: Miscellaneous UI
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/miscellaneous-ui.md
section: trading
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/miscellaneous-ui.md).

# Miscellaneous UI

### Max Drawdown

The max drawdown on the portfolio page is only used on the frontend for users' convenience. It does not affect any margining or computations on Hyperliquid. Users who care about the precise formula can get their account value and pnl history and compute it however they choose.

The formula used on the frontend is the maximum over times `end > start` of the value `(pnl(end) - pnl(start)) / account_value(start)`&#x20;

Note that the denominator is account value and the numerator is pnl. Also note that this not equal to absolute max drawdown divided by some account value. Each possible time range considered uses its own denominator.&#x20;


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/trading/miscellaneous-ui.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
