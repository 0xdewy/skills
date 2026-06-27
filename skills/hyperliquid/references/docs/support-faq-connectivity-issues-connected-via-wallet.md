---
title: Connected via wallet
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/connectivity-issues/connected-via-wallet.md
section: support
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/connectivity-issues/connected-via-wallet.md).

# Connected via wallet

If you’re experiencing issues connecting your wallet to Hyperliquid, such as a recursive "Establish Connection" loop, failed transaction signing, or your wallet extension not loading, try the following troubleshooting steps.&#x20;

### Quick fixes

* Update your wallet extension to the latest version and make sure it’s enabled
* Hard refresh your browser (on most browsers: Ctrl+Shift+R or Cmd+Shift+R) and clear cache
* Disconnect and reconnect your wallet
* Switch networks (e.g., to Ethereum) and then switch back to Arbitrum if you’re trying to deposit USDC on Arbitrum or the HyperEVM if you’re trying to use the HyperEVM

### Wallet specific compatibility issues with Hyperliquid <a href="#wallet-specific-issues" id="wallet-specific-issues"></a>

* Coinbase: Users on mobile may face connection problems. Try using the Coinbase Chrome extension instead
* Metamask: Some users face issues with MetaMask on the HyperEVM. If this persists, consider migrating to a more compatible wallet like Rabby
* Trezor forbidden keypath error: This is related to privacy settings within Trezor. In Trezor Suite's Security / Safety Checks change from "Strict" to "Prompt"&#x20;
* Ledger "Transfer Failed" error on the HyperEVM: Update to the latest Ledger software/firmware
* Reinstall your wallet extension: Make sure you have your seed phrase or private key backed up before doing this

Lastly, you can try switching to Rabby Wallet, which often works more smoothly with Hyperliquid. Your trades, history, and address remain the same even if you use a new wallet extension. <https://support.rabby.io/en/articles/14120403-migrating-from-metamask-or-other-wallets>


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/connectivity-issues/connected-via-wallet.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
