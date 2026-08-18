#!/usr/bin/env bash
# newsbin scanner wrapper — run scan, commit new items, push to remote.
# Used by cron on arc-vps as an automated push source.
#
# This wrapper is the "push" half: scan.py appends new items to data/, then this
# script commits them and pushes to origin. It never rewrites history.

set -euo pipefail

REPO_DIR="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$REPO_DIR"

# 1. Ensure we're on main and up to date
git fetch origin >/dev/null 2>&1 || true
git checkout main >/dev/null 2>&1 || true
git pull --rebase origin main >/dev/null 2>&1 || true

# 2. Run the scanner (append-only; adds new items to today's data file)
python3 scanner/scan.py --watchlist watchlist.json --data-dir data --limit 3

# 3. Commit any new data + the run receipt
if git status --porcelain | grep -q .; then
  git add data/ receipts/
  git -c core.hooksPath=/dev/null commit -q -m "newsbin: automated scan $(date -u +%Y-%m-%dT%H:%M:%SZ)" || true
  git push origin main
  echo "pushed new items"
else
  echo "no new items to push"
fi
