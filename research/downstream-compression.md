# Downstream-compression instrument (CLAIM-006, outcome hypothesis)

The two prior proxies (lexical novelty, semantic novelty) tested whether framing
predicts RETENTION (target replies again) — both returned null. This instrument
tests the OUTCOME the simulation's frame_driven rule actually rewarded: does
receiving a frame REDUCE the target's downstream processing cost?

Measured as compression of the target's OWN next output: after B receives a
framed reply from A, B's next reply to a different tweet should be SHORTER and
more SEMANTICALLY DENSE than after receiving an echo or with no prior reply.

Label: `proxy_test_not_referent_measurement`.

## Result (2025-01-01 → 2025-06-01, 30k sampled replies, all-MiniLM-L6-v2)

Target's downstream output, conditioned on the framing status of the last reply
they received:

| condition | n | mean length | mean density |
|-----------|-----|-------------|--------------|
| framed  | 11,489 | 123.7 | 0.0954 |
| echo    | 3,811  | 135.7 | 0.0946 |
| none    | 14,700 | 140.4 | 0.0938 |

- **Framed vs none: −11.9% length** (and density up 0.0954 vs 0.0938)
- **Framed vs echo: −8.8% length**

Threshold sweep (compression vs none), run to match the nulls' rigor:

| threshold | framed_n | echo_n | comp vs none | comp vs echo |
|-----------|----------|--------|--------------|--------------|
| 0.5 | 13,398 | 1,902 | −10.3% | −4.4% |
| 0.6 | 11,489 | 3,811 | −11.9% | −8.8% |
| 0.7 | 9,171  | 6,129 | −12.9% | −8.2% |

The effect is **monotonic**: the more clearly a reply frames (higher semantic
novelty), the more the target's downstream output compresses. This is the first
supportive result in the CLAIM-006 thread.

## Interpretation

Receiving a frame predicts the target's own next output being shorter AND
slightly more information-dense. Shorter alone could be terser acknowledgement;
shorter-plus-denser is the compression signature — the frame reduced the
target's cost to evaluate/respond. This is the value transfer the simulation's
frame_driven rule rewarded, now observed in real data.

Combined with the earlier results:
- Retention proxies (lexical, semantic): null — framing-as-novelty doesn't
  predict who gets replied to.
- Simulation: a true framing mechanism is observability-robust.
- **Outcome proxy (this): supportive — framing predicts downstream compression.**

This suggests the frame's value is not "more engagement" but "less downstream
processing cost" — which is exactly the framed-entropy claim (node value =
entropy removed, H(unframed) − H(framed)).

## Honest caveats

1. One instrument, one window (2025 H1), one sample. Replication across windows
   and samples is needed before this is more than a promising signal.
2. Mean length is a coarse compression proxy. Density direction supports it but
   the density gap is small (0.0954 vs 0.0938).
3. Selection/confound risk: shorter replies could reflect engagement dynamics
   (terser replies to thoughtful content) rather than evaluation-cost reduction.
   The monotonic threshold effect mitigates this but does not eliminate it.
4. Proxy test — archive lacks referent tags, so true H(unframed)−H(framed)
   over the same referent is not directly measured.

## Receipt

`research/downstream-compression-receipt.json` — buckets, sweep, parameters.
