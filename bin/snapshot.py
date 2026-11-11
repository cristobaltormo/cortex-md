#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

BRAIN = Path(os.environ.get("BRAIN_DIR") or Path(__file__).resolve().parent.parent)
TARGET = BRAIN / "inventory" / "state.json"
BACKUP_DIR = os.environ.get("BACKUP_DIR", "")


def sh(cmd, timeout=20):
    try:
        return subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        ).stdout
    except Exception:
        return ""


def have(program):
    return shutil.which(program) is not None


def docker_containers():
    found = {}
    if not have("docker"):
        return found
    for line in sh("docker ps -a --format '{{.Names}}\t{{.State}}\t{{.Image}}'").splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            found[parts[0]] = {"kind": "docker", "state": parts[1], "image": parts[2]}
    return found


def lxc_containers():
    found = {}
    if not have("pct"):
        return found
    for line in sh("pct list").splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 3:
            found[parts[-1]] = {"kind": "lxc", "state": parts[1], "id": parts[0]}
    return found


def proxmox_vms():
    found = {}
    if not have("qm"):
        return found
    for line in sh("qm list").splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 3:
            found[parts[1]] = {"kind": "vm", "state": parts[2], "id": parts[0]}
    return found


def disks():
    found = {}
    out = sh("df -P -x tmpfs -x devtmpfs -x squashfs -x overlay")
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 6 and parts[4].endswith("%") and parts[4][:-1].isdigit():
            found[parts[5]] = int(parts[4][:-1])
    return found


def ports():
    found = {}
    for line in sh("ss -tlnH").splitlines():
        fields = line.split()
        if len(fields) < 4:
            continue
        port = fields[3].rsplit(":", 1)[-1]
        if port.isdigit():
            proc = re.search(r'users:\(\("([^"]+)"', line)
            found[port] = proc.group(1) if proc else "?"
    return found


def failed_units():
    return sorted(
        line.split()[0]
        for line in sh("systemctl --failed --no-legend --plain").splitlines()
        if line.strip()
    )


def backup_age_days():
    if not BACKUP_DIR or not Path(BACKUP_DIR).is_dir():
        return None
    newest = max((p.stat().st_mtime for p in Path(BACKUP_DIR).rglob("*") if p.is_file()), default=None)
    if newest is None:
        return 999
    return int((time.time() - newest) // 86400)


def main():
    containers = {**docker_containers(), **lxc_containers()}
    pending = max(0, len(sh("apt list --upgradable 2>/dev/null").splitlines()) - 1)
    state = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "host": {
            "kernel": sh("uname -r").strip(),
            "cpus": int(sh("nproc").strip() or 0),
            "ram_gb": int(sh("free -g | awk '/^Mem:/{print $2}'").strip() or 0),
            "pending_updates": pending,
        },
        "containers": containers,
        "machines": proxmox_vms(),
        "disks": disks(),
        "ports": ports(),
        "failed_units": failed_units(),
        "backup_age_days": backup_age_days(),
    }
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    tmp = TARGET.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=1, ensure_ascii=False, sort_keys=True) + "\n")
    tmp.replace(TARGET)
    print(
        f"Snapshot: {len(containers)} containers, {len(state['machines'])} machines, "
        f"{len(state['ports'])} ports, {len(state['disks'])} filesystems"
    )


if __name__ == "__main__":
    sys.exit(main() or 0)
