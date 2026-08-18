# Newsbin claims ledger — schema & lifecycle

`claims/ledger.jsonl` turns tagged newsbin items into structured, falsifiable
claims. A claim is a **prediction with a falsifier**, not a measurement and not
a settled conclusion. It stays `open` until the observation window closes and
the outcome ledger scores it.

This is the middle layer of the pipeline:

```
newsbin/data  →  claims/ledger.jsonl  →  Axiom (Statements / User Axioms)
   raw intake      falsifiable claims      formal commitments
```

Newsbin is the *source of claims*; the ledger is where claims become testable;
Axiom is where the user decides a claim becomes an attributed Statement or an
adopted User Axiom.

## Record shape (JSON object, one per line, append-only)

| field | type | required | meaning |
|-------|------|----------|---------|
| `claim_id` | string | yes | stable id, e.g. `CLAIM-001`. Never reused or reassigned. |
| `statement` | string | yes | the falsifiable claim, crisp and single-sentence where possible |
| `falsifier` | string | yes | the observable event/data that would disprove the claim |
| `observation_window` | string | yes | ISO date by which the claim is tested (e.g. `2026-12-31`) |
| `metrics` | object | yes | machine-checkable numbers relevant to the claim (e.g. margin targets) |
| `source_items` | array of string | yes | newsbin item ids (or URLs) that give rise to the claim |
| `status` | string | yes | one of `open` / `partially_confirmed` / `failed` / `resolved` |
| `created_at` | string | yes | ISO-8601 UTC when the claim entered the ledger |
| `evidence` | array | no | appended outcome observations as data arrives |
| `origin` | string | no | report / source / narrative the claim comes from |
| `author` | string | no | `human` or the agent/script that drafted the claim |

## `status` lifecycle

- `open` — claim entered, not yet tested; window not closed.
- `partially_confirmed` — some directional evidence supports it but the window
  is not closed or the falsifier has not been fully cleared.
- `failed` — the falsifier fired / the window closed and the claim did not hold.
- `resolved` — the window closed and the outcome is judged either way. A
  `resolved` claim is either confirmed or failed, never both.

A claim is **not** `resolved` merely because the calendar window passed; it is
`resolved` when an outcome observation has been recorded and adjudicated.

## `evidence` entries

Each appended evidence entry is an object:

| field | type | meaning |
|-------|------|---------|
| `observed_at` | string | ISO date of the observation |
| `source` | string | URL / filing / source of the observation |
| `value` | string/number | what was observed |
| `verdict` | string | `supports` / `undermines` / `neutral` / `falsifier_fired` |
| `note` | string | optional context |

Append-only. Never edit or delete a prior evidence entry or a prior claim line.

## Provenance & boundary

1. A claim's `source_items` must reference newsbin items that actually exist in
   `data/`. If a claim has no newsbin source, mark `origin` and keep `source_items`
   empty rather than inventing an id.
2. Claims are falsifiable predictions. Do not label an observation as a claim, and
   do not label a claim as a measurement.
3. `metrics` holds checkable numbers only — no prose, no unmeasurable targets.
4. The Axiom stage is a separate, user-gated step. A claim in the ledger is not
   automatically a Statement or a User Axiom. The user decides which claims become
   attributed Statements and which become adopted User Axioms, and formalizes them
   in the Axiom workspace with explicit approval of the exact content.
5. Append-only: new claims go at the end; new evidence appends to an existing
   claim's `evidence` array only via a new line is NOT done here — evidence
   appends mutate the last line of that claim id in place (see `process.py`).

## Dedup

`process.py --add` refuses a claim whose `(statement, falsifier, observation_window)`
triple already exists in the ledger. It does not silently merge similar claims.
