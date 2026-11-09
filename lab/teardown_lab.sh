#!/usr/bin/env bash
set -euo pipefail

BASE=/opt/privesc-lab
MANIFEST="$BASE/manifest.txt"
if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  echo "Run teardown as root inside the disposable Linux VM or container." >&2
  exit 2
fi
if [[ ! -f "$MANIFEST" ]]; then
  echo "No lab manifest found; nothing to remove."
  exit 0
fi

while IFS= read -r item; do
  case "$item" in
    USER:privlab)
      if id privlab >/dev/null 2>&1; then
        userdel -r privlab
      fi
      ;;
    /opt/privesc-lab/*|/etc/cron.d/privesc-lab|/etc/sudoers.d/privesc-lab|/etc/systemd/system/privesc-lab.service)
      if [[ -f "$item" || -L "$item" ]]; then
        rm -f -- "$item"
      elif [[ -d "$item" ]]; then
        rmdir -- "$item" 2>/dev/null || { echo "Directory is not empty; refusing recursive removal: $item" >&2; exit 4; }
      fi
      ;;
    ""|SKIPPED*) ;;
    *) echo "Unexpected manifest entry; refusing removal: $item" >&2; exit 3 ;;
  esac
done < "$MANIFEST"

if [[ -f "$MANIFEST" ]]; then rm -f -- "$MANIFEST"; fi
if [[ -d "$BASE" ]]; then rmdir -- "$BASE"; fi

for target in "$BASE" /etc/cron.d/privesc-lab /etc/sudoers.d/privesc-lab /etc/systemd/system/privesc-lab.service /home/privlab; do
  if [[ -e "$target" ]]; then
    echo "Teardown verification failed: $target remains" >&2
    exit 5
  fi
done
if id privlab >/dev/null 2>&1; then
  echo "Teardown verification failed: privlab user remains" >&2
  exit 5
fi
echo "Lab teardown complete; no manifest-listed artifacts remain."
