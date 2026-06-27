# Hyperliquid Trading and Protocol Reference

This guide routes common protocol questions to the mirrored official docs.

## Architecture

Hyperliquid is an L1 with state execution split into HyperCore and HyperEVM.
HyperCore contains the onchain perp and spot order books. HyperEVM is the EVM
environment that can compose with HyperCore liquidity and state.

Core pages:

- Overview: `references/docs/hypercore-overview.md`
- Bridge: `references/docs/hypercore-bridge.md`
- API servers: `references/docs/hypercore-api-servers.md`
- Clearinghouse: `references/docs/hypercore-clearinghouse.md`
- Oracle: `references/docs/hypercore-oracle.md`
- Order book: `references/docs/hypercore-order-book.md`
- Staking: `references/docs/hypercore-staking.md`
- Vaults: `references/docs/hypercore-vaults.md`
- Multi-sig: `references/docs/hypercore-multi-sig.md`
- Quote assets: `references/docs/hypercore-permissionless-spot-quote-assets.md`
  and `references/docs/hypercore-aligned-quote-assets.md`

## Trading Mechanics

Primary trading pages:

- Trading overview: `references/docs/trading.md`
- Fees: `references/docs/trading-fees.md`
- Sub-accounts: `references/docs/trading-sub-accounts.md`
- Builder codes: `references/docs/trading-builder-codes.md`
- Perpetual assets: `references/docs/trading-perpetual-assets.md`
- Contract specifications:
  `references/docs/trading-contract-specifications.md`
- Margining: `references/docs/trading-margining.md`
- Account abstraction modes:
  `references/docs/trading-account-abstraction-modes.md`
- Portfolio margin: `references/docs/trading-portfolio-margin.md`
- Margin tiers: `references/docs/trading-margin-tiers.md`
- Robust price indices:
  `references/docs/trading-robust-price-indices.md`
- Liquidations: `references/docs/trading-liquidations.md`
- Auto-deleveraging: `references/docs/trading-auto-deleveraging.md`
- Funding: `references/docs/trading-funding.md`
- Trading order book: `references/docs/trading-order-book.md`
- Order types: `references/docs/trading-order-types.md`
- TP/SL: `references/docs/trading-take-profit-and-stop-loss-orders-tp-sl.md`
- Entry price and PnL:
  `references/docs/trading-entry-price-and-pnl.md`
- Self-trade prevention:
  `references/docs/trading-self-trade-prevention.md`
- Index perpetual contracts:
  `references/docs/trading-index-perpetual-contracts.md`
- Uniswap perpetuals: `references/docs/trading-uniswap-perpetuals.md`
- Hyperps: `references/docs/trading-hyperps.md`
- Delisting: `references/docs/trading-delisting.md`
- Market making: `references/docs/trading-market-making.md`

When answering trading questions, separate mechanics from advice. Explain how
margin, funding, liquidations, fees, or order types work; do not recommend
positions, leverage, or risk.

## Order Behavior

For implementation-level order placement, use `references/api-reference.md` and
`references/docs/for-developers-api-exchange-endpoint.md`.

Protocol-level pages to consult:

- `references/docs/trading-order-types.md`
- `references/docs/trading-order-book.md`
- `references/docs/trading-take-profit-and-stop-loss-orders-tp-sl.md`
- `references/docs/trading-self-trade-prevention.md`

Common order API concepts:

- Limit TIF: `Alo`, `Ioc`, `Gtc`.
- Trigger orders use `triggerPx`, `isMarket`, and `tpsl` values of `tp` or
  `sl`.
- `reduceOnly` rejects or constrains orders that would increase exposure.
- `cloid` is a 128-bit hex client order ID used for client-side tracking and
  cancel-by-client-ID flows.

## HIPs and Asset Deployment

HIP pages:

- HIP overview:
  `references/docs/hyperliquid-improvement-proposals-hips.md`
- HIP-1 native token standard:
  `references/docs/hyperliquid-improvement-proposals-hips-hip-1-native-token-standard.md`
- HIP-2 Hyperliquidity:
  `references/docs/hyperliquid-improvement-proposals-hips-hip-2-hyperliquidity.md`
- HIP-3 builder-deployed perpetuals:
  `references/docs/hyperliquid-improvement-proposals-hips-hip-3-builder-deployed-perpetuals.md`
- HIP-4 outcome markets:
  `references/docs/hyperliquid-improvement-proposals-hips-hip-4-outcome-markets.md`
- Frontend checks:
  `references/docs/hyperliquid-improvement-proposals-hips-frontend-checks.md`

Developer deployment pages:

- HIP-1/HIP-2 API deployment:
  `references/docs/for-developers-api-deploying-hip-1-and-hip-2-assets.md`
- HIP-3 deployer actions:
  `references/docs/for-developers-api-hip-3-deployer-actions.md`
  and `references/docs/for-developers-api-hip-3-deployer-actions-1.md`

Before giving deployment steps, identify whether the user means spot token,
spot pair, builder-deployed perp, outcome market, testnet deployment, or mainnet
deployment.

## Vaults, Validators, Staking

Vault pages:

- Current vault overview: `references/docs/hypercore-vaults.md`
- Protocol vaults: `references/docs/hypercore-vaults-protocol-vaults.md`
- Legacy vault leader/depositor pages remain mirrored for historical context.

Validator pages:

- Overview: `references/docs/validators.md`
- Running a validator: `references/docs/validators-running-a-validator.md`
- Delegation program: `references/docs/validators-delegation-program.md`

Staking and referral pages:

- Staking: `references/docs/hypercore-staking.md`
- HYPE staking onboarding:
  `references/docs/onboarding-how-to-stake-hype.md`
- Referrals: `references/docs/referrals.md`
- Staking referral proposal:
  `references/docs/referrals-proposal-staking-referral-program.md`

## Historical Data and Audits

- Historical data: `references/docs/historical-data.md`
- Risks: `references/docs/risks.md`
- Bug bounty: `references/docs/bug-bounty-program.md`
- Audits: `references/docs/audits.md`

For historical blocks, explorer requests can be expensive; the rate-limit docs
recommend S3/bulk data for large block queries.
