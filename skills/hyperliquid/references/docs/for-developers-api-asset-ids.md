---
title: Asset IDs
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/asset-ids.md
section: api
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/asset-ids.md).

# Asset IDs

Asset IDs are the integer representation for sending orders and cancels via actions. See [here](/hyperliquid-docs/for-developers/api/exchange-endpoint.md) for more details.

### Perps

Perpetual endpoints expect an integer for `asset`, which is the index of the coin found in the `meta` info response. E.g. `BTC = 0` on mainnet.

Builder-deployed perps expect `100000 + perp_dex_index * 10000 + index_in_meta` . For example, `test:ABC` on testnet has `perp_dex_index = 1` ,`index_in_meta = 0` , `asset = 110000` . Note that builder-deployed perps always have name in the format `{dex}:{coin}` .

### Spot

Spot endpoints expect `10000 + spotInfo["index"]` where `spotInfo` is the corresponding object in `spotMeta` that has the desired quote and base tokens. For example, when submitting an order for `PURR/USDC`, the asset that should be used is `10000` because its asset index in the spot info is `0`.

Note that spot ID is different from token ID, and that mainnet and testnet have different asset IDs. For example, for HYPE:

Mainnet token ID: 150

Mainnet spot ID: 107

Testnet token ID: 1105

Testnet spot ID: 1035

### Outcomes

Outcomes share most implementation details with spot trading, with a different token representing each outcome side. However, the API representation of outcomes is different from both spot and perps.

Outcome assets are derived from an `outcome` id plus a binary `side`. These are found in the `outcomeMeta` info response.

For an outcome with id `outcome` and side `side`:

```
encoding = 10 * outcome + side
```

Only side `0` and side `1` are valid.

Example:

* outcome `1`, side `0` -> encoding `10`

The same `encoding` is used in three different representations:

* Outcome spot coin: `#<encoding>`
* Outcome token name: `+<encoding>`
* Outcome asset ID: `100_000_000 + encoding`

Example:

* `#10` = outcome `1`, side `0`
* `+10` = the corresponding token name
* `100000010` = asset ID


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/asset-ids.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
