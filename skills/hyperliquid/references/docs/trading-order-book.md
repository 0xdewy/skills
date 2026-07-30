---
title: Order book
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/order-book.md
section: trading
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/order-book.md).

# Order book

The order book works in essentially the same way as all centralized exchanges but is fully on-chain. Orders are added where price is an integer multiple of the tick size, and size is an integer multiple of lot size. The orders are matched in price-time priority.&#x20;

See this[ ](/hyperliquid-docs/hypercore/order-book.md)[section](/hyperliquid-docs/hypercore/order-book.md) for further details on order book implementation.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/trading/order-book.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
