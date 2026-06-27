---
title: Deposited via Plasma network
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/deposit-or-transfer-issues-missing-lost/deposited-via-plasma-network.md
section: support
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/deposit-or-transfer-issues-missing-lost/deposited-via-plasma-network.md).

# Deposited via Plasma network

* The Plasma address can only receive XPL on the Plasma network. Deposits other than XPL or on other networks will fail and not be credited, e.g., Depositing USDC on Plasma will fail and not be credited.
  * If you accidentally sent USDT0 on Plasma, you can try Unit's revert feature: <https://app.hyperunit.xyz/revert>. Instructions can be found here: <https://docs.hyperunit.xyz/how-to/revert>.&#x20;
  * If you accidentally sent another asset that is not supported on Plasma or sent XPL on a chain other than Plasma, there isn't a way to retrieve these assets currently, unless Unit adds support for them.
  * If you sent the right token on the right chain and deposited more than the minimum amount, but your XPL still shows up as “Failed", reach out to the Unit team, which manages Plasma network deposits & withdrawals: [https://app.hyperunit.xyz/support](<https://app.hyperunit.xyz/support >)​
* There is a minimum deposit of 60 XPL. Deposits below 60 XPL will result in a loss of funds.
* Note that Plasma deposits take \~1 minute to arrive in your wallet. You can check the time estimate in the same deposit pop-up where you copied the deposit address.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/deposit-or-transfer-issues-missing-lost/deposited-via-plasma-network.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
