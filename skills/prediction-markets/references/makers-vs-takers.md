# Makers vs Takers

## Core Definitions

| Role | Description | When It Happens | On The Book |
|------|-------------|-----------------|-------------|
| **Maker** | Adds liquidity to the orderbook | Your order rests on the book and is later matched against an incoming order | Your order was resting (not immediately filled) |
| **Taker** | Removes liquidity from the orderbook | Your incoming order matches immediately against resting orders | Your order crossed the spread and matched instantly |

## How To Be A Maker

A maker places a **limit order** that does NOT immediately match an existing order on the opposite side. This means:

- **Buy (bid)**: Place at a price BELOW the lowest resting ask
- **Sell (ask)**: Place at a price ABOVE the highest resting bid

The order then sits on the book until someone else's order matches against it.

### Maker Example (Polymarket)
```
Orderbook:
  Bids: $0.48, $0.47, $0.46
  Asks: $0.52, $0.53, $0.54

Place a BUY limit at $0.49 → RESTING (doesn't cross the $0.52 ask) → You are a MAKER
Place a SELL limit at $0.51 → RESTING (doesn't cross the $0.48 bid) → You are a MAKER
```

## How To Be A Taker

A taker places an order that immediately matches against a resting order. This happens when:

- **Buy**: Price >= lowest ask → fills immediately
- **Sell**: Price <= highest bid → fills immediately

All "market orders" (FOK/FAK on Polymarket, `type: "market"` on Kalshi) are takers by definition.

### Taker Example (Polymarket)
```
Orderbook:
  Bids: $0.48, $0.47, $0.46
  Asks: $0.52, $0.53, $0.54

Place a BUY at $0.52 or higher → MATCHES the $0.52 ask → You are a TAKER
Place a SELL at $0.48 or lower → MATCHES the $0.48 bid → You are a TAKER
```

## Platform-Specific Details

### Polymarket

- **Post-Only orders** guarantee maker status. Order is rejected if it would cross the spread.
- **Makers NEVER pay fees.** Only takers are charged fees.
- **Maker Rebates**: Makers earn daily USDC rebates funded by taker fees.
  - Rebate % by category: Crypto 20%, others 25%.
  - Calculated per market: `rebate = (your_fee_equivalent / total_fee_equivalent) * rebate_pool`
  - Minimum $1 USDC accrued for payout.
- **Taker fee formula**: `fee = C * feeRate * p * (1 - p)` — symmetric around 50%.
- **Taker fee rates**: Crypto 0.07, Sports 0.03, Finance/Politics 0.04, Economics/Culture/Weather 0.05. Geopolitics 0.
- **Price improvement**: When a taker's order crosses the spread, the taker gets the better resting price, not their own limit price. If you place a BUY at $0.55 but the lowest ask is $0.52, you pay $0.52.

### Kalshi

- Kalshi does not explicitly label makers vs takers in the same way, but the mechanics are identical.
- **Limit orders resting on the book** are maker orders.
- **Market orders** (`type: "market"`) are taker orders.
- **RFQ system**: Adds a pre-trade negotiation layer. Quoters (market makers) provide quotes; acceptors are takers.
- **Fee rounding**: Both makers and takers may see small rounding fees/rebates due to subpenny pricing and fractional contracts. The fee accumulator ensures fairness across fills.
- **Order groups**: Can auto-cancel orders when a contracts limit is hit (risk management for makers).

## Economic Rationale

### Why Makers Get Paid
- Makers provide the service of **liquidity** — they make it possible for others to trade instantly.
- Without makers, markets have wide spreads and high slippage.
- Maker rebates and fee exemptions incentivize consistent quoting.
- Makers take on **inventory risk** — holding positions that may move against them.

### Why Takers Pay
- Takers consume liquidity — they want immediate execution.
- Taker fees fund maker rebates.
- The fee structure encourages adding liquidity over removing it.

## Key Takeaways for LLMs Answering User Questions

1. When a user asks about "placing a limit order below the ask" — that's a **maker** strategy.
2. When a user asks about "buying at market" or "getting filled immediately" — that's a **taker** strategy.
3. On Polymarket, always mention that makers pay **zero fees** and can earn **rebates**.
4. Post-only orders are the safest way to guarantee maker status on Polymarket.
5. On Kalshi, the RFQ system adds an OTC negotiation layer on top of the standard maker/taker mechanics.
6. Price improvement always benefits the taker — they get the resting order's price, not their own limit.
7. Makers face inventory risk: if you quote both sides and the market moves sharply, you may accumulate unwanted positions.
