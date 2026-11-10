#!/usr/bin/env python3
"""Project consistency and integrity checker for Linux Privilege Escalation Automation Toolkit."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
EVIDENCE = ROOT / "evidence"

REQUIRED_FILES = [
    # Core CLI & library
    "privesc_scan.py",
    "run_scan.sh",
    "privesc/__init__.py",
    "privesc/runner.py",
    "privesc/models.py",
    "privesc/scan.py",
    "privesc/analysis.py",
    "privesc/report.py",
    "privesc/compare.py",
    "privesc/modules/__init__.py",
    "privesc/modules/sysinfo.py",
    "privesc/modules/suid.py",
    "privesc/modules/perms.py",
    "privesc/modules/services.py",
    "privesc/modules/sudo.py",
    "privesc/modules/cron.py",
    "privesc/modules/caps.py",
    "privesc/modules/kernel.py",
    # Data files
    "privesc/data/gtfobins.json",
    "privesc/data/suid_standard.json",
    "privesc/data/kernel_cves.json",
    "privesc/data/kernel_eol.json",
    "privesc/data/dangerous_caps.json",
    # Lab scripts
    "lab/setup_lab.sh",
    "lab/teardown_lab.sh",
    "lab/run_lab_demo.sh",
    "lab/preflight.sh",
    "lab/collect_evidence.sh",
    "lab/test_interrupt_teardown.sh",
    # Deployment & Site
    "config/site.json",
    ".github/workflows/pages.yml",
    "site_src/index.html",
    "site_src/viewer.html",
    "site_src/style.css",
    "site_src/app.js",
    "tests/test_site.py",
    # Tools
    "tools/make_docs.py",
    "tools/make_handoff.py",
    "tools/ingest_evidence.py",
    "tools/verify_all.py",
    "tools/check_consistency.py",
    "tools/render_terminal_png.py",
    "tools/set_live_url.py",
    "tools/build_site.py",
    "tools/check_site.py",
    "tools/render_site_previews.py",
    # Docs
    "README.md",
    "docs/BUILD_LOG.md",
    "docs/DECISIONS.md",
    "docs/AUDIT_FINDINGS.md",
    "docs/IMPROVEMENT_PLAN.md",
    "docs/KALI_HANDOFF_GUIDE.md",
    "docs/LINUX_TEST_GUIDE.md",
    "docs/RECORDING_GUIDE.md",
    "docs/SUBMISSION_CHECKLIST.md",
    "docs/TRACEABILITY_MATRIX.md",
    "docs/CODE_WALKTHROUGH.md",
    "docs/GITHUB_REPO_INFO.md",
    "docs/DEPLOYMENT_GUIDE.md",
    "docs/DEPLOYMENT_PROOF.md",
    "docs/SITE_QA.md",
    "docs/Project_Report.docx",
    "docs/Final_Presentation.pptx",
    "docs/architecture.png",
    "docs/flowchart.png",
    "docs/architecture.drawio",
    "docs/flowchart.drawio",
    "docs/PPT_QA.md",
]

FORBIDDEN_PATTERNS = [
    re.compile(r"(?<![A-Za-z0-9_/-])TODO(?![A-Za-z0-9_/-])"),
    re.compile(r"\blorem\s+ipsum\b", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9_/-])XXX(?![A-Za-z0-9_/-])"),
]

# Paths to skip when scanning text for absolute personal paths or forbidden tokens
SCAN_IGNORE_DIRS = {".git", ".venv", "__pycache__", "dist", "incoming", "docx_render", "ppt_preview", "site", "site_preview"}


def check_file_inventory() -> list[str]:
    missing = []
    for rel_path in REQUIRED_FILES:
        target = ROOT / rel_path
        if not target.exists():
            missing.append(rel_path)
    return missing


def check_line_endings_and_syntax() -> list[str]:
    errors = []
    # Check that all .sh and .py files in git have LF endings
    for path in ROOT.rglob("*"):
        if path.is_file() and any(part in SCAN_IGNORE_DIRS for part in path.parts):
            continue
        if path.suffix in (".sh", ".py", ".json", ".md"):
            try:
                data = path.read_bytes()
                if b"\r\n" in data and path.suffix in (".sh",):
                    errors.append(f"{path.relative_to(ROOT)} has CRLF line endings (must be LF)")
            except Exception as e:
                errors.append(f"Could not read {path.relative_to(ROOT)}: {e}")
    return errors


def check_text_hygiene(is_final: bool) -> list[str]:
    issues = []
    win_user_re = re.compile(r"[A-Za-z]:\\[Uu]sers\\[^\s\"'<>\\/]+")

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SCAN_IGNORE_DIRS for part in path.parts):
            continue
        # Only scan source, docs, and configs
        if path.suffix not in (".py", ".sh", ".md", ".json", ".txt"):
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        rel = path.relative_to(ROOT).as_posix()

        # Check for TODO / lorem / XXX (allow in this file and AUDIT docs if referring to checks)
        if rel not in ("tools/check_consistency.py", "docs/AUDIT_FINDINGS.md", "docs/SUBMISSION_CHECKLIST.md", "docs/SITE_QA.md", "docs/DEPLOYMENT_GUIDE.md"):
            for pat in FORBIDDEN_PATTERNS:
                if pat.search(content):
                    issues.append(f"{rel}: contains forbidden placeholder matching {pat.pattern}")

        # Check for personal Windows paths
        # (Exclude DECISIONS.md or BUILD_LOG.md if recording historical commands, but flag in code/docs)
        if win_user_re.search(content):
            issues.append(f"{rel}: contains absolute Windows user path (leak)")

        # In --final mode, check for "PENDING REAL RUN" in markdown and text docs
        if is_final and rel not in ("tools/check_consistency.py", "tools/make_docs.py", "tools/check_site.py", "docs/BUILD_LOG.md") and "PENDING REAL RUN" in content:
            issues.append(f"{rel}: contains 'PENDING REAL RUN' which is forbidden in final mode")

    return issues


def check_evidence_sync(is_final: bool) -> list[str]:
    issues = []
    ingest_report = EVIDENCE / "INGEST_REPORT.md"
    if is_final:
        if not ingest_report.exists():
            issues.append("Final mode requires evidence/INGEST_REPORT.md")
        else:
            text = ingest_report.read_text(encoding="utf-8", errors="replace")
            if "FAIL" in text:
                issues.append("evidence/INGEST_REPORT.md indicates failures")
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--draft", action="store_true", default=True, help="Allow PENDING REAL RUN")
    mode.add_argument("--final", action="store_true", help="Disallow PENDING REAL RUN, require full evidence")
    args = parser.parse_args()

    is_final = bool(args.final)
    mode_name = "FINAL" if is_final else "DRAFT"
    print(f"=== Project Consistency Check [{mode_name} MODE] ===")

    # 1. File inventory
    missing = check_file_inventory()
    if missing:
        print(f"[FAIL] Missing required files ({len(missing)}):")
        for f in missing:
            print(f"  - {f}")
    else:
        print(f"[PASS] All {len(REQUIRED_FILES)} required files are present.")

    # 2. Line endings
    le_errors = check_line_endings_and_syntax()
    if le_errors:
        print(f"[FAIL] Line ending issues ({len(le_errors)}):")
        for e in le_errors:
            print(f"  - {e}")
    else:
        print("[PASS] Shell script line endings (LF) verified.")

    # 3. Text hygiene
    hygiene_issues = check_text_hygiene(is_final=is_final)
    if hygiene_issues:
        print(f"[FAIL] Text hygiene issues ({len(hygiene_issues)}):")
        for h in hygiene_issues:
            print(f"  - {h}")
    else:
        print("[PASS] Text hygiene check passed (no TODO/lorem/XXX, no personal paths).")

    # 4. Evidence sync
    ev_issues = check_evidence_sync(is_final=is_final)
    if ev_issues:
        print(f"[FAIL] Evidence sync issues ({len(ev_issues)}):")
        for ev in ev_issues:
            print(f"  - {ev}")
    else:
        print(f"[PASS] Evidence sync check passed for {mode_name} mode.")

    total_failures = len(missing) + len(le_errors) + len(hygiene_issues) + len(ev_issues)
    if total_failures > 0:
        print(f"\n[SUMMARY] FAILED with {total_failures} issue(s).")
        sys.exit(1)
    else:
        print(f"\n[SUMMARY] ALL CHECKS PASSED [{mode_name} MODE].")
        sys.exit(0)


if __name__ == "__main__":
    main()
