---
name: project-invoice-tool-storage-choice
description: "Example: the invoice tool stores data in SQLite instead of Postgres, and why"
metadata:
  type: project
  verified: 2026-11-11
  status: current
---

The invoice tool uses a single SQLite file. Postgres was considered and dropped.

**Why:** one user, under a thousand invoices a year, and a file copy is the whole backup story.
A database server would add a service to patch and monitor for no gain.
**How to apply:** do not propose migrating to Postgres unless the user count or write concurrency changes.

Part of: [[index-projects]]. Related: [[nas-disk-spindown-quirk]].
