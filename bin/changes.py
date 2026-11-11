#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

BRAIN = Path(os.environ.get("BRAIN_DIR") or Path(__file__).resolve().parent.parent)
CURRENT = BRAIN / "inventory" / "state.json"
PREVIOUS = BRAIN / "state" / "previous-state.json"
JOURNAL = BRAIN / "inventory" / "CHANGES.md"
NOTIFY = BRAIN / "bin" / "notify.sh"
KEEP_DAYS = 90
DISK_JUMP = 10
DISK_ALERT = 85
BACKUP_ALERT_DAYS = 3
SUSPICIOUS_DISAPPEARANCE = 0.5
SERIOUS = ("is new", "has disappeared", "filling up", "failed", "not updated", "no backup")


def notify_if_serious(lines):
    serious = [l for l in lines if any(s in l for s in SERIOUS)]
    if serious:
        summary = "; ".join(re.sub(r"\*\*", "", l) for l in serious)
        subprocess.run([str(NOTIFY), "Machine changes", summary], check=False)


def suspicious(old, new):
    before, after = old.get("containers", {}), new.get("containers", {})
    if not before:
        return False
    if not after:
        return True
    return len(set(before) - set(after)) / len(before) > SUSPICIOUS_DISAPPEARANCE


def compare(old, new):
    lines = []
    before, after = old.get("containers", {}), new.get("containers", {})

    for name in sorted(set(after) - set(before)):
        lines.append(f"**container {name} ({after[name].get('kind')}) is new**")
    for name in sorted(set(before) - set(after)):
        lines.append(f"**container {name} has disappeared**: notes about it may no longer be valid")
    for name in sorted(set(before) & set(after)):
        if before[name].get("state") != after[name].get("state"):
            lines.append(f"container {name}: {before[name].get('state')} -> {after[name].get('state')}")
        if before[name].get("image") != after[name].get("image"):
            lines.append(f"container {name}: image {before[name].get('image')} -> {after[name].get('image')}")

    vm_before, vm_after = old.get("machines", {}), new.get("machines", {})
    for name in sorted(set(vm_after) - set(vm_before)):
        lines.append(f"**machine {name} is new**")
    for name in sorted(set(vm_before) - set(vm_after)):
        lines.append(f"**machine {name} has disappeared**")

    ha, hb = old.get("host", {}), new.get("host", {})
    for key, label in (("kernel", "kernel"), ("cpus", "host CPUs"), ("ram_gb", "host RAM (GB)")):
        if ha.get(key) is not None and ha.get(key) != hb.get(key):
            lines.append(f"**{label}**: {ha.get(key)} -> {hb.get(key)}")
    if ha.get("pending_updates") is not None and ha.get("pending_updates") != hb.get("pending_updates"):
        lines.append(f"pending updates on the host: {ha.get('pending_updates')} -> {hb.get('pending_updates')}")

    pa, pb = old.get("ports", {}), new.get("ports", {})
    for port in sorted(set(pb) - set(pa), key=int):
        lines.append(f"port {port} opened ({pb[port]})")
    for port in sorted(set(pa) - set(pb), key=int):
        lines.append(f"port {port} no longer listening (was {pa[port]})")

    da, db = old.get("disks", {}), new.get("disks", {})
    for mount in sorted(set(da) & set(db)):
        was, now = da[mount], db[mount]
        if abs(now - was) >= DISK_JUMP or (now >= DISK_ALERT > was):
            warning = "  <- filling up" if now >= DISK_ALERT else ""
            lines.append(f"filesystem {mount}: {was}% -> {now}% used{warning}")

    for unit in sorted(set(new.get("failed_units", [])) - set(old.get("failed_units", []))):
        lines.append(f"**systemd unit {unit} has failed**")

    age = new.get("backup_age_days")
    if age is not None:
        if age >= 999:
            lines.append("**no backup** files found in the backup directory")
        elif age >= BACKUP_ALERT_DAYS:
            lines.append(f"the newest backup is {age} days old: **not updated**")

    return lines


def prune(text):
    limit = date.today() - timedelta(days=KEEP_DAYS)
    out, skipping = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            try:
                skipping = datetime.strptime(line[3:].strip(), "%Y-%m-%d").date() < limit
            except ValueError:
                skipping = False
        if not skipping:
            out.append(line)
    return "\n".join(out)


def main():
    if not CURRENT.exists():
        print("No current snapshot: run bin/snapshot.py first", file=sys.stderr)
        return 1

    new = json.loads(CURRENT.read_text())

    if not PREVIOUS.exists():
        PREVIOUS.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(CURRENT, PREVIOUS)
        print("First snapshot stored: changes are detected from tomorrow on")
        return 0

    try:
        old = json.loads(PREVIOUS.read_text())
    except ValueError:
        shutil.copy(CURRENT, PREVIOUS)
        print("The previous snapshot was corrupt and has been replaced")
        return 0

    if suspicious(old, new) and "--accept" not in sys.argv:
        print(
            "Today's snapshot drops too many containers at once: this looks like a failure of "
            "the inventory itself, not a real change. Nothing compared, previous snapshot kept. If the change is real, run bin/changes.py --accept.",
            file=sys.stderr,
        )
        return 1

    lines = compare(old, new)
    shutil.copy(CURRENT, PREVIOUS)

    if not lines:
        print("No infrastructure changes")
        return 0

    today = date.today().isoformat()
    since = old.get("generated", "?")[:16].replace("T", " ")
    header = (
        "# What changed on the machine\n\n"
        "_Written by `bin/changes.py` by comparing each day's snapshot. Do not edit by hand._\n"
    )
    previous = JOURNAL.read_text(encoding="utf-8") if JOURNAL.exists() else ""
    body = previous[len(header):] if previous.startswith(header) else previous
    block = f"\n## {today}\n\n_Compared with the snapshot of {since}._\n\n"
    block += "\n".join(f"- {l}" for l in lines) + "\n"

    JOURNAL.write_text(prune(header + block + body).rstrip() + "\n", encoding="utf-8")
    print(f"{len(lines)} changes detected and recorded in inventory/CHANGES.md")
    for line in lines:
        print(f"  - {line}")
    notify_if_serious(lines)
    return 0


if __name__ == "__main__":
    sys.exit(main())
