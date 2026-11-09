#!/usr/bin/env python3
"""Verify the expected lab evidence without trusting the scanner's exit code alone."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys


REQUIRED = {"SUID-001", "SUID-002", "PERM-001", "PERM-002", "PERM-004", "CRON-001", "CRON-002", "CRON-003", "SUDO-001", "SUDO-002", "SUDO-003", "SVC-001", "SVC-002", "SVC-003"}


def check(ok: bool, label: str, detail: str = "") -> bool:
    state = "PASS" if ok else "FAIL"
    print(f"[{state}] {label}" + (f" — {detail}" if detail else ""))
    return ok


def finding_ids(path: Path) -> tuple[set[str], dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {item["id"] for item in data.get("findings", [])}, data


def is_lab_finding(item: dict) -> bool:
    evidence = item.get("evidence", {})
    rule = item.get("id", "")
    path = str(evidence.get("path", ""))
    source = str(evidence.get("source", ""))
    subject = str(evidence.get("subject", ""))
    unit = str(evidence.get("unit", ""))
    command = str(evidence.get("command", ""))
    if rule.startswith(("SUID-", "PERM-001", "PERM-002", "CAP-")):
        return path.startswith("/opt/privesc-lab/")
    if rule == "PERM-004":
        return path == "/home/privlab"
    if rule.startswith("CRON-"):
        return source == "/etc/cron.d/privesc-lab" or path.startswith("/opt/privesc-lab/") or command == "backup-relative.sh"
    if rule.startswith("SUDO-"):
        return subject == "privlab"
    if rule.startswith("SVC-"):
        return "privesc-lab" in unit or "privesc-lab" in path or path.startswith("/opt/privesc-lab/")
    return False


def verify(root: Path) -> int:
    failures = 0
    act2 = root / "act2_lab" / "scan_act2_lab.json"
    act3 = root / "act3_fixed" / "scan_act3_fixed.json"
    kernel = root / "act2_kernel_sim" / "scan_act2_kernel_sim.json"
    for path in (act2, act3, kernel):
        failures += not check(path.is_file(), f"report exists: {path.relative_to(root)}")
    if not (act2.is_file() and act3.is_file() and kernel.is_file()):
        return failures + 1

    ids2, data2 = finding_ids(act2)
    ids3, data3 = finding_ids(act3)
    k_ids, kernel_data = finding_ids(kernel)
    manifest_path = root / "lab_manifest.txt"
    manifest = manifest_path.read_text(encoding="utf-8") if manifest_path.exists() else ""
    expected = set(REQUIRED)
    if "SKIPPED python capability" not in manifest:
        expected |= {"CAP-001", "CAP-002"}
    lab_ids = {item["id"] for item in data2.get("findings", []) if is_lab_finding(item)}
    failures += not check(expected <= lab_ids, "expected lab finding IDs present in Act 2", ", ".join(sorted(expected - lab_ids)) if expected - lab_ids else "")
    lab_fingerprints = {item.get("fingerprint") for item in data2.get("findings", []) if is_lab_finding(item)}
    after_fingerprints = {item.get("fingerprint") for item in data3.get("findings", [])}
    failures += not check(not (lab_fingerprints & after_fingerprints), "planted findings absent after teardown", f"{len(lab_fingerprints & after_fingerprints)} lab fingerprints remain")
    failures += not check({"KERN-001", "KERN-002"} <= k_ids, "simulated kernel findings present", ", ".join(sorted({"KERN-001", "KERN-002"} - k_ids)) if not {"KERN-001", "KERN-002"} <= k_ids else "")
    failures += not check(kernel_data.get("meta", {}).get("simulated_kernel") is True, "kernel simulation banner recorded in JSON")

    proof_path = root / "safety_proof.txt"
    proof = proof_path.read_text(encoding="utf-8") if proof_path.exists() else ""
    blocks = re.findall(r"SCAN ([^\n]+)\nBEFORE\n(.*?)\nAFTER\n(.*?)\nSTATUS (PASS|FAIL)", proof, re.S)
    same = bool(blocks) and all(before == after and status == "PASS" for _, before, after, status in blocks)
    failures += not check(same and len(blocks) >= 5, "safety hash proof passed for every scan", f"{len(blocks)} scan checks")

    for label in ("act1_clean", "act2_lab", "act2_lab_limited", "act2_kernel_sim", "act3_fixed"):
        folder = root / label
        present = all((folder / f"scan_{label}.{ext}").is_file() for ext in ("json", "md", "html"))
        failures += not check(present, f"JSON, Markdown, and HTML reports exist: {label}")

    compare = root / "compare_act2_lab_vs_act3_fixed.md"
    text = compare.read_text(encoding="utf-8") if compare.exists() else ""
    fixed_match = re.search(r"FIXED:\s*(\d+)", text)
    failures += not check(bool(fixed_match and int(fixed_match.group(1)) > 0), "compare reports FIXED findings")

    teardown = root / "teardown_check.txt"
    teardown_text = teardown.read_text(encoding="utf-8") if teardown.exists() else ""
    failures += not check(bool(teardown_text) and "FAIL" not in teardown_text, "teardown left no lab artifact")
    independent = root / "independent_check.txt"
    independent_text = independent.read_text(encoding="utf-8") if independent.exists() else ""
    evidence_count = sum(bool(re.search(pattern, independent_text)) for pattern in (r"find_suid", r"world_writable\.conf", r"open_dir", r"backup\.sh", r"python_cap", r"privesc-lab\.service", r"/home/privlab", r"NOPASSWD|\(ALL"))
    failures += not check(evidence_count >= 8, "independent checks cover at least eight planted weaknesses", f"{evidence_count} markers")
    transcript = root / "console_transcript.txt"
    failures += not check(transcript.is_file() and transcript.stat().st_size > 0, "real console transcript recorded")
    print(f"\nResult: {'PASS' if failures == 0 else 'FAIL'} ({failures} failed checks)")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    evidence = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("evidence/run1")
    raise SystemExit(verify(evidence))
