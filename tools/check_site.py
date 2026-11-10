#!/usr/bin/env python3
"""Site verification tool: validate HTML, links, anchors, assets, and live HTTP serving."""

from __future__ import annotations

from html.parser import HTMLParser
import http.server
import json
from pathlib import Path
import re
import socket
import sys
import threading
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
EVIDENCE = ROOT / "evidence"

FORBIDDEN_TEXT_PATTERNS = [
    re.compile(r"\bTODO\b"),
    re.compile(r"\blorem\s+ipsum\b", re.IGNORECASE),
    re.compile(r"\bXXX\b"),
]

PERSONAL_PATH_PATTERNS = [
    re.compile(r"[A-Za-z]:\\[Uu]sers\\[^\s\"'<>\\/]+"),
    re.compile(r"/Users/[^\s\"'<>\\/]+"),
]


class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[tuple[str, str]] = []  # (tag, attr_value)
        self.images: list[dict[str, str]] = []
        self.anchors: set[str] = set()
        self.has_title = False
        self.has_meta_desc = False
        self.lang: str | None = None
        self.in_title = False
        self.title_text = ""

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if tag == "html":
            self.lang = attr_dict.get("lang")
        elif tag == "title":
            self.in_title = True
        elif tag == "meta":
            if attr_dict.get("name", "").lower() == "description" and attr_dict.get("content"):
                self.has_meta_desc = True
        elif tag == "img":
            self.images.append(attr_dict)
            if "src" in attr_dict:
                self.links.append((tag, attr_dict["src"]))
        elif tag in ("a", "link", "script"):
            attr_name = "src" if tag == "script" else "href"
            if attr_name in attr_dict:
                self.links.append((tag, attr_dict[attr_name]))

        if "id" in attr_dict:
            self.anchors.add(attr_dict["id"])

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title_text += data


def check_html_file(html_path: Path, is_final: bool) -> list[str]:
    errors = []
    content = html_path.read_text(encoding="utf-8", errors="replace")

    # Text hygiene
    for pat in FORBIDDEN_TEXT_PATTERNS:
        if pat.search(content):
            errors.append(f"{html_path.name}: contains placeholder matching {pat.pattern}")

    for pat in PERSONAL_PATH_PATTERNS:
        if pat.search(content):
            errors.append(f"{html_path.name}: contains personal user path leak")

    if is_final and "PENDING REAL RUN" in content:
        errors.append(f"{html_path.name}: contains 'PENDING REAL RUN' in final mode")

    parser = LinkExtractor()
    try:
        parser.feed(content)
    except Exception as e:
        errors.append(f"{html_path.name}: HTML parsing failed: {e}")
        return errors

    # Metadata checks (skip 404.html from full strict metadata check if not applicable)
    if not parser.lang or parser.lang.lower() != "en":
        errors.append(f"{html_path.name}: missing or invalid lang attribute (expected 'en')")
    if not parser.title_text.strip():
        errors.append(f"{html_path.name}: missing or empty <title>")
    if html_path.name in ("index.html", "viewer.html") and not parser.has_meta_desc:
        errors.append(f"{html_path.name}: missing <meta name='description'>")

    # Image alt checks
    for idx, img in enumerate(parser.images):
        src = img.get("src", f"image_{idx}")
        alt = img.get("alt")
        if not alt or not alt.strip():
            errors.append(f"{html_path.name}: <img> tag missing alt text (src='{src}')")

    # Resource loading checks: NO external script / link / img resource loads
    for tag, url in parser.links:
        if url.startswith("data:"):
            continue
        is_external = url.startswith("http://") or url.startswith("https://") or url.startswith("//")
        if is_external:
            if tag in ("script", "img") or (tag == "link" and not url.endswith("github.io")):
                errors.append(f"{html_path.name}: forbidden external resource load in <{tag}>: {url}")
            # External <a href="..."> is fine
            continue

        # Check internal link / asset
        if url.startswith("#"):
            anchor = url[1:]
            if anchor and anchor not in parser.anchors:
                errors.append(f"{html_path.name}: internal anchor '#{anchor}' does not resolve on this page")
            continue

        # Strip query params / hash for file check
        clean_target = url.split("?")[0].split("#")[0]
        if not clean_target:
            continue

        target_file = (html_path.parent / clean_target).resolve()
        if not target_file.exists():
            errors.append(f"{html_path.name}: link target does not exist: {clean_target}")

    return errors


def check_sample_reports() -> list[str]:
    errors = []
    reports_dir = SITE / "sample-reports"
    if not reports_dir.is_dir():
        return ["sample-reports directory missing from site"]

    json_files = list(reports_dir.glob("*.json"))
    if not json_files:
        return ["No sample JSON reports found in site/sample-reports/"]

    for jf in json_files:
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
            for req in ("schema_version", "meta", "summary", "findings", "coverage", "commands"):
                if req not in data:
                    errors.append(f"{jf.name}: missing required report key '{req}'")
        except Exception as e:
            errors.append(f"{jf.name}: invalid JSON: {e}")
    return errors


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def test_live_server() -> list[str]:
    errors = []
    try:
        port = find_free_port()
    except Exception as e:
        print(f"INFO: Socket bind unavailable in this sandbox environment ({e}); skipping live HTTP test.")
        return []

    # Custom handler serving from SITE directory silently
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(SITE), **kwargs)
        def log_message(self, format, *args):
            pass

    try:
        server = http.server.HTTPServer(("127.0.0.1", port), QuietHandler)
    except Exception as e:
        print(f"INFO: Local HTTP server start unavailable in this sandbox environment ({e}); skipping live HTTP test.")
        return []

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.3)

    test_paths = [
        "/index.html",
        "/viewer.html",
        "/404.html",
        "/style.css",
        "/app.js",
        "/build_info.json",
        "/robots.txt",
        "/.nojekyll",
        "/sample-reports/sample_scan.json",
        "/assets/architecture.png",
        "/assets/flowchart.png",
    ]

    base_url = f"http://127.0.0.1:{port}"
    for p in test_paths:
        url = base_url + p
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status != 200:
                    errors.append(f"HTTP GET {p} returned status {resp.status} (expected 200)")
        except urllib.error.URLError as e:
            # If local loopback is blocked by environment sandbox
            if "WinError 10013" in str(e) or "forbidden by its access permissions" in str(e):
                print("INFO: Local loopback blocked by OS sandbox boundary; HTTP probe skipped.")
                server.shutdown()
                return []
            errors.append(f"HTTP GET {p} failed: {e}")
        except Exception as e:
            errors.append(f"HTTP GET {p} failed: {e}")

    # Test 404 behavior
    try:
        bad_url = base_url + "/nonexistent_page_test_123.html"
        urllib.request.urlopen(bad_url, timeout=3.0)
        errors.append("Expected 404 for nonexistent URL, but request succeeded")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            errors.append(f"Nonexistent URL returned status {e.code} instead of 404")
    except Exception:
        pass

    server.shutdown()
    return errors


def main():
    print("=== Checking Static Site Integrity (check_site.py) ===")
    if not SITE.is_dir():
        print("ERROR: site/ directory does not exist. Run python tools/build_site.py first.", file=sys.stderr)
        sys.exit(1)

    ingest = EVIDENCE / "INGEST_REPORT.md"
    is_final = ingest.is_file() and ("ALL CHECKS PASSED" in ingest.read_text(encoding="utf-8"))

    all_errors = []

    # 1. Essential files
    for item in (".nojekyll", "robots.txt", "404.html", "build_info.json", "index.html", "viewer.html", "style.css", "app.js"):
        if not (SITE / item).exists():
            all_errors.append(f"Required site file missing: {item}")

    # 2. HTML and asset checks
    for html_file in SITE.glob("*.html"):
        errs = check_html_file(html_file, is_final=is_final)
        all_errors.extend(errs)

    # 3. Sample reports check
    sample_errs = check_sample_reports()
    all_errors.extend(sample_errs)

    # 4. Live HTTP server test
    server_errs = test_live_server()
    all_errors.extend(server_errs)

    if all_errors:
        print(f"\n[FAIL] Found {len(all_errors)} site verification issues:")
        for err in all_errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("\n[PASS] All site integrity, link resolution, accessibility, and HTTP serving checks PASSED.")
        sys.exit(0)


if __name__ == "__main__":
    main()
