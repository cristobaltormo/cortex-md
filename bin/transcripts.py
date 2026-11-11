#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

HOME = Path.home()
BRAIN = Path(os.environ.get("BRAIN_DIR") or Path(__file__).resolve().parent.parent)
AGENTS = ("claude", "antigravity", "codex")
TOPIC_LINES = 60


def roots():
    return {
        "claude": Path(os.environ.get("CLAUDE_PROJECTS_DIR") or HOME / ".claude" / "projects"),
        "antigravity": Path(os.environ.get("GEMINI_HOME") or HOME / ".gemini"),
        "codex": Path(os.environ.get("CODEX_HOME") or HOME / ".codex") / "sessions",
    }


def candidates(agent):
    root = roots()[agent]
    if not root.is_dir():
        return []
    if agent == "claude":
        own = re.sub(r"[^A-Za-z0-9]", "-", str(BRAIN))
        return [p for p in root.glob("*/*.jsonl") if p.parent.name != own]
    if agent == "antigravity":
        return list(root.glob("antigravity*/brain/*/.system_generated/logs/transcript_full.jsonl"))
    return list(root.rglob("rollout-*.jsonl"))


def find(days, agents=AGENTS, skip_session=""):
    found = []
    for agent in agents:
        for path in candidates(agent):
            if skip_session and skip_session in str(path):
                continue
            try:
                age = time.time() - path.stat().st_mtime
            except OSError:
                continue
            if age < days * 86400:
                found.append((age, path, agent))
    return sorted(found, key=lambda item: item[0])


def squash(text):
    return " ".join(text.split())


def claude_text(event):
    if event.get("type") != "user":
        return ""
    content = event.get("message", {}).get("content")
    if isinstance(content, list):
        content = " ".join(p.get("text", "") for p in content if isinstance(p, dict))
    return squash(content) if isinstance(content, str) else ""


def antigravity_text(event):
    if event.get("type") != "USER_INPUT":
        return ""
    content = event.get("content") or ""
    match = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", content, re.S)
    return squash(match.group(1) if match else content)


def codex_text(event):
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else event
    if payload.get("role") != "user":
        return ""
    content = payload.get("content")
    if isinstance(content, list):
        content = " ".join(p.get("text", "") for p in content if isinstance(p, dict))
    return squash(content) if isinstance(content, str) else ""


EXTRACTORS = {"claude": claude_text, "antigravity": antigravity_text, "codex": codex_text}
IGNORED_PREFIXES = ("<", "Caveat:", "[Request", "# AGENTS.md", "# Context from")


def topic_of(path, agent, length=120):
    extract = EXTRACTORS[agent]
    try:
        with path.open(encoding="utf-8", errors="replace") as handle:
            for index, line in enumerate(handle):
                if index > TOPIC_LINES:
                    break
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                text = extract(event)
                if text and not text.startswith(IGNORED_PREFIXES):
                    if len(text) <= length:
                        return text
                    return text[:length].rsplit(" ", 1)[0] + "..."
    except OSError:
        pass
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=float, default=1)
    parser.add_argument("--agent", choices=AGENTS)
    parser.add_argument("--count", action="store_true")
    args = parser.parse_args()
    items = find(args.days, (args.agent,) if args.agent else AGENTS)
    if args.count:
        print(len(items))
        return
    for _, path, agent in items:
        print(f"{agent}\t{path}")


if __name__ == "__main__":
    main()
