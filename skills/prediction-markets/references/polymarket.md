# Polymarket Reference

> Polymarket is the world's largest prediction market, built on Polygon. CLOB (Central Limit Order Book) hybrid-decentralized trading — offchain order matching + onchain settlement.

## Quick Facts

| Aspect | Detail |
|--------|--------|
| Network | Polygon PoS (chain ID 137) |
| Collateral | pUSD (Polymarket USD, backed 1:1 by USDC) |
| Token Standard | ERC1155 (Gnosis CTF) |
| Order Model | CLOB — offchain matching, onchain settlement |
| Order Format | EIP-712 signed messages |
| SDKs | TypeScript (`@polymarket/clob-client-v2`), Python (`py-clob-client-v2`), Rust (`polymarket_client_sdk_v2`) |

## Four APIs

| API | Base URL | Auth | Purpose |
|-----|----------|------|---------|
| Gamma API | `https://gamma-api.polymarket.com` | None | Markets, events, tags, series, search, profiles |
| Data API | `https://data-api.polymarket.com` | None | Positions, trades, leaderboards, open interest |
| CLOB API | `https://clob.polymarket.com` | L1/L2 | Orderbook, pricing, order placement/cancellation |
| Bridge API | `https://bridge.polymarket.com` | Varies | Deposits and withdrawals (proxied via fun.xyz) |

## Core Concepts

### Markets & Events

- **Market**: Single binary question with Yes/No outcomes. Identified by condition ID, question ID, and two token IDs.
- **Event**: Container grouping 1+ related markets. Has a unique slug used in URLs.
- A market can only be traded on the CLOB if `enableOrderBook` is `true`.
- Sports markets: outstanding limit orders auto-cancelled at game start.

### Outcome Tokens (ERC1155 CTF)

- **Yes token**: Redeems for $1.00 if event occurs
- **No token**: Redeems for $1.00 if event does not occur
- Every Yes/No pair is backed by exactly $1 of pUSD locked in the CTF contract.
- Operations: **Split** (pUSD → tokens), **Merge** (tokens → pUSD), **Redeem** (winning tokens → pUSD after resolution)

### Prices

- Each share priced $0.00–$1.00. Price = implied probability.
- Displayed price = midpoint of bid-ask spread (or last trade if spread > $0.10)
- No trading size limits on the orderbook.

### Order Lifecycle

1. **Create & Sign**: EIP-712 signature with private key
2. **Submit to CLOB**: Validation (signature, balance, allowances, tick size)
3. **Match or Rest**: Marketable → immediate match; non-marketable → rests on book
4. **Onchain Settlement**: Matched trades settle atomically via Exchange contract on Polygon

## Authentication

### Two Levels

| Level | Method | Purpose |
|-------|--------|---------|
| L1 | EIP-712 signature (private key) | Create/derive API credentials |
| L2 | HMAC-SHA256 (API key, secret, passphrase) | Place/cancel orders, query trades |

### Signature Types

| Type | ID | Use Case |
|------|-----|----------|
| EOA | 0 | Standalone wallet (pay own gas) |
| POLY_PROXY | 1 | Existing proxy wallet |
| GNOSIS_SAFE | 2 | Existing Gnosis Safe |
| POLY_1271 | 3 | Deposit wallet (recommended for new users) |

New API users should use deposit wallets with signature type 3.

### L2 Headers

Required for all trading operations:
- `POLY_ADDRESS` — wallet address
- `POLY_SIGNATURE` — HMAC-SHA256 signature
- `POLY_TIMESTAMP` — Unix timestamp
- `POLY_API_KEY` — API key
- `POLY_PASSPHRASE` — API passphrase

## Order Types

| Type | Behavior | Use Case |
|------|----------|----------|
| GTC | Good-Til-Cancelled — rests until filled/cancelled | Standard limit orders |
| GTD | Good-Til-Date — auto-expires at specified time | Time-limited / event-driven |
| FOK | Fill-Or-Kill — fill entirely or cancel | All-or-nothing market orders |
| FAK | Fill-And-Kill — fill what's available, cancel rest | Partial-fill market orders |

**Post-Only**: Guarantees maker status. Rejected if would cross the spread immediately.

### GTD Expiration
There is a 60-second security threshold buffer on GTD expiration. For N-second effective lifetime: `now + 60 + N`.

## Tick Sizes

Order prices must conform to the market's tick size:

| Tick Size | Precision | Examples |
|-----------|-----------|----------|
| 0.1 | 1 decimal | 0.1, 0.5 |
| 0.01 | 2 decimals | 0.01, 0.50, 0.99 |
| 0.001 | 3 decimals | 0.001, 0.500 |
| 0.0001 | 4 decimals | 0.0001, 0.5000 |

## Batch Orders

Up to 15 orders per request via `postOrders` / `post_orders`.

## Heartbeat

Heartbeat endpoint maintains session liveness. If no valid heartbeat within 10 seconds (5-second buffer), **all open orders are cancelled**. Include previous `heartbeat_id` in each request.

## Order Statuses

| Status | Description |
|--------|-------------|
| `live` | Resting on the book |
| `matched` | Matched immediately with resting order |
| `delayed` | Marketable order subject to matching delay |
| `unmatched` | Marketable but failed to delay |

## Trade Statuses

| Status | Terminal | Description |
|--------|----------|-------------|
| MATCHED | No | Matched, sent for onchain submission |
| MINED | No | Transaction mined |
| CONFIRMED | Yes | Finality achieved |
| RETRYING | No | Failed, being retried |
| FAILED | Yes | Permanently failed |

## Fees

Formula: `fee = C * feeRate * p * (1 - p)` where C = shares, p = price.

Fees are symmetric around 50% — 30¢ trade = same fee as 70¢ trade. Rounded to 5 decimal places (minimum fee: 0.00001 USDC).

| Category | Taker Fee Rate | Maker Fee Rate | Maker Rebate % |
|----------|---------------|----------------|-----------------|
| Crypto | 0.07 | 0 | 20% |
| Sports | 0.03 | 0 | 25% |
| Finance / Politics / Mentions / Tech | 0.04 | 0 | 25% |
| Economics / Culture / Weather / Other | 0.05 | 0 | 25% |
| Geopolitics | 0 | 0 | — |

Geopolitical and world events markets are fee-free for both sides.

### Maker Rebates
- Paid daily in USDC, directly to wallet
- Minimum $1 USDC accrued for payout
- Calculated per market: `rebate = (your_fee / total_fee) * rebate_pool`
- Positioning rewards based on orders that add liquidity and get filled

## Negative Risk (Neg Risk)

Multi-outcome events (3+ outcomes) use the Neg Risk CTF Exchange. Pass `negRisk: true` / `neg_risk=True` for these markets.

## Heartbeat / Session Liveness

Post to heartbeat endpoint every 5 seconds. Include previous `heartbeat_id`. If server doesn't receive valid heartbeat within 10 seconds (5s buffer), all open orders are cancelled.

## WebSocket Channels

| Channel | Auth | Purpose |
|---------|------|---------|
| Market Channel (public) | No | Real-time orderbook, prices, market lifecycle |
| Sports Channel (public) | No | Live sports scores and game state |
| User Channel (authenticated) | Yes | Real-time order and trade updates |
| RTDS (public) | No | Comments, crypto/equity prices |

## Error Responses

Key CLOB error messages:
- `INVALID_ORDER_MIN_TICK_SIZE` — price doesn't conform to tick size
- `INVALID_ORDER_MIN_SIZE` — below minimum
- `INVALID_ORDER_DUPLICATED` — identical order already placed
- `INVALID_ORDER_NOT_ENOUGH_BALANCE` — insufficient balance/allowance
- `INVALID_ORDER_EXPIRATION` — expiration in the past
- `INVALID_POST_ONLY_ORDER` — would cross the book
- `FOK_ORDER_NOT_FILLED_ERROR` — FOK couldn't fully fill
- `ORDER_DELAYED` — match delayed
- `MARKET_NOT_READY` — not accepting orders

## Key Endpoints (CLOB)

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/order` | POST | L2 | Create and post single order |
| `/orders` | POST | L2 | Batch create (max 15) |
| `/order/{id}` | GET | L2 | Get single order by ID |
| `/orders` | GET | L2 | Get user's open orders |
| `/order/{id}` | DELETE | L2 | Cancel single order |
| `/cancel-all` | DELETE | L2 | Cancel all open orders |
| `/cancel-market` | DELETE | L2 | Cancel all orders in a market |
| `/book` | GET | None | Get orderbook for a token |
| `/midpoint` | GET | None | Get midpoint price |
| `/spread` | GET | None | Get spread |
| `/price` | GET | None | Get best bid/ask |
| `/last-trade-price` | GET | None | Get last trade price |
| `/trades` | GET | L2 | Get user's trades |
| `/heartbeat` | POST | L2 | Send heartbeat |

## Key Endpoints (Gamma API)

| Endpoint | Purpose |
|----------|---------|
| `/events` | List events (with pagination) |
| `/events?slug=X` | Get event by slug |
| `/markets` | List markets |
| `/markets?condition_id=X` | Get market by condition ID |
| `/markets?slug=X` | Get market by slug |
| `/prices-history` | Historical price data |
| `/search` | Search markets, events, profiles |
| `/series` | List series |
| `/tags` | List tags |
