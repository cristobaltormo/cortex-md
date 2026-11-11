#!/usr/bin/env bash
set -euo pipefail
BRAIN="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTS="auto"
while [ $# -gt 0 ]; do
  case "$1" in
    --agents) AGENTS="${2:?--agents needs a value}"; shift 2 ;;
    -h|--help) echo "usage: install.sh [--agents auto|all|claude,codex,antigravity]"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 1 ;;
  esac
done

command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 1; }
command -v git >/dev/null || { echo "git is required" >&2; exit 1; }
command -v flock >/dev/null || { echo "flock is required (util-linux)" >&2; exit 1; }

[ -d "$BRAIN/.git" ] || git -C "$BRAIN" init --quiet
chmod +x "$BRAIN"/bin/*.sh "$BRAIN"/bin/*.py "$BRAIN/install.sh"

python3 "$BRAIN/bin/install-hooks.py" --brain "$BRAIN" --agents "$AGENTS"

"$BRAIN/bin/inventory.sh" || true
"$BRAIN/bin/health.py" || true

cat <<MSG

Installed.

Next:
  1. Copy INSTRUCTIONS.example.md to the file your agent reads and edit it:
       Claude Code: CLAUDE.md    Codex CLI: AGENTS.md    Antigravity: GEMINI.md or AGENTS.md
  2. Add the nightly jobs to your crontab (cron has a minimal PATH: set CLAUDE_BIN in .env to the full path of claude):
       0 3 * * *     $BRAIN/bin/inventory.sh
       30 3 * * *    $BRAIN/bin/curator.sh
       */15 * * * *  $BRAIN/bin/curator-retry-check.sh
  3. Optional: copy .env.example to .env to get push notifications.
  4. Replace the example notes in memory/ with your own.
MSG
