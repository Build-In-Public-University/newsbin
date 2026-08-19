#!/usr/bin/env python3
"""
Observability x Engagement simulation for CLAIM-006.

Maps under what observability conditions competing engagement rules produce
similar vs divergent outcomes. This is a ROBUSTNESS instrument, not empirical
validation: it tests "IF framing is the mechanism, does observability flip who
wins?" It does NOT prove framing creates value in the world.

Design:
  Agents: N accounts, each with a frame_richness drawn to mirror the real
          archive distribution (some high-output high-originality, some echo).
  Stream: entropy events arrive over T timesteps. An observing agent either
          frames (compresses -> novel structure, LOW output entropy) or echoes
          (re-emits -> SAME entropy). frame_richness sets P(frames).
  Observability (independent var, 2 models):
    - fanout:       each output seen by a random subset of size floor(frac*N)
    - rank_bias:    an exogenous surface-weight per agent; some agents' outputs
                    surface more regardless of content (the Twitter confound).
  Engagement (mechanism under test, 3 rules):
    - frame_driven:  agents retain sources that REDUCE their processing cost
                     (they saw framed output -> value received).
    - connection:    agents retain pre-existing network ties (who they know).
    - recency:       agents retain whoever surfaced most (pure observability).

Outcome per cell: rank correlation between frame_richness and final influence
(retained weight received). We sweep observability intensity (fanout frac / rank
skew) and report correlation per (model, rule, level).

Label: simulation_not_empirical_validation. Deterministic (seeded).

Usage:
  python3 scanner/observability_engagement_sim.py [--n 80] [--steps 4000]
      [--fanout-levels 0.05,0.2,0.5,1.0] [--rank-levels 1,2,5,20]
"""

import argparse
import json
import random
from datetime import datetime
from pathlib import Path


def rank_corr(xs, ys):
    n = len(xs)
    rx = [sorted(xs).index(v) for v in xs]
    ry = [sorted(ys).index(v) for v in ys]
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = sum((a - mx) ** 2 for a in rx) ** 0.5
    dy = sum((b - my) ** 2 for b in ry) ** 0.5
    if dx == 0 or dy == 0:
        return 0.0
    return num / (dx * dy)


def make_agents(rng, n):
    # frame_richness bimodal: a mass of echo-heavy + a tail of high-originality,
    # mirroring the archive's observed distribution.
    rich = []
    for _ in range(n):
        if rng.random() < 0.65:
            rich.append(rng.betavariate(2, 8))     # echo-leaning
        else:
            rich.append(rng.betavariate(8, 2))     # framing-leaning
    return rich


def run_sim(rng, n, steps, rich, model, level, rule, p_conn=0.06):
    # influence[j] = retained weight pointing at agent j (incoming)
    influence = [0.0] * n

    if model == "fanout":
        fanout = max(1, int(level * n))
    elif model == "rank_bias":
        # level = skew multiplier; surface weight proportional to rank^(1/level)
        weights = [(i + 1) ** (1.0 / level) for i in range(n)]
        total_w = sum(weights)
        surf_p = [w / total_w for w in weights]

    if rule == "connection":
        # static pre-existing ties, independent of frame richness
        ties = [set() for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i != j and rng.random() < p_conn:
                    ties[i].add(j)

    for _ in range(steps):
        source = rng.randrange(n)
        frames = rng.random() < rich[source]
        # who sees it
        if model == "fanout":
            viewers = rng.sample(range(n), fanout)
        else:  # rank_bias
            viewers = [j for j in range(n) if rng.random() < surf_p[source]]
        # value: framed output reduces viewer processing cost
        for v in viewers:
            if v == source:
                continue
            if rule == "frame_driven":
                influence[source] += 1.0 if frames else 0.05
            elif rule == "connection":
                influence[source] += 1.0 if source in ties[v] else 0.0
            elif rule == "recency":
                influence[source] += 1.0  # pure observability
    return influence


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=80)
    ap.add_argument("--steps", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--fanout-levels", default="0.02,0.05,0.15,0.4,1.0")
    ap.add_argument("--rank-levels", default="0.5,1,2,5,20")
    ap.add_argument("--min-steps-per-source", type=int, default=50)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    n = args.n
    rich = make_agents(rng, n)
    fanout_levels = [float(x) for x in args.fanout_levels.split(",")]
    rank_levels = [float(x) for x in args.rank_levels.split(",")]
    rules = ["frame_driven", "connection", "recency"]

    results = []
    print(f"N={n}, steps={args.steps}, seed={args.seed}")
    print(f"frame_richness range: {min(rich):.3f}..{max(rich):.3f}")

    for rule in rules:
        for model in ["fanout", "rank_bias"]:
            levels = fanout_levels if model == "fanout" else rank_levels
            print(f"\n### rule={rule} model={model}")
            for level in levels:
                influence = run_sim(rng, n, args.steps, rich, model, level, rule)
                corr = rank_corr(rich, influence)
                results.append({
                    "rule": rule, "model": model, "level": level,
                    "rank_corr_frame_richness_to_influence": round(corr, 4),
                })
                print(f"  level={level:<5}  corr(frame_richness, influence) = {corr:+.4f}")

    # ---- convergence / divergence summary ----
    print("\n=== CONVERGENCE / DIVERGENCE MAP ===")
    # For each model, compare rules at the extremes
    def cell(model, rule, level):
        for r in results:
            if r["model"] == model and r["rule"] == rule and r["level"] == level:
                return r["rank_corr_frame_richness_to_influence"]
        return None

    for model in ["fanout", "rank_bias"]:
        levels = fanout_levels if model == "fanout" else rank_levels
        lo, hi = levels[0], levels[-1]
        print(f"\n{model}: low obs {lo} vs high obs {hi}")
        print(f"  {'rule':16} {'low':>7} {'high':>7}  relation")
        for rule in rules:
            c_lo = cell(model, rule, lo)
            c_hi = cell(model, rule, hi)
            rel = "same sign" if (c_lo > 0) == (c_hi > 0) else "SIGNS FLIP"
            print(f"  {rule:16} {c_lo:>+7.3f} {c_hi:>+7.3f}  {rel}")

    # Where do frame_driven and recency agree vs diverge?
    print("\n  frame_driven vs recency (do they converge?):")
    for model in ["fanout", "rank_bias"]:
        levels = fanout_levels if model == "fanout" else rank_levels
        for lv in levels:
            f = cell(model, "frame_driven", lv)
            r = cell(model, "recency", lv)
            delta = f - r
            tag = "converge" if abs(delta) < 0.05 else "diverge"
            print(f"    {model} level={lv:<5} frame={f:+.3f} recency={r:+.3f}  delta={delta:+.3f}  {tag}")

    receipt = {
        "instrument": "observability_engagement_sim",
        "label": "simulation_not_empirical_validation",
        "n": n, "steps": args.steps, "seed": args.seed,
        "models": ["fanout", "rank_bias"], "rules": rules,
        "fanout_levels": fanout_levels, "rank_levels": rank_levels,
        "frame_richness_bimodal": True,
        "engagement_rules": {
            "frame_driven": "retain sources that reduce processing cost (framed output)",
            "connection": "retain pre-existing ties",
            "recency": "retain whoever surfaced most (pure observability)",
        },
        "results": results,
        "run_at": datetime.utcnow().isoformat() + "Z",
    }
    out = Path("research/observability-engagement-receipt.json")
    out.write_text(json.dumps(receipt, indent=2))
    print(f"\nreceipt written to {out}")


if __name__ == "__main__":
    main()
