#!/usr/bin/env bash
set -uo pipefail
BRAIN="${BRAIN_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
F="$BRAIN/state/retry-at"

[ -f "$F" ] || exit 0
RETRY_EPOCH=$(cat "$F" 2>/dev/null)
[ -n "$RETRY_EPOCH" ] || exit 0
[ "$(date +%s)" -ge "$RETRY_EPOCH" ] || exit 0

rm -f "$F"
exec "$BRAIN/bin/curator.sh"
