# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/cristobaltormo/cortex-md/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/cristobaltormo/cortex-md/releases/tag/v0.1.0
