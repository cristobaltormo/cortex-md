#!/usr/bin/env bash
set -uo pipefail
BRAIN="${BRAIN_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
. "$BRAIN/bin/load-env.sh"
INV="$BRAIN/inventory"
NOW=$(date '+%Y-%m-%d %H:%M')
mkdir -p "$INV" "$BRAIN/state"

exec 9>"$BRAIN/state/inventory.lock"
flock -n 9 || { echo "Another inventory pass is running"; exit 0; }

{
  echo "# Host"
  echo
  echo "_Generated automatically on $NOW by \`bin/inventory.sh\`. Do not edit by hand._"
  echo
  echo "- **OS:** $(. /etc/os-release 2>/dev/null && echo "${PRETTY_NAME:-unknown}")"
  echo "- **Kernel:** $(uname -r)"
  echo "- **CPU:** $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | xargs) ($(nproc) threads)"
  echo "- **RAM:** $(free -h | awk '/^Mem:/{print $3" used of "$2" ("$7" available)"}')"
  echo "- **Uptime:** $(uptime -p | sed 's/^up //')"
  echo "- **Load:** $(cut -d' ' -f1-3 /proc/loadavg)"
  echo "- **IP:** $(hostname -I 2>/dev/null | awk '{print $1}')"
  echo
  echo "## Filesystems"
  echo
  echo "| Mount | Type | Used | Size | % |"
  echo "|---|---|---|---|---|"
  df -hT -x tmpfs -x devtmpfs -x squashfs -x overlay 2>/dev/null | tail -n +2 | awk '{printf "| %s | %s | %s | %s | %s |\n", $7, $2, $4, $3, $6}'
} > "$INV/host.md"

{
  echo "# Services and ports"
  echo
  echo "_Generated automatically on $NOW. Do not edit by hand._"
  echo
  echo "## Listening"
  echo
  echo "| Port | Process |"
  echo "|---|---|"
  ss -tlnp 2>/dev/null | tail -n +2 | awk '
      { line=$0; split($4,a,":"); port=a[length(a)]; proc="?";
        if (index(line,"users:") > 0) { p=line; sub(/.*users:\(\("/,"",p); sub(/".*/,"",p); proc=p }
        if (port ~ /^[0-9]+$/) print port"\t"proc }' \
    | sort -un | while IFS=$'\t' read -r p proc; do echo "| $p | $proc |"; done
  echo
  echo "## Running systemd services"
  echo
  systemctl list-units --type=service --state=running --no-legend --no-pager 2>/dev/null \
    | awk '{print "- " $1}' | head -40
  echo
  echo "## Scheduled jobs (crontab of the user running the inventory)"
  echo
  echo '```'
  crontab -l 2>/dev/null | grep -vE '^\s*#|^\s*$' || echo "(no crontab)"
  echo '```'
} > "$INV/services.md"

{
  echo "# Containers and machines"
  echo
  echo "_Generated automatically on $NOW. Do not edit by hand._"
  echo
  if command -v docker >/dev/null 2>&1; then
    echo "## Docker"
    echo
    echo "| Name | Image | Status |"
    echo "|---|---|---|"
    docker ps -a --format '| {{.Names}} | {{.Image}} | {{.Status}} |' 2>/dev/null
    echo
  fi
  if command -v pct >/dev/null 2>&1; then
    echo "## Proxmox LXC"
    echo
    pct list 2>/dev/null | sed 's/^/    /'
    echo
  fi
  if command -v qm >/dev/null 2>&1; then
    echo "## Proxmox VMs"
    echo
    qm list 2>/dev/null | sed 's/^/    /'
    echo
  fi
  if ! command -v docker >/dev/null 2>&1 && ! command -v pct >/dev/null 2>&1 && ! command -v qm >/dev/null 2>&1; then
    echo "No container runtime found on this host."
  fi
} > "$INV/containers.md"

"$BRAIN/bin/snapshot.py"
"$BRAIN/bin/changes.py"

echo "Inventory regenerated: $NOW"
