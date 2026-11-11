#!/usr/bin/env bash
set -uo pipefail
BRAIN="${BRAIN_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
. "$BRAIN/bin/load-env.sh"
STATE="$BRAIN/state"
LOG="$STATE/notifications.log"
mkdir -p "$STATE"

TITLE="${1:?usage: notify.sh <title> <body> [--no-limit]}"
BODY="${2:?usage: notify.sh <title> <body> [--no-limit]}"
NO_LIMIT="${3:-}"
TODAY=$(date +%F)
LAST="$STATE/last-notification-$(printf '%s' "$TITLE" | md5sum | cut -c1-12)"

if [ -z "${NOTIFY_WEBHOOK_URL:-}" ]; then
  echo "[$(date '+%F %T')] no NOTIFY_WEBHOOK_URL, logged only: $TITLE - $BODY" >> "$LOG"
  exit 0
fi

if [ "$NO_LIMIT" != "--no-limit" ] && [ -f "$LAST" ] && [ "$(cat "$LAST")" = "$TODAY" ]; then
  echo "[$(date '+%F %T')] suppressed (already notified today): $TITLE - $BODY" >> "$LOG"
  exit 0
fi

PAYLOAD=$(python3 -c 'import json,sys; print(json.dumps({"title": sys.argv[1], "body": sys.argv[2]}))' "$TITLE" "$BODY")

HEADER_FILE=$(mktemp)
trap 'rm -f "$HEADER_FILE"' EXIT
chmod 600 "$HEADER_FILE"
echo "Content-Type: application/json" > "$HEADER_FILE"
[ -n "${NOTIFY_AUTH_HEADER:-}" ] && echo "$NOTIFY_AUTH_HEADER" >> "$HEADER_FILE"

CODE=$(curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 60 \
  --retry 3 --retry-delay 5 --retry-all-errors -X POST -H "@$HEADER_FILE" -d "$PAYLOAD" "$NOTIFY_WEBHOOK_URL")

if [ "$CODE" -ge 200 ] && [ "$CODE" -lt 300 ] 2>/dev/null; then
  [ "$NO_LIMIT" != "--no-limit" ] && echo "$TODAY" > "$LAST"
  echo "[$(date '+%F %T')] sent ($CODE): $TITLE - $BODY" >> "$LOG"
else
  echo "[$(date '+%F %T')] FAILED ($CODE): $TITLE - $BODY" >> "$LOG"
  exit 1
fi
