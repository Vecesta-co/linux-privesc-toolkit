#!/usr/bin/env bash
set -euo pipefail

BASE=/opt/privesc-lab
MANIFEST="$BASE/manifest.txt"
CRON=/etc/cron.d/privesc-lab
SUDOERS=/etc/sudoers.d/privesc-lab
SERVICE=/etc/systemd/system/privesc-lab.service
USER_NAME=privlab

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  echo "Run as root inside a disposable Linux VM or container." >&2
  exit 2
fi
if [[ ${1:-} != "--yes-i-am-in-a-disposable-lab" ]]; then
  echo "Refusing to create weaknesses without --yes-i-am-in-a-disposable-lab." >&2
  echo "This script intentionally weakens a disposable Linux environment." >&2
  exit 2
fi

for target in "$BASE" "$CRON" "$SUDOERS" "$SERVICE" /home/privlab; do
  if [[ -e "$target" ]]; then
    echo "Refusing to overwrite existing path: $target" >&2
    exit 3
  fi
done
if id "$USER_NAME" >/dev/null 2>&1; then
  echo "Refusing to overwrite existing user: $USER_NAME" >&2
  exit 3
fi

mkdir -m 0755 "$BASE"
umask 077
touch "$MANIFEST"
manifest_add() { printf '%s\n' "$1" >> "$MANIFEST"; }
manifest_add "$MANIFEST"

manifest_add "$BASE/find_suid"
cp -- /usr/bin/find "$BASE/find_suid"
chmod 4755 "$BASE/find_suid"
manifest_add "$BASE/find_suid"
if [[ -x /usr/bin/awk ]]; then
  manifest_add "$BASE/awk_suid"
  cp -- /usr/bin/awk "$BASE/awk_suid"
  chmod 4755 "$BASE/awk_suid"
  manifest_add "$BASE/awk_suid"
else
  echo "SKIPPED awk copy: /usr/bin/awk unavailable" >> "$MANIFEST"
fi

manifest_add "$BASE/world_writable.conf"
manifest_add "$BASE/open_dir"
printf 'lab-only writable configuration\n' > "$BASE/world_writable.conf"
chmod 0666 "$BASE/world_writable.conf"
mkdir -m 0777 "$BASE/open_dir"
manifest_add "$BASE/world_writable.conf"
manifest_add "$BASE/open_dir"

manifest_add "$BASE/backup.sh"
cat > "$BASE/backup.sh" <<'SCRIPT'
#!/bin/sh
echo "Disposable lab backup placeholder"
SCRIPT
chmod 0777 "$BASE/backup.sh"
manifest_add "$BASE/backup.sh"
manifest_add "$CRON"
cat > "$CRON" <<'CRONFILE'
SHELL=/bin/sh
@yearly root /opt/privesc-lab/backup.sh
@yearly root /usr/bin/tar -cf /opt/privesc-lab/archive.tar *
@yearly root backup-relative.sh
CRONFILE
chmod 0644 "$CRON"
manifest_add "$CRON"

sudo_tmp="$(mktemp /run/privesc-lab-sudoers.XXXXXX)"
trap 'rm -f -- "$sudo_tmp"' EXIT
cat > "$sudo_tmp" <<'SUDOFILE'
privlab ALL=(root) NOPASSWD: /usr/bin/find
privlab ALL=(root) NOPASSWD: ALL
SUDOFILE
chmod 0440 "$sudo_tmp"
if ! command -v visudo >/dev/null 2>&1; then
  echo "visudo is required to validate the lab sudoers file" >&2
  exit 4
fi
visudo -cf "$sudo_tmp"
manifest_add "$SUDOERS"
install -o root -g root -m 0440 "$sudo_tmp" "$SUDOERS"
manifest_add "$SUDOERS"
rm -f -- "$sudo_tmp"
trap - EXIT

manifest_add "$BASE/service_task.sh"
cat > "$BASE/service_task.sh" <<'SCRIPT'
#!/bin/sh
echo "Disposable lab service placeholder"
SCRIPT
chmod 0777 "$BASE/service_task.sh"
manifest_add "$SERVICE"
cat > "$SERVICE" <<'UNIT'
[Unit]
Description=Disposable privilege audit lab service
[Service]
ExecStart=/opt/privesc-lab/service_task.sh
Environment=PATH=/tmp:/usr/bin:/bin
[Install]
WantedBy=multi-user.target
UNIT
chmod 0666 "$SERVICE"
manifest_add "$BASE/service_task.sh"
manifest_add "$SERVICE"

if command -v setcap >/dev/null 2>&1 && [[ -x /usr/bin/python3 ]]; then
  manifest_add "$BASE/python_cap"
  cp -L -- /usr/bin/python3 "$BASE/python_cap"
  setcap cap_setuid+ep "$BASE/python_cap"
  manifest_add "$BASE/python_cap"
else
  echo "SKIPPED python capability: setcap or /usr/bin/python3 unavailable" >> "$MANIFEST"
fi

manifest_add "USER:$USER_NAME"
manifest_add /home/privlab
useradd -m -d /home/privlab -s /bin/bash -p '!' "$USER_NAME"
usermod -L "$USER_NAME"
chmod 0777 /home/privlab
manifest_add "USER:$USER_NAME"
manifest_add /home/privlab

echo "Disposable lab weaknesses created. Review $MANIFEST and run teardown_lab.sh when finished."
