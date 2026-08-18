# Community archive ticker scan — 2026-08-18

Scanned the local Community Archive enriched-tweets corpus
(`semantic-axis-v0/data/community_archive_global/enriched_tweets.parquet`,
~8.08M rows) for stock-ticker discussion and news-article sharing. This is a
first reconnaissance pass to see whether the community archive is a useful
push source for newsbin. It is not a thesis ledger and not investment advice.

## Coverage

- Corpus: 8,077,872 tweets, ~2024-07 through 2026-06 (dates are `created_at`
  strings, month 2026-06 is incomplete/partial).
- Freshness: this parquet is a June 2026 snapshot; it is NOT live. For current
  pushes use the live Community Archive API / RSS, not this file.

## Cashtag signal (real-stock tickers present)

Top real-stock `$TICKER` mentions (unambiguous uppercase cashtags; crypto/meme
noise like $MARVIN, $LEGO, $CLAWED, $ETH, $BTC excluded from this list):

| ticker | count | users |
|--------|-------|-------|
| GME    | 77    | 33    |
| SPY    | 52    | 7     |
| TWTR   | 34    | 16    |
| TSLA   | 33    | 15    |
| NVDA   | 29    | 12    |
| AAPL   | 22    | 12    |
| NFLX   | 20    | 4     |
| AMZN   | 15    | 11    |
| SPX    | 65    | 2     |

Plus SPX/QQQ/COIN/MSTR/PLTR at lower counts. Crypto/meme cashtags dominate the
overall cashtag list; the equities signal is real but thin.

Users most frequently discussing real-stock cashtags:
DanielleFong (107), 0xptimystic (104), mykola (23), robotNiMA (17),
IgorBrigadir (14), patio11 (8), TheZvi (2), plus leo_guinan (5).

## News-article sharing (sparse)

News-domain URLs shared across the corpus:

| domain | count |
|--------|-------|
| on.wsj.com     | 21 |
| on.cnn.com     | 10 |
| news.yahoo.com | 3  |
| techcrunch.com | 1  |
| uk.reuters.com | 1  |
| www.cnbc.com   | 1  |
| msnbc          | 4  |

Reading: the archive shares few prominent news-domain links directly. Most
outbound links are inline or t.co-shortened. WSJ and CNN are the only news
domains with meaningful volume. This community is not primarily a news-sharer.

## OPEN / Opendoor discussion

Most "opendoor" hits are false positives from `@opendoorforever` (a psychology /
retreat account, unrelated to Opendoor the company). One genuine practitioner
signal found:

- 2026-01-14 justindross: "My last company, Opendoor ($7B), replaced real estate
  brokers. Today, my new company WithCoverage raised $42M to replace…"

That is the kind of practitioner-visible signal the thesis lens is after, and it
did not show up as a `$OPEN` cashtag in volume.

## Interpretation for newsbin

1. The archive is a *weak* direct news-push source — news-domain links are sparse.
2. It is a *useful* signal-discovery source: specific practitioners discussing
   specific equities (and occasionally naming the operating mechanism) are
   findable, e.g. the Opendoor practitioner thread.
3. For volume, live Yahoo/Reuters/WSJ RSS feeds are a better push source (see
   `scanner/`). The archive is best used to catch practitioner-visible,
   low-volume signals that headline feeds miss.

## Boundary

- This is a June-2026 snapshot, not current.
- Cashtag counts are lower bounds (regular tweets only in this parquet; note-tweets
  and community-tweets are in the raw archive, not this table).
- News-domain URL counts are lower bounds because many links are t.co-shortened.
