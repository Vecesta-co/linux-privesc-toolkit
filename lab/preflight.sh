#!/usr/bin/env bash
set -euo pipefail

echo "=== Linux Privilege Escalation Toolkit: Preflight Environment Check ==="

MISSING_REQUIRED=0
MISSING_OPTIONAL=0

check_tool() {
  local tool="$1"
  local required="$2"
  local hint="$3"

  if command -v "$tool" >/dev/null 2>&1; then
    printf "[  OK  ] %-15s found: %s\n" "$tool" "$(command -v "$tool")"
    return 0
  else
    if [[ "$required" == "true" ]]; then
      printf "[FAILED] %-15s MISSING (Required) -> Install hint: %s\n" "$tool" "$hint"
      MISSING_REQUIRED=$((MISSING_REQUIRED + 1))
    else
      printf "[ WARN ] %-15s MISSING (Optional) -> Install hint: %s\n" "$tool" "$hint"
      MISSING_OPTIONAL=$((MISSING_OPTIONAL + 1))
    fi
    return 1
  fi
}

# 1. Python 3 (>= 3.10)
if check_tool python3 true "sudo apt-get install -y python3"; then
  PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
  PY_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
  PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
  if [[ "$PY_MAJOR" -lt 3 ]] || { [[ "$PY_MAJOR" -eq 3 ]] && [[ "$PY_MINOR" -lt 10 ]]; }; then
    echo "[FAILED] python3 version is $PY_VER (requires >= 3.10)"
    MISSING_REQUIRED=$((MISSING_REQUIRED + 1))
  else
    printf "[  OK  ] %-15s version %s satisfies >= 3.10\n" "python3-ver" "$PY_VER"
  fi
fi

# 2. GNU find
if check_tool find true "sudo apt-get install -y findutils"; then
  if find --version 2>&1 | grep -iq "gnu find"; then
    printf "[  OK  ] %-15s is GNU find\n" "find-type"
  else
    echo "[ WARN ] find is not GNU find; some -printf predicates may degrade."
  fi
fi

# 3. Required administrative and user-management utilities
check_tool sudo true "sudo apt-get install -y sudo"
check_tool visudo true "sudo apt-get install -y sudo"
check_tool useradd true "sudo apt-get install -y passwd"
check_tool userdel true "sudo apt-get install -y passwd"
check_tool runuser true "sudo apt-get install -y util-linux"
check_tool unzip true "sudo apt-get install -y unzip"
check_tool sha256sum true "sudo apt-get install -y coreutils"

# 4. Optional tools: getcap/setcap (libcap2-bin)
check_tool getcap false "sudo apt-get install -y libcap2-bin (optional; cap scans skipped if missing)"
check_tool setcap false "sudo apt-get install -y libcap2-bin (optional; cap lab weakness skipped if missing)"

# 5. Informational check: systemctl
if command -v systemctl >/dev/null 2>&1; then
  if systemctl is-system-running >/dev/null 2>&1 || [[ "$(systemctl is-system-running 2>&1)" =~ (running|degraded|starting) ]]; then
    printf "[ INFO ] %-15s available and systemd active\n" "systemctl"
  else
    printf "[ INFO ] %-15s available but systemd manager is offline/inactive (scanner reads unit files directly; full compatibility maintained)\n" "systemctl"
  fi
else
  printf "[ INFO ] %-15s not installed (scanner parses unit files directly from /etc/systemd and /lib/systemd)\n" "systemctl"
fi

echo "------------------------------------------------------------------------"
if [[ "$MISSING_REQUIRED" -gt 0 ]]; then
  echo "Preflight check FAILED: $MISSING_REQUIRED required tool(s) missing."
  exit 1
fi

echo "Preflight check PASSED: All required tools are available."
if [[ "$MISSING_OPTIONAL" -gt 0 ]]; then
  echo "Note: $MISSING_OPTIONAL optional tool(s) missing; capabilities checks will gracefully degrade to SKIPPED."
fi
exit 0
