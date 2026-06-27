# Unified SDK (RECOMMENDED) — @polymarket/client / polymarket-client

Scope: the recommended path. One SDK across discovery, market data, trading,
account data, and realtime streams. Defaults to the deposit-wallet flow.
Source: https://docs.polymarket.com/dev-tooling/typescript · https://docs.polymarket.com/dev-tooling/python · last verified: 2026-06-09

> Beta. TS: `@polymarket/client@beta`. Python: `polymarket-client` (ships
> parallel `AsyncPublicClient`/`PublicClient` and `AsyncSecureClient`/
> `SecureClient`; streams are async-only). Re-verify before trading code.

## Install

```bash
# TypeScript
pnpm add @polymarket/client@beta viem        # or npm i / yarn add
# Python
uv add polymarket-client                      # or pip install polymarket-client
```

## Public client (no auth)

```ts
import { createPublicClient, OrderSide } from "@polymarket/client";
const client = createPublicClient();
const markets = client.listMarkets({ closed: false, pageSize: 5 });
const first = await markets.firstPage();           // first.items: Market[]
const book = await client.fetchOrderBook({ tokenId: market.outcomes.yes.tokenId! });
const mid  = await client.fetchMidpoint({ tokenId: market.outcomes.yes.tokenId! });
```

```python
from polymarket import AsyncPublicClient
async with AsyncPublicClient() as client:
    markets = client.list_markets(closed=False, page_size=5)
    first = await markets.first_page()             # first.items: tuple[Market, ...]
```

Patterns: paginate with `for await (const page of list)` / `async for page in
list`; resume from `page.nextCursor` / `page.next_cursor`. Errors: TS per-action
guards (`ListMarketsError.isError`); Python exceptions all subclass
`PolymarketError` (catch `RateLimitError`, `UserInputError`, then
`PolymarketError`). Discovery: `listEvents/listMarkets/listTeams/listTags/
listComments/search`, `listSports`. Market data: `fetchMarket/fetchEvent`
(by `id`/`slug`/`url`), `fetchPrice/fetchMidpoint/fetchSpread/
fetchLastTradePrice/fetchPriceHistory`, batch `fetchPrices/fetchMidpoints`.

## Secure client (auth + trading)

`createSecureClient` (TS) / `AsyncSecureClient.create` (Python) resolves the
signer's **deterministic deposit wallet by default** and deploys it if needed.
Pass `wallet` only to target an explicit existing wallet (deposit wallet, Poly
Safe, Poly Proxy, or the EOA itself for EOA trading).

```ts
import { createSecureClient } from "@polymarket/client";
import { privateKey } from "@polymarket/client/viem";
const secure = await createSecureClient({ signer: privateKey(process.env.PRIVATE_KEY) });
await secure.setupTradingApprovals();              // idempotent; waits internally
```

```python
from polymarket import AsyncSecureClient
async with await AsyncSecureClient.create(private_key=os.environ["POLYMARKET_PRIVATE_KEY"]) as secure:
    await secure.setup_trading_approvals()
```

Wallet adapters (TS): `@polymarket/client/viem`, `/privy`, `/ethers-v5`. API-key
authorization (only needed when the SDK must deploy a wallet or submit approval
txns): `relayerApiKey({ key, address })` or `builderApiKey({ key, secret,
passphrase })` / Python `RelayerApiKey` / `BuilderApiKey`.

> Builder API keys are for wallet ops / backwards-compat only — **not** order
> attribution. For attribution use `builderCode` / `builder_code` on the order.

## Trading

Check `response.ok` before reading `response.orderId` / `.order_id`; else use
`response.code` (`OrderResponseErrorCode`) + `.message`.

```ts
import { OrderSide, OrderType } from "@polymarket/client";
await secure.placeLimitOrder({ tokenId, side: OrderSide.BUY, price: 0.52, size: 10 });
await secure.placeLimitOrder({ tokenId, side: OrderSide.SELL, price: 0.52, size: 10,
                               expiration: Math.floor(Date.now()/1000)+3600 });
await secure.placeMarketOrder({ tokenId, side: OrderSide.BUY, amount: 10, maxSpend: 11,
                                orderType: OrderType.FAK });      // partial-fill
await secure.placeMarketOrder({ tokenId, side: OrderSide.SELL, shares: 10,
                                orderType: OrderType.FOK });      // all-or-nothing
// create-then-post / batch:
const o = await secure.createLimitOrder({ tokenId, side: OrderSide.BUY, price: 0.52, size: 10 });
await secure.postOrder(o);   // or secure.postOrders([o1, o2])
```

Python mirrors these: `place_limit_order`, `place_market_order`,
`create_limit_order`, `post_order`, `post_orders` (sides/types/prices as strings,
e.g. `side="BUY"`, `price="0.52"`, `order_type="FAK"`).

## Lifecycle, management, account, streams

- Position lifecycle: `splitPosition` / `mergePositions` / `redeemPositions`
  (`split_position` / `merge_positions` / `redeem_positions`); `await handle.wait()`
  → `transactionHash`.
- Wallet ops: `transferErc20({ amount, recipientAddress, tokenAddress })`
  (`secureClient.environment.collateralToken`).
- Order mgmt: `fetchOrder`/`get_order`, `listOpenOrders`, `cancelOrder`,
  `cancelMarketOrders`.
- Rewards/scoring: `listCurrentRewards`, `listMarketRewards`, `fetchOrderScoring`,
  `fetchOrdersScoring`.
- Account: `listPositions`, `fetchPortfolioValue`/`get_portfolio_values`,
  `listActivity`, `listAccountTrades`, `fetchNotifications`.
- Realtime (Python async only / TS): `subscribe([...specs])` merges market +
  crypto-price streams; secure clients add a user spec for order/trade events.
- Sessions: persist `secureClient.credentials` and pass `credentials` back to
  skip re-auth.

> Changelog: `wallet` is now optional (defaults to deposit wallet);
> `setupTradingApprovals()` waits internally (no `await handle.wait()`);
> `isGaslessReady()` / `setupGaslessWallet()` are **deprecated** — just create the
> client then call `setupTradingApprovals()`.
