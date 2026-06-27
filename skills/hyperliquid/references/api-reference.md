# Hyperliquid API Reference

This guide is a curated map over the official mirrored docs. For exact schemas,
open the linked page in `references/docs/`.

## Core Surfaces

- REST Info endpoint: `POST https://api.hyperliquid.xyz/info`
  - Read-only exchange and user data.
  - Exact page: `references/docs/for-developers-api-info-endpoint.md`
  - Perp-specific page:
    `references/docs/for-developers-api-info-endpoint-perpetuals.md`
  - Spot-specific page:
    `references/docs/for-developers-api-info-endpoint-spot.md`
- REST Exchange endpoint: `POST https://api.hyperliquid.xyz/exchange`
  - Signed actions that mutate HyperCore state.
  - Exact page: `references/docs/for-developers-api-exchange-endpoint.md`
- WebSocket:
  - Overview: `references/docs/for-developers-api-websocket.md`
  - Subscriptions:
    `references/docs/for-developers-api-websocket-subscriptions.md`
  - WebSocket post requests:
    `references/docs/for-developers-api-websocket-post-requests.md`
  - Timeouts/heartbeats:
    `references/docs/for-developers-api-websocket-timeouts-and-heartbeats.md`

Use mainnet examples against `https://api.hyperliquid.xyz`. Use testnet
equivalents at `https://api.hyperliquid-testnet.xyz`.

## REST Info Patterns

All documented Info calls use `POST /info` with JSON body field `type`.

Common general `type` values include:

- `allMids`
- `openOrders`
- `frontendOpenOrders`
- `userFills`
- `userFillsByTime`
- `userRateLimit`
- `orderStatus`
- `l2Book`
- `candleSnapshot`
- `maxBuilderFee`
- `historicalOrders`
- `subAccounts`
- `vaultDetails`
- `portfolio`
- `referral`
- `userFees`

Perpetuals pages cover:

- `perpDexs`
- `meta`
- `metaAndAssetCtxs`
- `clearinghouseState`
- `userFunding`
- `fundingHistory`
- `predictedFundings`
- open-interest caps and deploy auction queries
- active asset data
- builder-deployed market limits and status

Spot pages cover:

- `spotMeta`
- `spotMetaAndAssetCtxs`
- `spotClearinghouseState`
- spot deploy auction queries
- token details
- outcome metadata and settled outcomes

Pagination: responses over time ranges return at most 500 elements or distinct
blocks of data. For larger ranges, use the last returned timestamp as the next
`startTime`.

User address pitfall: account data must be queried with the actual master,
sub-account, or vault address. Querying an agent wallet address commonly returns
empty results.

## REST Exchange Action Families

The Exchange endpoint signs and submits actions. Always inspect the exact page
before coding a payload.

Trading and order actions:

- `order`
- `cancel`
- `cancelByCloid`
- `scheduleCancel`
- `modify`
- `batchModify`
- `updateLeverage`
- `updateIsolatedMargin`
- `twapOrder`
- `twapCancel`

Transfer and account actions:

- `sendAsset`
- `sendAssetFromSubAccount`
- `sendToEvmWithData`
- `usdSend`
- `spotSend`
- `withdraw3`
- `usdClassTransfer`
- staking deposit/withdraw/delegate actions
- vault transfer and backstop liquidator actions
- API wallet approval
- builder fee approval
- nonce invalidation
- account abstraction and HIP-3 DEX abstraction actions
- outcome split/merge/negate actions

Order action compact keys:

- `a`: numeric asset ID
- `b`: is buy
- `p`: price string
- `s`: size string
- `r`: reduce-only boolean
- `t`: order type object
- `c`: optional client order ID, a 128-bit hex string

Limit order TIF values:

- `Alo`: add-liquidity-only/post-only
- `Ioc`: immediate-or-cancel
- `Gtc`: good-til-canceled

Cancel action compact keys:

- `a`: asset
- `o`: order ID
- `f`: optional fast flag. Skip the key when false; actions hashed with
  `f: false` are rejected.

Response handling: `status: "ok"` can still contain per-order errors in nested
`response.data.statuses`. Check each status entry for `resting`, `filled`,
`success`, or `error`.

## Asset IDs

Exact page: `references/docs/for-developers-api-asset-ids.md`.

- Perp asset ID: index in the `meta.universe` response. Example from docs:
  `BTC = 0` on mainnet.
- Builder-deployed perp asset ID:
  `100000 + perp_dex_index * 10000 + index_in_meta`.
- Spot asset ID: `10000 + spotInfo["index"]`, where `spotInfo` is the matching
  entry in `spotMeta.universe`.
- Spot token ID and spot pair ID are different, and mainnet/testnet IDs differ.
- Outcomes use `encoding = 10 * outcome + side`, where side is `0` or `1`.
  - Spot coin: `#<encoding>`
  - Token name: `+<encoding>`
  - Asset ID: `100000000 + encoding`

For spot Info/WebSocket `coin`, use `PURR/USDC` for PURR and `@{index}` for
other spot pairs, where the index is from `spotMeta.universe`.

## Tick, Lot, and Numeric Formatting

Exact page: `references/docs/for-developers-api-tick-and-lot-size.md`.

- Prices can have up to 5 significant figures.
- Perp price decimal places are capped at `6 - szDecimals`.
- Spot price decimal places are capped at `8 - szDecimals`.
- Integer prices are always allowed regardless of significant figures.
- Sizes are rounded to the asset's `szDecimals`.
- Remove trailing zeroes when signing.

## Signing and Nonces

Exact pages:

- `references/docs/for-developers-api-signing.md`
- `references/docs/for-developers-api-nonces-and-api-wallets.md`

Prefer official SDKs for signing. Common signing failure causes:

- Confusing L1 action signing with user-signed action signing.
- Msgpack field order mismatch.
- Trailing zeroes on numeric strings.
- Uppercase address fields; lowercase before signing and sending.
- Assuming local signer recovery means the Hyperliquid payload was signed
  correctly.

For sub-accounts and vaults, sign with the master account and set
`vaultAddress` to the sub-account or vault address.

Some actions support `expiresAfter` in milliseconds. If stale, the action is
rejected and consumes 5x the normal address-based rate-limit weight. User-signed
actions such as Core USDC transfer do not support `expiresAfter`.

## Rate Limits

Exact page: `references/docs/for-developers-api-rate-limits-and-user-limits.md`.

IP-based highlights:

- REST aggregate weight: 1200 per minute.
- Documented `exchange` actions weigh `1 + floor(batch_length / 40)`.
- Some `info` requests weigh 2: `l2Book`, `allMids`, `clearinghouseState`,
  `orderStatus`, `spotClearinghouseState`, `exchangeStatus`.
- `userRole` weighs 60.
- Most other documented `info` requests weigh 20.
- Certain history endpoints add weight per items returned; `candleSnapshot`
  adds weight per 60 items.
- WebSocket maxes: 10 connections, 30 new connections/minute, 1000
  subscriptions, 10 unique users across user-specific subscriptions, 2000
  sent messages/minute, 100 simultaneous inflight post messages.

Address-based highlights:

- Actions are limited per user, with sub-accounts treated separately.
- Each address starts with an initial buffer of 10000 requests.
- When rate limited, an address gets one request every 10 seconds.
- Cancels have a larger cumulative limit so orders can still be canceled.
- Batched orders/cancels count as one request for IP limits but `n` requests
  for address-based limits.

## WebSocket Subscriptions

Exact page: `references/docs/for-developers-api-websocket-subscriptions.md`.

Subscribe with:

```json
{
  "method": "subscribe",
  "subscription": { "type": "l2Book", "coin": "BTC" }
}
```

Subscription types include:

- Market data: `allMids`, `candle`, `l2Book`, `trades`, `activeAssetCtx`,
  `bbo`, `allDexsAssetCtxs`, `fastAssetCtxs`, `outcomeMetaUpdates`
- User data: `notification`, `webData3`, `twapStates`,
  `clearinghouseState`, `openOrders`, `orderUpdates`, `userEvents`,
  `userFills`, `userFundings`, `userNonFundingLedgerUpdates`,
  `activeAssetData`, `userTwapSliceFills`, `userTwapHistory`, `spotState`,
  `allDexsClearinghouseState`

Snapshot note: streaming user endpoints send an initial message with
`isSnapshot: true`; later updates have `isSnapshot: false`.

`fastAssetCtxs` data is base64 encoded and raw-DEFLATE compressed. Decode,
decompress with raw deflate, UTF-8 decode, then parse JSON.

## Error Responses

Exact page: `references/docs/for-developers-api-error-responses.md`.

For exchange actions, distinguish:

- HTTP or top-level response failure.
- Top-level `status: "ok"` with nested per-action errors.
- Signing errors that recover an unexpected user/API wallet address.
- User/action errors such as min notional, stale action, missing deposit,
  invalid asset, or already canceled/filled orders.
