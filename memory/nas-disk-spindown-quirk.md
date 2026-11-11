---
name: nas-disk-spindown-quirk
description: "Example: the NAS spins its disks down at night, so the first read of the morning takes about 10 seconds"
metadata:
  type: reference
  verified: 2026-11-11
  status: current
---

The NAS spins down its disks after 30 idle minutes. The first request after a pause blocks for
roughly 10 seconds while they spin up; it is not a fault and a retry succeeds.

**Why:** power saving was turned on deliberately; the user prefers the delay to the noise and cost.
**How to apply:** when a morning health check times out once and then passes, do not raise an alarm.
Measured: 3 mornings in a row, first read 9 to 12 s, second read under 100 ms.

Part of: [[index-infrastructure]].
