# Gamma API — discovery (markets, events, tags, series, search)

Scope: public, no-auth discovery of markets/events and metadata.
Source: https://docs.polymarket.com (Gamma API) · last verified: 2026-06-09
Base URL: `https://gamma-api.polymarket.com`

## Endpoints

| Method & path | Purpose |
|---|---|
| `GET /events` | List events (offset pagination: `limit`, `offset`, `order`, `ascending`) |
| `GET /events/keyset` | List events with **keyset/cursor** pagination (preferred for large scans) |
| `GET /events/{id}` | Event by id |
| `GET /events/slug/{slug}` | Event by slug |
| `GET /events/{id}/tags` | Tags attached to an event |
| `GET /markets` | List markets |
| `GET /markets/keyset` | List markets with keyset/cursor pagination |
| `GET /markets/{id}` | Market by id (`include_tag` optional) |
| `GET /markets/slug/{slug}` | Market by slug |
| `GET /markets/{id}/tags` | Tags attached to a market |

### More Gamma endpoints

| Method & path | Purpose |
|---|---|
| `GET /public-search` | Search markets, events, and profiles |
| `GET /tags` · `GET /tags/{id}` · `GET /tags/slug/{slug}` | Tags |
| `GET /tags/{id}/related-tags` | Related-tag relationships (also by slug) |
| `GET /series` · `GET /series/{id}` | Series |
| `GET /comments` | List comments (also by comment id / user address) |
| `GET /public-profile?address=<wallet>` | Public profile by wallet address |
| `GET /sports` | Sports metadata |
| `GET /sports/market-types` | Valid sports market types |
| `GET /teams` | List teams |

Full param schemas: `references/openapi/gamma-openapi.yaml`.

## Pagination

- **Offset** (`/events`, `/markets`): `limit`, `offset`, `order` (comma-separated
  JSON field names), `ascending`.
- **Keyset** (`/events/keyset`, `/markets/keyset`): pass `after_cursor` =
  previous response's `next_cursor`. **`offset` is rejected (422)** on keyset
  endpoints. `next_cursor` is present only when a full page was returned; omitted
  on the last page. Limits: events max 500 (default 20), markets max 100
  (default 20).

## Common filters

Events: `id`, `slug`, `closed`, `live`, `featured`, `tag_id`/`tag_slug`,
`exclude_tag_id`, `liquidity_min/max`, `volume_min/max`, `start_date_min/max`,
`end_date_min/max`, `series_id`, `game_id`, `created_by`, `parent_event_id`.
Markets: `id`, `slug`, `closed`, `clob_token_ids`, `condition_ids`,
`question_ids`, `market_maker_address`, `liquidity_num_min/max`,
`volume_num_min/max`, date ranges, `tag_id`, `rfq_enabled`,
`uma_resolution_status`, `game_id`, `sports_market_types`, `include_tag`.

## Key fields you'll actually use

**Market**: `id`, `conditionId`, `question`, `slug`, `description`,
`clobTokenIds` (JSON-string array of the YES/NO token ids), `outcomes`,
`outcomePrices`, `active`, `closed`, `enableOrderBook`, `acceptingOrders`,
`orderPriceMinTickSize`, `orderMinSize`, `negRisk`, `bestBid`, `bestAsk`,
`lastTradePrice`, `spread`, `volumeNum`, `liquidityNum`, `endDateIso`,
`rewardsMinSize`, `rewardsMaxSpread`, `feeSchedule`, `umaResolutionStatus`.

> Note: `clobTokenIds`, `outcomes`, and `outcomePrices` are returned as
> JSON-encoded **strings** — parse them before use.

**Event**: `id`, `slug`, `title`, `description`, `markets[]` (nested Market),
`series[]`, `tags[]`, `active`, `closed`, `liquidity`, `volume`, `openInterest`,
`negRisk`, `startDate`, `endDate`, `competitive`.

## Rate limits (Gamma)

In the single rate-limit table in `troubleshooting.md` (Gamma section).
