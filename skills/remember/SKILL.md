---
name: remember
description: Save something to the brain right now. Use it when the user says "remember this", "note this down", "don't forget", "keep it for next time", or asks to see or correct what is already remembered.
---

# Remember

The user wants something to survive this conversation. Do it **before moving on**: if the
session is cut, it is lost.

## If asked to save something

1. Decide where it goes, using the rules of the `memory-keeping` skill:
   - a fact, a decision or a preference: a note in `memory/`
   - a repeatable procedure: a new skill in `skills/`
   - something half done or waiting for their decision: a line in `PENDING.md`
   - something the machine already knows (addresses, RAM, ports): **do not save it**, it is in `inventory/`
2. Before creating a note, `grep` `memory/` in case one exists that should be updated. Two notes
   that contradict each other are worse than one outdated note.
3. Write the note with complete frontmatter (`verified` set to today, `status: current`), add
   the line to the index of its area (`memory/index-*.md`, never `MEMORY.md`), and link it from
   related notes with `[[name]]`.
4. Run `bin/health.py` to make sure the index is not out of step and no link is broken.
5. Confirm in one line what was saved and where. Do not show the whole file.

## If asked what is remembered

```bash
grep -i "<topic>" memory/index-*.md
grep -ril "<topic>" memory/
```

Summarise what you find in your own words; do not dump raw markdown.

## If told that something remembered is wrong

Fix it at once. Edit the existing note (do not create a second one), move the old content to a
`## Before` section if it deserves keeping, and set `verified` to today. Having been corrected is
the strongest sign that this had to be stored properly.
