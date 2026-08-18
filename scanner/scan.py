#!/usr/bin/env python3
"""
newsbin scanner — example push source.

Fetches news for the watchlist, scores each item against the thesis lens,
dedups against what's already in the repo, and appends new items to the
dated data file. Simple by design: the point is to show one working way to
push into newsbin, not to be the only way.

Run:
    python3 scanner/scan.py --watchlist watchlist.json --data-dir data [--limit N] [--dry-run]

Requires: requests
"""

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("Missing dependency: requests. Run: pip install requests")

# --- thesis lens: keyword rules for tagging ---------------------------------
SIGNAL_RULES = {
    "scaling_efficiency": [
        r"gross margin", r"contribution margin", r"margin (improved|expanded|rose)",
        r"quarter over quarter", r"year over year", r"record (quarter|revenue|volume)",
    ],
    "human_time_saved": [
        r"saves? (hours|time|weeks|days)", r"hours (saved|per)", r"productivity",
        r"headcount", r"did in (minutes|seconds|hours)", r"time (saved|savings)",
        r"fewer (people|employees|headcount)", r"x faster",
    ],
    "verification_gap": [
        r"guidance", r"management (said|targets|expects)", r"pre-announc",
        r"preliminary", r"subject to", r"illustrative",
    ],
    "transformation": [
        r"transform", r"restructur", r"turnaround", r"reorg", r"pivot",
        r"shift (to|toward)", r"new direction",
    ],
    "capital_allocation": [
        r"buyback", r"repurchase", r"dilution", r"convertible", r"issuance",
        r"offering", r"notes (due|offering)", r"capital (raise|allocation)",
    ],
    "earnings": [
        r"earnings", r"revenue (of|rose|grew|was)", r"ebitda", r"adjusted net",
        r"eps", r"quarter", r"guidance",
    ],
}

# News domains that look like real sources (used only to label; a URL not on
# this list is still accepted — it just keeps its raw domain).
KNOWN_SOURCES = ["wsj", "reuters", "bloomberg", "cnbc", "cnn", "ft.com", "apnews",
                 "axios", "theinformation", "yahoo", "marketwatch", "seekingalpha",
                 "businessinsider", "techcrunch", "theverge", "fortune", "coindesk"]


def tag_signal(text):
    text_l = text.lower()
    hits = set()
    for signal, patterns in SIGNAL_RULES.items():
        for pat in patterns:
            if re.search(pat, text_l):
                hits.add(signal)
                break
    return sorted(hits) if hits else ["none"]


def item_id(ticker, url, headline, published_at=""):
    return hashlib.sha256(
        f"{ticker}|{url}|{headline}|{published_at}".encode()
    ).hexdigest()[:16]


def fetch_yahoo_rss(symbol, limit=3):
    """Yahoo Finance RSS headline feed for a symbol — no API key. Stable RSS."""
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    r.raise_for_status()
    out = []
    for m in re.finditer(r"<item>(.*?)</item>", r.text, re.S):
        block = m.group(1)
        t = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", block, re.S)
        l = re.search(r"<link>(.*?)</link>", block, re.S)
        p = re.search(r"<pubDate>(.*?)</pubDate>", block, re.S)
        title = t.group(1).strip() if t else ""
        link = l.group(1).strip() if l else ""
        pub = p.group(1).strip() if p else ""
        if title and link:
            out.append({"title": title, "url": link, "published": pub})
        if len(out) >= limit:
            break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--watchlist", default="watchlist.json")
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--limit", type=int, default=2, help="items per ticker")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    wl = json.load(open(args.watchlist))
    tickers = wl["tickers"]

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    daily_file = data_dir / f"{today}.jsonl"

    # Load existing IDs for dedup
    existing_ids = set()
    if daily_file.exists():
        for line in daily_file.open():
            line = line.strip()
            if line:
                try:
                    existing_ids.add(json.loads(line).get("id"))
                except json.JSONDecodeError:
                    pass
    # Also scan the whole data dir so we don't re-add a story from a prior day
    for f in data_dir.glob("*.jsonl"):
        for line in f.open():
            line = line.strip()
            if line:
                try:
                    existing_ids.add(json.loads(line).get("id"))
                except json.JSONDecodeError:
                    pass

    captured_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_items = []
    fetch_fail = []
    fetched_total = 0

    for t in tickers:
        sym = t["symbol"]
        results = []
        # one retry with a short backoff — DDG HTML scraping is flaky
        for attempt in (0, 1):
            try:
                results = fetch_yahoo_rss(sym, limit=args.limit)
                if results:
                    break
            except Exception as e:  # noqa: BLE001
                last_err = e
                time.sleep(1.5)
        if not results:
            fetch_fail.append(f"{sym}: no results ({last_err if 'last_err' in dir() else 'empty feed'})")
            time.sleep(0.4)
            continue
        fetched_total += len(results)
        for res in results:
            # derive source domain
            m = re.search(r"https?://([^/\s]+)", res["url"])
            dom = m.group(1).replace("www.", "") if m else "unknown"
            src = dom.split(".")[0] if not any(k in dom for k in KNOWN_SOURCES) else dom
            sig = tag_signal(res["title"])
            item = {
                "ticker": sym,
                "company": t["company"],
                "headline": res["title"],
                "url": res["url"],
                "source": src,
                "captured_at": captured_at,
                "thesis_signal": sig,
            }
            if res.get("published"):
                item["published_at"] = res["published"]
            item["id"] = item_id(sym, res["url"], res["title"], res.get("published", ""))
            if item["id"] not in existing_ids:
                new_items.append(item)

    # Append
    if args.dry_run:
        print(f"[dry-run] would append {len(new_items)} new items to {daily_file}")
    else:
        with daily_file.open("a") as f:
            for it in new_items:
                f.write(json.dumps(it) + "\n")
        print(f"appended {len(new_items)} new items to {daily_file}")

    if new_items:
        print("\n--- new items ---")
        for it in new_items:
            print(f"[{it['ticker']}] ({','.join(it['thesis_signal'])}) {it['headline']}")

    # Receipt
    receipt = {
        "run_at": captured_at,
        "source": "yahoo_rss",
        "watchlist_size": len(tickers),
        "fetched": fetched_total,
        "new_items": len(new_items),
        "dedup_against": len(existing_ids),
        "fetch_failures": fetch_fail,
    }
    Path("receipts").mkdir(exist_ok=True)
    if not args.dry_run:
        (Path("receipts") / f"scan-{captured_at.replace(':','')}.json").write_text(
            json.dumps(receipt, indent=2)
        )
    print(f"\nreceipt: {json.dumps(receipt, indent=2)}")


if __name__ == "__main__":
    main()
