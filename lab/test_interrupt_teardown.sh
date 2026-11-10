#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"

echo "=== Interrupt-Safety Teardown Test ==="
TARGET_LOG="/tmp/privesc_interrupt_test_run.log"
OUTPUT_DIR="/tmp/privesc_interrupt_test_out"
rm -rf "$OUTPUT_DIR" "$TARGET_LOG"
mkdir -p "$OUTPUT_DIR"

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  echo "This test must run as root (or via sudo) to verify lab lifecycle." >&2
  exit 2
fi

echo "Starting lab demo in background with 5s pace..."
bash "$SCRIPT_DIR/run_lab_demo.sh" --yes-i-am-in-a-disposable-lab --out "$OUTPUT_DIR" --pace 5 --no-color > "$TARGET_LOG" 2>&1 &
DEMO_PID=$!

echo "Waiting for Act 2 to plant weaknesses (polling /opt/privesc-lab)..."
WAIT_COUNT=0
while [[ ! -d /opt/privesc-lab ]] && kill -0 "$DEMO_PID" 2>/dev/null; do
  sleep 0.5
  WAIT_COUNT=$((WAIT_COUNT + 1))
  if [[ "$WAIT_COUNT" -gt 60 ]]; then
    echo "Timed out waiting for lab creation."
    kill -KILL "$DEMO_PID" 2>/dev/null || true
    exit 1
  fi
done

# Give it 2 seconds inside Act 2
sleep 2

echo "Sending SIGINT (Ctrl+C simulation) to demo process (PID $DEMO_PID)..."
kill -INT "$DEMO_PID" 2>/dev/null || true

echo "Waiting for process to exit and trap to execute teardown..."
wait "$DEMO_PID" 2>/dev/null || true

echo "Verifying cleanup..."
CLEANUP_FAILED=0

for path in /opt/privesc-lab /etc/cron.d/privesc-lab /etc/sudoers.d/privesc-lab /etc/systemd/system/privesc-lab.service /home/privlab; do
  if [[ -e "$path" ]]; then
    echo "FAIL: $path was NOT cleaned up after interrupt"
    CLEANUP_FAILED=1
  else
    echo "PASS: $path successfully removed"
  fi
done

if id privlab >/dev/null 2>&1; then
  echo "FAIL: privlab user still exists after interrupt"
  CLEANUP_FAILED=1
else
  echo "PASS: privlab user removed"
fi

rm -rf "$OUTPUT_DIR" "$TARGET_LOG"

if [[ "$CLEANUP_FAILED" -eq 0 ]]; then
  echo "Interrupt safety test PASSED: trap successfully tore down all lab weaknesses upon SIGINT."
  exit 0
else
  echo "Interrupt safety test FAILED: leftover artifacts detected."
  exit 1
fi
