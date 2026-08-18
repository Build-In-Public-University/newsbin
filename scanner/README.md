# Scanner

Reference push source for newsbin. Fetches news for the watchlist, scores each
item against the thesis lens, dedups, and appends to `data/YYYY-MM-DD.jsonl`.

## Install

```bash
pip install requests
```

## Run

```bash
# dry-run (no writes, shows what would be added)
python3 scanner/scan.py --watchlist watchlist.json --data-dir data --limit 2 --dry-run

# real run
python3 scanner/scan.py --watchlist watchlist.json --data-dir data --limit 2
```

## What it does

1. Reads `watchlist.json`.
2. Fetches recent headlines per ticker (Yahoo Finance RSS — no API key).
3. Tags each item with `thesis_signal` keywords (scaling_efficiency,
   human_time_saved, verification_gap, transformation, capital_allocation,
   earnings, none).
4. Dedups against every existing item across all `data/*.jsonl`.
5. Appends new items to the daily file, and writes a run receipt to `receipts/`.

## Notes / limitations

- Yahoo Finance RSS is the fetch source: stable, no API key, but headline-only
  (no full article text) and it is a label for sourcing, not verified authorship.
  Swap in a real news API (Finnhub, Alpha Vantage, Polygon) for higher fidelity.
- `source` is derived from the item URL domain.
- Dedup is content-based on `(ticker, url, headline, published_at)`, stable across
  runs. Same story from two sources stays as two items.
- DuckDuckGo HTML scraping was the original source but proved unreliable (serves
  captcha/anomaly pages intermittently); it is kept out of the active path.
