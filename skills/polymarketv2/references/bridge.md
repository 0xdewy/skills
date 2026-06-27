# Bridge — cross-chain deposits & withdrawals

Scope: funding a Polymarket account from other chains and withdrawing back out.
All deposits auto-convert to **pUSD on Polygon** (see `concepts.md` for pUSD).
Mechanics only — this is not a geoblock workaround.
Source: https://docs.polymarket.com/trading/bridge/* ·
https://docs.polymarket.com/api-reference/bridge/* · last verified: 2026-06-09
Base URL: `https://bridge.polymarket.com` · no auth · rate limit 50 / 10s
(see `troubleshooting.md`).

## Endpoints

| Method & path | Purpose |
|---|---|
| `POST /deposit` | Create per-wallet bridge addresses (deposit) |
| `POST /withdraw` | Create withdrawal bridge addresses for a destination |
| `POST /quote` | Preview fees / estimated output (deposit or withdraw) |
| `GET /supported-assets` | Supported chains + tokens + min deposit amounts |
| `GET /status/{address}` | Track transactions for a **bridge** address |

Address types in every create response: `evm` (Ethereum/Arbitrum/Base/Optimism/…),
`svm` (Solana), `btc` (Bitcoin), `tvm` (Tron). Each address is unique to your
wallet/destination — send only supported assets to the matching type.

## Deposit

`POST /deposit` `{ "address": "<your Polymarket wallet>" }` → `{ address: {evm,
svm, btc}, note }`. Flow: get address → check `/supported-assets` (token + min) →
send funds from source chain → poll `/status/{bridgeAddress}`. Incoming USDC or
USDC.e is wrapped to pUSD via the **Collateral Onramp**; pUSD is what you trade.

- **Large deposits** (> \$50k from a non-Polygon chain): use a third-party bridge
  (DeBridge / Across / Portal) to your Polygon USDC bridge address to cut slippage.
- **Wrong/unsupported token** → possible irrecoverable loss; recovery tool:
  `recovery.polymarket.com`. Always verify against `/supported-assets` first.

## Withdraw

`POST /withdraw` `{ address, toChainId, toTokenAddress, recipientAddr }` → same
`{evm,svm,btc}` shape. Flow: check supported → `/quote` → `/withdraw` → send pUSD
from your Polymarket wallet to the returned address → poll `/status`.

- Withdrawals are **instant** and **free** (Polymarket charges no withdrawal fee).
- **Do not pre-generate** withdrawal addresses — each is configured for one
  destination; generate only when ready.
- pUSD is unwrapped to USDC via the Collateral Offramp and swapped through a
  Uniswap v3 pool for native USDC (UI enforces < 10bp output diff). If the pool is
  exhausted, split into smaller amounts, wait for rebalance, or withdraw pUSD
  directly (some exchanges no longer accept pUSD deposits).

## Quote

`POST /quote` `{ fromAmountBaseUnit, fromChainId, fromTokenAddress,
recipientAddress, toChainId, toTokenAddress }`. Response: `quoteId`,
`estCheckoutTimeMs`, `estInputUsd`, `estOutputUsd`, `estToTokenBaseUnit`, and
`estFeeBreakdown { gasUsd, appFeeLabel, appFeePercent, appFeeUsd, fillCostPercent,
fillCostUsd, maxSlippage, minReceived, swapImpact, swapImpactUsd, totalImpact,
totalImpactUsd }`. Quotes are estimates.

## Supported chains (from `/supported-assets`; call it for current list)

EVM (`evm`): Ethereum (min \$7), Polygon/Arbitrum/Base/Optimism/BNB/HyperEVM/
Abstract/Monad/Ethereal/Katana/Lighter (min \$2). Solana (`svm`, \$2),
Bitcoin (`btc`, \$9), Tron (`tvm`, \$9). Each asset carries a `minCheckoutUsd`.

## Status

`GET /status/{bridgeAddress}` (the bridge address, **not** your wallet) →
`{ transactions: [{ fromChainId, fromTokenAddress, fromAmountBaseUnit, toChainId,
toTokenAddress, status, txHash, createdTimeMs }] }`. Empty array = nothing detected
yet. Statuses: `DEPOSIT_DETECTED` → `PROCESSING` → `ORIGIN_TX_CONFIRMED` →
`SUBMITTED` → `COMPLETED` (terminal) / `FAILED` (terminal). Poll every 10–30s;
`txHash` only on `COMPLETED`. Stuck/compliance-held funds → the bridge provider's
support (funxyz Intercom, linked in docs).

## See also

`concepts.md` (pUSD wrap/unwrap), `deposit-wallets.md` (where pUSD must sit for
trading), `resources.md` (Onramp/Offramp addresses), full schemas in
`references/openapi/bridge-openapi.yaml`.
