#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
OUT=evidence/run1
PACE=0
NO_COLOR=0
YES_FLAG=""
while (($#)); do
  case "$1" in
    --out) OUT=${2:?--out needs a directory}; shift 2 ;;
    --pace) PACE=${2:?--pace needs seconds}; shift 2 ;;
    --no-color) NO_COLOR=1; shift ;;
    --yes-i-am-in-a-disposable-lab) YES_FLAG="--yes-i-am-in-a-disposable-lab"; shift ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done
if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  echo "Run the lab demo as root inside a disposable Linux VM or container." >&2
  exit 2
fi
if ! [[ "$PACE" =~ ^[0-9]+$ ]]; then echo "--pace must be a whole number of seconds" >&2; exit 2; fi

mkdir -p "$OUT"
chmod 0777 "$OUT"
OUT="$(cd -- "$OUT" && pwd)"
TRANSCRIPT="$OUT/console_transcript.txt"
SAFETY="$OUT/safety_proof.txt"
: > "$TRANSCRIPT"
: > "$SAFETY"
exec > >(tee -a "$TRANSCRIPT") 2>&1

COLOR_GREEN=$'\033[1;32m'; COLOR_CYAN=$'\033[1;36m'; COLOR_RESET=$'\033[0m'
if ((NO_COLOR)); then COLOR_GREEN=; COLOR_CYAN=; COLOR_RESET=; fi
LAB_ACTIVE=0
cleanup() {
  status=$?
  if ((LAB_ACTIVE)); then
    echo "Cleanup trap: attempting manifest-based teardown."
    bash "$SCRIPT_DIR/teardown_lab.sh" || status=$?
  fi
  exit "$status"
}
trap cleanup EXIT INT TERM

pause_demo() { if ((PACE > 0)); then sleep "$PACE"; fi; }
snapshot() {
  local path
  for path in /etc/passwd /etc/group /etc/shadow /etc/sudoers; do
    if [[ -r "$path" ]]; then sha256sum -- "$path"; else printf 'UNREADABLE %s\n' "$path"; fi
  done
}
scan_checked() {
  local label=$1 out_dir=$2 log_dir=$3
  shift 3
  local before after
  before="$(snapshot)"
  mkdir -p "$out_dir" "$log_dir"
  if [[ "$label" == "act2_lab_limited" ]] && id privlab >/dev/null 2>&1; then
    chmod 0777 "$out_dir" "$log_dir"
    if command -v runuser >/dev/null 2>&1; then
      runuser -u privlab -- python3 "$PROJECT_ROOT/privesc_scan.py" scan --label "$label" --fast --no-color --output-dir "$out_dir" --log-dir "$log_dir" "$@"
    else
      su -s /bin/bash privlab -c "python3 \"$PROJECT_ROOT/privesc_scan.py\" scan --label \"$label\" --fast --no-color --output-dir \"$out_dir\" --log-dir \"$log_dir\" $*"
    fi
  else
    python3 "$PROJECT_ROOT/privesc_scan.py" scan --label "$label" --fast --no-color --output-dir "$out_dir" --log-dir "$log_dir" "$@"
  fi
  after="$(snapshot)"
  {
    printf 'SCAN %s\nBEFORE\n%s\nAFTER\n%s\n' "$label" "$before" "$after"
    if [[ "$before" == "$after" ]]; then printf 'STATUS PASS hashes identical\n'; else printf 'STATUS FAIL hash mismatch\n'; fi
  } >> "$SAFETY"
  if [[ "$before" != "$after" ]]; then echo "Safety proof failed after $label" >&2; return 1; fi
  pause_demo
}

echo "${COLOR_GREEN}Linux Privilege Escalation Automation Toolkit${COLOR_RESET}"
echo "Detection-only audit · disposable lab · findings are evidence, not authorization"
mkdir -p "$OUT/act1_clean" "$OUT/act2_lab" "$OUT/act2_lab_limited" "$OUT/act2_kernel_sim" "$OUT/act3_fixed" "$OUT/logs"
chmod 0777 "$OUT/act2_lab_limited" "$OUT/logs"

echo "${COLOR_CYAN}ACT 1 / 3 — clean system baseline${COLOR_RESET}"
scan_checked act1_clean "$OUT/act1_clean" "$OUT/logs/act1"

echo "${COLOR_CYAN}ACT 2 / 3 — controlled weak configurations${COLOR_RESET}"
LAB_ACTIVE=1
bash "$SCRIPT_DIR/setup_lab.sh" --yes-i-am-in-a-disposable-lab
scan_checked act2_lab "$OUT/act2_lab" "$OUT/logs/act2_root"
scan_checked act2_lab_limited "$OUT/act2_lab_limited" "$OUT/logs/act2_limited"
scan_checked act2_kernel_sim "$OUT/act2_kernel_sim" "$OUT/logs/act2_kernel" --kernel-override 4.4.0-210-generic

{
  echo "Independent checks while the lab is active"
  echo '$ ls -l /opt/privesc-lab'
  ls -l /opt/privesc-lab
  echo '$ stat -c "%a %U:%G %n" /opt/privesc-lab/find_suid /opt/privesc-lab/world_writable.conf /opt/privesc-lab/open_dir /opt/privesc-lab/backup.sh /etc/systemd/system/privesc-lab.service'
  stat -c '%a %U:%G %n' /opt/privesc-lab/find_suid /opt/privesc-lab/world_writable.conf /opt/privesc-lab/open_dir /opt/privesc-lab/backup.sh /etc/systemd/system/privesc-lab.service
  echo '$ find /opt/privesc-lab -xdev -type f -perm /6000 -printf "%m %p\n"'
  find /opt/privesc-lab -xdev -type f -perm /6000 -printf '%m %p\n'
  echo '$ getcap -r /opt/privesc-lab'
  getcap -r /opt/privesc-lab || true
  echo '$ cat /etc/cron.d/privesc-lab'
  cat /etc/cron.d/privesc-lab
  echo '$ sudo -l -U privlab'
  sudo -l -U privlab
  echo '$ stat -c "%a %U:%G %n" /home/privlab /opt/privesc-lab/service_task.sh /etc/sudoers.d/privesc-lab'
  stat -c '%a %U:%G %n' /home/privlab /opt/privesc-lab/service_task.sh /etc/sudoers.d/privesc-lab
  if [[ -e /opt/privesc-lab/python_cap ]]; then
    echo '$ getcap /opt/privesc-lab/python_cap'
    getcap /opt/privesc-lab/python_cap || true
  else
    echo 'SKIPPED optional python capability binary'
  fi
} > "$OUT/independent_check.txt" 2>&1
cp -- /opt/privesc-lab/manifest.txt "$OUT/lab_manifest.txt"
pause_demo

echo "${COLOR_CYAN}ACT 3 / 3 — teardown and verify fixes${COLOR_RESET}"
bash "$SCRIPT_DIR/teardown_lab.sh"
LAB_ACTIVE=0
{
  for path in /opt/privesc-lab /etc/cron.d/privesc-lab /etc/sudoers.d/privesc-lab /etc/systemd/system/privesc-lab.service /home/privlab; do
    if [[ -e "$path" ]]; then echo "FAIL remains $path"; else echo "PASS absent $path"; fi
  done
  if id privlab >/dev/null 2>&1; then echo "FAIL user privlab remains"; else echo "PASS user privlab removed"; fi
} | tee "$OUT/teardown_check.txt"
scan_checked act3_fixed "$OUT/act3_fixed" "$OUT/logs/act3"

python3 "$PROJECT_ROOT/privesc_scan.py" compare "$OUT/act1_clean/scan_act1_clean.json" "$OUT/act2_lab/scan_act2_lab.json" --output-dir "$OUT" | tee "$OUT/compare_act1_vs_act2.txt"
python3 "$PROJECT_ROOT/privesc_scan.py" compare "$OUT/act2_lab/scan_act2_lab.json" "$OUT/act3_fixed/scan_act3_fixed.json" --output-dir "$OUT" | tee "$OUT/compare_act2_vs_act3.txt"
python3 "$PROJECT_ROOT/tools/verify_all.py" "$OUT"
echo "Demo evidence saved in $OUT"
trap - EXIT INT TERM
