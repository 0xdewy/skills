# v1 vs v2 — how to tell, and what changed

Scope: disambiguating legacy v1 from current v2, and the package renames.
Source: https://docs.polymarket.com/v2-migration · https://docs.polymarket.com/api-reference/clients-sdks · last verified: 2026-06-09

## How to tell at a glance

You are on **v2** if you see any of:

- Package names with a **v2 suffix**: `@polymarket/clob-client-v2`,
  `py-clob-client-v2`, `polymarket_client_sdk_v2`, or the unified beta
  `@polymarket/client` / `polymarket-client`.
- The relayer / builder clients `@polymarket/builder-relayer-client` /
  `py-builder-relayer-client`.
- **`signatureType = 3` (POLY_1271)** and the **deposit wallet** flow.
- References to the **CTF Exchange V2** verifying contract.

You are looking at **v1 / legacy** if you see the un-suffixed
`@polymarket/clob-client` or `py-clob-client`, or only signature types 0/1/2 with
no deposit-wallet / POLY_1271 concept.

## Package renames (use the v2 one)

| Legacy (v1) | Current (v2) |
|---|---|
| `py-clob-client` | `py-clob-client-v2` |
| `@polymarket/clob-client` | `@polymarket/clob-client-v2` |
| (n/a) | unified `@polymarket/client` (TS) / `polymarket-client` (Python) — **recommended** |
| (n/a) | `@polymarket/builder-relayer-client` / `py-builder-relayer-client` |
| (n/a) | `polymarket_client_sdk_v2` (Rust) |

> If a user references `py-clob-client` / `@polymarket/clob-client`, point them to
> the `-v2` package (or the unified SDK). The bare names are the older clients.

## What's new in v2

- **Deposit wallets** for new API users: an ERC-1967 proxy that holds pUSD and
  conditional tokens; orders use **`signatureType = 3` (POLY_1271)** validated via
  ERC-1271; the deposit wallet is the funder and is both order `maker` and
  `signer`. (`deposit-wallets.md`)
- **Relayer** `WALLET-CREATE` / `WALLET` batches for gasless wallet deploy and
  on-chain actions. (`relayer.md`)
- **Unified SDK** (beta) spanning discovery, data, trading, and realtime streams
  with a single client, deposit-wallet-by-default. (`sdk-unified.md`)
- Existing **Safe (type 2)** and **Proxy (type 1)** users are unaffected and keep
  their funder/signature type.

## Stability note

The unified SDKs are **beta**; v2 is still being hardened with a documented
migration path coming. Re-verify against the live docs (`sources.md`) before
shipping trading code.
