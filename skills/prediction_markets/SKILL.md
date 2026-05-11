---
name: prediction-markets
description: >
  Authoritative reference for prediction market platforms Polymarket and Kalshi.
  Use this skill whenever the user asks about prediction markets, Polymarket,
  Kalshi, betting markets, event contracts, market making, makers vs takers,
  orderbook mechanics, prediction market APIs, CLOB trading, binary outcome
  markets, or wants to build/integrate/trade on Polymarket or Kalshi. Also
  trigger on questions about prediction market fees, order types, RFQ,
  authentication, or comparing how these platforms work — even if the user
  doesn't name the platform explicitly.
---

# Prediction Markets Skill

Authoritative reference for Polymarket and Kalshi prediction market platforms. This skill provides organized documentation covering platform architecture, trading mechanics, APIs, market concepts, and the maker/taker model.

## Commonly Confused Facts

These facts are frequently gotten wrong by even experienced developers. **Always read this section before answering** any Polymarket or Kalshi question.

### Post-Only Orders (MOST COMMONLY CONFUSED)

| Platform | Post-Only Support | Details |
|----------|------------------|---------|
| **Polymarket** | **YES** — `postOnly: true` | Order rejected with `INVALID_POST_ONLY_ORDER` if it would cross the book |
| **Kalshi** | **NO** — no post-only flag | No built-in mechanism to reject crossing orders; must implement yourself |

Polymarket is the platform with post-only. Kalshi is the platform without it. Never claim the opposite.

### Kalshi V2 API — Exact Endpoint Path

The correct V2 order creation endpoint is:
```
POST /trade-api/v2/portfolio/orders
```
Common wrong paths: `/portfolio/events/orders`, `/v2/portfolio/orders`, `/trade-api/v2/orders`. Always use `/trade-api/v2/portfolio/orders`.

### Kalshi V2 Field Names

Correct V2 field names (not the V1 field names):

| Wrong (V1/deprecated) | Correct (V2) | Type |
|------------------------|-------------|------|
| `side` | `book_side` | `"bid"` or `"ask"` |
| (not applicable) | `outcome_side` | `"yes"` or `"no"` |
| `count` | `count_fp` | Fixed-point string, e.g. `"5.00"` |
| `price` | `price_dollars` | Dollar string, e.g. `"0.4200"` |
| `yes_price` | `price_dollars` | Dollar string, e.g. `"0.4200"` |

**Important:** V1's single `side` field decomposes into TWO V2 fields. V1 had `side: "yes"` for buying YES or `side: "no"` for buying NO. V2 splits this into `book_side` (`"bid"` for buy, `"ask"` for sell) plus `outcome_side` (`"yes"` or `"no"`). For example:
- V1 `action: "buy", side: "yes"` → V2 `book_side: "bid", outcome_side: "yes"`
- V1 `action: "buy", side: "no"`  → V2 `book_side: "bid", outcome_side: "no"`

### Kalshi Orderbook Structure

Kalshi uses a **bids-only orderbook** — there are no asks in the API response. YES bids and NO bids are returned. Asks are implied via the $1.00 complement:
- YES ask price = $1.00 - (best NO bid price)
- NO ask price = $1.00 - (best YES bid price)

Polymarket uses a standard bid/ask orderbook with both sides visible.

### Polymarket Signature Types

| Type ID | Name | Use Case |
|---------|------|----------|
| 0 | EOA | Standalone wallet (pay own gas) |
| 1 | POLY_PROXY | Existing proxy wallet |
| 2 | GNOSIS_SAFE | Existing Gnosis Safe |
| 3 | POLY_1271 | **Deposit wallet (recommended for new users)** |

New users should use deposit wallets with signature type 3 (POLY_1271).

### Polymarket Heartbeat

- Post to heartbeat endpoint every **5 seconds**
- Include previous `heartbeat_id` in each request
- If server doesn't receive valid heartbeat within **10 seconds** (5s buffer), **all open orders are cancelled**
- First heartbeat: use an empty string (`""`) as the `heartbeat_id`; subsequent heartbeats use the ID from the response
- GTD expiration has a **60-second security threshold buffer**: for N-second effective lifetime, use `now + 60 + N`

## When and How to Use

Load this skill when answering questions about Polymarket, Kalshi, or prediction markets in general. The reference files contain organized documentation from official sources.

For **general platform questions** — "how does Polymarket work?", "what's the Kalshi API?", "how are fees charged?" — read the relevant reference file to ground your answer in documented facts.

For **coding/trading tasks** — "place an order on Polymarket", "fetch markets from Kalshi" — use the reference files for endpoint paths, auth requirements, parameter formats, and error codes, then implement using the documented patterns.

## Reference Files

Organized by topic. Read only the files relevant to the user's question:

| File | Contents | When to Read |
|------|----------|--------------|
| `references/polymarket.md` | Polymarket API, CLOB trading, authentication, order types, fees, concepts | Polymarket-specific questions |
| `references/kalshi.md` | Kalshi API, environments, authentication, RFS, fixed-point pricing, pagination | Kalshi-specific questions |
| `references/makers-vs-takers.md` | Detailed maker vs taker mechanics, platform differences, economic rationale | Questions about market making, liquidity, fees, post-only orders, or maker/taker roles |

If the user's question spans both platforms, read both reference files. If it's purely about maker/taker mechanics, start with `makers-vs-takers.md` and supplement with platform-specific files as needed.

## Platform Selection Cheat Sheet

When a user doesn't specify which platform, or asks about differences:

| Consideration | Polymarket | Kalshi |
|--------------|------------|--------|
| Regulation | DeFi (non-custodial, onchain) | CFTC-regulated exchange |
| Blockchain | Polygon PoS | None (traditional exchange) |
| Collateral | pUSD (crypto) | USD (fiat) |
| Order Model | CLOB (EIP-712 signed messages) | Traditional orderbook + RFQ |
| Pricing | Decimal (0.00–1.00) | Fixed-point dollar strings |
| Auth | EIP-712 signatures + HMAC | RSA-PSS with private key |
| Post-Only | **YES** — `postOnly: true`, rejects crossing orders with `INVALID_POST_ONLY_ORDER` | **NO** — no post-only flag available |
| Fees | Maker 0%, Taker 0–7% | Per-trade fees |
| APIs | Gamma, Data, CLOB, Bridge | Single Trade API v2 |
| SDKs | TS, Python, Rust | Python, TypeScript |
| Orderbook | Standard bid/ask | Bids-only (asks implied via $1.00 complement) |
| Unique Feature | Gasless transactions, Maker Rebates | RFQ system, Order Groups, Subpenny pricing |

## Responding to Common Questions

### "How do I place an order?"
Check which platform. For Polymarket: auth (EIP-712 derive API key), then `createAndPostOrder` with token ID, price, size, side, tick size, negRisk flag. For Kalshi: RSA-PSS sign (timestamp+method+path), then POST with ticker, side, count, type, price, client_order_id.

### "What's the difference between maker and taker?"
Read `references/makers-vs-takers.md`. Core: maker provides liquidity (resting limit order, no fee), taker removes liquidity (immediate fill, pays fee). On Polymarket, use post-only to guarantee maker status.

### "How do fees work?"
Read the platform's reference file. Polymarket: `fee = C * feeRate * p * (1-p)`, symmetric around 50%, maker=0%, taker varies by category. Kalshi: per-market fee model with fee rounding for sub-cent adjustments.

### "How do I authenticate?"
Polymarket: L1 (EIP-712) to derive L2 credentials (API key/secret/passphrase), then L2 (HMAC-SHA256) for trading. Kalshi: RSA-PSS signature with private key on timestamp+method+path, base64 encoded.

### "What's the orderbook structure?"
Polymarket: standard bid/ask orderbook. Kalshi: bids-only orderbook (YES bids + NO bids), asks are implied via $1.00 complement.

## Quick Polymarket Code Patterns

```python
from py_clob_client_v2 import ClobClient, OrderArgs, OrderType, PartialCreateOrderOptions
from py_clob_client_v2.order_builder.constants import BUY

# Init client
client = ClobClient("https://clob.polymarket.com", key=private_key, chain_id=137,
                     creds=api_creds, signature_type=3, funder=deposit_address)

# Get orderbook
book = client.get_order_book("TOKEN_ID")

# Place limit order
order = client.create_and_post_order(
    OrderArgs(token_id="TOKEN_ID", price=0.50, size=10, side=BUY),
    options=PartialCreateOrderOptions(tick_size="0.01", neg_risk=False),
    order_type=OrderType.GTC
)

# Cancel all
client.cancel_all()
```

## Quick Kalshi Code Patterns

```python
import requests, base64, datetime, json
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

# Authentication helper
def sign(timestamp, method, path, private_key):
    message = f"{timestamp}{method}{path.split('?')[0]}".encode()
    sig = private_key.sign(message,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
        hashes.SHA256())
    return base64.b64encode(sig).decode()

# Make authenticated request
def request(method, path, private_key, api_key_id, base_url, data=None):
    ts = str(int(datetime.datetime.now().timestamp() * 1000))
    headers = {
        'KALSHI-ACCESS-KEY': api_key_id,
        'KALSHI-ACCESS-SIGNATURE': sign(ts, method, path, private_key),
        'KALSHI-ACCESS-TIMESTAMP': ts,
    }
    if data: headers['Content-Type'] = 'application/json'
    return requests.request(method, base_url + path, headers=headers, json=data)

# Base URL (use demo-api.kalshi.co for testing, api.elections.kalshi.com for production)
BASE_URL = "https://demo-api.kalshi.co/trade-api/v2"

# Get markets
resp = requests.get(f"{BASE_URL}/markets?status=open&limit=10")
markets = resp.json()['markets']

# Place order
order = {"ticker": "MARKET-TICKER", "book_side": "bid", "outcome_side": "yes",
         "count_fp": "1.00", "type": "limit", "price_dollars": "0.50",
         "client_order_id": str(uuid.uuid4())}
resp = request("POST", "/trade-api/v2/portfolio/orders", pk, key_id, BASE_URL, order)
```
