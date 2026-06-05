# Kalshi Reference

> Kalshi is a CFTC-regulated prediction market exchange. Binary outcome markets with dollar-based pricing (subpenny support via fixed-point strings).

## Quick Facts

| Aspect | Detail |
|--------|--------|
| Regulation | CFTC-regulated exchange |
| Market Type | Binary (Yes/No) outcomes |
| Pricing | Dollar strings (`_dollars` suffix), subpenny support |
| Contracts | Fixed-point strings (`_fp` suffix), fractional support |
| Auth | RSA-PSS with SHA256 signatures |
| SDKs | Python (`kalshi-python`), TypeScript (`kalshi-typescript`) |
| Order Limit | 200,000 open orders per user |

## API Environments

| Environment | REST Base URL | WebSocket URL |
|-------------|--------------|---------------|
| **Production** | `https://external-api.kalshi.com/trade-api/v2` | `wss://external-api-ws.kalshi.com/trade-api/ws/v2` |
| **Demo** | `https://external-api.demo.kalshi.co/trade-api/v2` | `wss://external-api-ws.demo.kalshi.co/trade-api/ws/v2` |

Credentials are NOT shared between environments. Demo API keys only work on demo, production keys only on production.

The recommended `external-api` hosts are dedicated to the external Trade API. Legacy hosts (`api.elections.kalshi.com`, `demo-api.kalshi.co`) remain supported for now.

## Authentication

### Signature Method
- **RSA-PSS with SHA256**
- Sign the full URL path from API root, WITHOUT query parameters
- Encode signature as base64

### Required Headers

| Header | Description | Example |
|--------|-------------|---------|
| `KALSHI-ACCESS-KEY` | API Key ID (UUID) | `a952bcbe-ec3b-4b5b-b8f9` |
| `KALSHI-ACCESS-TIMESTAMP` | Current time in milliseconds | `1703123456789` |
| `KALSHI-ACCESS-SIGNATURE` | Base64 RSA-PSS signature | `base64_string` |

### Signing Steps
1. Concatenate: `timestamp + HTTP_METHOD + path_without_query`
2. Sign with RSA-PSS (SHA256) using private key
3. Base64 encode the signature

Important: Sign the path from API root, NOT including hostname and NOT including query string.

### Getting API Keys
1. Log in → Account & security → API Keys → Create Key
2. Save private key (`.key` file, cannot be retrieved after page close)
3. Save API Key ID (UUID displayed on screen)

## Market Structure

### Market Lifecycle Statuses

| Status | Meaning |
|--------|---------|
| `initialized` | Created but not yet open |
| `active` | Open for trading |
| `inactive` | Temporarily paused by exchange |
| `closed` | Past close_time, awaiting determination |
| `determined` | Result known, settlement timer running |
| `disputed` | Result challenged |
| `amended` | Re-determined after dispute |
| `finalized` | Settlement complete (terminal state) |

### Filter Values

| Filter | Matches |
|--------|---------|
| `unopened` | `initialized` |
| `open` | `active` |
| `paused` | `inactive` |
| `closed` | Past close_time, not yet finalized |
| `settled` | `finalized` |

### Key Time Fields
- `open_time` — when market opens for trading
- `close_time` — when trading stops (may move earlier if `can_close_early`)
- `expected_expiration_time` — when outcome expected to be known
- `latest_expiration_time` — latest possible expiration
- After `close_time`, all order operations rejected with `MARKET_INACTIVE`

## Event Structure

Events group one or more related markets. Events themselves don't have a status — filtering by status checks child market statuses. An event appears in results if any child market matches the status filter.

Multivariate Events (MVE/Combo): Dynamically created events from multivariate event collections (tickers starting with `KXMVE`).

## Series

A series is a template for recurring events (e.g., "Monthly Jobs Report", "Weekly Jobless Claims", "Daily Weather in NYC"). Identified by ticker prefix (e.g., `KXHIGHNY`).

## Pricing

### Fixed-Point Representation

Two independent changes:
1. **Subpenny Pricing**: Price fields use `_dollars` suffix (e.g., `"0.1200"`) with up to 4 decimals
2. **Fractional Contracts**: Count fields use `_fp` suffix (e.g., `"10.00"`) with 0-2 decimal places, minimum 0.01

### Price Level Structures

| Structure | Ranges | Tick Size |
|-----------|--------|-----------|
| `linear_cent` | $0.00–$1.00 | $0.01 |
| `tapered_deci_cent` | $0.00–$0.10 | $0.001 |
| | $0.10–$0.90 | $0.01 |
| | $0.90–$1.00 | $0.001 |
| `deci_cent` | $0.00–$1.00 | $0.001 |

Check `price_ranges` on `GET /markets/{ticker}` for the valid step size for a specific market.

## Orderbook

### Key Difference from Traditional Orderbooks
Kalshi only returns **bids** (not asks). Since binary markets sum to $1.00:
- YES BID at $X = NO ASK at ($1.00 - X)
- NO BID at $Y = YES ASK at ($1.00 - Y)

### Response Structure
```json
{
  "orderbook_fp": {
    "yes_dollars": [["0.4200", "13.00"], ...],   // [price, count] sorted ascending
    "no_dollars": [["0.5600", "17.00"], ...]      // last element = highest/best bid
  }
}
```

### Calculating Spreads
- Best YES bid = highest price in `yes_dollars` array
- Best YES ask = $1.00 - (highest price in `no_dollars` array)
- YES spread = Best YES ask - Best YES bid

## Order Types

| Type | Description |
|------|-------------|
| `limit` | Resting order at specified price |
| `market` | Execute at best available price (not recommended — use limit) |

### Order Parameters (v1 Legacy)
- `ticker` — market ticker
- `action` — `buy` or `sell`
- `side` — `yes` or `no`
- `count` — number of contracts (integer)
- `type` — `limit` or `market`
- `yes_price` / `no_price` — price in cents (1–99)
- `client_order_id` — UUID for deduplication

### Order Parameters (V2 — recommended for new integrations)
- `ticker` — market ticker
- `book_side` — `bid` or `ask`
- `outcome_side` — `yes` or `no`
- `count_fp` — number of contracts (fixed-point string, e.g., `"10.00"`)
- `type` — `limit` or `market`
- `price_dollars` — price as dollar string (e.g., `"0.4200"`)
- `client_order_id` — UUID for deduplication

Legacy v1 endpoint `/portfolio/orders` will be deprecated no earlier than May 6, 2026.

### Order Group
Create order groups with a contracts limit over a rolling 15-second window. When limit is hit, all orders in the group are cancelled and no new orders can be placed until reset.

## Fees

### Rate Limits (Token-Based)

Every authenticated request costs tokens. Most requests cost 10 tokens. Reads and writes billed separately.

| Tier | Read Budget (tokens/sec) | Write Budget (tokens/sec) |
|------|--------------------------|---------------------------|
| Basic | 200 | 100 |
| Advanced | 300 | 300 |
| Premier | 1,000 | 1,000 |
| Paragon | 2,000 | 2,000 |
| Prime | 4,000 | 4,000 |

Write bucket holds 2 seconds of budget (Basic: 1 second). Burst above steady rate is possible.

### Fee Rounding

User balances must be exact multiples of $0.01. When subpenny pricing or fractional contracts produce sub-cent balance changes, the exchange charges a rounding fee.

Components per fill:
1. **Trade fee** — from fee model, rounded up to nearest $0.0001
2. **Rounding fee** — sub-cent adjustment restoring cent-alignment ($0.0000–$0.0099)
3. **Rebate** — refund from accumulated rounding overpayment (whole cent multiples)

**Fee accumulator**: Tracks cumulative rounding across all fills of an order. Once accumulated rounding exceeds $0.01, a whole-cent rebate is issued. This ensures total fee across many small fills ≈ single equivalent fill cost.

## Pagination

Cursor-based pagination. Default page size: 100. Continue until `cursor` is null.

Parameters:
- `cursor` — token from previous response
- `limit` — items per page (1–100)

Supports: `/markets`, `/events`, `/series`, `/markets/trades`, `/portfolio/history`, `/portfolio/fills`, `/portfolio/orders`

## Historical Data

Live endpoints return last ~3 months of data. Older data via `/historical/*` endpoints.

| Cutoff Field | Partitions | Historical Endpoint |
|-------------|-----------|-------------------|
| `market_settled_ts` | Settled markets + candlesticks | `/historical/markets` |
| `trades_created_ts` | Filled trades | `/historical/trades`, `/historical/fills` |
| `orders_updated_ts` | Cancelled/executed orders | `/historical/orders` |

Get current cutoffs: `GET /historical/cutoff`

## RFQ (Request for Quote)

Pre-execution communication between members.

Flow:
1. Requester creates RFQ (ticker, size, rest_remainder)
2. Broadcast to all makers
3. Makers respond with `yes_bid` and `no_bid` (full size, private per maker)
4. Requester accepts best-priced quote (one side)
5. Maker confirms within window
6. Orders placed on public book after execution timeout

Timing:
- Standard: 30s confirmation, 15s execution
- HVM (High Volatility, incl. all combos): 3s confirmation, 1s execution

Sizing: specify either `contracts_fp` (whole only) or `target_cost_dollars`.

Max 100 open RFQs at a time. Can't have multiple open RFQs on same ticker.

## Key REST Endpoints

### Public (no auth)
| Endpoint | Purpose |
|----------|---------|
| `GET /markets` | List markets (filterable by status, series, etc.) |
| `GET /markets/{ticker}` | Single market details |
| `GET /markets/{ticker}/orderbook` | Market orderbook |
| `GET /markets/trades` | Public trade history |
| `GET /events` | List events |
| `GET /events/{event_ticker}` | Single event |
| `GET /series` | List series |
| `GET /exchange/status` | Exchange status |
| `GET /exchange/schedule` | Exchange schedule |
| `GET /historical/cutoff` | Historical data cutoffs |

### Authenticated
| Endpoint | Purpose |
|----------|---------|
| `GET /portfolio/balance` | Account balance |
| `GET /portfolio/positions` | Your positions |
| `GET /portfolio/orders` | Your orders (v1 legacy) |
| `POST /portfolio/orders` | Create order (v1 legacy) |
| `DELETE /portfolio/orders/{id}` | Cancel order (v1 legacy) |
| `GET /portfolio/orders/{id}` | Single order |
| `GET /portfolio/fills` | Your trade fills |
| `POST /trade-api/v2/portfolio/orders` | Create order (V2, recommended) |
| `DELETE /trade-api/v2/portfolio/orders/{id}` | Cancel order (V2) |

## WebSocket Channels

All WebSocket communication through single connection. Auth headers required during handshake.

| Channel | Auth Required | Purpose |
|---------|--------------|---------|
| `market_ticker` | No* | Price, volume, open interest updates |
| `market_lifecycle_v2` | No* | Market lifecycle events |
| `orderbook` | No* | Real-time orderbook updates |
| `public_trades` | No* | Public trade notifications |
| `user_orders` | Yes | Your order created/updated |
| `user_fills` | Yes | Your order fill notifications |
| `market_positions` | Yes | Your position updates |
| `communications` | Yes | RFQ and quote notifications |

*Connection itself requires auth, but these channels carry only public data.

## Common Errors

| Error | Cause |
|-------|-------|
| `401 Unauthorized` | Bad API keys or signature |
| `400 Bad Request` | Invalid order params (price 1–99 cents) |
| `409 Conflict` | Duplicate `client_order_id` or RFQ exists |
| `429 Too Many Requests` | Rate limited — exponential backoff |
| `MARKET_INACTIVE` | Market past close_time |
| `RFQ_CLOSED` | RFQ deleted, expired, or executed |
| `INSUFFICIENT_BALANCE` | Not enough funds |
| `invalid_parameters` | Price not on valid step, or RFQ closed |

## Order Queue Position

Get order's queue position via `GET /portfolio/orders/queue_position`. Represents number of contracts ahead of your order at that price level (price-time priority).
