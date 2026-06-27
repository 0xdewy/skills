---
title: Transfer or deposit to USDC (Perps) missing
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/deposit-or-transfer-issues-missing-lost/transfer-or-deposit-to-usdc-perps-missing.md
section: support
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/deposit-or-transfer-issues-missing-lost/transfer-or-deposit-to-usdc-perps-missing.md).

# Transfer or deposit to USDC (Perps) missing

Situation 1: Transferred 1,000 from USDC (Spot) to USDC (Perps). When I checked, I see <1,000 USDC in my Available Balance. Where did it go?

Situation 2: Deposited 1,000 USDC from Arbitrum, and the deposit was successful. When I checked, I see <1,000 USDC in my Available Balance. Where did it go?

### Reasoning

* If you have open positions on cross margin with negative unrealized P\&L, your deposits and Spot to Perp transfers will go toward collateral for those open positions. Please refer to the Docs to understand how margining works: <https://hyperliquid.gitbook.io/hyperliquid-docs/trading/margining#unrealized-pnl-and-transfer-margin-requirements>


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/deposit-or-transfer-issues-missing-lost/transfer-or-deposit-to-usdc-perps-missing.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
