---
name: close-session
description: Orderly end of a work session. Use it when the user says "closing the session", "that's it for today", "I'm leaving" or similar, and on your own initiative after finishing a big block of work. Leaves memory, pending items, project files and git up to date so the next session does not start blank.
---

# Close the session

The user says it at the end so that nothing stays loose. Do all of it, in order; skip whatever
does not apply without commenting.

## 1. Review what happened

A short list, for yourself: what was done, what was decided and why, what was learned, what is
left half done. What only mattered inside the conversation is not saved.

## 2. Memory

For each decision with its reason, new preference, odd device behaviour or hard-won procedure,
apply the `memory-keeping` skill:

- If a note on the topic exists, **fix it**; do not create a second one. Old content goes to `## Before`.
- If it is new: one fact per file, `verified` set to today, a line in the index of its area.
- **Link**: every new note links with `[[ ]]` to its project or topic, and the project note links
  back. Do not repeat what another note says; link it.
- Do not write what the inventory already knows, or anything readable from the code.
- A repeatable procedure is a new skill, not a note.

## 3. PENDING.md

Add what is waiting for a decision or unfinished; **remove** what closed. The file must stay
short: detail lives in the note, here only a link and the action.

## 4. Project files

If you worked on a project, bring its README, changelog, docs and internal notes up to date,
without contradictions between them (`grep` before closing).

## 5. Cold review

For complex or long work, launch a subagent **without the session's context** to critically
review the documented result. Check what it says and fix what is true. Not needed for small changes.

## 6. Check and push

- `bin/health.py` clean (or say which defect predates this session).
- Commit and push the brain, and check it went up: `git status -sb` must not say `ahead`.

## 7. Farewell

- If the memory system itself stumbled for real, **one** improvement proposal in two or three
  sentences (rules in `memory-keeping`).
- If the session was long, suggest continuing in a new one.
- Answer in a few lines: what was saved and where, and what is pending. No file dumps.
