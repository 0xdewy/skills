# Concepts — markets, orders, positions, prices, pUSD, resolution

Scope: the conceptual mental model the API/SDK files assume — what markets/events
are, how the order lifecycle works (the **canonical** description; `orders.md`
covers the REST mechanics), how positions/tokens behave, how prices form, what
pUSD is, and how markets resolve.
Source: https://docs.polymarket.com/concepts/* · last verified: 2026-06-09

## Markets & events

- **Market** — the fundamental tradable unit: one binary Yes/No question. Each has
  a **conditionId**, a **questionId** (hash of the question, used for resolution),
  and **two ERC1155 token ids** (one per outcome). Tradable on the CLOB only when
  `enableOrderBook == true`.
- **Event** — a container grouping one or more related markets. Single-market
  event ≈ the market itself; multi-market events express mutually-exclusive
  multi-outcome predictions (often neg-risk — see `ctf.md`).
- **Slug** — the URL identifier (`polymarket.com/event/<slug>`); usable to fetch
  via Gamma (`api-gamma.md`).
- **Sports markets**: resting limit orders are auto-cancelled at the official game
  start time; start times can shift earlier, so monitor orders around start.

## Order lifecycle (canonical)

All orders are **limit orders** — a "market order" is just a limit order priced to
execute immediately against resting orders. Orders are **EIP-712-signed** messages;
the exchange settles on-chain without custody of funds.

**Order types:** `GTC` (good-till-cancelled), `GTD` (good-till-date, auto-expires),
`FOK` (fill-or-kill — fully filled or cancelled), `FAK` (fill-and-kill — fill
available, cancel rest). **Post-only** orders only rest; if they would cross the
spread they are rejected (guarantees maker, never taker).

Flow: **Create & sign** (token id, side, price, size, expiration, ms timestamp) →
**Submit to CLOB** (operator validates signature, balance, allowance, tick size) →
**Match or rest** → **Settlement** (exchange verifies both sigs, swaps tokens ↔
pUSD atomically) → **Confirmation** (finality on Polygon).

**Taker/sports delay:** some crypto/finance up-down markets apply a **250 ms**
taker delay before matching; configured sports markets apply a delay window. The
order is pending (cannot be cancelled) during the delay; if checks fail when it
expires the order is rejected. Detect via public CLOB
`GET /clob-markets/{condition_id}` / `getClobMarketInfo(conditionID)` →
`itode: true`.

**Order statuses:** `live` (resting), `matched`, `delayed` (in a seconds-delay
window), `unmatched` (placed on book after delay, no match).
**Trade statuses:** `MATCHED` → `MINED` → `CONFIRMED` (terminal, success);
`RETRYING`; `FAILED` (terminal). 

**Maker vs taker:** maker adds liquidity (rests then matched); taker removes it
(matches immediately). Price improvement always benefits the taker (buy at \$0.55
matching a \$0.52 ask → you pay \$0.52).

**Cancellation:** any time before match (except during a pending delay window).
Partial fills can't be cancelled — only the unfilled remainder.
`maxOrderSize = balance − Σ(openOrderSize − filledAmount)`.

(REST endpoints, batching, heartbeat, attribution: `orders.md`.)

## Positions & tokens

A **position** is your balance of a market's outcome tokens. Yes redeems for
\$1.00 if the event occurs, No if it doesn't. ERC1155, fully backed (every Yes/No
pair = \$1 pUSD locked). Acquire via **trade** or **split**; exit via **trade**,
**merge**, or (post-resolution) **redeem** — see `ctf.md`.

`Position value = token balance × current price`. **Holding Reward:** 4.00%
annualized (variable) on total position value in eligible markets, sampled hourly,
paid daily.

## Prices & orderbook

Prices are between \$0.00 and \$1.00 and read as **probabilities** (\$0.75 ⇒ 75%).
Displayed price = **midpoint** of bid/ask; if the spread > \$0.10, the **last
traded price** is shown instead. You trade at the ask (buying) or bid (selling),
not the midpoint. **Spread** = best ask − best bid; tighter = more liquid.

Hybrid-decentralized CLOB: **off-chain matching** by an operator + **on-chain
settlement**, custody retained. Price discovery: a new market has no price until a
buy-Yes and buy-No order sum to \$1.00 and match, minting one Yes + one No. No
trade-size limits, but large orders move price — check book depth first.

## pUSD (Polymarket USD)

The collateral for all trading: a standard **ERC-20** on Polygon, **6 decimals**,
backed 1:1 by **USDC** (enforced on-chain), transferable. Wrapping/unwrapping is
enforced by `CollateralOnramp` / `CollateralOfframp` (addresses in `resources.md`).

- **Wrap** USDC.e → pUSD: approve `CollateralOnramp` to spend USDC.e, then
  `wrap(_asset=USDC.e, _to, _amount)` (6-dec base units). Reverts `OnlyUnpaused()`
  if paused.
- **Unwrap** pUSD → USDC.e: approve `CollateralOfframp`, then
  `unwrap(_asset=USDC.e, _to, _amount)`.

For CLOB buying power, pUSD must sit in the **deposit wallet** (not the owner EOA)
— see `deposit-wallets.md`. Cross-chain deposits auto-wrap to pUSD — see
`bridge.md`.

## Resolution

Markets resolve via the **UMA Optimistic Oracle** (permissionless). Always read a
market's **resolution rules** (source, end date, edge cases) — the title is the
question, the rules define the answer.

Flow: **Propose** (pick outcome, post bond ~\$750 pUSD) → **2-hour challenge
window** → if undisputed, resolves (~2 h total). If **disputed** (counter-bond),
a second proposal round; a second dispute escalates to UMA's **DVM** token-holder
vote. Disputed resolution: ~4–6 days (24–48 h debate + ~48 h vote). Possible
vote results: proposer wins / disputer wins / **Too Early** (event not concluded)
/ **Unknown 50-50** (each token redeems \$0.50).

After resolution: trading stops; winning tokens redeem for \$1.00 (via the CTF
adapter — `ctf.md`), losing tokens are worth \$0. **Clarifications** ("Additional
context") may be issued on-chain via the bulletin board but cannot change the
question's intent.

UMA CTF Adapter addresses (v1/v2/v3): `resources.md`.

## See also

`api-gamma.md`, `api-clob-public.md`, `orders.md`, `ctf.md`, `deposit-wallets.md`,
`bridge.md`, `rewards-rebates.md`.
