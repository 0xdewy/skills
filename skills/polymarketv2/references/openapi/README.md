# Bundled machine-readable specs

The **canonical** Polymarket OpenAPI (REST) and AsyncAPI (WebSocket) specs, fetched
from `https://docs.polymarket.com/api-spec/*` and the published AsyncAPI files
(last verified: 2026-06-09). Use these for exact schemas, enums, and field types; the prose
reference files distill them. (Searchable via `scripts/search_refs.py` only through
this README — the `.yaml`/`.json` files themselves are not indexed.)

## OpenAPI (REST)

| File | API | Base URL | Prose reference |
|---|---|---|---|
| `gamma-openapi.yaml` | Gamma (discovery) | `https://gamma-api.polymarket.com` | `api-gamma.md` |
| `clob-openapi.yaml` | CLOB (public + trading) | `https://clob.polymarket.com` | `api-clob-public.md`, `orders.md`, `auth-l1-l2.md`, `rewards-rebates.md`, `builders.md` |
| `data-openapi.yaml` | Data (analytics) | `https://data-api.polymarket.com` | `api-data.md` |
| `bridge-openapi.yaml` | Bridge | `https://bridge.polymarket.com` | `bridge.md` |
| `relayer-openapi.yaml` | Relayer (gasless) | `RELAYER_URL` | `relayer.md` |
| `combos-rfq-openapi.yaml` | Combinatorial RFQ | `https://combos-rfq-api.polymarket.sh` | `combos-rfq.md` |

## AsyncAPI (WebSocket)

| File | Channel(s) | Prose reference |
|---|---|---|
| `asyncapi.json` | market data sockets (market/RTDS) | `api-websockets.md` |
| `asyncapi-user.json` | user channel | `api-websockets.md` |
| `asyncapi-sports.json` | sports channel | `api-websockets.md` |
| `asyncapi-rfq.json` | RFQ quoter gateway | `combos-rfq.md` |

## Excluded non-canonical variants (do not use)

The docs site also publishes partial/duplicate specs. Verified by download+diff on
2026-06-09 and intentionally **not** bundled:

- `api-reference/clob-subset-openapi.yaml` — a ~17KB **subset** (0 operationIds)
  of the 218KB `clob-openapi.yaml`. Use the full one.
- `api-reference/data-api-openapi.yaml` — a smaller (~40KB) variant that differs
  from the canonical `api-spec/data-openapi.yaml` (~50KB).
- `api-reference/gamma-openapi copy.json` — a stray copy.
- The per-endpoint `developers/open-api/*.json` fragments (get-book, get-trades,
  …) — covered by the full specs above.
