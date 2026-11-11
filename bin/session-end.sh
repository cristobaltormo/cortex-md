#!/usr/bin/env bash
set -uo pipefail
BRAIN="${BRAIN_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$BRAIN" 2>/dev/null || exit 0

git add -A 2>/dev/null
if ! git diff --cached --quiet 2>/dev/null; then
  SUMMARY=$(git diff --cached --name-only | sed 's|^|  |' | head -8)
  git commit --quiet -m "Session of $(date '+%Y-%m-%d %H:%M')

$SUMMARY" 2>/dev/null || true
  if git remote get-url origin >/dev/null 2>&1; then
    if ! timeout 20 git push --quiet -u origin HEAD 2>/dev/null; then
      "$BRAIN/bin/notify.sh" "Brain not pushed" "git push failed; run git -C $BRAIN push" || true
    fi
  fi
fi

echo '{}'
exit 0
