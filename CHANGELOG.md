# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-11-11

### Added
- Terminal demo in the README, generated from the real output of the scripts.
- The curator and the session-start summary now read the conversations of Claude Code, Antigravity CLI and Codex CLI through `bin/transcripts.py`.
- The session-start summary skips the conversation that is starting, using the id the hook receives.

### Fixed
- `session-start.sh` no longer lets `git pull --autostash` print to stdout, which made strict agents (Antigravity) reject the hook output.

## [0.2.0] - 2026-11-11

### Added
- Multi-agent support: Antigravity CLI and Codex CLI alongside Claude Code, with an installer that detects the agents present (`--agents`), merges hooks without touching foreign ones, and links the skills.
- `bin/install-hooks.py`, `context.py --agent`, and an agent-aware `inject-memory.py` that answers in the format each agent expects.
- `session-end.sh --light`: commit on every stop and push in the background at most every five minutes, for agents with no end-of-session event.
- `docs/agents.md` with the support matrix and the differences between agents.

### Changed
- `CLAUDE.example.md` is now `INSTRUCTIONS.example.md`: one template for `CLAUDE.md`, `AGENTS.md` or `GEMINI.md`.
- The project describes itself as memory for AI coding agents, not only Claude Code.

## [0.1.0] - 2026-11-11

First public release.

### Added
- Three-layer brain: `inventory/` (generated), `memory/` (notes), `skills/` (procedures).
- Session hooks: start (continuity context), per message (note suggestions), end (commit and push).
- Nightly curator that distils conversations, reacts to machine changes and re-verifies old notes,
  with quota-aware retry.
- Inventory collectors for Linux, Docker, LXC and Proxmox, with a daily snapshot and change journal.
- `bin/health.py` validator: index reachability, broken links, missing links, stale dates, oversized
  notes, dead entities and leaked secrets.
- Skills `memory-keeping`, `remember` and `close-session`.
- `install.sh` that merges the hooks into Claude Code settings idempotently.
- Optional webhook notifications, at most one per title per day.

[Unreleased]: https://github.com/cristobaltormo/cortex-md/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/cristobaltormo/cortex-md/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/cristobaltormo/cortex-md/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/cristobaltormo/cortex-md/releases/tag/v0.1.0
