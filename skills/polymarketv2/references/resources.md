# Resources — contracts, error codes, on-chain data

Scope: the **canonical** Polymarket contract registry, the CLOB error-code
reference, and where to get on-chain analytics. All addresses live here and
nowhere else in this skill — other files point back to this one.
Source: https://docs.polymarket.com/resources/contracts ·
https://docs.polymarket.com/resources/error-codes ·
https://docs.polymarket.com/resources/blockchain-data ·
https://docs.polymarket.com/resources/referral-program · last verified: 2026-06-09

## Contracts (Polygon mainnet, chainId 137)

`resources/contracts` is the official single source of truth. All addresses below
are Polygon mainnet.

### Core trading

| Contract | Address |
|---|---|
| CTF Exchange (V2) | `0xE111180000d2663C0091e4f400237545B87B996B` |
| Neg Risk CTF Exchange | `0xe2222d279d744050d28e00520010520000310F59` |
| Neg Risk Adapter | `0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296` |
| Conditional Tokens (CTF) | `0x4D97DCd97eC945f40cF65F87097ACe5EA0476045` |

### Collateral

| Contract | Address |
|---|---|
| pUSD — CollateralToken (proxy) | `0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB` |
| pUSD — CollateralToken (impl) | `0x6bBCef9f7ef3B6C592c99e0f206a0DE94Ad0925f` |
| CollateralOnramp (wrap USDC.e → pUSD) | `0x93070a847efEf7F70739046A929D47a521F5B8ee` |
| CollateralOfframp (unwrap pUSD → USDC.e) | `0x2957922Eb93258b93368531d39fAcCA3B4dC5854` |
| PermissionedRamp | `0xebC2459Ec962869ca4c0bd1E06368272732BCb08` |
| CtfCollateralAdapter | `0xAdA100Db00Ca00073811820692005400218FcE1f` |
| NegRiskCtfCollateralAdapter | `0xadA2005600Dec949baf300f4C6120000bDB6eAab` |
| USDC.e (underlying) | `0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174` |

### Wallet factories

| Contract | Address |
|---|---|
| Deposit Wallet Factory | `0x00000000000Fb5C9ADea0298D729A0CB3823Cc07` |
| Deposit Wallet Beacon | `0x7A18EDfe055488A3128f01F563e5B479D92ffc3a` |
| Gnosis Safe Factory | `0xaacfeea03eb1561c4e67d661e40682bd20e3541b` |
| Polymarket Proxy Factory | `0xaB45c5A4B0c941a2F231C04C3f49182e1A254052` |

### Resolution

| Contract | Address |
|---|---|
| UMA CTF Adapter v3.0 | `0x157Ce2d672854c848c9b79C49a8Cc6cc89176a49` |
| UMA CTF Adapter v2.0 | `0x6A9D222616C90FcA5754cd1333cFD9b7fb6a4F74` |
| UMA CTF Adapter v1.0 | `0xCB1822859cEF82Cd2Eb4E6276C7916e692995130` |
| UMA Optimistic Oracle | `0xCB1822859cEF82Cd2Eb4E6276C7916e692995130` |

> Note: the `resources/contracts` page lists "UMA Adapter" as
> `0x6A9D222616C90FcA5754cd1333cFD9b7fb6a4F74` (= v2.0); the `concepts/resolution`
> page additionally documents the v3.0 adapter. Verify which version a given
> market uses on-chain before integrating.

Audits (CTF Exchange V2): Quantstamp (March 2026) and Cantina (March 2026), in
`github.com/Polymarket/ctf-exchange-v2/audits`. Bug bounty: Cantina.

## CLOB error codes

All CLOB errors return `{ "error": "<message>" }`. Full catalog:
`resources/error-codes`. Status-code summary:

| Status | Meaning | Common causes |
|---|---|---|
| 400 | Bad Request | invalid params/payload, business-logic violation |
| 401 | Unauthorized | missing/invalid API key, bad HMAC sig, expired timestamp, `Invalid L1 Request headers` |
| 404 | Not Found | market/order/token doesn't exist |
| 425 | Too Early | matching engine restarting — retry with backoff (see `orders.md` / `troubleshooting.md`) |
| 429 | Too Many Requests | rate limit — exponential backoff |
| 500 | Internal Server Error | retry with backoff |
| 503 | Service Unavailable | exchange paused, or `cancel-only` / `post-only` mode |

Override quirk: any CLOB error message containing `"not found"` returns 404,
`"unauthorized"` returns 401, `"context canceled"` returns 400 — regardless of the
original status code.

High-signal order-processing messages (returned in the body of `POST /order` /
`POST /orders`):

- `not enough balance / allowance` — see `troubleshooting.md` and
  `deposit-wallets.md` (sync with `signature_type=3`).
- `invalid post-only order: order crosses book` — adjust price so it rests.
- `... breaks minimum tick size rule` — check `GET /tick-size`.
- `... Size (...) lower than the minimum` — below market min size.
- `order couldn't be fully filled. FOK orders are fully filled or killed.`
- `no orders found to match with FAK order.`
- `post-only mode: only post-only orders and cancels are allowed` — response adds
  `code: "post_only_mode"` and `retry_after_seconds`; same delay in the
  `Retry-After` header.
- Balance-allowance `Invalid signature_type` lists `EOA`, `POLY_PROXY`,
  `GNOSIS_SAFE` — note v2 deposit-wallet flows use `POLY_1271` (`signature_type=3`)
  on the order path (see `auth-l1-l2.md`, `deposit-wallets.md`).

## On-chain / analytics data

Polymarket's own REST/WS APIs are the primary source (`api-data.md`,
`api-websockets.md`). For raw on-chain activity (trades, balances, positions,
redeems):

- **Goldsky** — streaming pipelines to your DB; ClickHouse "CryptoHouse"
  (`crypto.clickhouse.com`) for SQL.
- **Dune** (`dune.com`) — SQL + dashboards. Starter queries: Volume
  (`dune.com/queries/6545441`), TVL (`/6588784`), Open Interest (`/6555478`).
- **Allium** (`docs.allium.so/historical-data/predictions`) — SQL + dashboards.
- Aggregators: Blockworks, Artemis, DeFiLlama, The Block, Token Terminal.

## Referral program

≥ \$10,000 lifetime volume to earn. Direct referral = **10%** of net trading
fees; indirect = **5%**. "Net" = fees Polymarket keeps after the referred user's
tier rebate. Rewards run from the referral's first trade until they reach
**Platinum** tier or **30 days** elapse (whichever first); a referral must sign up
within 30 days of the click. Paid daily at midnight UTC in pUSD. No self-referrals
/ linked accounts / inauthentic trading. Free markets (e.g. Geopolitical/world
events) earn nothing. (`trading/taker-rebates` for the tiers — see
`rewards-rebates.md`.)
