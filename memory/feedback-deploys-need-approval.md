---
name: feedback-deploys-need-approval
description: "Nothing goes to production without an explicit OK; work happens on a test port or branch"
metadata:
  type: feedback
  verified: 2026-11-11
  status: current
---

Work is done on a test instance. Promoting to production happens only after the user says so, in
this conversation, for this change. An earlier approval does not cover a later change.

**Why:** the user changed their mind about what is ready more than once; an unwanted deploy is
harder to undo than a delayed one.
**How to apply:** when in doubt, leave it on test and say what is waiting for their OK.

Part of: [[index-working-style]].
