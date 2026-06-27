# Combos & RFQ (quoter / market-maker flow)

Scope: **Combos** (multi-leg YES/NO positions) and the **RFQ** (request-for-quote)
system that prices and executes them, from the market-maker (quoter) side. Plain
CLOB market-making is in `orders.md` / `rewards-rebates.md`.
Source: https://docs.polymarket.com/market-makers/combos ·
https://docs.polymarket.com/api-reference/maker/* ·
https://docs.polymarket.com/api-reference/combo-markets/* ·
https://docs.polymarket.com/api-reference/wss/rfq · last verified: 2026-06-09
Base URL (RFQ REST): `https://combos-rfq-api.polymarket.sh`
WS quoter gateway: `wss://combos-rfq-gateway-quoter.polymarket.sh/ws/rfq`

## What a Combo is

A **Combo** bundles multiple underlying market outcomes into a single YES or NO
position, identified by **derived YES/NO position IDs** that are *complementary* to
the CLOB token ids — a market can be traded directly on the CLOB **or** included as
a Combo leg. Combos execute via **RFQ**, not the order book.

Encoding conventions (RFQ API): `*_e6` fields are 6-decimal fixed-point encoded as
**strings**; timestamps are **Unix ms**; errors are `{ "error": "..." }`.

## RFQ flow & timing

Two roles: **requester** (Polymarket user) and **quoter** (market maker). Auction:

1. User creates an unsigned **Request** for a Combo price.
2. RFQ broadcasts it to connected quoters.
3. Quoters submit **signed Quotes** — **400 ms** submission window.
4. RFQ returns the **best** Quote to the user.
5. User **accepts** by signing the trade — **5 s** acceptance window.
6. If **Last Look** is enabled, RFQ asks the winning quoter to confirm.
7. Quoter **confirms/declines** — **1 s** window.
8. RFQ executes; both sides get execution updates.

## REST endpoints (quoter side)

| Method & path | Auth | Purpose |
|---|---|---|
| `GET /v1/rfq/combo-markets` | public | Catalog of markets usable as combo legs, by volume desc. `position_ids`/`outcomes`/`outcome_prices` index-aligned (`[0]`=YES,`[1]`=NO); paginate via `next_cursor` (`null` = last page) |
| `POST /v1/maker/quotes` | **L2** | Submit a signed maker quote for an active RFQ |
| `POST /v1/maker/quotes/cancel` | **L2** | Cancel a submitted quote |
| `POST /v1/maker/confirmations` | **L2** | Last-look response (`decision` = `CONFIRM` \| `DECLINE`) |

Maker endpoints require **CLOB L2** auth for the maker role (`POLY_API_KEY`,
`POLY_ADDRESS`, `POLY_SIGNATURE` — see `auth-l1-l2.md`). **REST does not assign a
quote id — generate `quote_id` client-side.**

Quote body (key fields): `quote_id`, `rfq_id`, `signer_address`, `maker_address`,
`signature_type`, `price_e6`, `size_e6`, and a `signed_order` (the V2 order struct:
`salt, maker, signer, tokenId, makerAmount, takerAmount, side, signatureType,
timestamp, metadata, builder, signature`). A successful `POST` returns the current
**RFQSnapshot**. Confirmation body: `rfq_id`, `quote_id`, `signer_address`,
`maker_address`, `signature_type`, `decision`.

## WS Quoter Gateway

Connect to `wss://combos-rfq-gateway-quoter.polymarket.sh/ws/rfq`. Send the `auth`
message **first**, within **30 s**, or the connection closes. The gateway then
broadcasts active RFQ requests and accepts signed quotes over the socket (lower
latency than REST polling). Full message schemas:
`references/openapi/combos-rfq-openapi.yaml` and the AsyncAPI `asyncapi-rfq.json`.
The unified SDK (`@polymarket/client`) exposes a quoting session helper — see
`sdk-unified.md`.

## Combo user data (Data API)

`GET /v1/activity/combos` (user combo activity) and `GET /v1/positions/combos`
(user combo positions) — see `api-data.md` /
`references/openapi/data-openapi.yaml`.

## See also

`orders.md` (V2 order struct, CLOB trading), `api-websockets.md` (other WS
channels), `auth-l1-l2.md` (L2 maker auth), `sdk-unified.md` (quoting session),
`rewards-rebates.md` (maker rebates).
