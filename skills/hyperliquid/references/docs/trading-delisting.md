---
title: Delisting
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/delisting.md
section: trading
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/delisting.md).

# Delisting

Validators vote on whether to delist validator-operated perps. If validators vote to delist an asset, the perps will settle to the 1 hour time weighted spot oracle price before the scheduled delisting voting time. This is a settlement mechanism used by many centralized exchanges.&#x20;

When an asset is delisted, all positions are settled and open orders are cancelled. Users who wish to avoid automatic settlement should close their positions beforehand. After settlement, no new orders will be accepted.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/trading/delisting.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
