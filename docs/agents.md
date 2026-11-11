# Supported agents

The brain is plain files, so any agent that can read markdown can use it. What differs is how much
runs automatically. cortex-md has three tiers.

| Agent | Hooks (automatic context) | Skills | Instructions file | Status |
|---|---|---|---|---|
| Claude Code | SessionStart, UserPromptSubmit, SessionEnd | `~/.claude/skills` | `CLAUDE.md` | Tested end to end, including the nightly curator |
| Antigravity CLI | SessionStart, PreInvocation, Stop | `~/.gemini/config/skills.json` entry | `GEMINI.md` or `AGENTS.md` | Hooks verified against a real `antigravity` run |
| Codex CLI | SessionStart, UserPromptSubmit, SessionEnd | `~/.agents/skills` | `AGENTS.md` | Written from the official hooks documentation; not run against a real Codex yet |
| Anything that reads `AGENTS.md` | None | Read the files | `AGENTS.md` | Works by instruction only: no automatic context |

```bash
./install.sh                        # detects the agents installed on this machine
./install.sh --agents all           # or choose: --agents claude,codex,antigravity
```

The installer merges into each agent's own configuration, keeps a timestamped backup of any file
it changes, never overwrites hooks it did not write, and is idempotent.

## What each agent gets

**Claude Code.** Hooks in `~/.claude/settings.json`, `autoMemoryDirectory` pointing at `memory/`,
and each skill linked into `~/.claude/skills`.

**Antigravity CLI.** A hook group named `cortex-md` in `~/.gemini/config/hooks.json`:
`SessionStart` injects the continuity context as a persistent system message, `PreInvocation`
injects the suggested notes as an ephemeral message before every model call, and `Stop` commits the
brain. The brain's `skills/` directory is registered in `~/.gemini/config/skills.json`. Antigravity
reads `GEMINI.md` and `AGENTS.md` from the working directory upward and expands `@[label](path)`
includes, so the instructions file can include `memory/MEMORY.md` directly.

**Codex CLI.** Hooks in `~/.codex/hooks.json` (the output format is the same one Claude Code uses),
skills linked into `~/.agents/skills`. Codex asks you to review new hooks once: run `/hooks` in the
CLI and trust them. If your `~/.codex/config.toml` already defines inline `[hooks]`, Codex uses one
representation per layer and the installer warns you.

## Differences you should know about

- **Stop versus SessionEnd.** Antigravity has no end-of-session event, only `Stop` after each turn.
  The hook runs `session-end.sh --light`: it commits whenever something changed, and pushes in the
  background at most once every five minutes. Codex uses `SessionEnd`, whose timeout is a few
  seconds, so it uses the same light mode.
- **Memory directory.** `autoMemoryDirectory` is a Claude Code setting. Other agents find the notes
  through the instructions file and the per-message suggestions.
- **The curator.** The nightly curator runs through the Claude Code CLI and distils Claude Code
  transcripts. Notes written by the other agents are still re-verified, linted and fixed, but their
  conversations are not mined yet.
- **Hook payloads.** `inject-memory.py` detects the agent from the payload (`prompt` for Claude
  Code and Codex, `lastUserInput` for Antigravity) and answers in the format that agent expects.
  `context.py --agent antigravity` prints the Antigravity format; the default is the Claude Code and
  Codex one.

## Using the brain from an agent without hooks

Put the same instructions file where the agent reads it (`AGENTS.md` covers most of them) and tell
it to read `memory/MEMORY.md` at the start and to follow the `memory-keeping` skill when it writes.
You lose the automatic continuity and the per-message suggestions, and keep everything else.

## Adding another agent

Add an `install_<agent>` function to `bin/install-hooks.py`, a branch in `context.py` and
`inject-memory.py` if its hook output differs, and a test in `tests/test_engine.py`. The engine has
no other agent-specific code.
