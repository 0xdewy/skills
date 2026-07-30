---
title: Protocol vaults
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/vaults/protocol-vaults.md
section: hypercore
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/vaults/protocol-vaults.md).

# Protocol vaults

Hyperliquidity Provider (HLP) is a protocol vault that provides liquidity to Hyperliquid through multiple market making strategies, performs liquidations, supplies USDC in Earn, and accrues a portion of trading fees.

HLP democratizes strategies typically reserved for privileged parties on other exchanges. The community can provide liquidity for the vault and share its pnl. HLP is fully community-owned.

The deposit lock-up period is 4 days. This means you can withdraw 4 days after your most recent deposit. E.g., if you deposited on Sep 14 at 08:00, you would be able to withdraw on Sep 18 at 08:00.

For more information about HLP, see these blog posts:&#x20;

<https://medium.com/@hyperliquid/hyperliquidity-provider-hlp-democratizing-market-making-bb114b1dff0f>\
<https://medium.com/@hyperliquid/hlp-update-3-months-in-42327abe3e57>\
Note that the blog posts may not be up-to-date.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/vaults/protocol-vaults.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
