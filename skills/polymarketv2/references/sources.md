# Sources & provenance

This skill was seeded from the official Polymarket documentation as of
**last verified: 2026-06-09**. The v2 SDKs are in beta and the docs change
quickly — **re-verify against the live docs before writing any code that moves
funds, places orders, or signs payloads.** Discovery starts at the docs index
and the `llms.txt` file.

| Topic / reference file | Source URL |
|---|---|
| Docs index / overview | https://docs.polymarket.com/api-reference |
| LLM discovery index | https://docs.polymarket.com/llms.txt |
| `concepts.md` | https://docs.polymarket.com/concepts/* |
| `api-gamma.md` | https://docs.polymarket.com (Gamma API: `gamma-api.polymarket.com`) · /api-reference/{sports,profiles,comments,tags,series,search}/* |
| `api-data.md` | https://docs.polymarket.com (Data API: `data-api.polymarket.com`) · /api-reference/{core,misc}/* |
| `api-clob-public.md` | https://docs.polymarket.com (CLOB API: `clob.polymarket.com`) · /api-reference/{market-data,markets}/* |
| `api-websockets.md` | https://docs.polymarket.com/market-data/websocket/* · /api-reference/wss/* |
| `auth-l1-l2.md` | https://docs.polymarket.com/api-reference/authentication |
| `deposit-wallets.md` | https://docs.polymarket.com/trading/deposit-wallets |
| `relayer.md` | https://docs.polymarket.com/trading/deposit-wallets · /trading/gasless · /api-reference/relayer/* |
| `orders.md` | https://docs.polymarket.com/trading/orders/* · /trading/matching-engine · /api-reference/trade/* |
| `ctf.md` | https://docs.polymarket.com/trading/ctf/* · /advanced/neg-risk |
| `bridge.md` | https://docs.polymarket.com/trading/bridge/* · /api-reference/bridge/* |
| `rewards-rebates.md` | https://docs.polymarket.com/trading/fees · /market-makers/{liquidity-rewards,maker-rebates} · /trading/taker-rebates · /api-reference/{rewards,rebates}/* |
| `builders.md` | https://docs.polymarket.com/builders/* · /trading/orders/attribution · /api-reference/builders/* |
| `combos-rfq.md` | https://docs.polymarket.com/market-makers/combos · /api-reference/maker/* · /api-reference/combo-markets/* · /api-reference/wss/rfq |
| `resources.md` | https://docs.polymarket.com/resources/{contracts,error-codes,blockchain-data,referral-program} |
| `openapi/` (bundled specs) | https://docs.polymarket.com/api-spec/* · AsyncAPI `asyncapi*.json`; see `openapi/README.md` |
| `sdk-unified.md` | https://docs.polymarket.com/dev-tooling/typescript · https://docs.polymarket.com/dev-tooling/python |
| `sdk-clob-ts.md` | https://github.com/Polymarket/clob-client-v2 · https://github.com/Polymarket/builder-relayer-client |
| `sdk-clob-python.md` | https://github.com/Polymarket/py-clob-client-v2 · https://github.com/Polymarket/py-builder-relayer-client |
| `sdk-rust.md` | https://github.com/Polymarket/rs-clob-client-v2 · https://crates.io/crates/polymarket_client_sdk_v2 |
| Rate limits | https://docs.polymarket.com (Rate Limits) |
| Geoblock | https://polymarket.com/api/geoblock · https://docs.polymarket.com/api-reference/geoblock |
| `v1-v2-migration.md` | https://docs.polymarket.com/v2-migration |
| Clients & SDKs overview | https://docs.polymarket.com/api-reference/clients-sdks |

## Key addresses (Polygon mainnet, chainId 137)

All contract addresses live in **`references/resources.md`** (the canonical
registry, sourced from `https://docs.polymarket.com/resources/contracts`). They
are intentionally not duplicated here.
