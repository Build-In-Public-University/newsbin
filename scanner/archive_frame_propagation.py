#!/usr/bin/env python3
"""
Frame-propagation instrument for CLAIM-006.

Tests whether a clarifying frame in a reply predicts future cross-referent
engagement - the temporal, non-circular version of the framed-entropy claim.

Design (breaks the circularity trap):
  Predictor (t0):  A replies to B's tweet with a frame. "Frame" = the reply
                   introduces content-words not present in the parent tweet B
                   posted (incremental information). An echo reply introduces
                   few/no new words.
  Outcome (t>t0):  B later replies to a DIFFERENT tweet by A (cross-referent
                   propagation = the frame turned A into a source B engages again).

Falsifier: framed replies predict future cross-referent engagement at the SAME
rate as unframed/echo replies. If echoes propagate just as much, framing is not
the mechanism - engagement is.

This is a PROXY test of the survival half of CLAIM-006, labeled
proxy_test_not_referent_measurement: it does not measure H(unframed)-H(framed)
over the same referent, which the archive cannot provide. It tests whether
framing predicts retention.

Usage:
  python3 scanner/archive_frame_propagation.py --parquet <path> [--min-replies N]
"""

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import duckdb

STOP = set("""a an and are as at be but by for from has have he her his i if in
is it its like of on or that the their them they this to was we were what when
which who will with you your not no so do don't you're i'm it's can't im yeah
just really much think know get got would there about out how then""".split())


def content_words(text):
    words = re.findall(r"[A-Za-z]{3,}", (text or "").lower())
    return [w for w in words if w not in STOP]


def novelty_ratio(reply_text, parent_text):
    """Fraction of reply content-words absent from the parent tweet."""
    rw = content_words(reply_text)
    if not rw:
        return 0.0
    pw = set(content_words(parent_text))
    novel = [w for w in rw if w not in pw]
    return len(novel) / len(rw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", required=True)
    ap.add_argument("--min-replies", type=int, default=3,
                    help="min replies a replier must have to be included")
    ap.add_argument("--frame-threshold", type=float, default=0.5,
                    help="novelty ratio >= this = framed; < = echo")
    ap.add_argument("--window-start", default="2025-01-01")
    ap.add_argument("--window-end", default="2026-06-01")
    args = ap.parse_args()

    con = duckdb.connect()
    p = args.parquet

    print("=== loading window tweets + replies ===")
    rows = con.execute("""
        SELECT tweet_id, username, created_at, full_text, reply_to_tweet_id,
               reply_to_username
        FROM read_parquet(?)
        WHERE created_at >= ? AND created_at < ?
    """, [p, args.window_start, args.window_end]).fetchall()

    tweets = {}      # tweet_id -> (author, text)
    replies = []     # (replier, target, reply_to_tweet_id, ts, text)
    for tweet_id, author, ts, text, rto_id, rto_user in rows:
        tweet_id = str(tweet_id)
        if rto_id is None or rto_user is None:
            tweets[tweet_id] = (author, text or "")
        else:
            replies.append((author, rto_user, str(rto_id), ts, text or ""))

    print(f"  tweets: {len(tweets)}  replies: {len(replies)}")

    # replier activity filter
    replier_count = defaultdict(int)
    for author, *_ in replies:
        replier_count[author] += 1

    # outcome index: for (replier, target) -> sorted [(ts, parent_tweet_id)]
    pair_replies = defaultdict(list)
    for author, target, rto_id, ts, text in replies:
        pair_replies[(author, target)].append((ts, rto_id))
    for k in pair_replies:
        pair_replies[k].sort()

    framed = {"n": 0, "propagated": 0}
    echo = {"n": 0, "propagated": 0}

    print("=== scoring: frame at t0, cross-referent outcome at t>t0 ===")
    for author, target, rto_id, ts, text in replies:
        if replier_count[author] < args.min_replies:
            continue
        parent = tweets.get(rto_id)
        if parent is None:
            continue
        nr = novelty_ratio(text, parent[1])
        bucket = framed if nr >= args.frame_threshold else echo
        bucket["n"] += 1
        # outcome: target replied to author at ts2 > ts on a DIFFERENT parent
        out = False
        for (ts2, rt_parent) in pair_replies.get((target, author), []):
            if ts2 > ts and rt_parent != rto_id:
                out = True
                break
        if out:
            bucket["propagated"] += 1

    def rate(b):
        return b["propagated"] / b["n"] if b["n"] else 0.0

    fr, er = rate(framed), rate(echo)
    print("\n=== RESULT ===")
    print(f"framed replies: {framed['n']}  propagated: {framed['propagated']}  rate: {fr:.4f}")
    print(f"echo   replies: {echo['n']}  propagated: {echo['propagated']}  rate: {er:.4f}")
    lift = (fr - er) / er if er else None
    if lift is not None:
        print(f"lift (framed vs echo): {lift:+.2f}x")
    else:
        print("lift: n/a (echo rate 0)")
    verdict = "supports framing hypothesis" if fr > er else "does NOT support (falsifier on proxy)"
    print(f"verdict: {verdict}")

    receipt = {
        "instrument": "archive_frame_propagation",
        "parquet": args.parquet,
        "window": [args.window_start, args.window_end],
        "min_replies": args.min_replies,
        "frame_threshold": args.frame_threshold,
        "frame_definition": "novelty_ratio = new content words in reply / reply content words",
        "outcome": "target replies to a different future tweet by replier",
        "label": "proxy_test_not_referent_measurement",
        "framed": framed,
        "echo": echo,
        "framed_rate": fr,
        "echo_rate": er,
        "lift": lift,
        "verdict": verdict,
        "run_at": datetime.utcnow().isoformat() + "Z",
    }
    out = Path("research/frame-propagation-receipt.json")
    out.write_text(json.dumps(receipt, indent=2))
    print(f"\nreceipt written to {out}")


if __name__ == "__main__":
    main()
