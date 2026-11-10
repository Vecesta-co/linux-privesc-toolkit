#!/usr/bin/env python3
"""Render desktop and mobile headless browser screenshots of the static site."""

from __future__ import annotations

import http.server
from pathlib import Path
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
PREVIEW = ROOT / "docs" / "site_preview"
PORT = 8089

EDGE_PATH = Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")
CHROME_PATH = Path("C:/Program Files/Google/Chrome/Application/chrome.exe")


def get_browser() -> str | None:
    if EDGE_PATH.is_file():
        return str(EDGE_PATH)
    if CHROME_PATH.is_file():
        return str(CHROME_PATH)
    return None


def render_screenshots():
    browser = get_browser()
    if not browser:
        print("WARNING: Neither Edge nor Chrome found. Skipping browser screenshots.")
        return

    PREVIEW.mkdir(parents=True, exist_ok=True)

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(SITE), **kwargs)
        def log_message(self, format, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", PORT), QuietHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.5)

    base = f"http://127.0.0.1:{PORT}"
    targets = [
        ("index.html", "index_desktop_1440.png", "1440,900"),
        ("index.html", "index_mobile_390.png", "390,844"),
        ("viewer.html", "viewer_desktop_1440.png", "1440,900"),
        ("viewer.html", "viewer_mobile_390.png", "390,844"),
    ]

    for page, out_name, size in targets:
        url = f"{base}/{page}"
        out_path = PREVIEW / out_name
        cmd = [
            browser,
            "--headless=new",
            "--disable-gpu",
            f"--window-size={size}",
            f"--screenshot={out_path}",
            url,
        ]
        print(f"Capturing {out_name} ({size})...")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if out_path.is_file() and out_path.stat().st_size > 0:
            print(f"  Saved {out_name} ({out_path.stat().st_size} bytes)")
        else:
            print(f"  WARNING: Screenshot failed for {out_name}: {res.stderr}")

    server.shutdown()
    print("Screenshot capture complete.")


if __name__ == "__main__":
    render_screenshots()
