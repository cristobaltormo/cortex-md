---
name: feedback-small-commits
description: "Example: the user wants one logical change per commit, with the reason in the message"
metadata:
  type: feedback
  verified: 2026-11-11
  status: current
---

One logical change per commit. The message says why, not what: the diff already shows what.

**Why:** the user reviews history to understand decisions months later and bisects when something breaks.
**How to apply:** split unrelated fixes into separate commits even when they were found in the same session.

Part of: [[index-working-style]].
