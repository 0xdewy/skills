---
title: Raw HyperEVM block data
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/raw-hyperevm-block-data.md
section: hyperevm-dev
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/raw-hyperevm-block-data.md).

# Raw HyperEVM block data

Builders running a non-validating node can index the HyperEVM using data written to `~/hl/data/evm_block_and_receipts` . This data is written after committed blocks are verified by the node, and therefore has no additional trust assumptions compared to running the EVM RPC directly from the node itself.

Builders that wish to index the HyperEVM without running a node can use the S3 bucket: `aws s3 ls s3://hl-mainnet-evm-blocks/ --request-payer requester`.&#x20;

There is a similar bucket `s3://hl-testnet-evm-blocks/` for testnet.

Builders interested in robustness can merge the two data sources, relying primarily on local data and falling back to S3 data.

Some potential applications include a JSON-RPC server with custom rate limits, a HyperEVM block explorer, or other indexed services and tooling for builders.

While the data is public for anyone to use, the requester must pay for data transfer costs. The filenames are predictably indexed by EVM block number, e.g. `s3://hl-mainnet-evm-blocks/0/6000/6123.rmp.lz4.` An indexer can copy block data from S3 on new HyperEVM blocks. The files are stored in MessagePack format and then compressed using LZ4.

Note that testnet starts with directory `s3://hl-testnet-evm-blocks/18000000`and the earlier testnet RPC blocks were not backfilled.

An example can be found in the Python SDK: <https://github.com/hyperliquid-dex/hyperliquid-python-sdk/blob/master/examples/evm_block_indexer.py>


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/raw-hyperevm-block-data.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
