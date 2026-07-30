---
title: Interaction timings
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/interaction-timings.md
section: hyperevm-dev
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/interaction-timings.md).

# Interaction timings

## Transfer Timing

Transfers from HyperCore to HyperEVM are queued on the L1 until the next HyperEVM block. Transfers from HyperEVM to HyperCore happen in the same L1 block as the HyperEVM block, immediately after the HyperEVM block is built.

## Timing within a HyperEVM block

On an L1 block that produces a HyperEVM block:

1. L1 block is built
2. EVM block is built
3. EVM -> Core transfers are processed&#x20;
4. CoreWriter actions are processed&#x20;

Note that the account performing the CoreWriter action must exist on HyperCore before the EVM block is built. An EVM -> Core transfer to initialize the account in the same block will still result in the CoreWriter action being rejected.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/interaction-timings.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
