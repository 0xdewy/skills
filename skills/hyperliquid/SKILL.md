---
name: hyperliquid
description: >-
  Hyperliquid protocol and developer reference for HyperCore, HyperEVM,
  trading APIs, signing, asset IDs, transfers, CoreWriter, HIPs,
  validators, vaults, and support workflows. Only use when explicitly
  requested.
license: MIT
disable-model-invocation: true
metadata:
  author: 0xdewy
  version: 1.0.0
  category: finance
  activation: explicit
  tags:
    - hyperliquid
    - hypercore
    - hyperevm
    - trading-api
    - websocket
    - clob
---

# Hyperliquid

Answer implementation questions about Hyperliquid using local references or
official docs. Do not guess endpoint shapes, signing formats, asset IDs, or rate
limits.

## Source Discipline

Run `scripts/search_refs.py --limit 4 "<question terms>"`, then open only the
best matching reference sections. Browse official Hyperliquid docs if freshness
matters or the local reference is missing.

## Routing

- HyperCore trading/API: info, exchange, signing, order placement, transfers.
- WebSocket: subscriptions, message formats, reconnect/state handling.
- HyperEVM/CoreWriter: precompiles, CoreWriter actions, bridging, HIPs.
- Ops/support: deposits, withdrawals, validators, vaults, troubleshooting.

For financial advice or market commentary, use a finance skill instead. For
generic EVM work with no Hyperliquid angle, use `rust-evm`.
