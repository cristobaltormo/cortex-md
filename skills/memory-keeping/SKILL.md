---
name: memory-keeping
description: How to write, correct and curate the brain's memory. Use it when saving something the user wants remembered, when a note contradicts reality, when looking for what is already known about a project, or when running as the nightly curator.
---

# Keeping the brain

The brain directory is a git repo with three layers. Before writing anything, decide which one:

| Goes in | When |
|---|---|
| `inventory/` | **You never write it.** `bin/inventory.sh` generates it from the machine. |
| `memory/` | A fact, a decision, a reason or a preference that exists only because a conversation happened. |
| `skills/` | A repeatable **procedure**: "how X is done here". Loaded only when needed. |

The most expensive mistake is putting in `memory/` something the inventory derives by itself
(addresses, RAM, ports, which container exists). It ages silently and you end up stating false
things with full confidence. Store the **why**, not the **how much**.

## Note format

One file, one fact. kebab-case name. Frontmatter:

```markdown
---
name: example-decision
description: One line; this is what gets read when deciding whether the note is relevant
metadata:
  type: user | feedback | project | reference
  verified: 2026-01-15
  status: current | historical
  entities: web-1, db-1
---

The fact, in short concrete prose.

**Why:** the reason it was decided this way (feedback and project notes only).
**How to apply:** what to do with this next time.

Related: [[other-note]].
```

- `verified` is the date you **checked** it is still true, not the date you wrote it. If you did
  not check it, do not bump it.
- If the note claims that something works or is verified, say what it was checked with (a
  number, a concrete case, a command). "Tested end to end" without figures is useless to your
  future self. Equally, if it was tested in only one case, say so.
- `status: historical` is for what was true and no longer is. **Do not delete**: knowing that
  something was tried and dropped is worth as much as knowing what exists now. Say what replaced
  it. `status: archived` is the same for a closed project that lives in an `archived-*` index.
- `entities` is optional and lists the container or machine names the note is about.
  `bin/health.py` flags the note when one of them vanishes from the inventory.
- Link with `[[name]]` freely: a link to a note that does not exist yet marks something worth
  writing.

After creating or renaming a note, add its line (`- [Title](file.md) - short hook`) to the index
of its area (`memory/index-*.md`), **not to `MEMORY.md`**. `MEMORY.md` is loaded whole in every
session and carries only the essential notes plus links to the area indexes.

**Always link.** Every new note ends with `Part of: [[hub]]` or `Related: [[a]], [[b]]`, and
links in its body the notes it depends on instead of repeating their content. `bin/health.py`
warns about notes with no links, and the per-message hook also suggests the notes linked from the
most likely one.

Then run **`bin/health.py`**: it checks that the index matches the files, that there are no
broken links, that every note has `verified`, that none has grown unreadable, and that no
credential slipped in. If it is clean, you finished well.

## What is half done goes to PENDING.md

`PENDING.md` lists open fronts and **is loaded at the start of every session**. It holds things
waiting for the user's decision or left unfinished, not accomplished facts (those go in
`memory/`). When something closes, remove it: it stays in git history, and the file has to stay
short to be of any use. A section named "Parked" is summarised to names only.

## When to write

During the session, as soon as it appears. At the end of a long conversation, review: was there
a decision with a reason, a new preference, a device that misbehaves, a procedure that was hard
to discover? Save that. Do not save what is in the code, what the inventory already knows, or
what only mattered inside that conversation.

If a new fact **contradicts** an existing note, do not create a second one: fix the existing one
and move the old content to a `## Before` section in the same file. Two notes that contradict
each other are worse than none.

## Proposing improvements to the memory system itself

The system matures because every real stumble becomes an adjustment. That only happens if, when
it occurs, you tell the user at the moment you notice. Signals that the structure is not coping:

- You lacked a fact you should have had, and you see where it should have been stored.
- A note gave wrong or outdated information, and it is a pattern, not an isolated case.
- Something important did not fit any of the three layers.
- You are repeating yourself: it is the third time the same thing is explained because it is
  written nowhere.
- An automation (curator, `health.py`, hooks) did not do what it should.

Propose it in two or three sentences: what failed, what concrete change would fix it, what it
costs. The user decides: now, noted in `IMPROVEMENTS.md`, or no.

With a brake: only with concrete evidence from this conversation, never mid-task (mention it at
the end), at most one proposal per conversation (the rest go to `IMPROVEMENTS.md` without
asking), and if the answer is no, record the "no" with a date in the relevant note so it is not
proposed again within a month.

## When you run as the curator (nightly cron)

1. Read the day's transcripts. The curator prompt lists them with `agent<TAB>path`; run
   `bin/transcripts.py --days 1` to list them yourself. They come from Claude Code, Antigravity CLI and
   Codex CLI. Use `Grep` and `Read` with an offset rather than reading whole files.
2. Extract **only** what meets the criteria above. Most days that is zero or one note.
3. Re-verify: for each note whose `verified` is over 30 days old and that can be checked from
   this host, check it. If still right, bump `verified`. If not, correct the note and say in the
   commit what changed.
4. Merge duplicates and split any note past ~6 KB: a note that cannot be read in one sitting is
   not memory, it is an archive.
5. `git add -A && git commit` with a message saying what you learned or corrected.

Be conservative: **correcting and consolidating is worth more than accumulating**. Forty true
notes beat three hundred of which none can be trusted.

## Searching before answering

```bash
grep -ril "word" memory/
grep -i "word" memory/index-*.md
```

At this volume, `grep` finds everything. If it ever stops being enough, the answer is to add an
index, not to change systems.
