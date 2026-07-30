---
title: Auto-deleveraging
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/auto-deleveraging.md
section: trading
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/auto-deleveraging.md).

# Auto-deleveraging

Auto-deleveraging strictly ensures that the platform stays solvent. If a user's account value or isolated position value becomes negative, the users on the opposite side of the position are ranked by unrealized pnl and leverage used. Backstop liquidated positions have no special treatment in the ADL queue logic. The specific sorting index to determine the affected users in profit is `(mark_price / entry_price) * (notional_position / account_value)`. Those traders' positions are closed at the previous mark price against the now underwater user, ensuring that the platform has no bad debt. &#x20;

Auto-deleveraging is an important final safeguard on the solvency of the platform. There is a strict invariant that under all operations, a user who has no open positions will not socialize any losses of the platform.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/trading/auto-deleveraging.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
