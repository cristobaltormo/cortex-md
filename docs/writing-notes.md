# Writing notes

One fact per file. The file name is a kebab-case slug and matches `name:` in the frontmatter.

```markdown
---
name: nas-disk-spindown-quirk
description: The NAS spins its disks down at night, so the first morning read takes about 10 seconds
metadata:
  type: reference
  verified: 2026-11-11
  status: current
  entities: nas
---

The NAS spins down its disks after 30 idle minutes. The first request after a pause blocks for
roughly 10 seconds; it is not a fault and a retry succeeds.

**Why:** power saving was turned on deliberately.
**How to apply:** when a morning health check times out once and then passes, do not raise an alarm.

Part of: [[index-infrastructure]].
```

## Fields

| Field | Meaning |
|---|---|
| `name` | Slug, same as the file name without `.md` |
| `description` | One line. It is what gets shown when the note is suggested, so write it for relevance |
| `type` | `user`, `feedback`, `project` or `reference` |
| `verified` | The date you checked the note is still true. Not the date you wrote it |
| `status` | `current`, `historical` (was true, no longer) or `archived` (closed project) |
| `entities` | Optional. Container or machine names the note is about |

`feedback-*` notes (how the user wants you to work) are exempt from the staleness check: they do
not rot with the machine.

## Types

- **user**: who the user is and how they like answers.
- **feedback**: a correction or a confirmed approach, with the reason.
- **project**: ongoing work and decisions that the code does not show.
- **reference**: where things live, and quirks of devices and services.

## Rules the validator enforces

- Every note is reachable from `MEMORY.md`, through an `index-*.md` if needed.
- A note linked from `MEMORY.md` must not also be listed in an index it reaches (one path in).
- Every `[[link]]` points at a note that exists, and every note links to at least one other.
- Every note has `description` and `verified`; none is older than `BRAIN_STALE_DAYS` (default 90).
- No note exceeds `BRAIN_MAX_NOTE_BYTES` (default 8000): split it by topic.
- No note contains a private key, a GitHub or AWS token, an API key or a password assignment.

## "Verified" means measured

When a note says something works, add what it was checked with: a figure, a case, a command.
"Tested end to end" with no numbers tells your future self nothing. If it was tested in only one
case, say so.

## Changing your mind

If a new fact contradicts a note, fix that note and move the old content to a `## Before` section.
Do not create a second note. Two notes that disagree are worse than none.
