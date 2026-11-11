# Security policy

## Supported versions

Only the latest release receives fixes.

## Reporting a vulnerability

Please do not open a public issue. Use GitHub's private reporting:
**Security** tab, then **Report a vulnerability**.

Include what you found, how to reproduce it and what you expect the impact to be. You will get an
acknowledgement within a few days, and a fix or a clear explanation as soon as it can be done.

## Scope worth knowing about

cortex-md runs scripts from agent hooks (Claude Code, Antigravity CLI, Codex CLI) and cron, and the nightly curator gives a headless
Claude session limited write access to the brain. Reports about any of these are in scope:

- a way for note, transcript or inventory content to cause code execution outside the curator's allowlist;
- a way for secrets to end up in the git history or in a notification;
- the installer damaging an existing agent configuration.

The threat model and the curator's allowlist are described in the README under "Security notes".
