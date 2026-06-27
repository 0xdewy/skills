---
title: What does \"Action already expired\" mean?
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/trade-outcome-looks-incorrect/what-does-action-already-expired-mean.md
section: support
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/trade-outcome-looks-incorrect/what-does-action-already-expired-mean.md).

# What does "Action already expired" mean?

This error message appears if you perform an action (e.g., placing an order) and it's not accepted by the L1 within 15 seconds. This is meant to prevent against situations where your connection is unstable or the chain is congested and you would not want the action to be delayed by more than 15 seconds.&#x20;

If you still want the action to go through (e.g., in a situation where your internet connection is bad, but you still want to trade), go to the settings dropdown and check the box next to "Disable Transaction Delay Protection".&#x20;

Important: Be aware that disabling this protection may cause delayed orders to be placed after reconnection or when congestion eases. This may result in multiple order placements (if you made multiple attempts to execute an order during the delay) when you only intended for a single action to take place. As an example, placing a short order to close a long position may result in closing the long and opening a short position if multiple short orders were attempted during the delay.

<figure><img src="/files/Q14XE9lXzXL0c2WVxMdS" alt="" width="270"><figcaption></figcaption></figure>


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/trade-outcome-looks-incorrect/what-does-action-already-expired-mean.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
