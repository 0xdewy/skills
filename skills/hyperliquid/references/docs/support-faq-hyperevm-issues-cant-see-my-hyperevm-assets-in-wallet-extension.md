---
title: Can\u2019t see my HyperEVM assets in wallet extension
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/hyperevm-issues/cant-see-my-hyperevm-assets-in-wallet-extension.md
section: support
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/hyperevm-issues/cant-see-my-hyperevm-assets-in-wallet-extension.md).

# Can’t see my HyperEVM assets in wallet extension

Here is a guide with common questions regarding how to use the HyperEVM: <https://hyperliquid.gitbook.io/hyperliquid-docs/onboarding/how-to-use-the-hyperevm>

### Add HyperEVM to your wallet extension

Follow the steps below or using Chainlist: <https://chainlist.org/chain/999>

* Add the chain to your wallet using "Add custom network":&#x20;
* Chain ID: 999&#x20;
* Network Name: Hyperliquid&#x20;
* RPC URL: <https://rpc.hyperliquid.xyz/evm&#x20>;
* Currency Symbol: HYPE

### For specific HyperEVM asset - add custom network token <a href="#custom-network-token" id="custom-network-token"></a>

* Click the wallet icon (see below) to the right of the Contract in the info bar for a given spot asset on the Trade page

<figure><img src="/files/OF6LVizNzj3bJEHcSZNG" alt=""><figcaption></figcaption></figure>

* To do this manually, you can add the contract address for a token directly to your wallet extension. You can find the contract address for a given token using a HyperEVM explorer, such as <https://www.hyperscan.com/token/0x9b498C3c8A0b8CD8BA1D9851d40D186F1872b44E> or <https://purrsec.com/address/0x9b498c3c8a0b8cd8ba1d9851d40d186f1872b44e> for PURR &#x20;

If you have tried the above, but your wallet extension does not support the HyperEVM as a custom network, consider using Rabby, which supports the HyperEVM as an integrated network: <https://support.rabby.io/en/articles/14120403-migrating-from-metamask-or-other-wallets>


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/hyperevm-issues/cant-see-my-hyperevm-assets-in-wallet-extension.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
