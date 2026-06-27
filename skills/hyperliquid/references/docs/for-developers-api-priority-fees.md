---
title: Priority fees
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/priority-fees.md
section: api
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/priority-fees.md).

# Priority fees

### Gossip (read) priority

Background: latency-sensitive users may find `split_client_blocks: true` useful, as it streams transactions to be committed before they are included in client blocks. This can lead to 70-150ms improvement in latency when reading inputs. As documented in the node repository, these are the fastest transaction inputs to execution, broadcast even before they are executed by the L1. The tradeoff with the faster input data is that the results from execution are not yet available. However, with simple actions like orders, the consumer can stream estimated account values for all users to predict execution results with reasonable accuracy.

There are 2 independent Dutch auctions synced to the same 3 minute schedule. The auction indices are optionally interpreted by nodes as an ordering for their peers when sending data. The priority ordering affects both split client blocks and normal client blocks that include responses. The foundation non-validator will opt into respecting the gossip priority auction ordering.&#x20;

The independent slot auctions are not additive, so an IP bidding multiple slots will be prioritized according to its lowest slot. For the auction to affect latency, the onchain IP must exactly match the IP seen by the peer sending data. Each auction's results only affect the duration of the following auction. For nodes that are connected via a chain of nodes to the validating network, note that each network hop may or may not respect the priority auction depending on how the parent node is configured.&#x20;

The lower auction indices are strictly prioritized over higher indices. The prioritization applies to all data in the mempool transactions stream equally. The ordering should be relatively consistent in expectation but is subject to variance from the p2p consensus network. Gossip priority applies only to reading data. For prioritization of sending data, see the section below on order priority. Nodes respecting gossip priority will use the previous auction winners relative to that node's current execution state. Similar to token, spot, and perp deployment auctions, fees come out of spot balance are burned.

The previous auction winners (i.e., current gossip priority ordering) and current auction statuses can be queried using the info request `{ "type": "gossipPriorityAuctionStatus"}`.&#x20;

Gossip priority reduces the need for market makers to hyper-optimize their infrastructure to remain competitive. To participate in the auction, users send action `{"type": "gossipPriorityBid", "slotId": 0, "ip": "1.2.3.4", "maxGas": 100000000}` where gas is wei (i.e. units of `0.00000001` HYPE) of HYPE charged from spot balance. Each auction resets to 10 times the previous winning price of that slot, and have a minimum price of `0.1 HYPE`. Any address may bid on behalf of any IP address.&#x20;

The current empirical effect of gossip priority on mainnet is approximately 25 ms reduction in latency per auction slot.

### Order (write) priority

Orders can be sent with grouping of the form `{"p": 12345}` where the rate is interpreted as a fraction `p / 100000000.0`. The rate is charged from undelegated staking balance as a fraction of the filled notional, converted to HYPE using the spot mark price. Currently, priority grouping is only supported for order actions where every order is IOC and on a perp asset. The max priority rate is 8bps, i.e. `p = 80000`. Under order priority, all cancels are prioritized before all immediately executable orders. However, higher priority orders are prioritized before lower priority orders as a linear function of priority rate.&#x20;

Order priority reduces the need for market makers to hyper-optimize their order entry and connectivity, and instead focus on the strategy itself. It further protects makers and allows responsiveness to price moves driven by traditional venues.

Order priority applies only to sending data. For prioritization of reading data, see the previous section on gossip priority. Similar to gossip priority auctions, order priority fees are burned.

Priority fee paid can be read from the `user_fills` file written by the nodes as field `priorityGas` .

The current empirical effect of order priority fees on mainnet is approximately 45 ms reduction in end-to-end latency per 1 bp of priority fee paid.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/priority-fees.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
