# CLOB authentication — L1 (private key) & L2 (API key)

Scope: how to authenticate CLOB trading endpoints. Gamma and Data APIs and CLOB
read endpoints are public and need none of this.
Source: https://docs.polymarket.com/api-reference/authentication · last verified: 2026-06-09

## Two levels

- **L1 (private key):** sign an EIP-712 message with the wallet key. Used to
  **create/derive API credentials** and to **sign order payloads** locally. Stays
  non-custodial — the key never leaves you.
- **L2 (API key):** `apiKey` + `secret` + `passphrase` (derived from L1). Used to
  authenticate requests (post orders, cancel, read balances/open orders) via
  HMAC-SHA256. **Even with L2 headers, creating an order still requires an L1
  signature over the order payload.**

## Getting credentials

- SDK: `createOrDeriveApiKey()` (TS) / `create_or_derive_api_key()` (Python) /
  `.authentication_builder(&signer).authenticate()` (Rust).
- REST: `POST /auth/api-key` (create) or `GET /auth/derive-api-key` (derive),
  with L1 headers. Response: `{ apiKey, secret, passphrase }`. **Save the nonce**
  (default `0`) — you need it to re-derive the same creds.

L1 EIP-712 struct (`ClobAuthDomain`, version `1`, chainId 137):
`ClobAuth { address, timestamp, nonce (uint256), message }`, where
`message = "This message attests that I control the given wallet"`.

## Headers

**L1** (creds endpoints): `POLY_ADDRESS`, `POLY_SIGNATURE` (EIP-712 sig),
`POLY_TIMESTAMP`, `POLY_NONCE`.

**L2** (all trading endpoints): `POLY_ADDRESS`, `POLY_SIGNATURE` (HMAC-SHA256 over
the request using `secret`), `POLY_TIMESTAMP`, `POLY_API_KEY`, `POLY_PASSPHRASE`.

## Signature types & funder

When you build an L2/trading client you set a **signatureType** and a **funder**
(the address that holds the money):

| Type | Value | Funder | Notes |
|---|---|---|---|
| EOA | `0` | the EOA | needs POL for gas |
| POLY_PROXY | `1` | proxy wallet | Magic-link / email-Google login users |
| GNOSIS_SAFE | `2` | Safe | existing Safe users |
| **POLY_1271** | `3` | **deposit wallet** | new API users; validated via ERC-1271; **V2 orders only** |

New API users: use `signatureType = 3` with the deposit wallet as funder — see
`deposit-wallets.md`. Existing Safe/Proxy users keep their current type/funder.

## Gotchas

- Relayer auth (for `/submit` wallet ops) and CLOB L1/L2 auth are **separate** —
  don't reuse one's headers/cookies for the other.
- `INVALID_SIGNATURE` → bad/misformatted key. `NONCE_ALREADY_USED` → re-derive
  with the same nonce instead of creating. Invalid funder → check the address at
  polymarket.com/settings; deploy the wallet first if it doesn't exist.
- Reference signing impls live in the `clob-client-v2` / `py-clob-client-v2`
  repos (`signing/eip712` and `signing/hmac`).

Auth-endpoint rate limit: API key endpoints 100 / 10s.
