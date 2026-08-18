# Newsbin item schema

Every line in `data/YYYY-MM-DD.jsonl` is one news item. Append-only. A line is
never edited or deleted after it is pushed.

## Item shape (JSON object, one per line)

| field | type | required | meaning |
|-------|------|----------|---------|
| `id` | string | no | content hash of `(ticker, url, headline, published_at)`; set by scanner for dedup. Content-based (not capture-time based) so the same story dedups across runs |
| `ticker` | string | yes | primary ticker (uppercase), or the symbol being discussed |
| `company` | string | yes | company name |
| `headline` | string | yes | short headline / gist |
| `url` | string | yes | public source URL |
| `source` | string | yes | publication / origin (e.g. `WSJ`, `Reuters`, `company press release`) |
| `captured_at` | string | yes | ISO-8601 UTC timestamp of when this item was captured |
| `published_at` | string | no | ISO-8601 UTC publish time if known |
| `thesis_signal` | array of string | no | which thesis lens the item hits (see below) |
| `notes` | string | no | free text; keep factual |

`captured_at` is the time the item entered the repo, not the publish time. This is
what makes the repo an audit trail: we know when each item became visible.

## `thesis_signal` vocabulary (the lens)

- `scaling_efficiency` — operating metrics improving while volume scales (the OPEN pattern)
- `human_time_saved` — explicit claim about human time saved / productivity / headcount leverage
- `verification_gap` — a claim the market can't easily verify but practitioners can
- `transformation` — a company implementing a transformation that takes time
- `capital_allocation` — buyback, issuance, dilution, financing structure
- `falsifier` — evidence that could falsify a prior thesis claim
- `earnings` — quarterly results, guidance, revenue/margin/EBITDA
- `none` — default when no lens applies

## Provenance rules

1. Only public-source news goes into `data/`. A private feed's raw payload never
   enters the repo.
2. `url` must resolve to a public source or be marked clearly in `notes` as
   unverified if it cannot.
3. Append-only: new items go at the end of the current day's file. Never rewrite
   history.
4. `captured_at` is set at capture time and is authoritative for ordering.
5. The same story captured by two sources is two items with different `url`/`source`;
   dedup happens on the content `id` (`ticker, url, headline, published_at`), which is
   stable across capture runs.
