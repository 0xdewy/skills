---
title: Withdrawing to Phantom Wallet
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/withdrawal-issues/withdrawing-to-phantom-wallet.md
section: support
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/withdrawal-issues/withdrawing-to-phantom-wallet.md).

# Withdrawing to Phantom Wallet

### Situation 1: You need 1 USDC for withdrawals and cannot deposit USDC via Phantom wallet, since Phantom does not support Arbitrum <a href="#need-usdc" id="need-usdc"></a>

* **Option 1**&#x20;
  * You sell some SOL/2Z/BONK/FARTCOIN/PUMP/SPX on Spot for USDC (Spot). Note that minimum transaction amount is $10.
* **Option 2**&#x20;
  * Export your Phantom wallet’s Ethereum private key and import it to another wallet like Rabby that supports the Arbitrum network.
    * Export: <https://help.phantom.com/hc/en-us/articles/25334064171795-How-to-view-your-recovery-phrase-or-private-key-in-Phantom>
    * Migrate to Rabby (optional): <https://support.rabby.io/en/articles/14120403-migrating-from-metamask-or-other-wallets>
  * Deposit USDC via Arbitrum Network on Rabby (or other Arbitrum compatible wallets). Note that minimum deposit is $5.

### Situation 2: You withdrew USDC over Arbitrum to your Phantom wallet but cannot find it <a href="#missing-usdc" id="missing-usdc"></a>

* Your funds are not lost, they are on the Arbitrum network.
* Export your Phantom wallet’s Ethereum private key and import it to another wallet like Rabby that supports the Arbitrum network.
  * Export: <https://help.phantom.com/hc/en-us/articles/28355165637011-Exporting-Your-Private-Key>
  * Migrate to Rabby (optional): <https://support.rabby.io/en/articles/14120403-migrating-from-metamask-or-other-wallets>


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/withdrawal-issues/withdrawing-to-phantom-wallet.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
