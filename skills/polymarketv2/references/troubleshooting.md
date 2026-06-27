# Troubleshooting, rate limits & geoblock

Scope: common errors and their v2 fixes, the full rate-limit tables, and the
geoblock endpoint.
Source: https://docs.polymarket.com (Deposit Wallets · Authentication · Rate Limits · Geoblock) · last verified: 2026-06-09

## Order rejected — "invalid signature"

For a deposit-wallet (POLY_1271) order, check all four inputs:
`signatureType == 3`; order `maker` == deposit wallet; order `signer` == deposit
wallet; `signature` is the **ERC-7739-wrapped POLY_1271** sig (not the raw order
EIP-712 sig). Also confirm the order was signed against the correct **CTF
Exchange V2** verifying contract for the market. Signing it as a normal EOA order
fails ERC-1271 validation. POLY_1271 is **V2 orders only**.

## "Not enough balance"

pUSD must be held by the **deposit wallet address**, not the owner EOA. After
funding, refresh the CLOB cache:
`GET /balance-allowance/update?asset_type=COLLATERAL&signature_type=3`.

## "Allowance is missing"

Approvals must come **from the deposit wallet**, submitted as a relayer `WALLET`
batch. An EOA `approve()` does **not** authorize spending from the deposit wallet.
(`relayer.md`, `deposit-wallets.md`.)

## Wallet batch rejected

Fetch a **fresh** `WALLET` nonce (`GET /nonce?address=0xOwner&type=WALLET`) before
signing; ensure the deadline is in the future and in range; the batch sig must be
a normal 65-byte EIP-712 sig over `DepositWallet` `Batch`.

## Auth confusion

Relayer auth (`/submit`) and CLOB L1/L2 auth are **separate systems** — never
reuse one's headers/cookies for the other. Use CLOB L1/L2 for order and balance
endpoints. (`auth-l1-l2.md`.)

## Credential errors

`INVALID_SIGNATURE` → bad/misformatted private key. `NONCE_ALREADY_USED` →
re-derive with the same nonce instead of creating new creds. Invalid funder →
verify the address at polymarket.com/settings; deploy the wallet first if it
doesn't exist. Lost creds **and** nonce → you must create fresh creds (save the
new nonce).

## Rate limits

All limits are Cloudflare sliding-window throttles (requests are delayed/queued,
not hard-rejected). General: 15,000 / 10s; `/ok` 100 / 10s.

CLOB general 9,000 / 10s · `GET` balance allowance 200 / 10s · `UPDATE` balance
allowance 50 / 10s. Market data: `/book` 1,500, `/books` 500, `/price` 1,500,
`/prices` 500, `/midpoint` 1,500, `/midpoints` 500, `/prices-history` 1,000 (all
/10s). Ledger: `/trades`,`/orders`,`/notifications`,`/order` 900 / 10s;
`/data/orders` 500; `/data/trades` 500; `/notifications` 125. Auth endpoints
100 / 10s.

Trading (burst / sustained per 10 min):
`POST /order` 5,000 / 120,000 · `DELETE /order` 5,000 / 120,000 ·
`POST /orders` 2,000 / 21,000 · `DELETE /orders` 2,000 / 15,000 ·
`DELETE /cancel-all` 250 / 6,000 · `DELETE /cancel-market-orders` 1,500 / 21,000.

Gamma (per 10s): general 4,000 · `/events` 500 · `/markets` 300 ·
`/markets`+`/events` listing 900 · `/public-search` 350 · `/comments` 200 ·
`/tags` 200.

Data (per 10s): general 1,000 · `/trades` 200 · `/positions` 150 ·
`/closed-positions` 150 · `/ok` 100 · User PnL 200.

Bridge 50 / 10s. Relayer `/submit` 25 / 1 min. This is the single rate-limit
table — other reference files point here rather than copy limits.

## Geoblock (do NOT help bypass)

`GET https://polymarket.com/api/geoblock` (on `polymarket.com`, not the API
hosts) → `{ blocked, ip, country, region }`. Check it before placing orders and
surface a clear message to blocked users. Blocked/close-only/UI-restricted
regions include US, GB, FR, DE, IT, NL, BE, AU, RU, and OFAC-sanctioned countries
(full list in the docs), plus regions like Canada-Ontario and parts of Ukraine.
You may explain the endpoint and the list; **never assist with circumventing the
geoblock** (VPN, IP spoofing, etc.).
