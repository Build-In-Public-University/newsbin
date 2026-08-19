# Archive frame-propagation instrument (CLAIM-006 proxy test)

First measured attempt at the framed-entropy claim (CLAIM-006) using the
Community Archive. This is a **proxy test** of the survival half of the claim,
not a measurement of H(unframed) − H(framed) over the same referent.

## Design

Breaks the circularity trap by separating predictor and outcome in time and
referent:

- **Predictor (t0):** A replies to B's tweet. The reply is "framed" if it
  introduces ≥50% new content-words not present in B's parent tweet (novelty
  ratio); it is an "echo" if it mostly restates the parent.
- **Outcome (t>t0):** B later replies to a **different** tweet by A
  (cross-referent propagation — the frame turned A into a source B engages
  again).

## Result (2025-01-01 → 2026-06-01, Community Archive)

- tweets loaded: 983,125; replies: 648,590
- framed replies: 178,390 → propagated 115,182 → **rate 0.646**
- echo replies: 2,815 → propagated 1,988 → **rate 0.706**
- lift (framed vs echo): **−0.09×**
- **verdict: does NOT support the framing hypothesis on this proxy**

## Honest caveats

1. **Bucket imbalance.** The ≥0.5 novelty threshold labeled ~98% of replies
   "framed" (178k vs 2.8k echo), because most genuine replies introduce some new
   content. The echo bucket is thin, so its 70.6% is noisier.
2. **No threshold-tuning to favor the thesis.** The as-run result stands as a
   published null on this proxy. Tuning the threshold until framed > echo would be
   motivated reasoning.
3. **Label:** proxy_test_not_referent_measurement. The archive lacks referent
   tags, so it cannot measure the true entropy difference. This tests only whether
   framing-as-defined predicts retention — and it does not (on this proxy).

## What this means

The falsifier "a node that removes bits is not retained / framing is not the
mechanism" **fired on this operationalization**. Echo replies propagated at least
as much as framed ones. Either framing isn't the retention mechanism, or the
novelty-ratio proxy is the wrong operationalization of "frame." Both are live
hypotheses; neither is confirmed. This is a miss logged with the same weight as a
hit — per the Faith Friday methodology.

## Receipt

`research/frame-propagation-receipt.json` — full run parameters, counts, rates,
and verdict.
