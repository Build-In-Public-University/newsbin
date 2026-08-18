# Newsbin

A collective repository for stock-market news that might be of interest, pushed by
people and agents. Each pushed item is a small structured record; the repo is the
shared inbox we can then scan for thesis-relevant signal (operating-metric
improvement while scaling, human-time-saved claims, verification gaps, etc.).

This is a shared news inbox, not a thesis ledger and not investment advice. The
formal thesis commitments live in the Axiom workspace; this repo feeds that work.

## Why

The "Proximity to the Future Fund" thesis cares about a specific kind of signal:
companies implementing transformations that take time, where the market cannot
differentiate marketing buzz from actual knowhow, but practitioners can. This repo
collects raw news items we can then filter through that lens and build case files
around (the OPEN / Opendoor case study is the template).

## How to contribute

Push a single JSON line into a dated file under `data/`. One item per line.
Append-only; never rewrite or delete a historical line. Prefer small, frequent,
sourced pushes over giant dumps.

Minimal valid item:

```json
{"ticker":"OPEN","company":"Opendoor","headline":"...","url":"https://...","source":"WSJ","captured_at":"2026-08-17T00:00:00Z"}
```

See `SCHEMA.md` for all fields and the provenance rules.

## Pipeline

Newsbin is stage one of a three-stage pipeline that turns raw news into
falsifiable claims and then into Axiom formal commitments:

```
newsbin/data → claims/ledger.jsonl → Axiom
```

See `docs/PIPELINE.md` for the full description of the claims ledger
(`claims/process.py`) and the Axiom formalization stage.

## Layout

```
newsbin/
├── README.md
├── SCHEMA.md          # item schema + provenance rules
├── watchlist.json     # tickers we care about (machine-readable)
├── scanner/
│   └── scan.py        # example scanner (thesis-signal scoring + dedup + append)
├── data/
│   └── YYYY-MM-DD.jsonl   # dated news items (append-only)
└── receipts/          # scanner run receipts (source, counts, dedup)
```

## Scanner

`scanner/scan.py` is a reference implementation of a *push source*: it fetches news
for the watchlist, scores each item against the thesis lens, dedups against what is
already in the repo, and appends new items to the daily file. It is deliberately
simple — the point is to show one working way to push into the repo, not to be the
only way. People and other agents can push by hand or via their own scripts.

Run locally:

```bash
python3 scanner/scan.py --watchlist watchlist.json --data-dir data --limit 5
```

Requires `requests`. See `scanner/README.md`.

## Public / private boundary

- `data/` holds public-source news. Only items citing a public source go here.
- Do not commit private raw social archives, brokerage ledgers, or credentials.
- `receipts/` records what a scanner run did (source, fetched count, dedup count),
  never the raw payload of a private feed.
