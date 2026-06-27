# WebSockets — real-time market, user, sports & RTDS channels

Scope: the four real-time streaming channels. The docs publish this material twice
(`market-data/websocket/*` and `api-reference/wss/*`) — they describe the **same**
endpoints/payloads; this file is the single deduped reference. The RFQ "Quoter
Gateway" WS is documented with the maker flow in `combos-rfq.md`.
Source: https://docs.polymarket.com/market-data/websocket/overview ·
.../market-channel · .../user-channel · .../sports · .../rtds · last verified: 2026-06-09

## Channels at a glance

| Channel | Endpoint | Auth |
|---|---|---|
| **Market** | `wss://ws-subscriptions-clob.polymarket.com/ws/market` | No |
| **User** | `wss://ws-subscriptions-clob.polymarket.com/ws/user` | **Yes** (L2 API creds) |
| **Sports** | `wss://sports-api.polymarket.com/ws` | No |
| **RTDS** | `wss://ws-live-data.polymarket.com` | Optional (`gamma_auth`) |

Heartbeats: **Market/User** — client sends `PING` every 10s, server replies
`PONG`. **Sports** — server sends `ping` every 5s, client must reply `pong` within
10s or the connection closes. **RTDS** — client sends `PING` every 5s.

General gotcha: send a valid subscription message immediately after connecting, or
the server may close the socket.

## Market channel (public, level-2 data)

Subscribe with token (asset) ids:

```json
{ "assets_ids": ["<token_id_1>", "<token_id_2>"], "type": "market",
  "custom_feature_enabled": true }
```

Message types (each carries `event_type`):

| `event_type` | When | Custom-feature? |
|---|---|---|
| `book` | on subscribe + when a trade affects the book (full snapshot, `bids`/`asks`, `hash`, `timestamp`) | No |
| `price_change` | order placed/cancelled (`price_changes[]` with `side`, `best_bid`, `best_ask`; `size:"0"` = level removed) | No |
| `tick_size_change` | tick size changes (price >0.96 or <0.04): `old_tick_size`/`new_tick_size` | No |
| `last_trade_price` | maker+taker matched: `price`, `side`, `size`, `fee_rate_bps` | No |
| `best_bid_ask` | best bid/ask changes: `best_bid`, `best_ask`, `spread` | **Yes** |
| `new_market` | market created (full metadata + `fee_schedule`) | **Yes** |
| `market_resolved` | market resolved (`winning_asset_id`, `winning_outcome`) | **Yes** |

The three "Custom Feature" types require `custom_feature_enabled: true` in the
subscription. `new_market`'s `fee_schedule` object: `exponent`, `rate`,
`taker_only`, `rebate_rate` (see `rewards-rebates.md`).

## User channel (authenticated)

Subscribes by **condition id** (market), not asset id. **Server-side only** — never
expose creds client-side.

```json
{ "auth": { "apiKey": "...", "secret": "...", "passphrase": "..." },
  "markets": ["0x...condition_id"], "type": "user" }
```

Message types:

- `trade` — emitted when your order is matched and at each subsequent trade status.
  Status machine: `MATCHED → MINED → CONFIRMED`; failures `RETRYING → FAILED`
  (`CONFIRMED`/`FAILED` terminal). Carries `maker_orders[]`, `taker_order_id`,
  `price`, `size`, `side`, `outcome`, `status`.
- `order` — `PLACEMENT` (placed), `UPDATE` (partially matched), `CANCELLATION`.
  Carries `original_size`, `size_matched`, `price`, `side`, `outcome`.

(L2 creds come from `auth-l1-l2.md`. Trade/order status semantics mirror
`concepts.md`.)

## Sports channel

No subscription message — connect and receive `sport_result` events (live scores,
periods, status) for all active sports events. Remember the 5s server-ping → `pong`
contract.

## RTDS — Real-Time Data Socket

Streams **crypto prices**, **equity prices**, and **comments**. Official TS client:
`github.com/Polymarket/real-time-data-client`. Subscriptions can be added/removed
without reconnecting. Subscribe/unsubscribe shape:

```json
{ "action": "subscribe", "subscriptions": [
  { "topic": "<topic>", "type": "<type>", "filters": "<optional>",
    "gamma_auth": { "address": "<wallet>" } } ] }
```

Every message: `{ topic, type, timestamp(ms), payload }`.

- **crypto_prices** (Binance) — `filters` = comma list of lowercase concatenated
  symbols (`btcusdt`,`ethusdt`,`solusdt`,`xrpusdt`). Payload: `symbol`, `timestamp`,
  `value`.
- **crypto_prices_chainlink** — `filters` = JSON `{"symbol":"eth/usd"}` (slash
  format: `btc/usd`,`eth/usd`,`sol/usd`,`xrp/usd`). Sponsored Chainlink key form
  linked in docs for 15m crypto markets.
- **equity_prices** (Pyth) — single topic for stocks/ETFs/forex/metals/commodities.
  `filters` = JSON `{"symbol":"AAPL"}` (case-insensitive in; payload symbol is
  lowercase). On subscribe you get a `type:"subscribe"` snapshot (last 2 min) then
  `type:"update"` ticks. Payload: `value`, `full_accuracy_value`, `timestamp`,
  `received_at`, `is_carried_forward:true` when the session is closed. Symbols incl.
  AAPL/TSLA/MSFT/GOOGL/NVDA/…, QQQ/SPY, EURUSD/GBPUSD/USDJPY, XAUUSD/XAGUSD,
  WTI/CC/NGD. Price-to-beat: `GET https://polymarket.com/api/equity/price-to-beat/{slug}`.
  Pyth feed: first 30 days free then \$99/mo (link in docs).
- **comments** — `comment_created` / `comment_removed` / `reaction_created` /
  `reaction_removed`. Payload has `body`, `createdAt`, `id`, `parentCommentID`
  (null = top-level), `parentEntityID`/`parentEntityType` (`Event`|`Market`),
  `profile{…}`. May need `gamma_auth` for user-specific data.

## See also

`api-clob-public.md` (REST equivalents), `concepts.md` (trade/order statuses),
`auth-l1-l2.md` (L2 creds for user channel), `combos-rfq.md` (RFQ Quoter Gateway
WS), `troubleshooting.md`.
