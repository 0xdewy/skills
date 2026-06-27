---
title: Optimizing latency
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/optimizing-latency.md
section: api
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/optimizing-latency.md).

# Optimizing latency

The following optimizations may help latency-sensitive traders:

1. Run a non-validating node against a reliable peer, such as Hyper Foundation non-validator.&#x20;
2. Run node with `--disable-output-file-buffering` to get outputs as soon as blocks are executed
3. Run node with sufficient machines specs, at least 32 logical cores, 128 GB RAM, and 500 MB/s disk throughput. Increasing cores can reduce latency because blocks will be faster to execute.
4. Construct book and other exchange state locally using outputs from node, which has faster and more granular data than the API. See <https://github.com/hyperliquid-dex/order_book_server> for an example on how to build an order book on the same machine that is running a node.
5. `--batch-by-block` on the node will wait until the end of the block to write the data. The example order book server above uses this to simplify logic, but a further optimization could include turning the flag off and inferring block boundaries otherwise.
6. Read and write priority fees can significantly improve latency. See [here](/hyperliquid-docs/for-developers/api/priority-fees.md) for more details.&#x20;


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/optimizing-latency.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
