# FAQ

**Is this a vector database for AI agents?**
No. It is a folder of markdown files, a git repo and a handful of scripts. Retrieval is keyword
scoring over a small, curated corpus.

**Does it send my notes anywhere?**
No. Everything stays in the repo. The only network use is optional: your own webhook for
notifications, and `git push` to whatever remote you configure. The nightly curator uses your
Claude Code installation like any other session.

**What does the curator cost?**
One headless Claude run a night, and only when there are new transcripts or validator defects.
Quota failures retry after the reset.

**Can I use it without the curator?**
Yes. Skip the cron lines. The hooks, the inventory and the validator work on their own, and you
lose the nightly distilling and re-verification.

**Which agents does it work with?**
Claude Code, Antigravity CLI and Codex CLI get automatic context through hooks; anything that reads
`AGENTS.md` can use the brain by instruction. See [agents.md](agents.md).

**Can it run on macOS or Windows?**
Not today: the scripts need `flock` and Linux tools. WSL should work but is untested.

**Why plain files and not a database?**
The valuable part is the discipline (do not duplicate what the machine knows, re-verify, link,
keep notes small), not the storage. Files diff, merge, grep and survive any tool.

**Why does the validator complain about my old notes?**
Notes older than 90 days without a new `verified` date are flagged, because stale confident notes
are the failure this project exists to prevent. Check the fact, then bump the date.

**How do I start from nothing?**
Delete the example notes, keep `MEMORY.md` with empty sections, and let the first sessions fill it.
