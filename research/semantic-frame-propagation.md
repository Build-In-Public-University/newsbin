# Semantic frame-propagation instrument (CLAIM-006, second swing)

Embedding-based replacement for the lexical-novelty proxy that returned a null
in the first test. Uses semantic novelty (1 − cos between reply and parent
embeddings) instead of word overlap. Same temporal, non-circular design: frame
in a reply at t0 → does the target reply to a *different* future tweet by the
replier at t>t0.

Label: `proxy_test_not_referent_measurement`.

## Result (2025-01-01 → 2025-06-01, 40k sampled replies, all-MiniLM-L6-v2)

Ran across three thresholds to check robustness, not cherry-pick:

| threshold | framed | framed rate | echo | echo rate | lift |
|-----------|--------|------------|------|-----------|------|
| 0.5 | 29,684 | 0.3775 | 3,914 | 0.4269 | −0.12× |
| 0.6 | 25,785 | 0.3724 | 7,813 | 0.4189 | −0.11× |
| 0.7 | 20,479 | 0.3628 | 13,119 | 0.4151 | −0.13× |

**The falsifier fired on the semantic proxy too.** Echo replies propagated MORE
than framed replies at every threshold (−0.11x to −0.13x lift). The result is
threshold-robust, so it is not an artifact of where we set the framing cutoff.

## What this means — and what it doesn't

Two independent operationalizations of "frame" (lexical novelty, semantic
novelty) both fail to predict cross-referent retention. Combined with the
observability simulation (which showed a *true* framing mechanism would be
observability-robust), this is now converging on one of two live hypotheses:

1. **Framing (as measured by novelty of the reply content) is not the retention
   mechanism.** Who gets replied to may be driven by reciprocity, social
   connection, prior relationship, or platform surfacing — not by whether the
   reply introduced new content, semantically or lexically.
2. **The outcome metric is the weak link.** "Target later replies to a different
   tweet by the replier" may be the wrong measure of the value a frame creates.
   The simulation's frame_driven rule rewarded a *processing-cost reduction*,
   which cross-referent reply-count only approximates poorly.

The semantic swing does NOT support the framed-entropy claim on this proxy. It
does not falsify the underlying idea — it narrows it: either the frame must be
measured as something other than reply-content novelty (e.g., actual compression
of downstream evaluation cost), or the retention outcome must be redefined.

## Honest caveats

- Bucket imbalance at 0.5 (29.7k framed vs 3.9k echo) driven by right-skewed
  novelty (median 0.76 — most genuine replies semantically re-encode). Reported
  at 0.6 and 0.7 to show the finding holds at balanced buckets too.
- The novelty distribution being right-skewed is itself informative: most
  replies to a parent ARE semantically distinct. So "framing" by novelty is the
  modal behavior, not the exceptional one — which may be why it doesn't
  discriminate retention.
- This is a proxy test. The archive lacks referent tags, so it cannot measure
  true H(unframed) − H(framed) over the same referent.

## Receipt

`research/semantic-frame-propagation-receipt.json` — all thresholds, counts,
rates, verdict.
