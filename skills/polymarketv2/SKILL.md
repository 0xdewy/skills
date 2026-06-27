---
name: polymarketv2
description: >-
  Developer reference for Polymarket v2 APIs and SDKs: Gamma, Data, CLOB,
  L1/L2 auth, deposit wallets, POLY_1271/signatureType 3, relayer, unified
  @polymarket/client / polymarket-client, clob-client-v2, py-clob-client-v2,
  and Polymarket-scoped orders, orderbooks, prices, positions, markets, events,
  and authentication. TRIGGER on: Polymarket API/SDK/CLOB questions, gamma-api, deposit wallet,
  funder, relayer, WALLET-CREATE, signatureType, POLY_1271, placing/fetching
  orders, or migration from legacy py-clob-client/clob-client. SKIP on: Kalshi,
  generic prediction-market theory, non-Polymarket web3/DeFi, and casual
  mentions of Polymarket with no integration intent.
license: MIT
metadata:
  author: iamky1e
  version: 1.1.0
  category: finance
  tags:
    - polymarket
    - prediction-markets
    - clob
    - trading
    - web3
    - api
---

# Polymarket v2 API & SDK

Developer reference for integrating with **Polymarket v2** — discovery, market
data, authentication, and non-custodial trading. Ground every answer in the
local reference files or live docs — never guess an endpoint, signature type, or
SDK method you have not checked; open the relevant reference file before
asserting how something works. This file is a router: it gives
the minimal mental model and points to the granular `references/` files. Load
only the reference you need.

## Safety & freshness (read before writing trading code)

- **v2 is evolving and the SDKs are in beta.** This skill was seeded from the
  official docs as of **2026-06-09**. For any code that moves funds, places
  orders, or signs payloads, **re-verify against the current docs first** — start
  at the index `https://docs.polymarket.com/api-reference` and the
  `https://docs.polymarket.com/llms.txt` discovery file. Provenance for every
  section is in `references/sources.md`. Run `python scripts/check_freshness.py`
  to flag reference files whose `last verified:` date has gone stale.
- **Never assist with geoblock circumvention.** Order placement is restricted in
  many jurisdictions (see `references/troubleshooting.md`). You may explain the
  geoblock endpoint and which regions are blocked; do not help bypass it.
- **Never put private keys or API secrets in code or version control.** Use env
  vars / a secret manager.

## v2 mental model (the short version)

Three separate APIs:

| API | Base URL | Serves | Auth |
|---|---|---|---|
| **Gamma** | `https://gamma-api.polymarket.com` | markets, events, tags, series, search, profiles | public |
| **Data** | `https://data-api.polymarket.com` | positions, trades, activity, holders, open interest, leaderboards | public |
| **CLOB** | `https://clob.polymarket.com` | orderbook, prices, midpoints, spreads, history (public) + order placement/cancel (authenticated) | mixed |

Plus: **Bridge** `https://bridge.polymarket.com` (cross-chain deposit/withdraw),
**RFQ** `https://combos-rfq-api.polymarket.sh` (combos/quoting), the **relayer**
(gasless on-chain), and **WebSockets** (`wss://ws-subscriptions-clob.polymarket.com`,
`wss://ws-live-data.polymarket.com`, …). See `references/concepts.md` for the
conceptual model and `references/index.md` to route to the right file.

Trading essentials (Polygon, `chainId = 137`):

- **New API users trade from a deposit wallet using `signatureType = 3`
  (`POLY_1271`).** The deposit wallet is the **funder**, and an order's `maker`
  and `signer` are **both** the deposit wallet address.
- **pUSD must sit in the deposit wallet**, not the owner EOA, to count as buying
  power. **Approvals must come from the deposit wallet** via a relayer `WALLET`
  batch — an EOA `approve()` does nothing for it.
- Signature types: `0` EOA · `1` POLY_PROXY · `2` GNOSIS_SAFE · `3` POLY_1271
  (deposit wallet, **V2 orders only**). Existing Safe/Proxy users keep their type.
- **Recommended SDK path:** the unified beta SDK — `@polymarket/client` (TS) /
  `polymarket-client` (Python) — which defaults to the deposit-wallet flow.
  Standalone `clob-client-v2` / `py-clob-client-v2` / `polymarket_client_sdk_v2`
  + the builder-relayer clients are the alternative.
- **Relayer auth and CLOB L1/L2 auth are independent systems.** Don't reuse one
  for the other.

## How to navigate

Start at `references/index.md` (a one-line-per-topic routing table). For a
targeted lookup without reading whole files, run the local search helper:

```bash
python scripts/search_refs.py "balance allowance signature_type 3"
```

It scans reference headings + `references/source-map.json` (which also maps
common **wrong/legacy** terms to the right v2 answer) and prints
`file#heading — snippet (source: url)`.

## Routing table

| Need | Read |
|---|---|
| Conceptual model: markets/events, order lifecycle, positions, prices, pUSD, resolution | `references/concepts.md` |
| Discover markets/events, search, pagination, filters, sports, profiles | `references/api-gamma.md` |
| Positions, trades, activity, open interest, volume, combo activity | `references/api-data.md` |
| Orderbook, prices, midpoint, spread, fee rate, history (public CLOB) | `references/api-clob-public.md` |
| Real-time WebSockets: market, user, sports, RTDS | `references/api-websockets.md` |
| L1/L2 auth, the 5 POLY_* headers, signature types, API creds | `references/auth-l1-l2.md` |
| Deposit wallets, POLY_1271, address derivation, balance sync | `references/deposit-wallets.md` |
| Relayer WALLET-CREATE / WALLET batches, nonces, query endpoints | `references/relayer.md` |
| Place/cancel/query orders (REST), order types, heartbeat, engine restarts | `references/orders.md` |
| Split/merge/redeem, CTF mechanics, neg-risk conversion | `references/ctf.md` |
| Cross-chain deposits/withdrawals (Bridge API) | `references/bridge.md` |
| Fees, liquidity rewards, maker/taker rebates, tiers | `references/rewards-rebates.md` |
| Builder program: builder code, fees, tiers, attribution | `references/builders.md` |
| Combos + RFQ quoter/market-maker flow | `references/combos-rfq.md` |
| Contract addresses, CLOB error codes, on-chain data, referrals | `references/resources.md` |
| **Recommended** unified SDK (TS + Python), trading, streams, account data | `references/sdk-unified.md` |
| Standalone TS CLOB + relayer client | `references/sdk-clob-ts.md` |
| Standalone Python CLOB + relayer client | `references/sdk-clob-python.md` |
| Rust CLOB client | `references/sdk-rust.md` |
| Errors: invalid signature, not-enough-balance, missing allowance, rate limits, geoblock | `references/troubleshooting.md` |
| Telling v1 from v2, package renames, what changed | `references/v1-v2-migration.md` |
| Machine-readable OpenAPI/AsyncAPI specs | `references/openapi/README.md` |
| Source URLs + last-verified dates | `references/sources.md` |
