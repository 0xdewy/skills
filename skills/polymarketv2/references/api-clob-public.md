# CLOB API — public market data

Scope: public, no-auth CLOB reads — orderbook, prices, midpoint, spread, last
trade, fee rate, token→market lookup. (Order placement/cancel is authenticated;
see `auth-l1-l2.md`, `deposit-wallets.md`, and the SDK files.)
Source: https://docs.polymarket.com (CLOB API) · last verified: 2026-06-09
Base URL: `https://clob.polymarket.com` (staging: `https://clob-staging.polymarket.com`)

## Endpoints

| Method & path | Purpose |
|---|---|
| `GET /book?token_id=<id>` | Order book summary for a token (bids/asks, `tick_size`, `min_order_size`, `neg_risk`, `last_trade_price`) |
| `POST /books` | Order books for multiple tokens; body = `[{ "token_id": "..." }, ...]` |
| `GET /price?token_id=<id>&side=BUY\|SELL` | Best price for a side |
| `POST /prices` | Prices for many `{token_id, side}` pairs; returns `{ tokenId: { side: price } }` |
| `GET /midpoint?token_id=<id>` | Midpoint price |
| `POST /midpoints` | Midpoints for many tokens |
| `GET /spread?token_id=<id>` | Spread (best ask − best bid), returned as `{ "spread": "0.02" }` |
| `GET /last-trade-price?token_id=<id>` | Last trade `{ price, side }` (defaults `"0.5"` / `""` if none) |
| `GET /fee-rate?token_id=<id>` | Base fee `{ "base_fee": <bps> }` |
| `GET /markets-by-token/{token_id}` | Resolve a token → `{ condition_id, primary_token_id (YES), secondary_token_id (NO) }` |
| `GET /clob-markets/{condition_id}` | CLOB market info for a condition (tick size, neg-risk, fee params `fd`/`mbf`/`tbf`, taker-delay flag `itode`) |
| `GET /tick-size?token_id=<id>` | Market tick size |
| `GET /neg-risk?token_id=<id>` | Whether the market is neg-risk |
| `GET /prices-history?...` | Historical prices for one token |
| `POST /batch-prices-history` | Historical prices for many tokens in one call |
| `GET /time` | Server time (Unix seconds) — use to align signed-order timestamps |

### Market listings (CLOB)

| Method & path | Purpose |
|---|---|
| `GET /simplified-markets` | Reduced market objects (lighter than Gamma) |
| `GET /sampling-markets` | Markets that have rewards/sampling enabled |
| `GET /sampling-simplified-markets` | Simplified + sampling-enabled |

## Prices history

`GET /prices-history` params: `market` (token id), time window `startTs`/`endTs`,
and `fidelity` (one of `1m`,`5m`,`15m`,`30m`,`1h`,`4h`,`1d`,`1w`); `limit` ≤ 1000
on OHLC/history routes. `POST /batch-prices-history` takes a body of multiple
token/window requests. (Full param schemas:
`references/openapi/clob-openapi.yaml`.)

## Order book shape (`/book`)

```json
{
  "market": "0x...conditionId",
  "asset_id": "<token_id>",
  "timestamp": "1234567890",
  "hash": "...",
  "bids": [{ "price": "0.45", "size": "100" }],   // price descending
  "asks": [{ "price": "0.46", "size": "150" }],   // price ascending
  "min_order_size": "1",
  "tick_size": "0.01",
  "neg_risk": false,
  "last_trade_price": "0.45"
}
```

`tick_size` and `neg_risk` from here feed the order-creation options
(`{ tickSize, negRisk }`) in the SDKs.

## Rate limits (CLOB market data)

In the single rate-limit table in `troubleshooting.md` (CLOB market-data section).
