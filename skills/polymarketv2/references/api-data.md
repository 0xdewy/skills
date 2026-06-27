# Data API — user & market analytics

Scope: public, no-auth analytics — positions, trades, activity, open interest,
volume, holders, leaderboards.
Source: https://docs.polymarket.com (Data API) · last verified: 2026-06-09
Base URL: `https://data-api.polymarket.com`

## Endpoints (commonly used)

| Method & path | Purpose |
|---|---|
| `GET /positions` | Open positions for a user |
| `GET /closed-positions` | Closed positions for a user |
| `GET /trades` | Trades |
| `GET /activity` | User activity feed |
| `GET /oi?market=<conditionId>[,<conditionId>...]` | Open interest per market (condition id is a 0x-prefixed 64-hex hash) |
| `GET /live-volume?id=<eventId>` | Live volume for an event (returns `total` + per-market `value`) |
| `GET /traded?user=<addr>` | Total number of markets a user has traded |
| `GET /holders?market=<conditionId>` | Top holders for a market |
| `GET /value?user=<addr>` | Total value of a user's positions |
| `GET /v1/accounting/snapshot` | Download an accounting snapshot (ZIP of CSVs) |
| `GET /v1/activity/combos` | User combo activity (see `combos-rfq.md`) |
| `GET /v1/positions/combos` | User combo positions (see `combos-rfq.md`) |

Also available: leaderboards (trader rankings), builder analytics (aggregated
builder leaderboard, daily builder volume time-series — see `builders.md`), and
user PnL. Full route list + schemas: `references/openapi/data-openapi.yaml`.

## Notes

- `market` here is the **condition id** (`0x` + 64 hex), not the numeric Gamma
  market id and not the CLOB token id. Resolve a token id → condition id with the
  CLOB `GET /markets-by-token/{token_id}` endpoint (see `api-clob-public.md`).
- Health check: `GET /ok`.

## Rate limits (Data)

In the single rate-limit table in `troubleshooting.md` (Data section).
