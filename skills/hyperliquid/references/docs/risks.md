---
title: Risks
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/risks.md
section: general
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/risks.md).

# Risks

### Smart contract risk

The onchain perp DEX depends on the correctness and security of the Arbitrum bridge smart contracts. Bugs or vulnerabilities in the smart contracts could result in the loss of user funds.&#x20;

### L1 risk

Hyperliquid runs on its own L1 which has not undergone as extensive testing and scrutiny as other established L1s like Ethereum. The network may experience downtime due to consensus or other issues.

### Market liquidity risk

As a relatively new protocol, there could be a potential risk of low liquidity, especially in the early stages. This can lead to significant price slippage for traders, negatively affecting the overall trading experience and possibly leading to substantial losses.

### Oracle manipulation risk

Hyperliquid relies on price oracles maintained by the validators to supply market data. If an oracle is compromised or manipulated for an extended period of time, the mark price could be affected and liquidations could occur before the price reverts to its fair value.

### Risk mitigation

There are additional measures in place to prevent oracle manipulation attacks on less liquid assets. One such restriction is open interest caps, which are based on a combination of liquidity, basis, and leverage in the system.&#x20;

When an asset hits the open interest cap, no new positions can be opened. Furthermore, orders cannot rest further than 1% from the oracle price. HLP is exempt from these rules in order to continue quoting liquidity.

Note that this is not an exhaustive list of potential risks.&#x20;


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/risks.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
