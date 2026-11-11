#!/usr/bin/env python3
import json
import os
import re
import select
import subprocess
import sys
import time
from pathlib import Path

import transcripts

BRAIN = Path(os.environ.get("BRAIN_DIR") or Path(__file__).resolve().parent.parent)
CURRENT_SESSION = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
TOPIC_LENGTH = 120
FRONT_LENGTH = 150


def run(*args):
    try:
        return subprocess.run(
            args, cwd=BRAIN, capture_output=True, text=True, timeout=8
        ).stdout.strip()
    except Exception:
        return ""


def ago(seconds):
    minutes = int(seconds // 60)
    if minutes < 60:
        return f"{minutes} min ago"
    hours = minutes / 60
    if hours < 24:
        return f"{hours:.0f} h ago"
    return f"{hours / 24:.0f} days ago"


def shorten(text, length):
    text = " ".join(text.split())
    if len(text) <= length:
        return text
    return text[:length].rsplit(" ", 1)[0] + "..."


def recent_conversations(session, count=3, days=7):
    result = []
    for age, path, agent in transcripts.find(days, skip_session=session)[:count * 3]:
        topic = transcripts.topic_of(path, agent, TOPIC_LENGTH)
        if topic:
            label = "" if agent == "claude" else f" ({agent})"
            result.append(f"- *{ago(age)}*{label}: {topic}")
        if len(result) == count:
            break
    return result


def latest_learnings():
    commits = run(
        "git", "log", "-4", "--format=%s (%ar)",
        "--invert-grep", "--grep=^Rescue:", "--grep=^Session of",
    )
    return [f"- {c}" for c in commits.splitlines()]


def recent_changes(days=2, limit=8):
    path = BRAIN / "inventory" / "CHANGES.md"
    if not path.exists():
        return []
    out, seen = [], 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            seen += 1
            if seen > days:
                break
        elif line.startswith("- ") and seen:
            out.append(line)
    return list(dict.fromkeys(out))[:limit]


def open_fronts():
    path = BRAIN / "PENDING.md"
    if not path.exists():
        return []
    active, parked, section = [], [], ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
        elif line.startswith("- "):
            (parked if section.startswith("Parked") else active).append(line)
        elif line.startswith("  ") and line.strip():
            target = parked if section.startswith("Parked") else active
            if target:
                target[-1] += " " + line.strip()
    result = [shorten(p, FRONT_LENGTH) for p in active]
    names = [
        (m.group(1) if (m := re.match(r"- \*\*([^*]+?):?\*\*", p)) else shorten(p[2:], 40))
        for p in parked
    ]
    if names:
        result.append("- **Parked, no action:** " + ", ".join(names))
    return result


def hours_since(path):
    return (time.time() - path.stat().st_mtime) / 3600


def system_warnings():
    warnings = []
    inventory = BRAIN / "inventory" / "host.md"
    if not inventory.exists():
        warnings.append("no inventory yet: run `bin/inventory.sh`")
    elif hours_since(inventory) > 26:
        warnings.append(f"the inventory is {hours_since(inventory):.0f} h old; refreshing in the background")

    defects = run(str(BRAIN / "bin" / "health.py"), "--brief")
    if defects:
        warnings.append(f"the brain has {len(defects.splitlines())} defect(s): `bin/health.py`")

    if (BRAIN / "state" / "retry-at").exists():
        warnings.append("the curator did not finish last time; it will retry by itself")

    log = BRAIN / "state" / "curator.log"
    if not log.exists():
        warnings.append("the curator has never run: check the cron entry")
    elif hours_since(log) > 72:
        warnings.append(f"the curator has not run for {hours_since(log) / 24:.0f} days: check the cron entry")

    improvements = BRAIN / "IMPROVEMENTS.md"
    if improvements.exists():
        count = len(re.findall(r"^## \d+\.", improvements.read_text(encoding="utf-8"), re.M))
        if count:
            warnings.append(f"{count} improvements to the brain are noted in IMPROVEMENTS.md")
    return [f"- {w}" for w in warnings]


def current_session():
    try:
        if not sys.stdin.isatty() and select.select([sys.stdin], [], [], 0.2)[0]:
            payload = json.loads(sys.stdin.read() or "{}")
            found = payload.get("session_id") or payload.get("conversationId")
            if found:
                return found
    except (ValueError, OSError, AttributeError):
        pass
    return CURRENT_SESSION


def agent_format():
    if "--agent" in sys.argv:
        index = sys.argv.index("--agent")
        if index + 1 < len(sys.argv):
            return sys.argv[index + 1]
    return os.environ.get("BRAIN_AGENT", "claude")


def block(title, lines):
    return [f"**{title}**", *lines, ""] if lines else []


def main():
    lines = [
        *block("Recent conversations", recent_conversations(current_session())),
        *block("What you learned last", latest_learnings()),
        *block("The machine has changed", recent_changes()),
        *block("Open fronts (details in PENDING.md)", open_fronts()),
        *block("System warnings", system_warnings()),
    ]
    if not lines:
        return
    text = "Continuity context (automatic, not a message from the user):\n\n" + "\n".join(lines).strip()
    if agent_format() == "antigravity":
        print(json.dumps({"injectSteps": [{"systemMessage": {"systemMessage": text}}]}))
    else:
        print(json.dumps({
            "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text},
        }))

if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
