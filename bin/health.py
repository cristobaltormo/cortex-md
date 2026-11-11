#!/usr/bin/env python3
import json
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

BRAIN = Path(os.environ.get("BRAIN_DIR") or Path(__file__).resolve().parent.parent)
MEM = BRAIN / "memory"
SKILLS = BRAIN / "skills"
SNAPSHOT = BRAIN / "inventory" / "state.json"
MAX_BYTES = int(os.environ.get("BRAIN_MAX_NOTE_BYTES", "8000"))
STALE_DAYS = int(os.environ.get("BRAIN_STALE_DAYS", "90"))

SECRETS = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key"),
    (re.compile(r"\bghp_[A-Za-z0-9]{20,}"), "GitHub token"),
    (re.compile(r"\bsk-[A-Za-z0-9]{32,}"), "API key"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key"),
    (re.compile(r"(?i)\b(password|passwd)\s*[:=]\s*\S{6,}"), "password"),
]


def frontmatter(text):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    data = {}
    for line in text[3:end].splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            data[key.strip()] = value.strip().strip('"')
    return data


def is_index(path):
    return path.stem.startswith("index-") or path.stem.startswith("archived-")


def living_entities():
    if not SNAPSHOT.exists():
        return None
    try:
        data = json.loads(SNAPSHOT.read_text())
    except ValueError:
        return None
    names = set(data.get("containers", {})) | set(data.get("machines", {}))
    return names or None


def check_index_reachability(notes, index_text, problems):
    linked = set(re.findall(r"\]\(([^)]+\.md)\)", index_text))
    direct = set(linked)
    pending, seen = list(linked), set()
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        sub = MEM / name
        if sub.exists() and sub.name != "MEMORY.md":
            found = set(re.findall(r"\]\(([^)]+\.md)\)", sub.read_text(encoding="utf-8", errors="replace")))
            for twice in sorted(found & direct):
                problems.append(
                    f"{twice} is linked directly in MEMORY.md AND inside {name}: "
                    f"drop the line from MEMORY.md, {name} already covers it"
                )
            pending.extend(found - seen)
            linked |= found
    names = {p.name for p in notes}
    for orphan in sorted(names - linked):
        problems.append(f"{orphan} is not reachable from MEMORY.md")
    for ghost in sorted(linked - names):
        problems.append(f"MEMORY.md links {ghost}, which does not exist")


def check_note(note, slugs, today, problems):
    text = note.read_text(encoding="utf-8", errors="replace")
    fm = frontmatter(text)
    if not fm:
        problems.append(f"{note.name} has no frontmatter")
    else:
        if not fm.get("description"):
            problems.append(f"{note.name} has no description (the index depends on it)")
        verified = fm.get("verified")
        if not verified:
            problems.append(f"{note.name} has no verified date")
        else:
            try:
                days = (today - datetime.strptime(verified, "%Y-%m-%d").date()).days
                if days > STALE_DAYS and not note.name.startswith("feedback-"):
                    problems.append(f"{note.name} has gone {days} days without being re-verified")
            except ValueError:
                problems.append(f"{note.name} has an unreadable verified date: {verified}")
    if not is_index(note) and not re.search(r"\[\[[^\]]+\]\]", text):
        problems.append(f"{note.name} links to no other note: add a 'Part of' or 'Related' line")
    size = len(text.encode())
    if size > MAX_BYTES:
        problems.append(f"{note.name} is {size // 1000} KB: split it into several notes")
    for target in set(re.findall(r"\[\[([^\]]+)\]\]", text)):
        if target not in slugs:
            problems.append(f"{note.name} links [[{target}]], which does not exist")
    for pattern, what in SECRETS:
        if pattern.search(text):
            problems.append(f"{note.name} seems to contain a {what}: remove it NOW")


def check_dead_entities(notes, problems):
    alive = living_entities()
    if alive is None:
        return
    for note in notes:
        fm = frontmatter(note.read_text(encoding="utf-8", errors="replace"))
        if fm.get("estado") in ("historical", "archived") or fm.get("status") in ("historical", "archived"):
            continue
        listed = [e.strip() for e in fm.get("entities", "").split(",") if e.strip()]
        dead = sorted(e for e in listed if e not in alive)
        if dead:
            problems.append(
                f"{note.name} is about entities that no longer exist ({', '.join(dead)}): "
                f"update it or mark it status: historical"
            )


def check_skills(problems):
    for skill in sorted(SKILLS.glob("*/SKILL.md")):
        fm = frontmatter(skill.read_text(encoding="utf-8", errors="replace"))
        if not fm.get("name"):
            problems.append(f"skills/{skill.parent.name} does not declare a name")
        elif fm["name"] != skill.parent.name:
            problems.append(f"skills/{skill.parent.name}: frontmatter name says '{fm['name']}'")
        if not fm.get("description"):
            problems.append(f"skills/{skill.parent.name} has no description: it will never trigger by itself")


def main():
    problems = []
    if not MEM.is_dir():
        print(f"FAIL: {MEM} does not exist")
        return 1

    notes = sorted(p for p in MEM.glob("*.md") if p.name != "MEMORY.md")
    index = MEM / "MEMORY.md"
    index_text = index.read_text(encoding="utf-8") if index.exists() else ""

    check_index_reachability(notes, index_text, problems)
    slugs = {p.stem for p in notes}
    today = date.today()
    for note in notes:
        check_note(note, slugs, today, problems)
    check_dead_entities(notes, problems)
    check_skills(problems)

    if "--brief" in sys.argv:
        for p in problems:
            print(p)
        return 0

    if not problems:
        print(f"Brain healthy: {len(notes)} notes, index up to date, no broken links.")
        return 0

    print(f"{len(problems)} thing(s) to review in {len(notes)} notes:\n")
    for p in problems:
        print(f"  - {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
