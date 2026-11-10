"""Unit and integration tests for the static website and deployment validation."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
BUILD_TOOL = ROOT / "tools" / "build_site.py"
CHECK_TOOL = ROOT / "tools" / "check_site.py"


def test_site_build_and_check():
    """Build the static site and run check_site.py verification."""
    # 1. Build site
    res_build = subprocess.run([sys.executable, str(BUILD_TOOL)], capture_output=True, text=True)
    assert res_build.returncode == 0, f"build_site failed:\n{res_build.stderr}\n{res_build.stdout}"

    # Verify essential artifacts
    expected_files = [
        SITE / "index.html",
        SITE / "viewer.html",
        SITE / "style.css",
        SITE / "app.js",
        SITE / "404.html",
        SITE / ".nojekyll",
        SITE / "robots.txt",
        SITE / "build_info.json",
        SITE / "assets" / "architecture.png",
        SITE / "assets" / "flowchart.png",
        SITE / "sample-reports" / "sample_scan.json",
    ]
    for ef in expected_files:
        assert ef.is_file(), f"Expected artifact missing: {ef}"

    # 2. Check site
    res_check = subprocess.run([sys.executable, str(CHECK_TOOL)], capture_output=True, text=True)
    assert res_check.returncode == 0, f"check_site failed:\n{res_check.stderr}\n{res_check.stdout}"


def test_sample_reports_schema():
    """Verify that all bundled sample reports in site adhere to the scanner schema."""
    reports_dir = SITE / "sample-reports"
    assert reports_dir.is_dir()
    json_files = list(reports_dir.glob("*.json"))
    assert len(json_files) > 0, "No sample JSON reports found"

    for jf in json_files:
        data = json.loads(jf.read_text(encoding="utf-8"))
        for key in ("schema_version", "meta", "summary", "findings", "coverage", "commands"):
            assert key in data, f"Missing required schema key '{key}' in {jf.name}"
        assert isinstance(data["findings"], list)
        assert isinstance(data["summary"], dict)


def test_no_personal_user_leaks_in_site():
    """Ensure no personal Windows user path leaks into the generated site."""
    import re
    win_user_re = re.compile(r"[A-Za-z]:\\[Uu]sers\\[^\s\"'<>\\/]+")

    for path in SITE.rglob("*"):
        if path.is_file() and path.suffix.lower() in (".html", ".css", ".js", ".json", ".txt"):
            content = path.read_text(encoding="utf-8", errors="ignore")
            assert not win_user_re.search(content), f"Personal Windows path detected in {path}"

