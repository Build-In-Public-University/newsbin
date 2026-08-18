# Newsbin → Claims → Axiom pipeline

This repo is the middle of a three-stage pipeline for turning raw market news
into falsifiable, formally-tracked claims.

```
newsbin/data       →  claims/ledger.jsonl   →  Axiom
raw intake             falsifiable claims       formal commitments
(scanner + pushes)     (process.py)             (Statements / User Axioms)
```

## Stage 1 — newsbin/data (raw intake)

Dated `data/YYYY-MM-DD.jsonl` files hold news items pushed by the VPS scanner
and by hand. Each item is tagged with `thesis_signal` vocabulary. This is the
*source* of claims, not claims itself. Append-only.

## Stage 2 — claims/ledger.jsonl (falsifiable claims)

`claims/process.py` turns tagged items into structured, falsifiable claims. A
claim is a **prediction with a falsifier**, not a measurement. Each record
carries: claim_id, statement, falsifier, observation_window, metrics,
source_items, status, and an evidence array that gets appended as the window
closes.

Lifecycle: `open` → `partially_confirmed` / `failed` / `resolved`, driven by
`process.py evidence` appends. Nothing is `resolved` until an outcome is
adjudicated against the falsifier.

See `claims/SCHEMA.md`.

## Stage 3 — Axiom (formal commitments)

Claims the user decides to formalize move into the Axiom workspace. The shape
depends on the kind of claim:

- **Falsifiable predictions under test** (have a falsifier + window) → Axiom
  `Statement`s. A Statement attributes the claim to you at a timestamp without
  endorsing it as settled truth — the honest form for a prediction that has a
  declared falsifier.
- **Claims you actually hold as actual commitments** → Axiom `User Axioms`
  (e.g. the Proximity Fund Pod thesis, the HumanPower Index thesis).

A claim in the ledger is NOT automatically a Statement or User Axiom. The user
decides, and formalizes with explicit approval of the exact content.

## Keeping provenance

Every claim's `source_items` references newsbin item ids in `data/`, and when it
is formalized in Axiom the Statement text should name its origin (report, source,
and claim_id) so the chain news → claim → Axiom is traceable end to end.
