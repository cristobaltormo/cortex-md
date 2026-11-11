#!/usr/bin/env bash
set -uo pipefail
BRAIN="${BRAIN_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$BRAIN" 2>/dev/null || exit 0

if git remote get-url origin >/dev/null 2>&1; then
  timeout 8 git pull --quiet --rebase --autostash 2>/dev/null || git rebase --abort 2>/dev/null || true
fi

if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
  git add -A 2>/dev/null
  git commit --quiet -m "Rescue: changes from a session that did not close cleanly ($(date '+%Y-%m-%d %H:%M'))" 2>/dev/null || true
fi

INV="$BRAIN/inventory/host.md"
if [ ! -f "$INV" ] || [ "$(( $(date +%s) - $(stat -c %Y "$INV") ))" -gt 43200 ]; then
  nohup "$BRAIN/bin/inventory.sh" >/dev/null 2>&1 &
fi

exec python3 "$BRAIN/bin/context.py"
