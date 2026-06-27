# Builders — builder code, fees, tiers, attribution

Scope: the Builder Program — routing user orders through your app, attributing
them with a builder code, charging builder fees, and tier limits. Order-side
attachment mechanics are in `orders.md`; relayer/gasless setup in `relayer.md` /
`sdk-clob-ts.md` / `sdk-clob-python.md`.
Source: https://docs.polymarket.com/builders/* ·
https://docs.polymarket.com/trading/orders/attribution ·
https://docs.polymarket.com/api-reference/builders/* · last verified: 2026-06-09

## Builder code

A **`bytes32`** identifier tied to your builder profile
(`polymarket.com/settings?tab=builder`). It's the **only** credential needed for
attribution — no HMAC signing, no extra headers/API key. It's a **public**
identifier and appears on-chain in the `builder` field of every order you
attribute. Store it as e.g. `POLY_BUILDER_CODE`.

Attach `builderCode` (TS) / `builder_code` (Python) to **every** order; omit it and
no builder fee is charged. You can also set `builderConfig: { builderCode }` once at
client construction to inherit it on all orders.

```ts
await client.createAndPostOrder(
  { tokenID:"0x...", price:0.55, size:100, side:Side.BUY,
    builderCode: process.env.POLY_BUILDER_CODE },
  { tickSize:"0.01", negRisk:false }, OrderType.GTC);
```

Verify attribution via `GET` builder trades (`getBuilderTrades({market?})`). A
`BuilderTrade`: `id`, `market`, `assetId`, `side`, `size`, `price`, `status`,
`outcome`, `owner`, `maker`, `builder`, `transactionHash`, `matchTime`, `fee`,
`feeUsdc`. Volume can take up to 24h to appear on `builders.polymarket.com`; only
**matched** trades count.

## Builder fees (CLOB V2)

A builder fee is collected when an order carrying your code matches. Flat % of
**notional**, **additive** to platform fees (never a replacement):

`builder_fee = notional × builder_fee_rate_bps / 10000`

Configure two rates on your profile: `builder_taker_fee_bps` (default 0, **max 100
bps / 1%**) and `builder_maker_fee_bps` (default 0, **max 50 bps / 0.5%**),
granularity 1 bp. Rate-change policy: **1 change / 7 days**, takes effect **3 days**
after scheduling, **one pending change** at a time.

| Market | Code attached | User pays |
|---|---|---|
| no platform fee | no | nothing |
| no platform fee | yes | builder fee only |
| platform fee | no | platform fee only |
| platform fee | yes | platform + builder fee |

Maker and taker sides of one trade can carry different builder codes/rates — each
side earns its own. The CLOB balance checker accounts for platform + builder fees;
for market buys pass `userUSDCBalance` so the SDK computes fee-adjusted fills.

Query a market's fee params: `getClobMarketInfo(conditionID)` → platform
`info.fd.{r,e,to}` (rate/exponent/taker-only), builder `info.mbf` (maker) /
`info.tbf` (taker).

### On-chain attribution

`builder` is part of the **signed V2 order struct** (`salt, maker, signer,
tokenId, makerAmount, takerAmount, side, signatureType, timestamp, metadata,
builder`) and appears in every `OrderFilled` event from CTF Exchange V2. The
EIP-712 Exchange **domain version is `"2"`** in V2 (was `"1"`) — update your domain
separator if hand-rolling typed data (see `v1-v2-migration.md`). The old
`@polymarket/builder-signing-sdk` + HMAC-header flow is **gone** in V2. Existing V1
builders are auto-provisioned a builder-code entity — just upgrade the SDK and
attach the code. Polymarket may disable a code (terms violation / abusive fees /
integrity); orders with a disabled code are rejected.

## Tiers

| Feature | Unverified | Verified | Partner |
|---|---|---|---|
| Daily relayer txns | 100/day | 10,000/day | Unlimited |
| API rate limits | Standard | Standard | Highest |
| Gasless / attribution / builder fees | Yes | Yes | Yes |
| Leaderboard / Telegram | — | Yes | Yes |
| Eng/marketing support | — | Standard | Elevated |
| Priority access | — | — | Yes |

Unverified is the default (no approval). Upgrade to **Verified** by emailing
`builder@polymarket.com` with your Builder API key, use case, and expected volume
(unlocks 100× relayer limit, builder-fee monetization, leaderboard, private
Telegram, possible weekly USDC rewards + grants). **Partner** is the enterprise
tier. If you only need more relayer txns **for your own wallet** (not routing for
others), a personal Relayer API key
(`polymarket.com/settings?tab=api-keys`) grants unlimited relayer txns.

Note: **EOA wallets have no relayer access** — EOA users pay their own gas.

## Builder API reference endpoints

- `GET` aggregated builder leaderboard
- `GET` daily builder volume time-series

(See `api-data.md` / `references/openapi/clob-openapi.yaml`.)

## See also

`orders.md` (attaching the code), `relayer.md` + `trading/gasless` (gasless),
`rewards-rebates.md` (fees that fund rebates), `v1-v2-migration.md`,
`deposit-wallets.md`.
