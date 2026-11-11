#!/usr/bin/env bash
set -euo pipefail
BRAIN="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SETTINGS="${CLAUDE_SETTINGS:-$HOME/.claude/settings.json}"

command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 1; }
command -v git >/dev/null || { echo "git is required" >&2; exit 1; }
command -v flock >/dev/null || { echo "flock is required (util-linux)" >&2; exit 1; }

[ -d "$BRAIN/.git" ] || git -C "$BRAIN" init --quiet
chmod +x "$BRAIN"/bin/*.sh "$BRAIN"/bin/*.py "$BRAIN/install.sh"

mkdir -p "$(dirname "$SETTINGS")"
[ -f "$SETTINGS" ] || echo '{}' > "$SETTINGS"

python3 - "$SETTINGS" "$BRAIN" <<'PY'
import json
import shutil
import sys
import time
from pathlib import Path

settings_path, brain = Path(sys.argv[1]), sys.argv[2]
template = (Path(brain) / "settings.example.json").read_text().replace("__BRAIN__", brain)
wanted = json.loads(template)


def fail(message):
    print(f"install.sh: {message}", file=sys.stderr)
    sys.exit(1)


try:
    current = json.loads(settings_path.read_text() or "{}")
except ValueError as error:
    fail(f"{settings_path} is not valid JSON ({error}); fix it and run again, nothing was changed")
if not isinstance(current, dict):
    fail(f"{settings_path} must contain a JSON object; nothing was changed")
hooks = current.get("hooks")
if hooks is None:
    hooks = current["hooks"] = {}
if not isinstance(hooks, dict):
    fail(f"'hooks' in {settings_path} must be an object; nothing was changed")

original = json.dumps(current, sort_keys=True)
for event, groups in wanted["hooks"].items():
    existing = hooks.setdefault(event, [])
    if not isinstance(existing, list):
        fail(f"hooks.{event} in {settings_path} must be a list; nothing was changed")
    known = {h.get("command") for g in existing if isinstance(g, dict) for h in g.get("hooks", [])}
    for group in groups:
        if not all(h["command"] in known for h in group["hooks"]):
            existing.append(group)

previous_dir = current.get("autoMemoryDirectory")
if previous_dir and previous_dir != wanted["autoMemoryDirectory"]:
    print(f"warning: autoMemoryDirectory was {previous_dir}; replacing it with {wanted['autoMemoryDirectory']}")
current["autoMemoryDirectory"] = wanted["autoMemoryDirectory"]

if json.dumps(current, sort_keys=True) != original:
    backup = settings_path.with_name(f"{settings_path.name}.bak-{time.strftime('%Y%m%d%H%M%S')}")
    shutil.copy2(settings_path, backup)
    settings_path.write_text(json.dumps(current, indent=2) + "\n")
    print(f"settings updated (backup: {backup})")
else:
    print("settings already up to date")
PY

"$BRAIN/bin/inventory.sh" || true
"$BRAIN/bin/health.py" || true

cat <<MSG

Installed. Hooks and autoMemoryDirectory are in $SETTINGS.

Next:
  1. Copy CLAUDE.example.md to the CLAUDE.md Claude Code reads and edit it.
  2. Add the nightly jobs to your crontab (cron has a minimal PATH: set CLAUDE_BIN in .env to the full path of claude):
       0 3 * * *     $BRAIN/bin/inventory.sh
       30 3 * * *    $BRAIN/bin/curator.sh
       */15 * * * *  $BRAIN/bin/curator-retry-check.sh
  3. Optional: copy .env.example to .env to get push notifications.
  4. Replace the example notes in memory/ with your own.
MSG
