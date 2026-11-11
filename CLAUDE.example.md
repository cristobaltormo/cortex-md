# Standing instructions

You work on <describe the machine or workspace>. Everything you already know lives in `<path-to-brain>`
(a git repo). It has three layers and each is maintained differently:

| Layer | What it is | Who writes it |
|---|---|---|
| `inventory/` | Real state of the machine: containers, ports, disks, changes | A script, every night. **Never by hand.** |
| `memory/` | Facts, decisions and reasons that exist only because the user told you | You, during sessions, plus the nightly curator |
| `skills/` | Procedures: how each thing is done here | You, when you learn a new procedure |

If you want to know what address a service has, that is in the inventory and true now. If you
want to know why it was set up that way, that is in memory. Never write into memory a fact the
inventory already derives from the machine: it ages and you end up contradicting yourself.

`memory/MEMORY.md` is loaded at session start. Open the area index (`memory/index-*.md`) when the
topic comes up. A hook suggests likely notes on every message; before answering about a project,
**read the whole note**, not just the index line.

## Working rules

- <your hard rules here: language, style, spending limits, what needs approval before production>

## Before ending a session

When the user says they are closing the session, run the `close-session` skill. If something
appeared that your future self would need to know (a decision and its reason, a new procedure, a
preference, a device that misbehaves), write it to memory before it ends. One fact per file, with
`verified` set to today. What is half done or waiting for a decision goes to `PENDING.md`.

Do not save: anything the inventory already knows, anything readable from the code, anything that
only matters inside this conversation.
