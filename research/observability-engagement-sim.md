# Observability × Engagement simulation (CLAIM-006 robustness test)

Simulation instrument testing the framed-entropy claim's *robustness*, not its
truth. It answers: **IF framing is the mechanism, does observability flip who
wins?** It does not prove framing creates value in the world.

Label: `simulation_not_empirical_validation`. Deterministic (seed 42).

## Design

- N=80 agents, each with a `frame_richness` drawn bimodal to mirror the real
  archive distribution (65% echo-leaning, 35% framing-leaning).
- Entropy stream over 4000 steps. An observing agent frames (compresses →
  low output entropy, value to network) with prob = frame_richness, else echoes.
- **Observability** (independent var, 2 models):
  - `fanout`: each output seen by floor(frac×N) random agents.
  - `rank_bias`: exogenous surface weight per agent; some surface regardless of
    content (the Twitter-algorithm confound, modeled explicitly).
- **Engagement rule** (mechanism under test, 3 rules):
  - `frame_driven`: retain sources that reduce your processing cost (saw framed).
  - `connection`: retain pre-existing ties (who you know).
  - `recency`: retain whoever surfaced most (pure observability).
- Outcome: rank correlation between `frame_richness` and final influence
  (retained weight received), swept over observability intensity.

## Results

**frame_driven rule — robust to observability (both models):**
- fanout: corr +0.950 (low obs) → +0.958 (full obs)
- rank_bias: corr +0.520 (low) → +0.910 (high)
- Even at near-zero observability (1 viewer per output), frame-rich agents
  dominate. The mechanism self-reinforces: they frame more often → accumulate
  more value → more retained influence.

**connection rule — frame richness is irrelevant (corr ≈ 0, ±0.05):**
- Influence tracks pre-existing ties, not framing. As designed.

**recency rule — frame richness is irrelevant (corr ≈ 0, noise):**
- Influence tracks pure surfacing, not framing.

**frame_driven vs recency: DIVERGE strongly at every level** (delta +0.43 to
+1.12, all fanout and rank_bias levels).

## What this tells us about the real-archive miss

The real archive test (frame-propagation instrument) returned a falsifier-fired
null: framed replies did NOT predict retention better than echoes.

This simulation narrows what that miss means. **IF framing were the true
mechanism, it would survive low observability** — the sim shows frame-rich
agents dominate even when almost nobody sees them. So the real miss is NOT
explained by "the Twitter algorithm swamps framing at low observability." The
sim says a framing mechanism is observability-robust.

Therefore the miss is more likely one of:

1. **Framing (as operationalized) is not the retention mechanism** — engagement,
   reciprocity, or social connection drives who gets replied to, not whether the
   reply introduced new content. OR
2. **The novelty-ratio proxy was the wrong operationalization of "frame"** —
   the sim's `frame_driven` rule rewards a *real value transfer* (processing
   cost reduced), which lexical novelty only approximates poorly.

The sim cannot distinguish these two (both are consistent with it). That is the
honest limit. It rules out the observability-explains-everything hypothesis and
points the next empirical effort at either a better frame model or a different
mechanism.

## Convergence / divergence summary

- **Convergence:** connection and recency both give frame-richness ≈ irrelevant
  (corr near 0) — they agree framing doesn't drive influence under their rules.
- **Divergence:** frame_driven vs recency diverge at every level; and under
  rank_bias, connection flips sign (low→high obs) while frame_driven stays
  strongly positive.

## Boundary

- Simulation, not empirical validation. It maps where the thesis *would* be
  robust, given its own mechanism; it cannot confirm the mechanism is real.
- `frame_richness` distribution is a modeled bimodal approximation of the
  archive, not the true ontology (we only have output proxies).
- `rank_bias` surface weights are a stylized power-law, not Twitter's actual
  ranking.

## Receipt

`research/observability-engagement-receipt.json` — all cells, parameters, and
correlations.
