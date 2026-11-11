# Configuration

Everything has a default. Set values in the environment or in `.env` at the root of the brain
(gitignored, read line by line, never executed).

| Variable | Default | Used by | Meaning |
|---|---|---|---|
| `BRAIN_DIR` | directory above `bin/` | all scripts | Where the brain lives |
| `CLAUDE_PROJECTS_DIR` | `~/.claude/projects` | `transcripts.py` | Where Claude Code stores transcripts |
| `GEMINI_HOME` | `~/.gemini` | `transcripts.py` | Where Antigravity stores its conversations |
| `CODEX_HOME` | `~/.codex` | `transcripts.py` | Where Codex stores its sessions |
| `CLAUDE_BIN` | `claude` | `curator.sh` | Full path to the CLI; set it for cron |
| `CURATOR_MODEL` | `sonnet` | `curator.sh` | Model for the nightly run |
| `BACKUP_DIR` | unset | `snapshot.py` | Watch the age of the newest file in this directory |
| `BRAIN_STALE_DAYS` | `90` | `health.py` | Days before a note needs re-verification |
| `BRAIN_MAX_NOTE_BYTES` | `8000` | `health.py` | Largest allowed note |
| `NOTIFY_WEBHOOK_URL` | unset | `notify.sh` | Where to POST `{"title", "body"}` JSON |
| `NOTIFY_AUTH_HEADER` | unset | `notify.sh` | A full header line, e.g. `Authorization: Bearer abc` |

## Cron

```cron
0 3 * * *     /path/to/brain/bin/inventory.sh
30 3 * * *    /path/to/brain/bin/curator.sh
*/15 * * * *  /path/to/brain/bin/curator-retry-check.sh
```

## Notifications

`notify.sh` sends one JSON POST to any webhook, at most once per day per title, and logs to
`state/notifications.log` when no webhook is set. It fires on serious machine changes (a new or
vanished container, a failed unit, a filesystem past 85 percent, a stale backup), on a failed push
and when the curator fails two nights running.

## Hooks

`install.sh` adds three hooks and `autoMemoryDirectory` to `~/.claude/settings.json`. To do it by
hand, copy `settings.example.json`, replacing `__BRAIN__` with the absolute path of the brain.
The hooks apply to every project of each installed agent on the machine. Per-agent details are in
[agents.md](agents.md).

## Adding a collector

`bin/snapshot.py` builds the state from small functions (`docker_containers`, `lxc_containers`,
`disks`, `ports`...). Add one that returns a dict and include it in `main()`. Then teach
`compare()` in `bin/changes.py` what a meaningful difference looks like.
