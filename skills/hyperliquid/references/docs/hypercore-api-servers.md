---
title: API servers
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/api-servers.md
section: hypercore
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/api-servers.md).

# API servers

API servers listen to updates from a node and maintain the blockchain state locally. The API server serves information about this state and also forwards user transactions to the node. The API serves two sources of data: REST and WebSocket.&#x20;

When user transactions are sent to an API server, they are forwarded to the connected node, which then gossips the transaction as part of the HyperBFT consensus algorithm. Once the transaction has been included in a committed block on the L1, the API server responds to the original request with the execution response from the L1.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/api-servers.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
