# CTF — Conditional Token Framework (split / merge / redeem) + neg-risk

Scope: the on-chain token mechanics under Polymarket positions — splitting pUSD
into outcome tokens, merging them back, redeeming after resolution, and the
neg-risk conversion. For the conceptual overview of tokens/positions see
`concepts.md`; for contract addresses see `resources.md`.
Source: https://docs.polymarket.com/trading/ctf/overview ·
https://docs.polymarket.com/advanced/neg-risk · last verified: 2026-06-09

## Mental model

Outcome tokens are **ERC1155** assets (Gnosis Conditional Token Framework). Every
binary market has exactly two: **Yes** and **No**, each redeemable for \$1.00 pUSD
on the winning side. Every Yes/No pair is always fully backed by \$1.00 pUSD locked
in the CTF contract.

Three core operations (+ neg-risk conversion):

| Op | Effect |
|---|---|
| **Split** | `$X pUSD → X Yes + X No` |
| **Merge** | `X Yes + X No → $X pUSD` |
| **Redeem** | after resolution: `X winning tokens → $X pUSD`; losing → \$0 |
| **Convert** (neg-risk only) | `1 No in outcome A → 1 Yes in every other outcome` |

> Polymarket routes these through thin **collateral adapter** contracts so flows
> stay pUSD-native. Approve the adapter **once** (`CtfCollateralAdapter` for
> standard, `NegRiskCtfCollateralAdapter` for neg-risk — see `resources.md`), then
> split/merge/redeem through it. The adapter handles USDC.e↔pUSD wrapping
> automatically. An EOA `approve()` of the raw CTF/exchange does not substitute.

## Token identifiers (position IDs)

Each outcome token's ERC1155 id is computed on-chain in three steps; the SDKs and
Gamma API expose them so manual computation is only needed for direct contract
integration. **Easiest path: read the token ids off Gamma** (`clobTokenIds` /
`tokens` on a market — see `api-gamma.md`).

1. `getConditionId(oracle, questionId, outcomeSlotCount)` — `oracle` = UMA CTF
   Adapter; `questionId` = `bytes32` hash of UMA ancillary data;
   `outcomeSlotCount = 2` for all binary markets.
2. `getCollectionId(parentCollectionId, conditionId, indexSet)` —
   `parentCollectionId = bytes32(0)`; `indexSet` is a bitmask: `1` (`0b01`) =
   first outcome, `2` (`0b10`) = second.
3. `getPositionId(collateralToken, collectionId)` — `collateralToken` = pUSD.

## Split / Merge / Redeem — function parameters

Common params (binary markets):

- `collateralToken` (`IERC20`) — pUSD (address in `resources.md`).
- `parentCollectionId` (`bytes32`) — always `0x00…00`.
- `conditionId` (`bytes32`) — market's condition id (from Gamma/Markets API).
- `partition` (`uint[]`) — `[1, 2]` (Yes = 1, No = 2). For **redeem** the param is
  `indexSets` (`uint[]`), e.g. `[1, 2]` to redeem both (only the winner pays).
- `amount` (`uint256`) — split/merge: number of full sets. **Redeem has no
  `amount`** — it burns your entire balance for the condition.

**Split** prerequisites: pUSD balance, pUSD approval to the adapter, condition
already `prepareCondition`-prepared on the CTF contract. Trivial/invalid
partitions revert. The op is atomic.

**Merge** requires equal Yes+No amounts; the adapter burns a full set per unit,
receives released USDC.e, wraps to pUSD, returns pUSD. Atomic.

**Redeem** is only available **after resolution** (check market `resolved`). No
deadline — winning tokens stay redeemable. Payout vector: Yes wins `[1,0]`, No
wins `[0,1]`. Winning tokens burn for \$1 each; losing tokens burn for \$0.

Code examples (Python + TypeScript): `github.com/Polymarket/examples`.

## Neg-risk markets

A mechanism for multi-outcome events where exactly one outcome wins. A **No** in
any market can be **converted** into **1 Yes in every other market** in the event,
via the **Neg Risk Adapter** — making "bet against A" ≡ "bet for everything else,"
capital-efficiently.

Identify via Gamma: `negRisk: true` on events/markets. Neg-risk markets use the
**Neg Risk CTF Exchange** + **Neg Risk Adapter** (not the standard CTF Exchange) —
addresses in `resources.md`.

When trading neg-risk markets you **must** pass the neg-risk flag in order options:

```ts
await client.createAndPostOrder(
  { tokenID: "TOKEN_ID", price: 0.5, size: 100, side: Side.BUY },
  { tickSize: "0.01", negRisk: true },   // required for neg-risk markets
);
```

(Python: `neg_risk=True`.) See `orders.md` / the SDK files for full order flow.

### Augmented neg-risk

Some events add outcomes after launch (e.g. a new candidate). Augmented neg-risk
uses **named** outcomes + reserved **placeholder** outcomes + an **explicit
"Other"**. Flags: `enableNegRisk: true` **and** `negRiskAugmented: true`.

> Only trade **named** outcomes. Placeholders are not shown in the UI and should
> be ignored until named or resolved; "Other" narrows as placeholders are
> clarified — avoid trading it directly. The SDK order option is always
> `negRisk: true` / `neg_risk: True` for any neg-risk market, standard or
> augmented.

## See also

`concepts.md` (positions/tokens, resolution), `resources.md` (addresses),
`troubleshooting.md` (rate limits, order errors), `api-gamma.md` (`negRisk`,
token ids).
