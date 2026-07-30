---
title: Gas problem on EVM
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/hyperevm-issues/gas-problem-on-evm.md
section: support
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/hyperevm-issues/gas-problem-on-evm.md).

# Gas problem on EVM

### **What is used for gas for HyperEVM?** <a href="#gas-on-hyperevm" id="gas-on-hyperevm"></a>

* The gas for EVM transfers and transactions on the HyperEVM is HYPE
* To transfer tokens from HyperCore to EVM, you will need HYPE on HyperCore (Spot)
* To transfer tokens from EVM to HyperCore and other transactions on the HyperEVM, you will need HYPE on the HyperEVM

### **Situation 1: I see this error “Invalid transaction envelope type: specified type “0x2” but included a gasPrice instead of maxFeePerGas and maxPriorityFeePerGas”** <a href="#gas-issue-metamask" id="gas-issue-metamask"></a>

* This is a known issue with MetaMask; you can try a different wallet like Rabby: <https://support.rabby.io/en/articles/14120403-migrating-from-metamask-or-other-wallets>

### **Situation 2: Why does my wallet indicate that I have insufficient ETH balance for transactions when I do in my wallet?** <a href="#eth-gas-issues" id="eth-gas-issues"></a>

* You don't need ETH for gas on the HyperEVM. You need HYPE for gas on the HyperEVM
* Usually this means you didn't add the HyperEVM network properly to your wallet extension. Please follow the instructions here: <https://hyperliquid.gitbook.io/hyperliquid-docs/onboarding/how-to-use-the-hyperevm#how-do-i-add-the-hyperevm-to-my-wallet-extension>
* Your wallet extension may not support the HyperEVM as a custom network. Consider switching to Rabby, which supports the HyperEVM as an integrated network: <https://support.rabby.io/en/articles/14120403-migrating-from-metamask-or-other-wallets>


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/hyperevm-issues/gas-problem-on-evm.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
