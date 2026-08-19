#!/usr/bin/env python3
"""
Downstream-compression instrument for CLAIM-006 (outcome hypothesis).

The two prior proxies tested whether framing predicts RETENTION (target replies
again). Both were null. This tests the OUTCOME the simulation's frame_driven
rule actually rewarded: does receiving a frame REDUCE the target's downstream
processing cost? Measured as compression of the target's own future output.

Hypothesis: after B receives a framed reply from A, B's own next reply to
another tweet should be SHORTER and MORE SEMANTICALLY DENSE (the frame reduced
B's cost to evaluate/respond) than after receiving an echo reply or with no
prior reply.

Design (temporal, non-circular):
  Predictor (t0):  A replies to B, scored framed (semantic novelty >= thr) or echo.
  Outcome (t>t0):  B's immediately-following reply to a DIFFERENT tweet. Measure:
                     - length (characters) - compression proxy
                     - semantic density (embedding norm stays ~1; we use
                       information-per-char via token uniqueness, and length)

Controls: B's own baseline reply length; compare framed-received vs
echo-received vs no-prior-received conditions.

Label: proxy_test_not_referent_measurement.

Usage:
  python3 scanner/downstream_compression.py --parquet <path> [--sample N]
      [--window-start ...] [--window-end ...]
"""

import argparse
import json
import random
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import duckdb
import numpy as np
from sentence_transformers import SentenceTransformer

STOP = set("""a an and are as at be but by for from has have he her his i if in
is it its like of on or that the their them they this to was we were what when
which who will with you your not no so do don't you're i'm it's can't im yeah
just really much think know get got would there about out how then""".split())


def content_words(text):
    return [w for w in re.findall(r"[A-Za-z]{3,}", (text or "").lower()) if w not in STOP]


def info_density(text):
    """unique content words per character - crude information density."""
    cw = content_words(text)
    if not cw or not text:
        return 0.0
    return len(set(cw)) / max(len(text), 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", required=True)
    ap.add_argument("--sample", type=int, default=20000)
    ap.add_argument("--window-start", default="2025-01-01")
    ap.add_argument("--window-end", default="2025-06-01")
    ap.add_argument("--frame-threshold", type=float, default=0.6)
    ap.add_argument("--seed", type=int, default=11)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    con = duckdb.connect()
    rows = con.execute("""
        SELECT tweet_id, username, created_at, full_text, reply_to_tweet_id, reply_to_username
        FROM read_parquet(?) WHERE created_at >= ? AND created_at < ?
    """, [args.parquet, args.window_start, args.window_end]).fetchall()

    tweets, replies = {}, []
    for tweet_id, author, ts, text, rto_id, rto_user in rows:
        tweet_id = str(tweet_id)
        if rto_id is None or rto_user is None:
            tweets[tweet_id] = (author, text or "")
        else:
            replies.append((author, rto_user, str(rto_id), ts, text or ""))
    print(f"tweets: {len(tweets)}  replies: {len(replies)}")

    scorable = [r for r in replies if r[2] in tweets and len(r[4]) > 5]
    rng.shuffle(scorable); scorable = scorable[: args.sample]
    print(f"scorable: {len(scorable)}")

    print("loading embedder...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    def embed(texts, batch=128):
        out = []
        for i in range(0, len(texts), batch):
            out.extend(model.encode(texts[i:i+batch], normalize_embeddings=True))
        return np.array(out)

    parents = [tweets[r[2]][1] for r in scorable]
    reply_texts = [r[4] for r in scorable]
    pe = embed(parents); re_ = embed(reply_texts)
    novelty = 1.0 - np.sum(pe * re_, axis=1)

    # For each reply, determine the framing status of the last reply the TARGET
    # received before THIS reply, then compare THIS reply's compression.
    # replies sorted by time
    scorable_sorted = sorted(range(len(scorable)), key=lambda i: scorable[i][3])
    # last received framing status per (target): map target -> most recent
    # prior reply's framing to them
    last_incoming = {}  # username -> ('framed'|'echo'|'none', ts)
    buckets = {"framed": [], "echo": [], "none": []}

    for i in scorable_sorted:
        author, target, rto_id, ts, text = scorable[i]
        status, _ = last_incoming.get(author, ("none", ""))
        # this reply by author is B's (the author's) output; record its metrics
        # under the condition of what author last received
        length = len(text)
        dens = info_density(text)
        buckets[status].append((length, dens, ts))
        # update incoming status for the TARGET based on this reply's framing
        this_is_framed = novelty[i] >= args.frame_threshold
        last_incoming[target] = ("framed" if this_is_framed else "echo", ts)

    print("\n=== RESULT: target's downstream output compression ===")
    for cond in ["framed", "echo", "none"]:
        data = buckets[cond]
        if not data:
            print(f"  {cond:8} n=0")
            continue
        lens = [d[0] for d in data]
        dens = [d[1] for d in data]
        print(f"  {cond:8} n={len(data):6}  mean_len={np.mean(lens):6.1f}  mean_density={np.mean(dens):.4f}")

    # Headline comparison: framed-received vs echo-received output length
    f_len = [d[0] for d in buckets["framed"]]
    e_len = [d[0] for d in buckets["echo"]]
    n_len = [d[0] for d in buckets["none"]]
    f_d = [d[1] for d in buckets["framed"]]
    e_d = [d[1] for d in buckets["echo"]]
    n_d = [d[1] for d in buckets["none"]]

    def mean(x): return sum(x)/len(x) if x else float('nan')
    print("\n=== comparison ===")
    print(f"  len  framed={mean(f_len):.1f}  echo={mean(e_len):.1f}  none={mean(n_len):.1f}")
    print(f"  dens framed={mean(f_d):.4f}  echo={mean(e_d):.4f}  none={mean(n_d):.4f}")
    # compression = framed output shorter than baseline
    if mean(f_len) and mean(n_len):
        comp_vs_none = (mean(f_len) - mean(n_len)) / mean(n_len)
        comp_vs_echo = (mean(f_len) - mean(e_len)) / mean(e_len) if mean(e_len) else float('nan')
        print(f"  framed length vs none: {comp_vs_none:+.3f} (neg=compression)")
        print(f"  framed length vs echo: {comp_vs_echo:+.3f} (neg=compression)")
        verdict = "supports compression hypothesis" if comp_vs_none < -0.02 else "does NOT support (falsifier on proxy)"
        print(f"  verdict: {verdict}")

    # Threshold sweep for robustness (symmetric with the nulls' rigor)
    print("\n=== threshold sweep (compression vs none) ===")
    sweep = {}
    for thr in [0.5, 0.6, 0.7]:
        sw_b = {"framed": [], "echo": [], "none": []}
        last_incoming = {}
        for i in scorable_sorted:
            author, target, rto_id, ts, text = scorable[i]
            status, _ = last_incoming.get(author, ("none", ""))
            sw_b[status].append(len(text))
            last_incoming[target] = ("framed" if novelty[i] >= thr else "echo", ts)
        fl = sw_b["framed"]; nl = sw_b["none"]; el = sw_b["echo"]
        c = (sum(fl)/len(fl) - sum(nl)/len(nl)) / (sum(nl)/len(nl)) if fl and nl else float('nan')
        ce = (sum(fl)/len(fl) - sum(el)/len(el)) / (sum(el)/len(el)) if fl and el else float('nan')
        sweep[thr] = {"comp_vs_none": round(c, 4), "comp_vs_echo": round(ce, 4),
                      "framed_n": len(fl), "echo_n": len(el)}
        print(f"  thr={thr}: framed_n={len(fl):6} echo_n={len(el):5} comp_vs_none={c:+.4f} comp_vs_echo={ce:+.4f}")

    receipt = {
        "instrument": "downstream_compression",
        "parquet": args.parquet,
        "window": [args.window_start, args.window_end],
        "sample": len(scorable),
        "embedder": "sentence-transformers/all-MiniLM-L6-v2",
        "frame_threshold": args.frame_threshold,
        "frame_definition": "semantic novelty >= threshold (1 - cos(reply,parent))",
        "outcome": "target's own next reply length + info density, conditioned on framing status of last reply they received",
        "label": "proxy_test_not_referent_measurement",
        "buckets": {c: {"n": len(buckets[c]), "mean_len": float(mean([d[0] for d in buckets[c]])),
                        "mean_density": float(mean([d[1] for d in buckets[c]]))} for c in buckets},
        "threshold_sweep": sweep,
        "run_at": datetime.utcnow().isoformat() + "Z",
    }
    out = Path("research/downstream-compression-receipt.json")
    out.write_text(json.dumps(receipt, indent=2))
    print(f"\nreceipt written to {out}")


if __name__ == "__main__":
    main()
