# bin/

Scripts carry no comments. This is what each does; the reasoning lives in the skills and the READMEs.
Every script finds the brain from its own location, or from `BRAIN_DIR`.

| Script | What it does |
|---|---|
| `session-start.sh` | Start hook: pulls, rescues unsaved changes, refreshes a stale inventory, runs `context.py` |
| `session-end.sh` | End hook: commits and pushes what was written in the brain |
| `context.py` | Start-of-session text: recent conversations, learnings, machine changes, open fronts, warnings |
| `inject-memory.py` | Per-message hook: suggests the likeliest notes and the ones they link to |
| `health.py` | Validator: index, links, dates, sizes, orphans, dead entities, secrets. `--brief` prints defects only |
| `curator.sh` | Nightly curator run through `claude -p`, with quota-aware retry |
| `curator-retry-check.sh` | Cron every 15 minutes; relaunches the curator when its retry time has passed |
| `inventory.sh` | Regenerates `inventory/*.md`, then runs `snapshot.py` and `changes.py` |
| `snapshot.py` | Writes `inventory/state.json`: containers, machines, ports, disks, failed units, backup age |
| `changes.py` | Diffs today's snapshot against yesterday's into `inventory/CHANGES.md` and notifies on serious changes |
| `load-env.sh` | Sourced by the scripts; reads `.env` line by line without executing it |
| `notify.sh` | Webhook push, at most one per day, logged when no webhook is configured |

Environment: `BRAIN_DIR`, `CLAUDE_PROJECTS_DIR`, `BACKUP_DIR` (watch a backup folder's age),
`CURATOR_MODEL`, `CLAUDE_BIN`, `BRAIN_STALE_DAYS`, `BRAIN_MAX_NOTE_BYTES`, `NOTIFY_WEBHOOK_URL`, `NOTIFY_AUTH_HEADER` (full header line, e.g. `Authorization: Bearer abc`). The variables can also be set in `.env`. The notification limit is one per day per title.
