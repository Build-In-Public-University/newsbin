#!/usr/bin/env python3
"""
newsbin claims processor — turns tagged newsbin items into falsifiable claims.

This is the deterministic middle layer between raw news (data/) and Axiom
formalization. It has no hidden LLM calls: candidate drafting is keyword/rule
based, and the user decides which candidates become ledger claims.

Operations:
  scan        — draft candidate claims from tagged newsbin items (no write)
  add         — validate + append a fully-formed claim to claims/ledger.jsonl
  snapshot    — write claims/ledger-snapshot.json summary (no mutation)
  evidence    — append an evidence observation to a claim's record (mutates last line)

Run:
  python3 claims/process.py scan  --data-dir data [--signal earnings]
  python3 claims/process.py add   --statement "..." --falsifier "..." \
      --window 2026-12-31 --metric margin_target:0.36 \
      --source <item_id> [--origin "AcadeResearch"] [--dry-run]
  python3 claims/process.py snapshot --ledger claims/ledger.jsonl
  python3 claims/process.py evidence --ledger claims/ledger.jsonl --claim CLAIM-001 \
      --value 0.315 --source https://... --verdict supports --note "Q3 result"

Requires: standard library only.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LEDGER_DEFAULT = Path(__file__).parent / "ledger.jsonl"
VALID_STATUS = {"open", "partially_confirmed", "failed", "resolved"}
VALID_VERDICT = {"supports", "undermines", "neutral", "falsifier_fired"}
THESIS_SIGNALS = {
    "scaling_efficiency", "human_time_saved", "verification_gap",
    "transformation", "capital_allocation", "earnings", "none",
}


def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_ledger(path):
    if not Path(path).exists():
        return []
    out = []
    for line in Path(path).open():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def load_items(data_dir):
    items = []
    for f in sorted(Path(data_dir).glob("*.jsonl")):
        for line in f.open():
            line = line.strip()
            if line:
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return items


# --- candidate drafting: rule-based, deterministic --------------------------
# Maps a thesis signal to a claim-statement template and a generic falsifier
# direction. This is a scaffold for human drafting, not a substitute for it.
# The output is a *candidate*: it needs a real falsifier, window, and metrics
# before it becomes a ledger claim.
def draft_candidates(items, signal_filter=None):
    candidates = []
    for it in items:
        sigs = it.get("thesis_signal") or ["none"]
        if signal_filter and signal_filter not in sigs:
            continue
        sym = it.get("ticker", "?")
        comp = it.get("company", sym)
        headline = it.get("headline", "")
        # a candidate is only drafted when a thesis signal is present
        active = [s for s in sigs if s in THESIS_SIGNALS and s != "none"]
        if not active:
            continue
        candidates.append({
            "ticker": sym,
            "company": comp,
            "source_items": [it.get("id")] if it.get("id") else [it.get("url")],
            "headline": headline,
            "signals": active,
            "statement_template": (
                f"{comp}: draft a falsifiable claim from this signal "
                f"({', '.join(active)})."
            ),
            "note": "candidate - requires human-authored statement, falsifier, window, metrics",
        })
    return candidates


def claim_exists(ledger, statement, falsifier, window):
    for c in ledger:
        if (c.get("statement") == statement
                and c.get("falsifier") == falsifier
                and c.get("observation_window") == window):
            return c.get("claim_id")
    return None


def next_claim_id(ledger):
    ids = [c.get("claim_id", "") for c in ledger]
    nums = []
    for i in ids:
        m = re.fullmatch(r"CLAIM-(\d+)", i)
        if m:
            nums.append(int(m.group(1)))
    return f"CLAIM-{max(nums, default=0) + 1:03d}"


def validate_claim(claim):
    errs = []
    for field in ("statement", "falsifier", "observation_window"):
        if not claim.get(field):
            errs.append(f"missing required field: {field}")
    if claim.get("status") not in VALID_STATUS:
        errs.append(f"invalid status: {claim.get('status')}")
    if not claim.get("metrics"):
        errs.append("missing required field: metrics (must be a non-empty object)")
    if claim.get("source_items") is None:
        errs.append("missing required field: source_items (may be empty array)")
    return errs


def cmd_scan(args):
    items = load_items(args.data_dir)
    candidates = draft_candidates(items, args.signal)
    print(f"scanned {len(items)} items, {len(candidates)} claim candidates")
    for c in candidates:
        print(f"  [{c['ticker']}] {c['headline'][:70]}")
        print(f"      signals={c['signals']} source={c['source_items'][0]}")
    if not args.dry_run:
        pass  # scan is read-only regardless


def cmd_add(args):
    ledger_path = Path(args.ledger)
    ledger = load_ledger(ledger_path)
    metrics = {}
    for m in args.metric or []:
        if ":" in m:
            k, v = m.split(":", 1)
            try:
                v = float(v)
            except ValueError:
                pass
            metrics[k] = v
        else:
            print(f"warning: metric '{m}' has no ':' - ignored")
    claim = {
        "claim_id": next_claim_id(ledger),
        "statement": args.statement,
        "falsifier": args.falsifier,
        "observation_window": args.observation_window,
        "metrics": metrics,
        "source_items": args.source or [],
        "status": "open",
        "created_at": now_utc(),
        "origin": args.origin or "",
        "author": "human",
    }
    errs = validate_claim(claim)
    if errs:
        print("validation failed:")
        for e in errs:
            print("  -", e)
        sys.exit(1)
    dup = claim_exists(ledger, claim["statement"], claim["falsifier"],
                       claim["observation_window"])
    if dup:
        print(f"dup: identical claim already exists as {dup}")
        sys.exit(1)
    if args.dry_run:
        print(f"[dry-run] would add {claim['claim_id']}")
        print(json.dumps(claim, indent=2))
        return
    with ledger_path.open("a") as f:
        f.write(json.dumps(claim) + "\n")
    print(f"added {claim['claim_id']} to {ledger_path}")


def cmd_snapshot(args):
    ledger = load_ledger(args.ledger)
    by_status = {}
    for c in ledger:
        by_status[c.get("status", "?")] = by_status.get(c.get("status", "?"), 0) + 1
    snap = {
        "generated_at": now_utc(),
        "ledger": args.ledger,
        "total_claims": len(ledger),
        "by_status": by_status,
        "claims": ledger,
    }
    out = Path(args.out)
    out.write_text(json.dumps(snap, indent=2))
    print(f"snapshot written to {out}: {len(ledger)} claims, {by_status}")


def cmd_evidence(args):
    ledger_path = Path(args.ledger)
    if not ledger_path.exists():
        sys.exit("ledger not found")
    if args.verdict not in VALID_VERDICT:
        sys.exit(f"invalid verdict: {args.verdict}")
    lines = ledger_path.read_text().splitlines()
    ev = {
        "observed_at": args.observed_at or now_utc(),
        "source": args.source,
        "value": args.value,
        "verdict": args.verdict,
        "note": args.note or "",
    }
    found = False
    out = []
    for line in lines:
        if not line.strip():
            continue
        c = json.loads(line)
        if c.get("claim_id") == args.claim:
            found = True
            c.setdefault("evidence", []).append(ev)
            if args.status:
                if args.status not in VALID_STATUS:
                    sys.exit(f"invalid status: {args.status}")
                c["status"] = args.status
        out.append(json.dumps(c))
    if not found:
        sys.exit(f"claim not found: {args.claim}")
    if args.dry_run:
        print(f"[dry-run] would append evidence to {args.claim}:")
        print(json.dumps(ev, indent=2))
        return
    ledger_path.write_text("\n".join(out) + "\n")
    print(f"appended evidence to {args.claim}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("scan")
    p.add_argument("--data-dir", default="data")
    p.add_argument("--signal", choices=sorted(THESIS_SIGNALS), default=None)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_scan)

    p = sub.add_parser("add")
    p.add_argument("--ledger", default=str(LEDGER_DEFAULT))
    p.add_argument("--statement", required=True)
    p.add_argument("--falsifier", required=True)
    p.add_argument("--window", dest="observation_window", required=True)
    p.add_argument("--metric", action="append", default=[])
    p.add_argument("--source", action="append", default=[])
    p.add_argument("--origin", default="")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("snapshot")
    p.add_argument("--ledger", default=str(LEDGER_DEFAULT))
    p.add_argument("--out", default="claims/ledger-snapshot.json")
    p.set_defaults(func=cmd_snapshot)

    p = sub.add_parser("evidence")
    p.add_argument("--ledger", default=str(LEDGER_DEFAULT))
    p.add_argument("--claim", required=True)
    p.add_argument("--value", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--verdict", choices=sorted(VALID_VERDICT), default="supports")
    p.add_argument("--note", default="")
    p.add_argument("--observed-at", dest="observed_at", default="")
    p.add_argument("--status", choices=sorted(VALID_STATUS), default=None)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_evidence)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
