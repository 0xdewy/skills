---
name: hyperliquid
description: >-
  Developer and protocol reference for Hyperliquid: HyperCore trading APIs,
  Info/Exchange/WebSocket endpoints, signing, rate limits, asset IDs, HyperEVM,
  CoreWriter/precompiles, bridges, HIPs, validators, and support workflows.
  TRIGGER on: Hyperliquid API, HyperCore, HyperEVM, HYPE, HL SDK, placing
  orders, CLOB, info endpoint, exchange endpoint, websocket subscriptions,
  asset IDs, tick/lot size, signing errors, rate limits, CoreWriter,
  HyperCore transfers, HIP-1/HIP-2/HIP-3/HIP-4, validator setup, vaults, or
  troubleshooting Hyperliquid deposits/withdrawals. SKIP on: unrelated
  exchanges, generic EVM/Solidity questions with no Hyperliquid angle, general
  crypto market commentary, or financial advice without an implementation or
  protocol-docs need.
license: MIT
metadata:
  author: 0xdewy
  version: 1.0.0
  category: finance
  tags:
    - hyperliquid
    - hypercore
    - hyperevm
    - trading-api
    - websocket
    - clob
---

# Hyperliquid

Use this skill when a user needs accurate implementation guidance for
Hyperliquid's official docs. Ground every claim in the local reference files or
the live docs — never speculate about an endpoint, asset id, or signature format
you have not checked; open the relevant reference file before asserting how
something works. The local reference set was scraped from the
official GitBook Markdown docs and is indexed under `references/`.

## Source Discipline

- Treat `references/docs/` as a local mirror of upstream docs, not as permanent
  truth. Each mirrored page has `source_url` and `scrape_status` frontmatter.
- Do not use GitBook `?ask=` query URLs during automated collection; the checked
  robots.txt disallows `ask` query paths. Use the local mirror or normal source
  page URLs instead.
- For production-sensitive answers, especially signing, rate limits, endpoint
  schemas, fees, transfers, bridge behavior, or protocol constants, cite the
  relevant mirrored page and mention the scrape provenance. If live freshness is
  required, verify the upstream `source_url`.
- Prefer official SDK behavior over hand-written signing code. Hyperliquid docs
  explicitly recommend SDKs for signing because small serialization differences
  cause misleading signer-recovery errors.
- Do not give trading, liquidation, or leverage advice as a recommendation. You
  can explain mechanics, API fields, risk constraints, and protocol behavior.
- Never ask for or expose private keys, seed phrases, or production API wallet
  secrets. When examples need credentials, use placeholders and recommend API
  wallets with limited permissions where supported.

## Reference Routing

Start with the smallest reference that matches the task:

- General map: read `references/index.md` to find every mirrored docs page.
- API implementation: read `references/api-reference.md`, then exact endpoint
  pages in `references/docs/for-developers-api-*.md`.
- Trading and protocol mechanics: read `references/trading-protocol.md`, then
  exact trading, HyperCore, HIP, vault, validator, or risk pages.
- HyperEVM and Core interactions: read `references/hyperevm-reference.md`, then
  exact HyperEVM developer pages.
- Support and troubleshooting: use the `support` section in
  `references/index.md`, then open the specific FAQ page.
- Scrape provenance: read `references/scrape-compliance.md` and
  `references/source-map.json`.

## Implementation Workflow

1. Identify the surface: Info REST, Exchange REST, WebSocket, HyperEVM JSON-RPC,
   CoreWriter/precompiles, bridge/transfer, SDK usage, or protocol mechanics.
2. Load the curated reference for that surface.
3. Load exact mirrored pages for request/response schemas, constants, or edge
   cases. Do not rely on memory for action payloads.
4. State assumptions: mainnet/testnet, perp/spot/outcome, master account vs
   sub-account/vault, SDK/language, and whether the user is asking for read-only
   data or signed actions.
5. For signed actions, prefer official SDK examples and call out pitfalls:
   signing scheme, msgpack field order, trailing zeroes, address case, nonce,
   and `vaultAddress` for sub-accounts/vaults.
6. For code, include minimal runnable examples with placeholders, endpoint URLs,
   rate-limit-aware retries, and validation of response `status` and nested
   per-order statuses.
7. End with the exact docs pages consulted so the user can audit the answer.

## Common Constants

- Mainnet API: `https://api.hyperliquid.xyz`
- Testnet API: `https://api.hyperliquid-testnet.xyz`
- Mainnet WebSocket: `wss://api.hyperliquid.xyz/ws`
- Testnet WebSocket: `wss://api.hyperliquid-testnet.xyz/ws`
- HyperEVM JSON-RPC examples in docs use `/evm` paths such as
  `https://rpc.hyperliquid.xyz/evm` and
  `https://rpc.hyperliquid-testnet.xyz/evm`; verify provider choice for
  production.
- CoreWriter system contract: `0x3333333333333333333333333333333333333333`
- HYPE HyperEVM transfer/system address:
  `0x2222222222222222222222222222222222222222`
- HyperEVM read precompile range starts at
  `0x0000000000000000000000000000000000000800`

## Output Expectations

When answering implementation questions, include:

- The exact API surface and endpoint.
- Required request fields and the meaning of compact keys such as `a`, `b`,
  `p`, `s`, `r`, `t`, `c`, `o`, and `f` when relevant.
- Asset ID rules for perps, spot, builder-deployed perps, and outcomes when an
  action uses numeric `asset`.
- A response-handling note that distinguishes top-level transport success from
  nested action errors.
- Relevant rate-limit or pagination constraints.
- Source pages consulted, using local paths and upstream URLs when useful.
