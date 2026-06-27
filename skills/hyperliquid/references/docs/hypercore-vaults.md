---
title: Vaults
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/vaults.md
section: hypercore
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/vaults.md).

# Vaults

Vaults are a general case of the powerful functionality that HyperEVM enables via CoreWriter and precompiles. Builders can create and tokenize vaults on the HyperEVM with fully customizable accounting. Builders can follow specs such as <https://eips.ethereum.org/EIPS/eip-4626> with the added benefit of trustless read and write operations on HyperCore. For example, vaults can trade onchain via CoreWriter, or they can delegate any number of authorized agents using CoreWriter. The net result is fully onchain accounting via precompiles, and full access to Core features including spot and HIP-3 in all quote assets.&#x20;

This is a strict improvement over the "legacy" HyperCore vaults, which were introduced in 2023 and do not support HIP-3 or spot trading.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/vaults.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
