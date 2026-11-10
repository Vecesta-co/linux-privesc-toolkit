#!/usr/bin/env python3
"""Set live URL and repository URL, rebuild static site, and refresh documentation."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = ROOT / "config" / "site.json"
README_FILE = ROOT / "README.md"
DOCS_BUILDER = ROOT / "tools" / "make_docs.py"
SITE_BUILDER = ROOT / "tools" / "build_site.py"
EVIDENCE = ROOT / "evidence"


def update_readme_urls(live_url: str, repo_url: str):
    if not README_FILE.is_file():
        return
    text = README_FILE.read_text(encoding="utf-8")
    
    # Update or add Live Demo badge and section
    if "## Live Demo" in text:
        # Replace existing section
        pattern = r"## Live Demo\n\n[^\n]+\n"
        replacement = f"## Live Demo\n\n- **Live Deployment:** [{live_url}]({live_url})\n- **GitHub Repository:** [{repo_url}]({repo_url})\n"
        text = re.sub(pattern, replacement, text)
    else:
        # Add after author section
        target = "Designed for dual-use in red-team enumeration and blue-team auditing practice.\n"
        demo_sec = (
            f"\n## Live Demo & Documentation Site\n\n"
            f"- **Live Site:** [{live_url}]({live_url})\n"
            f"- **Repository:** [{repo_url}]({repo_url})\n"
        )
        if target in text:
            text = text.replace(target, target + demo_sec)
        else:
            text += demo_sec

    README_FILE.write_text(text, encoding="utf-8")
    print(f"Updated {README_FILE.relative_to(ROOT)} with live URL and repo URL.")


def main():
    if len(sys.argv) < 3:
        print("Usage: python tools/set_live_url.py <live_url> <repo_url>", file=sys.stderr)
        print("Example: python tools/set_live_url.py https://username.github.io/linux-privesc-toolkit https://github.com/username/linux-privesc-toolkit")
        sys.exit(1)

    live_url = sys.argv[1].strip()
    repo_url = sys.argv[2].strip()

    if not CONFIG_FILE.is_file():
        print(f"ERROR: {CONFIG_FILE} not found.", file=sys.stderr)
        sys.exit(1)

    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    config["live_url"] = live_url
    config["repo_url"] = repo_url
    CONFIG_FILE.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {CONFIG_FILE.relative_to(ROOT)}:")
    print(f"  live_url: {live_url}")
    print(f"  repo_url: {repo_url}")

    update_readme_urls(live_url, repo_url)

    # Rebuild site
    if SITE_BUILDER.is_file():
        print("Rebuilding static site...")
        res = subprocess.run([sys.executable, str(SITE_BUILDER)], text=True)
        if res.returncode != 0:
            print("WARNING: Site build failed.", file=sys.stderr)

    # Rebuild docs
    if DOCS_BUILDER.is_file():
        mode_flag = "--final" if (EVIDENCE / "INGEST_REPORT.md").is_file() else "--draft"
        print(f"Rebuilding project report and deck in {mode_flag} mode...")
        res = subprocess.run([sys.executable, str(DOCS_BUILDER), mode_flag], text=True)
        if res.returncode != 0:
            print("WARNING: make_docs failed.", file=sys.stderr)

    print("Live URL configuration complete.")


if __name__ == "__main__":
    main()

