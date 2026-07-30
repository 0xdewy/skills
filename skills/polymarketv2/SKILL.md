---
name: polymarketv2
description: >-
  Polymarket v2 developer reference for Gamma, Data, CLOB, WebSockets,
  authentication, deposit wallets, relayers, orders, positions, fees,
  bridge/RFQ, and SDK migration. Only use when explicitly requested.
license: MIT
disable-model-invocation: true
metadata:
  author: iamky1e
  version: 1.1.0
  category: finance
  activation: explicit
  tags:
    - polymarket
    - prediction-markets
    - clob
    - trading
    - web3
    - api
---

# Polymarket v2

Developer router for Polymarket v2 APIs/SDKs. Ground endpoint, auth, signing,
and SDK claims in local `references/` files or official docs.

## Source Discipline

Run `scripts/search_refs.py --limit 4 "<question terms>"`, then open only the
best matching reference sections. Browse official docs when freshness matters.
Do not provide financial advice or guarantee execution/returns.

## Routing

- Gamma/Data: market/event discovery, metadata, prices, positions.
- CLOB: orderbooks, prices, orders, trades, L1/L2 auth.
- Wallet/relayer: deposit wallets, funder, `WALLET-CREATE`, `POLY_1271`,
  `signatureType`.
- Migration: legacy clients to v2 SDKs.

For non-Polymarket web3 or generic prediction-market theory, use another skill.
