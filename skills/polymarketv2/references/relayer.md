# Relayer — wallet deployment & on-chain wallet batches

Scope: deploying a deposit wallet and submitting on-chain wallet actions
(approvals, transfers, withdrawals, splits, merges) gaslessly via the relayer.
Source: https://docs.polymarket.com/trading/deposit-wallets · https://docs.polymarket.com/trading/gasless · last verified: 2026-06-09

Relayer auth is **independent** of CLOB L1/L2 auth. SDK relayer clients use
builder API key auth; direct API users use whatever their relayer environment
requires. Endpoint base is your `RELAYER_URL`.

## Endpoints

| Method & path | Purpose |
|---|---|
| `POST /submit` | Submit a transaction (`WALLET-CREATE`, `WALLET` batch, etc.) |
| `GET /deployed?address=<owner>&type=WALLET` | Whether a wallet is deployed on-chain |
| `GET /nonce?address=<owner>&type=WALLET` | Current `WALLET` nonce for a user |
| `GET /transaction?id=<txId>` | A relayer transaction by id (poll for state) |
| `GET /transactions?address=<owner>` | Recent transactions for a user |
| `GET /relay-payload` | Relayer address + nonce (for building a relay payload) |
| `GET /relayer/api/keys` | List your relayer API keys |

Full schemas: `references/openapi/relayer-openapi.yaml`. The two write flows
(`WALLET-CREATE`, `WALLET`) are detailed below.

## Deploy a wallet — `WALLET-CREATE`

`POST /submit`:

```json
{ "type": "WALLET-CREATE", "from": "0xOwnerAddress", "to": "0x00000000000Fb5C9ADea0298D729A0CB3823Cc07" }
```

- `to` = the deposit wallet factory for the chain (Polygon 137 above).
- **No user signature** in this payload.
- After submitting, **poll the relayer tx to `STATE_CONFIRMED`** before treating
  the wallet as ready. `STATE_MINED` or `GET /deployed?...&type=WALLET` can report
  the wallet exists on-chain before the relayer finishes registry updates;
  submitting a batch too early fails with a wallet-registration error.

## Submit a wallet action — `WALLET` batch

1. Fetch the current nonce: `GET /nonce?address=0xOwner&type=WALLET`.
2. Sign a `Batch` (normal 65-byte EIP-712 sig) under domain
   `{ name: "DepositWallet", version: "1", chainId, verifyingContract: <deposit wallet> }`.

EIP-712 types:

```text
Call  { target: address, value: uint256, data: bytes }
Batch { wallet: address, nonce: uint256, deadline: uint256, calls: Call[] }
```

3. Submit:

```json
{
  "type": "WALLET",
  "from": "0xOwnerAddress",
  "to": "0x00000000000Fb5C9ADea0298D729A0CB3823Cc07",
  "nonce": "0",
  "signature": "0x<65-byte EIP-712 sig>",
  "depositWalletParams": {
    "depositWallet": "0xDepositWallet",
    "deadline": "1760000000",
    "calls": [{ "target": "0xTokenOrContract", "value": "0", "data": "0xCalldata" }]
  }
}
```

Poll the resulting tx to `STATE_CONFIRMED` before relying on its effects.

## SDK relayer clients

- TS: `@polymarket/builder-relayer-client` — `deployDepositWallet()`,
  `deriveDepositWalletAddress()`, `executeDepositWalletBatch(calls, wallet,
  deadline)` (fetches the nonce for you). See `sdk-clob-ts.md`.
- Python: `py-builder-relayer-client` — `deploy_deposit_wallet()`,
  `get_expected_deposit_wallet()`, `get_nonce(...)`,
  `execute_deposit_wallet_batch(...)`. See `sdk-clob-python.md`.
- Rust has **no** relayer client — use the TS/Python client or the raw API for
  `WALLET-CREATE` / `WALLET`, then trade with the Rust CLOB client.

Rate limit: in the single table in `troubleshooting.md` (relayer `/submit`).

> The `WALLET` batch signature (65-byte EIP-712) is **different** from the
> ERC-7739-wrapped POLY_1271 order signature (`deposit-wallets.md`). They are not
> interchangeable.
