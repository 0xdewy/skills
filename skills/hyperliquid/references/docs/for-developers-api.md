---
title: API
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api.md
section: api
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api.md).

# API

Python SDK: <https://github.com/hyperliquid-dex/hyperliquid-python-sdk>

Rust SDK written by community member, Infinite Field: <https://github.com/infinitefield/hypersdk>

Typescript SDKs written by members of the community:\
<https://github.com/nktkas/hyperliquid>\
<https://github.com/nomeida/hyperliquid>

CCXT also maintains integrations in multiple languages that conforms with the standard CCXT API: <https://docs.ccxt.com/#/exchanges/hyperliquid><br>

All example API calls use the mainnet url (<https://api.hyperliquid.xyz>), but you can make the same requests against testnet using the corresponding url (<https://api.hyperliquid-testnet.xyz>)


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
