# Improvement Plan

**Author:** Vansh Dhawan
**Company:** Vecesta.co
**Internship:** Unified Mentor
**Date:** 2026-11-09
**Based on:** `docs/AUDIT_FINDINGS.md`

---

## Action Items by Priority

### Priority 0 (Broken / Critical)
*None. All components function as intended; runner safety is verified.*

---

### Priority 1 (Required-but-Weak)

#### P1-1: Expand `kernel_cves.json` to 7 Well-Known Local Privilege Escalation CVEs
- **Issue:** `privesc/data/kernel_cves.json` contains only 2 CVEs (`CVE-2016-5195` Dirty COW, `CVE-2022-0847` Dirty Pipe). The brief explicitly requests 6–10 candidate CVEs.
- **Remediation:** Add 5 well-known LPE candidates from the brief:
  1. `CVE-2021-22555` (Netfilter heap out-of-bounds write, Linux 2.6.19 - 5.12.4)
  2. `CVE-2021-3493` (Ubuntu OverlayFS user namespace privilege escalation, 3.13 - 5.11)
  3. `CVE-2023-0386` (Linux OverlayFS SUID copy-up privilege escalation, 5.11 - 6.2)
  4. `CVE-2017-16995` (eBPF verifier sign extension vulnerability, 4.9 - 4.14.8)
  5. `CVE-2022-2588` (Route4 cls_route heap out-of-bounds double-free / DirtyCred, 2.6.12 - 5.19)
- **Files Modified:** `privesc/data/kernel_cves.json`
- **Verification:** Unit test `tests/test_parsers.py` and direct script testing against sample kernel versions.

#### P1-2: Strengthen Runner Dangerous Find Argument Unit Test
- **Issue:** In `tests/test_runner_safety.py`, `["find", "/", "-type", "f", "-perm", "/6000", "-exec", "id", ";"]` included `;`, which triggers the shell operator check instead of verifying that `-exec` itself is trapped by the dangerous find action allowlist.
- **Remediation:** Add a test case with structured read-only flags but with `-exec`: `["find", "/", "-type", "f", "-perm", "/6000", "-exec", "id", "-printf", "%p\0"]` to verify that `-exec` alone causes rejection.
- **Files Modified:** `tests/test_runner_safety.py`
- **Verification:** `pytest tests/test_runner_safety.py -v`.

#### P1-3: Drop Privileges to `privlab` for `act2_lab_limited` Scan in Demo Script
- **Issue:** `lab/run_lab_demo.sh` executed `act2_lab_limited` as root, which did not accurately demonstrate the unprivileged user's limited visibility.
- **Remediation:** In `scan_checked()`, when the label is `act2_lab_limited`, execute via `runuser -u privlab -- python3 ...` (with fallback to `su -s /bin/bash privlab -c "..."`).
- **Files Modified:** `lab/run_lab_demo.sh`
- **Verification:** Shell syntax check (`bash -n lab/run_lab_demo.sh`) and command structure verification.

---

### Priority 2 (Polish & Documentation)

#### P2-1: Evidence Loader Path Flexibility in `tools/make_docs.py`
- **Issue:** `make_docs.py` looked only in `evidence/run2` and `evidence/run1`. If the final verification evidence is stored under `evidence/final` or `evidence/final/run1`, `make_docs.py` should discover it automatically.
- **Remediation:** Update `load_real_evidence()` to search `evidence/final/run2`, `evidence/final/run1`, `evidence/final`, `evidence/run2`, and `evidence/run1`.
- **Files Modified:** `tools/make_docs.py`
- **Verification:** Execute `make_docs.py` and inspect evidence resolution.

---

## Execution Schedule & Commits

1. **Commit 1:** Expand `kernel_cves.json` to 7 candidate CVEs (P1-1).
2. **Commit 2:** Strengthen dangerous `find` test in `tests/test_runner_safety.py` (P1-2).
3. **Commit 3:** Update `lab/run_lab_demo.sh` to drop privileges to `privlab` for limited user scan (P1-3).
4. **Commit 4:** Update `tools/make_docs.py` evidence search paths and regenerate documents (P2-1).
5. **Re-verification:** Run pytest twice, re-render docs and presentation, verify contact sheet and validation receipt.
