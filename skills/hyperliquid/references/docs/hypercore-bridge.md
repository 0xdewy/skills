---
title: Bridge
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/bridge.md
section: hypercore
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/bridge.md).

# Bridge

Deposits to the bridge are signed by the validators and are credited when more than 2/3 of the staking power has signed the deposit.

Withdrawals from Hyperliquid are immediately deducted from the L1 balance, and validators sign the withdrawal as separate transactions. When 2/3 of the staking power has signed the withdrawal, an EVM transaction can be sent to the bridge to request the withdrawal.&#x20;

After a withdrawal is requested, there is a dispute period during which the bridge can be locked for a malicious withdrawal that does not match the Hyperliquid state. Cold wallet signatures of 2/3 of the stake-weighted validator set are required to unlock the bridge. &#x20;

After the dispute period, finalization transactions are sent, which distribute the USDC to the corresponding destination addresses. There is a similar mechanism to maintain the set of active validators and their corresponding stake on the bridge contract.&#x20;

Withdrawals do not require any Arbitrum ETH from the user. Instead, a withdrawal gas fee of 1 USDC is paid by the user on Hyperliquid to cover the Arbitrum gas costs of the validators. &#x20;

The bridge and its logic in relation to the L1 staking have been audited by Zellic. See the Hyperliquid GitHub repository for the full bridge code, and the [Audits](/hyperliquid-docs/audits.md) section for the audit reports.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/bridge.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
