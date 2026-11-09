#!/usr/bin/env python3
"""Command line interface for scans, comparisons, and report re-rendering."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from privesc import __version__
from privesc.compare import render_compare
from privesc.report import render_console, render_html, render_markdown, write_reports
from privesc.scan import MODULES, scan


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="privesc_scan.py", description="Detection-only Linux privilege-escalation audit toolkit")
    root.add_argument("--version", action="version", version=__version__)
    sub = root.add_subparsers(dest="action", required=True)
    scan_cmd = sub.add_parser("scan", help="collect read-only Linux security configuration")
    scan_cmd.add_argument("--modules", default=",".join(MODULES))
    scan_cmd.add_argument("--fast", action="store_true")
    scan_cmd.add_argument("--exclude", action="append", default=[])
    scan_cmd.add_argument("--timeout", type=float, default=8.0)
    scan_cmd.add_argument("--label", default="scan")
    scan_cmd.add_argument("--output-dir", default="reports")
    scan_cmd.add_argument("--log-dir", default="logs")
    scan_cmd.add_argument("--format", default="json,md,html")
    scan_cmd.add_argument("--kernel-override", help="demonstration only; visibly marked as simulated")
    scan_cmd.add_argument("--no-color", action="store_true")
    compare_cmd = sub.add_parser("compare", help="compare two JSON scan reports")
    compare_cmd.add_argument("old")
    compare_cmd.add_argument("new")
    compare_cmd.add_argument("--output-dir", default="reports")
    render_cmd = sub.add_parser("render", help="re-render reports from JSON on any operating system")
    render_cmd.add_argument("scan_json")
    render_cmd.add_argument("--format", default="md,html")
    render_cmd.add_argument("--output-dir", default="reports")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.action == "scan":
        if sys.platform != "linux":
            print("Linux only — use WSL, Docker, or a Linux VM", file=sys.stderr)
            return 2
        label = re.sub(r"[^A-Za-z0-9_.-]+", "_", args.label).strip("._-") or "scan"
        selected = [name.strip() for name in args.modules.split(",") if name.strip()]
        for excluded in args.exclude:
            path = Path(excluded)
            if not path.is_absolute() or ".." in path.parts:
                print(f"exclude paths must be absolute and may not contain '..': {excluded}", file=sys.stderr)
                return 1
        try:
            result = scan(label, args.fast, selected, args.timeout, args.kernel_override, args.log_dir, args.exclude)
            reports = write_reports(result, args.output_dir, f"scan_{label}")
            print(render_console(result.to_dict(), args.no_color))
            print("Reports: " + ", ".join(str(path) for path in reports.values()))
            return 0
        except Exception as exc:
            print(f"scan failed: {exc}", file=sys.stderr)
            return 1
    if args.action == "compare":
        target, summary = render_compare(args.old, args.new, args.output_dir)
        print(summary)
        print(target)
        return 0
    data = json.loads(Path(args.scan_json).read_text(encoding="utf-8"))
    formats = {value.strip().lower() for value in args.format.split(",") if value.strip()}
    output = Path(args.output_dir)
    stem = Path(args.scan_json).stem
    if "md" in formats:
        target = output / f"{stem}.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_markdown(data), encoding="utf-8")
        print(target)
    if "html" in formats:
        target = output / f"{stem}.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_html(data), encoding="utf-8")
        print(target)
    if "json" in formats:
        target = output / f"{stem}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(target)
    unknown = formats - {"json", "md", "html"}
    if unknown:
        print(f"unsupported formats: {', '.join(sorted(unknown))}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
