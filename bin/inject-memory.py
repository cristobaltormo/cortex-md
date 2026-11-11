#!/usr/bin/env python3
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

BRAIN = Path(os.environ.get("BRAIN_DIR") or Path(__file__).resolve().parent.parent)
MEMORY = BRAIN / "memory"
SUGGESTIONS = 3
MAX_LINKED = 4
MIN_CANDIDATES = 1
HEADER_WEIGHT = 5
MAX_WORDS = 12
MAX_FREQUENCY = 0.3
MIN_WORD_LENGTH = 4

STOPWORDS = set(
    "about above after again against also because been before being below between both could "
    "does doing down during each every from further have having here himself into itself just "
    "like make more most much only other over please same should since some such than that "
    "their them then there these they this those through under until very want were what when "
    "where which while will with would your yours need needs help show tell give look using "
    "thanks hello always never still maybe".split()
)


def tokens(text):
    return re.findall(r"[^\W\d_]+", text.lower())


def words_of(prompt):
    return {w for w in tokens(prompt) if len(w) > MIN_WORD_LENGTH and w not in STOPWORDS}


def is_index(path):
    return path.name == "MEMORY.md" or path.stem.startswith("index-") or path.stem.startswith("archived-")


def header_and_body(text):
    parts = text.split("\n---", 1)
    return (parts[0], parts[1]) if len(parts) == 2 else ("", text)


def description_of(header):
    match = re.search(r'^description:\s*"?(.*?)"?\s*$', header, re.M)
    return match.group(1) if match else ""


def build_index():
    notes = []
    for path in MEMORY.glob("*.md"):
        if is_index(path):
            continue
        header, body = header_and_body(path.read_text(encoding="utf-8", errors="replace"))
        notes.append((path, Counter(tokens(header)), Counter(tokens(body))))
    return notes


def specific(words, index):
    frequency = {w: sum(1 for _, h, b in index if w in h or w in b) for w in words}
    present = [w for w in words if 0 < frequency[w] <= max(1, int(len(index) * MAX_FREQUENCY))]
    return sorted(present, key=lambda w: frequency[w])[:MAX_WORDS]


def score(words, index):
    notes = []
    for path, header, body in index:
        points = sum(body[w] + HEADER_WEIGHT * header[w] for w in words)
        if points:
            notes.append((points, path))
    return sorted(notes, key=lambda n: -n[0])


def linked_from(path, excluded):
    targets = re.findall(r"\[\[([^\]]+)\]\]", path.read_text(encoding="utf-8", errors="replace"))
    existing = [t for t in dict.fromkeys(targets) if t not in excluded and (MEMORY / f"{t}.md").exists()]
    return existing[:MAX_LINKED]


def main():
    try:
        prompt = json.load(sys.stdin).get("prompt") or ""
    except ValueError:
        return
    words = words_of(prompt)
    if not words:
        return
    index = build_index()
    notes = score(specific(words, index), index)
    if len(notes) < MIN_CANDIDATES:
        return
    lines = ["Memory notes that may be relevant (open them if they fit; do not assume you already know them):"]
    for _, path in notes[:SUGGESTIONS]:
        header, _ = header_and_body(path.read_text(encoding="utf-8", errors="replace"))
        lines.append(f"- {path.stem} - {description_of(header)}")
    suggested = [path.stem for _, path in notes[:SUGGESTIONS]]
    linked = linked_from(notes[0][1], suggested)
    if linked:
        lines.append(f"Linked from {suggested[0]}: " + ", ".join(linked))
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": "\n".join(lines),
        }
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
