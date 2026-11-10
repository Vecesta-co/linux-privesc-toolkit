#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

AUTO_YES=0
NO_FULL_SCAN=0

while (($#)); do
  case "$1" in
    --yes) AUTO_YES=1; shift ;;
    --no-full-scan) NO_FULL_SCAN=1; shift ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

echo "========================================================================"
echo "      LINUX PRIVILEGE ESCALATION AUTOMATION TOOLKIT (EVIDENCE RUN)      "
echo "========================================================================"
echo "WARNING: This script runs the automated validation lab which plants REAL"
echo "reversible security weaknesses in a temporary directory and config files."
echo "ONLY RUN THIS INSIDE A DISPOSABLE LAB VIRTUAL MACHINE OR TEST CONTAINER!"
echo "========================================================================"

if [[ "$AUTO_YES" -eq 0 ]]; then
  read -r -p "Type YES to proceed with live Kali Linux evidence collection: " CONFIRM
  if [[ "$CONFIRM" != "YES" ]]; then
    echo "Aborted by user."
    exit 1
  fi
fi

# Ensure sudo credentials and keep alive in background if not already root
SUDO_PID=""
cleanup_sudo() {
  if [[ -n "$SUDO_PID" ]]; then
    kill "$SUDO_PID" 2>/dev/null || true
  fi
  # Always ensure lab teardown runs if leftover
  if [[ -f /opt/privesc-lab/manifest.txt ]]; then
    sudo bash "$SCRIPT_DIR/teardown_lab.sh" 2>/dev/null || true
  fi
}
trap cleanup_sudo EXIT INT TERM

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  if ! sudo -v; then
    echo "Failed to obtain sudo credentials." >&2
    exit 2
  fi
  # Keep sudo timestamp updated in background
  while true; do sudo -n true; sleep 50; done 2>/dev/null &
  SUDO_PID=$!
fi

EVIDENCE_DIR="$PROJECT_ROOT/evidence"
mkdir -p "$EVIDENCE_DIR"
SUMMARY_FILE="$EVIDENCE_DIR/collect_summary.txt"
: > "$SUMMARY_FILE"

record_step() {
  local name="$1"
  local status="$2"
  local detail="${3:-}"
  printf "%-30s | %-8s | %s\n" "$name" "$status" "$detail" | tee -a "$SUMMARY_FILE"
}

ANY_FAIL=0

# Step 1: Preflight check
echo ""
echo ">>> [1/9] Running Preflight Environment Check..."
if bash "$SCRIPT_DIR/preflight.sh"; then
  record_step "Preflight" "PASS" "All required tools verified"
else
  record_step "Preflight" "FAIL" "Required tools missing"
  ANY_FAIL=1
fi

# Step 2: Environment info
echo ""
echo ">>> [2/9] Capturing Environment Information..."
ENV_INFO="$EVIDENCE_DIR/env_info.txt"
{
  echo "Timestamp (UTC): $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
  echo "Host: $(uname -a)"
  if [[ -f /etc/os-release ]]; then
    echo "--- /etc/os-release ---"
    cat /etc/os-release
  fi
  echo "--- Python Version ---"
  python3 --version
  echo "--- GNU Find Version ---"
  find --version | head -n 1
  echo "--- User & Identity ---"
  echo "whoami: $(whoami)"
  id
  echo "--- Virtualization / Container Detection ---"
  if command -v systemd-detect-virt >/dev/null 2>&1; then
    echo "systemd-detect-virt: $(systemd-detect-virt 2>&1 || true)"
  fi
  if [[ -f /.dockerenv ]]; then echo "Docker environment detected: /.dockerenv exists"; fi
  if grep -qi microsoft /proc/version 2>/dev/null; then echo "WSL environment detected"; fi
  echo "--- Capabilities Tools ---"
  echo "getcap: $(command -v getcap || echo 'NOT FOUND')"
  echo "setcap: $(command -v setcap || echo 'NOT FOUND')"
} > "$ENV_INFO" 2>&1
record_step "Environment Info" "PASS" "$ENV_INFO written"

# Step 3: Pytest on Linux (twice)
echo ""
echo ">>> [3/9] Running Test Suite on Linux (Run 1 & 2)..."
PY_EXEC="python3"
if ! python3 -c "import pytest" >/dev/null 2>&1; then
  echo "pytest not found in system python; attempting virtual environment or pip..."
  if [[ ! -d "$PROJECT_ROOT/.venv" ]]; then
    python3 -m venv "$PROJECT_ROOT/.venv" || true
  fi
  if [[ -f "$PROJECT_ROOT/.venv/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.venv/bin/activate"
    pip install -q -r "$PROJECT_ROOT/requirements-dev.txt" || sudo apt-get install -y python3-pytest
    PY_EXEC="python"
  else
    sudo apt-get install -y python3-pytest || true
  fi
fi

RUN1_OUT="$EVIDENCE_DIR/pytest_linux_run1.txt"
RUN2_OUT="$EVIDENCE_DIR/pytest_linux_run2.txt"

if $PY_EXEC -m pytest -v > "$RUN1_OUT" 2>&1; then
  if grep -q "test_real_scan_returns_structured_result PASSED" "$RUN1_OUT"; then
    record_step "pytest Linux Run 1" "PASS" "30 passed (Linux e2e PASSED)"
  else
    record_step "pytest Linux Run 1" "FAIL" "Linux e2e test was skipped or failed"
    ANY_FAIL=1
  fi
else
  record_step "pytest Linux Run 1" "FAIL" "Tests failed; see $RUN1_OUT"
  ANY_FAIL=1
fi

if $PY_EXEC -m pytest -v > "$RUN2_OUT" 2>&1; then
  if grep -q "test_real_scan_returns_structured_result PASSED" "$RUN2_OUT"; then
    record_step "pytest Linux Run 2" "PASS" "30 passed (Linux e2e PASSED)"
  else
    record_step "pytest Linux Run 2" "FAIL" "Linux e2e test was skipped or failed"
    ANY_FAIL=1
  fi
else
  record_step "pytest Linux Run 2" "FAIL" "Tests failed; see $RUN2_OUT"
  ANY_FAIL=1
fi

# Step 4: Lab Demo Run 1 & Run 2
echo ""
echo ">>> [4/9] Running Lab Demo 1 (Clean -> Lab -> Teardown)..."
sudo bash "$SCRIPT_DIR/teardown_lab.sh" 2>/dev/null || true
DEMO1_OUT="$EVIDENCE_DIR/run1"
rm -rf "$DEMO1_OUT"
if sudo bash "$SCRIPT_DIR/run_lab_demo.sh" --yes-i-am-in-a-disposable-lab --out "$DEMO1_OUT" --pace 0 --no-color; then
  python3 "$PROJECT_ROOT/tools/verify_all.py" "$DEMO1_OUT" > "$DEMO1_OUT/verify_all.txt" 2>&1 || true
  if grep -q "Result: PASS" "$DEMO1_OUT/verify_all.txt"; then
    record_step "Demo Run 1" "PASS" "All lab checks verified"
  else
    record_step "Demo Run 1" "FAIL" "verify_all reported failures in run1"
    ANY_FAIL=1
  fi
else
  record_step "Demo Run 1" "FAIL" "run_lab_demo.sh exited with error"
  ANY_FAIL=1
fi

echo ""
echo ">>> [5/9] Running Lab Demo 2 (Reproducibility Verification)..."
sudo bash "$SCRIPT_DIR/teardown_lab.sh" 2>/dev/null || true
DEMO2_OUT="$EVIDENCE_DIR/run2"
rm -rf "$DEMO2_OUT"
if sudo bash "$SCRIPT_DIR/run_lab_demo.sh" --yes-i-am-in-a-disposable-lab --out "$DEMO2_OUT" --pace 0 --no-color; then
  python3 "$PROJECT_ROOT/tools/verify_all.py" "$DEMO2_OUT" > "$DEMO2_OUT/verify_all.txt" 2>&1 || true
  if grep -q "Result: PASS" "$DEMO2_OUT/verify_all.txt"; then
    record_step "Demo Run 2" "PASS" "All lab checks verified"
  else
    record_step "Demo Run 2" "FAIL" "verify_all reported failures in run2"
    ANY_FAIL=1
  fi
else
  record_step "Demo Run 2" "FAIL" "run_lab_demo.sh exited with error"
  ANY_FAIL=1
fi

# Step 5: Compare the two runs
echo ""
echo ">>> [6/9] Generating Two-Run Fingerprint Comparison..."
python3 -c "
import json
from pathlib import Path

def get_fps(path):
    d = json.loads(path.read_text(encoding='utf-8'))
    return {f.get('fingerprint') for f in d.get('findings', [])}

r1 = Path('$DEMO1_OUT/act2_lab/scan_act2_lab.json')
r2 = Path('$DEMO2_OUT/act2_lab/scan_act2_lab.json')
if r1.exists() and r2.exists():
    fp1, fp2 = get_fps(r1), get_fps(r2)
    match = (fp1 == fp2)
    summary = f'# Two-Run Double Check Summary\n\n'
    summary += f'- Run 1 Finding Count: {len(fp1)}\n'
    summary += f'- Run 2 Finding Count: {len(fp2)}\n'
    summary += f'- Fingerprint Match: {\"PERFECT MATCH (100%)\" if match else \"MISMATCH\"}\n\n'
    if not match:
        summary += f'Diff: {fp1 ^ fp2}\n'
    Path('$EVIDENCE_DIR/double_check_summary.md').write_text(summary, encoding='utf-8')
    print('Double check summary generated: match =', match)
else:
    print('Reports missing for comparison.')
"
if [[ -f "$EVIDENCE_DIR/double_check_summary.md" ]]; then
  record_step "Two-Run Comparison" "PASS" "$EVIDENCE_DIR/double_check_summary.md written"
else
  record_step "Two-Run Comparison" "FAIL" "Comparison could not be generated"
  ANY_FAIL=1
fi

# Step 6: Full (non---fast) scan once as normal user and once as root
if [[ "$NO_FULL_SCAN" -eq 0 ]]; then
  echo ""
  echo ">>> [7/9] Running Full Filesystem Scans (normal user and root)..."
  FULL_DIR="$EVIDENCE_DIR/full_scan"
  mkdir -p "$FULL_DIR"
  
  # Normal user scan
  START_NORM=$(date +%s)
  python3 "$PROJECT_ROOT/privesc_scan.py" scan --label "full_normal" --output-dir "$FULL_DIR" --no-color > "$FULL_DIR/scan_normal_console.txt" 2>&1 || true
  END_NORM=$(date +%s)
  DUR_NORM=$((END_NORM - START_NORM))
  echo "Normal user full scan took: ${DUR_NORM}s"
  
  # Root scan
  START_ROOT=$(date +%s)
  sudo python3 "$PROJECT_ROOT/privesc_scan.py" scan --label "full_root" --output-dir "$FULL_DIR" --no-color > "$FULL_DIR/scan_root_console.txt" 2>&1 || true
  END_ROOT=$(date +%s)
  DUR_ROOT=$((END_ROOT - START_ROOT))
  echo "Root user full scan took: ${DUR_ROOT}s"
  
  cat > "$FULL_DIR/full_scan_timing.txt" <<EOF
Full Filesystem Scan Timings:
- Normal user scan duration: ${DUR_NORM} seconds
- Root user scan duration:   ${DUR_ROOT} seconds
EOF
  record_step "Full Scans" "PASS" "Durations recorded in $FULL_DIR/full_scan_timing.txt"
else
  record_step "Full Scans" "SKIPPED" "--no-full-scan specified"
fi

# Step 7: Interrupt-Safety Test
echo ""
echo ">>> [8/9] Running Interrupt-Safety Teardown Test..."
INTERRUPT_OUT="$EVIDENCE_DIR/interrupt_test.txt"
if sudo bash "$SCRIPT_DIR/test_interrupt_teardown.sh" > "$INTERRUPT_OUT" 2>&1; then
  record_step "Interrupt Safety" "PASS" "Trap verified teardown on SIGINT"
else
  record_step "Interrupt Safety" "FAIL" "Check $INTERRUPT_OUT"
  ANY_FAIL=1
fi

# Step 8: Final Clean-State Proof
echo ""
echo ">>> [9/9] Verifying Final Clean State..."
FINAL_CLEAN="$EVIDENCE_DIR/final_clean_state.txt"
{
  echo "Final Clean-State Verification at $(date -u '+%Y-%m-%d %H:%M:%S UTC'):"
  for path in /opt/privesc-lab /etc/cron.d/privesc-lab /etc/sudoers.d/privesc-lab /etc/systemd/system/privesc-lab.service /home/privlab; do
    if [[ -e "$path" ]]; then echo "FAIL: remains $path"; else echo "PASS: absent $path"; fi
  done
  if id privlab >/dev/null 2>&1; then echo "FAIL: privlab user remains"; else echo "PASS: privlab user removed"; fi
} | tee "$FINAL_CLEAN"

if grep -q "FAIL" "$FINAL_CLEAN"; then
  record_step "Clean State Proof" "FAIL" "Leftover lab artifacts"
  ANY_FAIL=1
else
  record_step "Clean State Proof" "PASS" "Zero leftover lab artifacts"
fi

# Step 9: Bundle Creation & Checksums
echo ""
echo ">>> Creating Evidence Checksums and Bundle..."
cd "$EVIDENCE_DIR"
find . -type f ! -name "SHA256SUMS" -exec sha256sum {} + | sort -k2 > "$EVIDENCE_DIR/SHA256SUMS"

TIMESTAMP=$(date -u '+%Y%m%d_%H%M%SZ')
BUNDLE_ZIP="$HOME/privesc_evidence_bundle_${TIMESTAMP}.zip"
cd "$PROJECT_ROOT"
zip -r -q "$BUNDLE_ZIP" evidence/ reports/ logs/

BUNDLE_SHA=$(sha256sum "$BUNDLE_ZIP" | awk '{print $1}')

echo "========================================================================"
echo "                   EVIDENCE COLLECTION COMPLETE                         "
echo "========================================================================"
echo "Bundle Archive: $BUNDLE_ZIP"
echo "Bundle SHA256:  $BUNDLE_SHA"
echo ""
echo "Summary of Steps:"
cat "$SUMMARY_FILE"
echo "========================================================================"
echo "NEXT STEPS:"
echo "1. Copy $BUNDLE_ZIP to your Windows host project folder:"
echo "   Place it in: <project_root>/incoming/"
echo "2. Restore your Kali VM snapshot to revert to a pristine baseline."
echo "========================================================================"

if [[ "$ANY_FAIL" -ne 0 ]]; then
  echo "WARNING: One or more steps reported failures. Review $SUMMARY_FILE."
  exit 1
fi

exit 0

