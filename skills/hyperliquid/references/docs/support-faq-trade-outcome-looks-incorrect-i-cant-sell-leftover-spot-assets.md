---
title: I can't sell leftover spot assets
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/trade-outcome-looks-incorrect/i-cant-sell-leftover-spot-assets.md
section: support
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/trade-outcome-looks-incorrect/i-cant-sell-leftover-spot-assets.md).

# I can't sell leftover spot assets

### Reasoning&#x20;

* Each spot deployer sets the minimum lot size for trading.&#x20;
* For JEFF, the minimum lot size is 1, so you cannot sell less than that on the order book. If you have <1 JEFF that you would like to sell, you can use a community member’s site that swaps JEFF for USDC: <https://www.heyjeff.fun/>
* For RUB, you can only sell in units of 0.00001
* For XAUT, the minimum lot size is 0.01, so you cannot sell less than that on the order book. You can try transferring to the HyperEVM and swapping it on protocols there or bridge out using <https://gold.usdt0.to/transfer>


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/trade-outcome-looks-incorrect/i-cant-sell-leftover-spot-assets.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
