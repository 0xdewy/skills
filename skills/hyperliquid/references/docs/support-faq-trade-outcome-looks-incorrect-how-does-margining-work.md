---
title: How does margining work?
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/trade-outcome-looks-incorrect/how-does-margining-work.md
section: support
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/trade-outcome-looks-incorrect/how-does-margining-work.md).

# How does margining work?

Situation: Why didn’t my margin become available after I closed a Perps position? I closed a Perps position that showed 1,000 USDC in margin, but after closing, my Available Balance increased by <1,000 USDC. Where did the rest go?

### Reasoning

* This typically happens if you're using cross margin and have other open positions with negative unrealized pnl.
* In cross margin mode, all your positions share a common pool of margin. When you close one position, the funds (\~1,000 USDC in this example) are not released directly into your Available Balance if other open positions with negative unrealized pnl still require margin because they didn’t meet the initial margin requirements. New margin, be it through closing a position or depositing USDC, goes toward these existing positions.&#x20;
* So while the 1,000 USDC is still part of your Total Balance, only a portion becomes available to trade, depending on your overall margin requirements.
* Please refer to the Docs to understand how Margining works: <https://hyperliquid.gitbook.io/hyperliquid-docs/trading/margining#unrealized-pnl-and-transfer-margin-requirements>


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/trade-outcome-looks-incorrect/how-does-margining-work.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
