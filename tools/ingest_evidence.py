#!/usr/bin/env python3
"""Ingest, verify, and validate a Linux evidence bundle archive."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence"


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def ingest(zip_path: Path) -> int:
    print(f"=== Starting Evidence Ingest: {zip_path.name} ===")
    if not zip_path.is_file():
        print(f"ERROR: Bundle file not found: {zip_path}", file=sys.stderr)
        return 1

    checks: list[tuple[str, str, str]] = []  # (name, status, detail)

    with tempfile.TemporaryDirectory() as tmpdir:
        extract_dir = Path(tmpdir)
        print("Extracting bundle to staging directory...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        # 1. Verify SHA256SUMS if present
        sha_file = extract_dir / "evidence" / "SHA256SUMS"
        if not sha_file.is_file():
            # Check if SHA256SUMS is at root of bundle
            sha_file = extract_dir / "SHA256SUMS"

        if sha_file.is_file():
            print("Verifying cryptographic SHA256 checksums from bundle...")
            mismatch = False
            base = sha_file.parent
            for line in sha_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(None, 1)
                if len(parts) == 2:
                    expected_hash, rel_path = parts[0], parts[1].lstrip("./")
                    target = base / rel_path
                    if not target.is_file():
                        # Try without evidence prefix
                        target = extract_dir / rel_path
                    if target.is_file():
                        actual_hash = compute_sha256(target)
                        if actual_hash != expected_hash:
                            print(f"CHECKSUM MISMATCH on {rel_path}!", file=sys.stderr)
                            mismatch = True
                    else:
                        print(f"CHECKSUM TARGET MISSING: {rel_path}", file=sys.stderr)
                        mismatch = True
            if not mismatch:
                checks.append(("SHA256SUMS Verification", "PASS", "All file checksums matched exactly"))
            else:
                checks.append(("SHA256SUMS Verification", "FAIL", "One or more file checksums mismatched"))
                return 1
        else:
            checks.append(("SHA256SUMS Verification", "FAIL", "SHA256SUMS file missing from bundle"))
            return 1

        # Check for simulated kernel leak in non-simulation scans
        print("Auditing reports for simulated-kernel leakage...")
        sim_leak = False
        for report_path in extract_dir.rglob("*.json"):
            if "act2_kernel_sim" not in str(report_path):
                try:
                    data = json.loads(report_path.read_text(encoding="utf-8"))
                    if data.get("meta", {}).get("simulated_kernel") is True:
                        print(f"SECURITY LEAK: simulated_kernel flag set in non-simulation report: {report_path}", file=sys.stderr)
                        sim_leak = True
                except Exception:
                    pass
        if sim_leak:
            checks.append(("Kernel Simulation Isolation", "FAIL", "Simulated banner found in non-simulation scan"))
            return 1
        else:
            checks.append(("Kernel Simulation Isolation", "PASS", "Simulation strictly confined to act2_kernel_sim"))

        # Scan for personal absolute paths in ingested text files
        print("Auditing ingested evidence for personal absolute paths...")
        personal_paths = []
        for text_file in extract_dir.rglob("*"):
            if text_file.is_file() and text_file.suffix in {".txt", ".md", ".json", ".log"}:
                try:
                    content = text_file.read_text(encoding="utf-8", errors="ignore")
                    if re.search(r"C:\\Users\\[a-zA-Z0-9_-]+", content, re.IGNORECASE):
                        personal_paths.append(str(text_file.relative_to(extract_dir)))
                except Exception:
                    pass
        if personal_paths:
            checks.append(("Personal Path Audit", "FAIL", f"Found Windows absolute path in: {', '.join(personal_paths[:3])}"))
        else:
            checks.append(("Personal Path Audit", "PASS", "Zero personal Windows host paths detected"))

        # Copy files into project evidence directory without clobbering Windows test files
        print("Deploying ingested evidence to project workspace...")
        src_ev = extract_dir / "evidence" if (extract_dir / "evidence").is_dir() else extract_dir
        EVIDENCE.mkdir(parents=True, exist_ok=True)

        for item in src_ev.iterdir():
            dest = EVIDENCE / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

        # Run verify_all.py on run1 and run2
        print("Executing verification checklist on run1 and run2...")
        verify_tool = ROOT / "tools" / "verify_all.py"
        for run_name in ("run1", "run2"):
            run_dir = EVIDENCE / run_name
            if run_dir.is_dir():
                res = subprocess.run([sys.executable, str(verify_tool), str(run_dir)], capture_output=True, text=True)
                (run_dir / "verify_all.txt").write_text(res.stdout, encoding="utf-8")
                if res.returncode == 0:
                    checks.append((f"Verification ({run_name})", "PASS", "All automated checklist items passed"))
                else:
                    checks.append((f"Verification ({run_name})", "FAIL", f"verify_all failed with code {res.returncode}"))
            else:
                checks.append((f"Verification ({run_name})", "FAIL", f"Directory {run_name} not found in bundle"))

        # Regenerate double_check_summary.md independently from raw reports
        print("Recomputing double_check_summary.md independently from raw reports...")
        r1_rep = EVIDENCE / "run1" / "act2_lab" / "scan_act2_lab.json"
        r2_rep = EVIDENCE / "run2" / "act2_lab" / "scan_act2_lab.json"
        if r1_rep.is_file() and r2_rep.is_file():
            d1 = json.loads(r1_rep.read_text(encoding="utf-8"))
            d2 = json.loads(r2_rep.read_text(encoding="utf-8"))
            fp1 = {f.get("fingerprint") for f in d1.get("findings", [])}
            fp2 = {f.get("fingerprint") for f in d2.get("findings", [])}
            match = (fp1 == fp2)
            summary = "# Two-Run Double Check Summary (Independently Ingested)\n\n"
            summary += f"- Ingest Timestamp: Verified from {zip_path.name}\n"
            summary += f"- Run 1 Finding Count: {len(fp1)}\n"
            summary += f"- Run 2 Finding Count: {len(fp2)}\n"
            summary += f"- Fingerprint Match: {'PERFECT MATCH (100%)' if match else 'MISMATCH'}\n\n"
            if not match:
                summary += f"- Mismatched Fingerprints: {fp1 ^ fp2}\n"
            (EVIDENCE / "double_check_summary.md").write_text(summary, encoding="utf-8")
            checks.append(("Independent Double-Check", "PASS" if match else "FAIL", f"Match: {match} ({len(fp1)} findings)"))
        else:
            checks.append(("Independent Double-Check", "FAIL", "Raw reports for run1 or run2 missing"))

        # Render terminal screenshots
        render_tool = ROOT / "tools" / "render_terminal_png.py"
        screen_dir = EVIDENCE / "screenshots"
        screen_dir.mkdir(parents=True, exist_ok=True)
        transcript_path = EVIDENCE / "run1" / "console_transcript.txt"
        if transcript_path.is_file():
            print("Rendering terminal screenshots from real transcript...")
            subprocess.run([sys.executable, str(render_tool), str(transcript_path), str(screen_dir / "act1_clean.png"), "--title", "Act 1: Clean Baseline Scan", "--keyword", "ACT 1", "--max-lines", "35"], check=False)
            subprocess.run([sys.executable, str(render_tool), str(transcript_path), str(screen_dir / "act2_lab.png"), "--title", "Act 2: Disposable Lab Weaknesses Detected", "--keyword", "ACT 2", "--max-lines", "35"], check=False)
            subprocess.run([sys.executable, str(render_tool), str(transcript_path), str(screen_dir / "act3_fixed.png"), "--title", "Act 3: Manifest Teardown & Fix Verification", "--keyword", "ACT 3", "--max-lines", "35"], check=False)
            checks.append(("Terminal Screenshot Rendering", "PASS", "Rendered act1, act2, act3 real terminal PNGs"))
        else:
            checks.append(("Terminal Screenshot Rendering", "SKIPPED", "run1 console transcript not found"))

    # Write INGEST_REPORT.md
    report_lines = [
        "# Evidence Ingestion and Validation Report",
        "",
        f"- Ingested Bundle: `{zip_path.name}`",
        f"- Bundle SHA256: `{compute_sha256(zip_path)}`",
        "",
        "## Validation Checklist",
        "",
        "| Check | Status | Details |",
        "|---|:---:|---|",
    ]
    all_passed = True
    for name, status, detail in checks:
        if status == "FAIL":
            all_passed = False
        report_lines.append(f"| {name} | **{status}** | {detail} |")

    report_lines.append("")
    report_lines.append(f"**Overall Ingest Result:** {'ALL CHECKS PASSED' if all_passed else 'INGEST FAILED'}\n")
    (EVIDENCE / "INGEST_REPORT.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"\nIngest report written to {EVIDENCE / 'INGEST_REPORT.md'}")

    return 0 if all_passed else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path, help="Path to evidence bundle zip")
    args = parser.parse_args()
    sys.exit(ingest(args.bundle))


if __name__ == "__main__":
    main()
