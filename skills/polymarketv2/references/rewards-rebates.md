# Fees, rewards & rebates

Scope: the base fee model and the four incentive programs — liquidity rewards,
maker rebates, taker rebates (tiers), and (cross-ref) referrals. The REST endpoints
for querying rewards/earnings live on the CLOB; see the rewards endpoints below.
Source: https://docs.polymarket.com/trading/fees ·
.../market-makers/liquidity-rewards · .../market-makers/maker-rebates ·
.../trading/taker-rebates · https://docs.polymarket.com/api-reference/rewards/* ·
last verified: 2026-06-09

## Fee model

Fees are applied **at match time** by the protocol — you never put fee info in an
order. **Makers are never charged; only takers pay.** Per-market, taker-only,
computed in USDC/pUSD:

```text
fee = C × feeRate × p × (1 − p)
```

`C` = shares, `p` = price. The dollar fee is **symmetric around 50%** (a 30¢ trade
== a 70¢ trade) and **peaks at p=0.50**. Rounded to 5 dp; min charge 0.00001.

| Category | Taker rate | Maker rebate share |
|---|---|---|
| Crypto | 0.07 | 20% |
| Sports | 0.03 | 25% |
| Finance / Politics / Mentions / Tech | 0.04 | 25% |
| Economics / Culture / Weather / Other | 0.05 | 25% |
| Geopolitics & world events | 0 (free) | — |

A market has fees when `feesEnabled == true`; query params with
`getClobMarketInfo(conditionID)` → `info.fd = { r:rate, e:exponent, to:takerOnly }`
(builder fee fields `info.mbf`/`info.tbf` in `builders.md`). No Polymarket fee to
deposit/withdraw.

## Liquidity rewards (resting-order incentives)

Posting resting limit orders auto-enrolls makers. Paid **daily at 00:00 UTC** to
maker addresses; **\$1 minimum** payout. Methodology is adapted from dYdX's LP
rewards for binary markets (per-market isolated pools, no staking).

Each market configures `max_incentive_spread` (`v`, max spread from midpoint in
cents) and `min_incentive_size` — both fetchable on the market object via CLOB /
Markets API; epoch allocations via the Markets API.

Quadratic order-scoring: `S(v,s) = ((v − s)/v)² · b` (`s` = spread from the
size-cutoff-adjusted midpoint, `b` = in-game multiplier). Two side scores `Q_one`,
`Q_two` are built from bid/ask sizes × `S`. Two-sided depth is boosted by taking
the min:

- midpoint in **[0.10, 0.90]**: `Q_min = max(min(Q_one,Q_two), max(Q_one/c, Q_two/c))`
  — single-sided still scores at reduced rate (`c = 3.0` scaling factor).
- midpoint in **[0,0.10)** or **(0.90,1.0]**: `Q_min = min(Q_one, Q_two)` —
  must be double-sided.

Sampled every minute (10,080 samples/epoch = 1 week); normalized per sample, summed
to `Q_epoch`, normalized again to `Q_final`, then × the market's reward pool.
(Time-bound seasonal pools — e.g. the April 2026 \$5M+ sports/esports program with
per-league pre/live splits — are listed in the live docs; not reproduced here.)

## Maker rebates

Funded by taker fees; redistributes the per-category share (table above) to makers
whose resting liquidity **got filled**. Paid **daily in pUSD**, \$1 min. Distributed
**fee-curve weighted** using the same `C × feeRate × p × (1−p)` per filled maker
order:

```text
rebate = (your_fee_equivalent / total_fee_equivalent) × rebate_pool
```

Totals are per-market — you only compete with makers in the same market. Eligible
categories = all fee-enabled ones (Geopolitics excluded). Check maker-rebate
scoring of a resting order via `GET /order-scoring` (`isOrderScoring` /
`areOrdersScoring` — see `orders.md`).

## Taker rebates (Tiers) — live 2026-05-28

Taker volume earns **Weighted Volume (wV)**; your tier = trailing **30-day** wV,
recomputed daily at 00:00 UTC; rebate paid daily in pUSD and applies **going
forward** from when you hit the tier (no backfill). Maker trades do **not** count.

```text
wV = TradeSize × (1 − EntryPrice) × CategoryWeight × Bonuses
```

Category weights: Sports 1.0 · Politics/Finance/Mentions/Tech 1.3 ·
Economics/Culture/Weather/Other 1.7 · Crypto 2.3 · Geopolitics 0.

| Tier | 30-day wV | Rebate | Level-up bonus |
|---|---|---|---|
| Bronze | \$2,000 | 3% | \$10 |
| Silver | \$20,000 | 8% | \$50 |
| Gold | \$200,000 | 18% | \$250 |
| Platinum | \$1,000,000 | 32% | \$1,500 |
| Diamond | \$4,000,000 | 44% | \$7,500 |
| Obsidian | \$10,000,000+ | 50% | \$25,000 |

(Under \$2,000 = no tier, 0%.) Tier drops after a short grace period if 30-day wV
falls below threshold. One-time level-up bonus the first time you reach a tier.

## Rewards REST endpoints (CLOB)

| Endpoint | Purpose |
|---|---|
| `GET` current active rewards configurations | per-market reward config |
| `GET` multiple markets with rewards | reward-enabled markets |
| `GET` raw rewards for a specific market | raw allocation for a market |
| `GET` reward percentages for user | your reward % |
| `GET` earnings for user by date | per-day earnings |
| `GET` total earnings for user by date | per-day totals |
| `GET` user earnings and markets configuration | combined |
| `GET` current rebated fees for a maker (rebates) | accrued maker rebates |

See `references/openapi/clob-openapi.yaml` for schemas.

## See also

`builders.md` (builder fees, additive), `resources.md` (referral program),
`orders.md` (`/order-scoring`), `combos-rfq.md` (market-maker quoting),
`api-gamma.md` / `market-data` (incentive fields on the market object).
