---
title: Overview
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/overview.md
section: hypercore
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/overview.md).

# Overview

### Consensus

Hyperliquid is secured by HyperBFT, a variant of HotStuff consensus. Like most proof-of-stake chains, blocks are produced by validators in proportion to the native token staked to each validator.&#x20;

### Execution

The Hyperliquid state consists of HyperCore and the general purpose HyperEVM.&#x20;

HyperCore includes margin and matching engine state. Importantly, HyperCore does not rely on the crutch of off-chain order books. A core design principle is full decentralization with one consistent order of transactions achieved through HyperBFT consensus.&#x20;

### Latency

Consensus currently uses an optimized consensus algorithm called HyperBFT, which is optimized for end-to-end latency. End-to-end latency is measured as duration between sending request and receiving committed response.&#x20;

For an order placed from a geographically co-located client, end-to-end latency has a median 0.2 seconds and 99th percentile 0.9 seconds. This performance allows users to port over automated strategies from other crypto venues with minimal changes and gives retail users instant feedback through the UI.

### Throughput

Mainnet currently supports approximately 200k orders/sec. The current bottleneck is execution. The consensus algorithm and networking stack can scale to millions of orders per second once the execution can keep up. There are plans to further optimize the execution logic once the need arises.&#x20;


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/overview.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
