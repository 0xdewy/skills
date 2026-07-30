# References index

Routing table only — load the one file that matches the task. For a targeted
lookup across all files, run `python scripts/search_refs.py "<terms>"`.
(last verified: 2026-06-09)

| Load this file when… | File |
|---|---|
| Learning the conceptual model (markets/events, order lifecycle, positions, prices, pUSD, resolution) | `concepts.md` |
| Discovering/browsing markets, events, tags, series, sports, profiles, or searching | `api-gamma.md` |
| Reading user positions, trades, activity, open interest, live volume, or combo activity | `api-data.md` |
| Reading public CLOB market data (book, prices, midpoint, spread, fee rate, history, market info) | `api-clob-public.md` |
| Streaming real-time data over WebSockets (market, user, sports, RTDS) | `api-websockets.md` |
| Setting up authentication (L1 private key, L2 API key, signature types, headers) | `auth-l1-l2.md` |
| Setting up a deposit wallet, signing POLY_1271 orders, deriving wallet addresses | `deposit-wallets.md` |
| Deploying a wallet or submitting on-chain wallet actions via the relayer | `relayer.md` |
| Placing/cancelling/querying orders (REST), order types, heartbeat, engine restarts | `orders.md` |
| Split / merge / redeem tokens, CTF mechanics, neg-risk conversion | `ctf.md` |
| Cross-chain deposits and withdrawals (Bridge API) | `bridge.md` |
| Fees, liquidity rewards, maker/taker rebates, tiers | `rewards-rebates.md` |
| Builder program: builder code, builder fees, tiers, attribution | `builders.md` |
| Combos and the RFQ quoter/market-maker flow | `combos-rfq.md` |
| Contract addresses, CLOB error codes, on-chain data sources, referrals | `resources.md` |
| Building anything with the **recommended** unified SDK (TS or Python) | `sdk-unified.md` |
| Using the standalone TypeScript CLOB / relayer client | `sdk-clob-ts.md` |
| Using the standalone Python CLOB / relayer client | `sdk-clob-python.md` |
| Using the Rust CLOB client | `sdk-rust.md` |
| Debugging an error, rate limit, or geoblock question | `troubleshooting.md` |
| Unsure whether code/packages are v1 or v2, or migrating | `v1-v2-migration.md` |
| Needing exact schemas (OpenAPI/AsyncAPI machine-readable specs) | `openapi/README.md` |
| Citing a source URL or checking the last-verified date | `sources.md` |
