#!/usr/bin/env python3
"""Build the static GitHub Pages site for Linux Privilege Escalation Automation Toolkit."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "site_src"
SITE = ROOT / "site"
DOCS = ROOT / "docs"
EVIDENCE = ROOT / "evidence"
REPORTS = ROOT / "reports"
CONFIG_FILE = ROOT / "config" / "site.json"

MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_SITE_BYTES = 50 * 1024 * 1024  # 50 MB

PRIVACY_PATTERNS = [
    re.compile(r"[A-Za-z]:\\[Uu]sers\\[^\s\"'<>\\/]+"),
    re.compile(r"/Users/[^\s\"'<>\\/]+"),
    re.compile(r"\bghp_[A-Za-z0-9]{36}\b"),  # GitHub personal access tokens
    re.compile(r"\bAIza[0-9A-Za-z-_]{35}\b"),  # Google API keys
]


def load_config() -> dict:
    if CONFIG_FILE.is_file():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "project_name": "Linux Privilege Escalation Automation Toolkit",
        "tagline": "Detection-only Linux security auditing toolkit for authorized systems",
        "author": "Vansh Dhawan",
        "company": "Vecesta.co",
        "program": "Unified Mentor",
        "repo_url": "",
        "live_url": ""
    }


def get_git_commit() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return "unknown"


def is_final_mode() -> bool:
    ingest = EVIDENCE / "INGEST_REPORT.md"
    if ingest.is_file():
        text = ingest.read_text(encoding="utf-8", errors="replace")
        return "ALL CHECKS PASSED" in text and "FAIL" not in text
    return False


def optimize_png(path: Path):
    try:
        from PIL import Image
        with Image.open(path) as img:
            img.save(path, optimize=True)
    except Exception:
        pass


def privacy_scan_file(path: Path) -> list[str]:
    # Only scan text/markup/json
    if path.suffix.lower() not in (".html", ".css", ".js", ".json", ".txt", ".md"):
        return []
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    issues = []
    for pat in PRIVACY_PATTERNS:
        match = pat.search(content)
        if match:
            issues.append(f"{path.relative_to(SITE)} matches forbidden pattern: {match.group(0)}")
    return issues


def build_404_html(config: dict) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Page Not Found (404) | {config.get('project_name', 'Security Toolkit')}</title>
  <link rel="stylesheet" href="style.css">
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%233FB950'><path d='M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z'/></svg>">
</head>
<body style="min-height:100vh;display:flex;align-items:center;justify-content:center;background:#0E1116;color:#E6EDF3;text-align:center;padding:20px;">
  <div style="max-width:550px;background:#161B22;border:1px solid #30363D;border-radius:12px;padding:40px 30px;">
    <div style="font-size:3.5rem;font-weight:800;color:#F85149;margin-bottom:10px;font-family:Consolas,monospace;">404</div>
    <h1 style="font-size:1.6rem;margin-bottom:12px;">Resource Not Found</h1>
    <p style="color:#8B949E;margin-bottom:24px;">The requested security documentation or report path does not exist on this server.</p>
    <a href="index.html" class="btn btn-primary" style="background:#3FB950;color:#0E1116;padding:10px 22px;border-radius:6px;font-weight:700;text-decoration:none;">Return to Documentation Home</a>
  </div>
</body>
</html>
"""


def clean_site_dir(dest: Path):
    dest.mkdir(parents=True, exist_ok=True)
    for item in dest.iterdir():
        try:
            if item.is_file() or item.is_symlink():
                item.unlink(missing_ok=True)
            elif item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
        except Exception:
            pass


def build():
    print("=== Building GitHub Pages Static Site ===")
    config = load_config()
    final_mode = is_final_mode()
    mode_str = "FINAL" if final_mode else "DRAFT"
    print(f"Mode: {mode_str} (Real Linux Evidence Present: {final_mode})")

    # 1. Clean & create site/
    clean_site_dir(SITE)
    assets_dir = SITE / "assets"
    screenshots_dir = assets_dir / "screenshots"
    downloads_dir = SITE / "downloads"
    sample_reports_dir = SITE / "sample-reports"

    assets_dir.mkdir(parents=True, exist_ok=True)
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    downloads_dir.mkdir(parents=True, exist_ok=True)
    sample_reports_dir.mkdir(parents=True, exist_ok=True)

    # 2. Copy site_src files
    if not SRC.is_dir():
        print(f"ERROR: Source directory {SRC} missing.", file=sys.stderr)
        sys.exit(1)

    for item in ("index.html", "viewer.html", "style.css", "app.js"):
        src_file = SRC / item
        if src_file.is_file():
            shutil.copy2(src_file, SITE / item)
        else:
            print(f"ERROR: Required file {src_file} missing.", file=sys.stderr)
            sys.exit(1)

    # 3. Copy diagrams
    for diag in ("architecture.png", "flowchart.png"):
        src_diag = DOCS / diag
        if src_diag.is_file():
            dest_diag = assets_dir / diag
            shutil.copy2(src_diag, dest_diag)
            optimize_png(dest_diag)

    # 4. Copy screenshots
    if (EVIDENCE / "screenshots").is_dir():
        for shot in (EVIDENCE / "screenshots").glob("*.png"):
            dest_shot = screenshots_dir / shot.name
            shutil.copy2(shot, dest_shot)
            optimize_png(dest_shot)

    # 5. Copy sample reports
    if REPORTS.is_dir():
        for r_file in REPORTS.glob("sample_scan.*"):
            shutil.copy2(r_file, sample_reports_dir / r_file.name)

    # Also check if real reports exist in evidence/run1 or evidence/final
    for ev_run in (EVIDENCE / "run1" / "act2_lab", EVIDENCE / "final" / "run1" / "act2_lab"):
        if ev_run.is_dir():
            for rep in ev_run.glob("scan_*.*"):
                shutil.copy2(rep, sample_reports_dir / rep.name)

    # 6. Copy downloads
    for doc in ("Project_Report.pdf", "Project_Report.docx", "Final_Presentation.pptx"):
        src_doc = DOCS / doc
        if src_doc.is_file():
            shutil.copy2(src_doc, downloads_dir / doc)

    # 7. Add GitHub Pages files
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    (SITE / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")
    (SITE / "404.html").write_text(build_404_html(config), encoding="utf-8")

    # 8. Add build_info.json
    build_info = {
        "build_time": datetime.now(timezone.utc).isoformat(),
        "git_commit": get_git_commit(),
        "mode": "final" if final_mode else "draft",
        "project_name": config.get("project_name", ""),
        "tagline": config.get("tagline", ""),
        "author": config.get("author", ""),
        "company": config.get("company", ""),
        "program": config.get("program", ""),
        "repo_url": config.get("repo_url", ""),
        "live_url": config.get("live_url", "")
    }
    (SITE / "build_info.json").write_text(json.dumps(build_info, indent=2) + "\n", encoding="utf-8")

    # 9. Privacy Scan & Size Verification
    print("Executing privacy scan and size audit on generated site...")
    privacy_issues = []
    total_size = 0
    file_count = 0

    for path in SITE.rglob("*"):
        if path.is_file():
            file_count += 1
            size = path.stat().st_size
            total_size += size

            if size > MAX_FILE_BYTES:
                print(f"ERROR: {path.relative_to(SITE)} exceeds 10 MB limit ({size} bytes)", file=sys.stderr)
                sys.exit(1)

            issues = privacy_scan_file(path)
            privacy_issues.extend(issues)

    if privacy_issues:
        print(f"ERROR: Privacy violations detected ({len(privacy_issues)}):", file=sys.stderr)
        for issue in privacy_issues:
            print(f"  - {issue}", file=sys.stderr)
        sys.exit(1)

    if total_size > MAX_SITE_BYTES:
        print(f"ERROR: Total site size exceeds 50 MB limit ({total_size} bytes)", file=sys.stderr)
        sys.exit(1)

    mb = total_size / (1024 * 1024)
    print(f"[PASS] Site built successfully in site/: {file_count} files, {mb:.2f} MB")
    print("Site ready for GitHub Pages publication.")


if __name__ == "__main__":
    build()
