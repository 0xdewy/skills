# Orders — REST endpoints, order types, batching, heartbeat, restarts

Scope: the authenticated CLOB order REST surface and order-management behavior.
The **order lifecycle** (statuses, maker/taker, settlement) lives canonically in
`concepts.md`; SDK code for these calls is in `sdk-unified.md` /
`sdk-clob-ts.md` / `sdk-clob-python.md` / `sdk-rust.md`. Builder-code attribution
is in `builders.md`.
Source: https://docs.polymarket.com/trading/orders/* ·
https://docs.polymarket.com/api-reference/trade/* ·
https://docs.polymarket.com/trading/matching-engine · last verified: 2026-06-09
Base URL: `https://clob.polymarket.com` · all endpoints require **L2** auth
(the five `POLY_*` headers — see `auth-l1-l2.md`).

## REST endpoints

| Method & path | Purpose |
|---|---|
| `POST /order` | Place one signed order |
| `POST /orders` | Place a batch (**max 15**) |
| `DELETE /order` | Cancel one (`{"orderID": "..."}`) |
| `DELETE /orders` | Cancel many (JSON array of ids) |
| `DELETE /cancel-all` | Cancel all open orders, all markets |
| `DELETE /cancel-market-orders` | Cancel by `market` (condition id) and/or `asset_id` (both optional) |
| `GET /data/order/{orderID}` | Single order by id |
| `GET /data/orders` | Open orders (filter `market`, `asset_id`) |
| `GET /data/trades` | Trades (filters `id`, `market`, `maker_address`, `asset_id`, `before`, `after`; cursor `next_cursor`) |
| `GET /order-scoring` | Whether resting order(s) are scoring for maker rebates |
| `POST /heartbeats` | Session liveness (see below) |

Cancel responses always include `canceled` (ids) and `not_canceled` (id →
reason). Rate limits for all of these: `troubleshooting.md` (Trading section).

## Order types

All orders are **limit orders**; a market order is a marketable limit order.

| Type | Behavior | Class |
|---|---|---|
| `GTC` | good-til-cancelled, rests | limit |
| `GTD` | good-til-date, auto-expires | limit |
| `FOK` | fill-or-kill (fully or cancel) | market |
| `FAK` | fill-and-kill (fill available, cancel rest) | market |

- **Market orders** (`FOK`/`FAK`): BUY `amount` = dollars to spend; SELL `amount`
  = shares to sell. The `price` field is a **worst-price limit (slippage
  protection)**, not a target.
- **GTD** has a **60-second security threshold**: for an effective lifetime of N
  seconds set `expiration = now + 60 + N`.
- **Post-only** (`postOnly: true`): only `GTC`/`GTD`; rejected if it would cross
  the book or if combined with FOK/FAK. Guarantees maker.

Every order needs two market options: `tickSize` (`0.1`/`0.01`/`0.001`/`0.0001`,
via `getTickSize`) and `negRisk` (via `getNegRisk`; `true` for multi-outcome — see
`ctf.md`). Signature types: `0` EOA · `1` POLY_PROXY · `2` GNOSIS_SAFE · `3`
POLY_1271 deposit wallet (`auth-l1-l2.md`, `deposit-wallets.md`).

## Prerequisites & sizing

Funder must have approved the Exchange: BUY needs pUSD allowance ≥ spend; SELL
needs conditional-token allowance ≥ size. Balances/allowances are monitored in
real time (intentional abuse → blacklist).
`maxOrderSize = balance − Σ(openOrderSize − filledAmount)`.

## Response & statuses

`POST /order` returns `{ success, errorMsg, orderID, takingAmount, makingAmount,
status, transactionsHashes, tradeIDs }`. Order statuses: `live`, `matched`,
`delayed`, `unmatched` (defined in `concepts.md`). Taker delay (250 ms on selected
crypto/finance up-down markets; detect via `clob-markets/{condition_id}` →
`itode:true`) — order can't be cancelled while pending.

Placement error codes: `INVALID_ORDER_MIN_TICK_SIZE`, `INVALID_ORDER_MIN_SIZE`,
`INVALID_ORDER_DUPLICATED`, `INVALID_ORDER_NOT_ENOUGH_BALANCE`,
`INVALID_ORDER_EXPIRATION`, `INVALID_POST_ONLY_ORDER_TYPE`,
`INVALID_POST_ONLY_ORDER`, `FOK_ORDER_NOT_FILLED_ERROR`, `ORDER_DELAYED`,
`MARKET_NOT_READY`, `INVALID_ORDER_ERROR`, `EXECUTION_ERROR`. Full HTTP-level
catalog: `resources.md`.

## OpenOrder / Trade objects (key fields)

- **OpenOrder**: `id`, `status`, `market`, `asset_id`, `side`, `original_size`,
  `size_matched`, `price`, `outcome`, `order_type`, `maker_address` (funder),
  `owner` (api key), `associate_trades[]`, `expiration`, `created_at`.
- **Trade**: `id`, `taker_order_id`, `market`, `asset_id`, `side`, `size`,
  `price`, `fee_rate_bps`, `status`, `match_time`, `outcome`, `maker_address`,
  `owner`, `transaction_hash`, `bucket_index`, `trader_side` (`TAKER`/`MAKER`),
  `maker_orders[]`. A logical trade may split across on-chain txs — reconcile via
  `bucket_index` + `match_time`.

## Heartbeat (`POST /heartbeats`)

Maintains session liveness. If no valid heartbeat arrives within **10 s** (5 s
buffer), **all open orders are cancelled**. Send the most recent `heartbeat_id`
each call (empty string first time); an expired id returns `400` with the correct
id — update and retry. (Rust SDK can auto-send via the `heartbeats` feature.) Note:
this is distinct from the WS `PING` heartbeats in `api-websockets.md`.

## Matching-engine restarts & restricted modes

Announced ~2 days ahead in Polymarket's Telegram (`t.me/polytradingapis`) /
Discord `#trading-apis`.

- **HTTP 425 (Too Early)** on order endpoints = engine restarting. Retry with
  exponential backoff (start 1–2 s, cap ~30 s); not a permanent error.
- After every restart the engine is in **post-only mode for 2 minutes**: cancels
  ok, new orders must be `postOnly: true`. `POST /order` returns `503` with
  `code: "post_only_mode"`, `retry_after_seconds`, and a `Retry-After` header;
  `POST /orders` returns per-order errors.
- **Cancel-only mode**: `503` `"Trading is currently cancel-only…"` — cancels
  still accepted. Do **not** blindly retry an unchanged non-post-only order;
  change flow or wait the indicated delay.

## Order attribution

Attach your `builderCode` (`bytes32`) to each order to credit volume/fees — see
`builders.md`. Verify via `GET` builder trades (`getBuilderTrades`).

## See also

`concepts.md` (lifecycle/statuses), `api-clob-public.md` (tick size, neg-risk,
book/prices), `ctf.md` (neg-risk), `rewards-rebates.md` (fees, scoring),
`builders.md`, `troubleshooting.md`, `references/openapi/clob-openapi.yaml`.
