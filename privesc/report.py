"""Self-contained JSON, Markdown, HTML, and console report renderers."""

from __future__ import annotations

from collections import defaultdict
from html import escape
import json
from pathlib import Path
from typing import Any

from .models import ScanResult


COLORS = {"Critical": "#F85149", "High": "#F0883E", "Medium": "#D29922", "Low": "#8B949E", "Info": "#58A6FF"}


def write_json(result: ScanResult, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def render_markdown(data: dict[str, Any]) -> str:
    summary = data.get("summary", {})
    meta = data.get("meta", {})
    lines = [f"# Security scan — {meta.get('label', 'unlabeled')}", "", f"- **Created:** {data.get('created_at', 'unknown')}", f"- **Host:** {meta.get('hostname', 'unknown')} ({meta.get('user', 'unknown')}, {meta.get('privilege', 'unknown')})", f"- **OS / kernel:** {meta.get('os', 'unknown')} / `{meta.get('kernel', 'unknown')}`", f"- **Overall risk:** {summary.get('overall_risk', 'unknown')}"]
    if meta.get("simulated_kernel"):
        lines += ["", "> **SIMULATED KERNEL VERSION** — the kernel shown below was supplied for demonstration; it is not the host's running kernel."]
    if meta.get("wsl"):
        lines += ["", "> WSL detected. Windows drive mounts under `/mnt/*` are excluded from recursive file scans."]
    lines += ["", "## Summary", "", "| Severity | Count |", "|---|---:|"]
    for severity, count in summary.get("by_severity", {}).items():
        lines.append(f"| {severity} | {count} |")
    lines += ["", "## Findings", ""]
    if not data.get("findings"):
        lines.append("No findings matched the enabled rules.")
    for item in sorted(data.get("findings", []), key=lambda f: (f.get("severity", ""), f.get("id", ""), f.get("fingerprint", ""))):
        lines += [f"### {item['id']} · {item['title']}", "", f"**Severity:** {item['severity']} · **Confidence:** {item['confidence']} · **Category:** {item['category']}", "", f"- **Evidence:** `{json.dumps(item.get('evidence', {}), sort_keys=True)}`", f"- **Exploitation possibility:** {item['exploitation']}", f"- **Mitigation:** {item['mitigation']}", f"- **References:** {', '.join(item.get('references', []))}", ""]
    lines += ["## Coverage", "", "| Check | Status | Reason |", "|---|---|---|"]
    for check, value in data.get("coverage", {}).items():
        lines.append(f"| {check} | {value.get('status', 'unknown')} | {value.get('reason', '')} |")
    lines += ["", "## Commands run", ""]
    if data.get("commands"):
        lines += ["| Command | Exit | Time (s) | Status |", "|---|---:|---:|---|"]
        for command in data["commands"]:
            lines.append(f"| `{command.get('display', '')}` | {command.get('returncode')} | {command.get('elapsed_seconds', 0)} | {command.get('skipped_reason', 'ran')} |")
    else:
        lines.append("No external commands were run.")
    return "\n".join(lines) + "\n"


def render_html(data: dict[str, Any]) -> str:
    summary = data.get("summary", {})
    meta = data.get("meta", {})
    cards = "".join(f'<div class="card"><b style="color:{COLORS.get(sev, "#E6EDF3")}">{count}</b><span>{escape(sev)}</span></div>' for sev, count in summary.get("by_severity", {}).items())
    findings = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in data.get("findings", []):
        grouped[item.get("category", "Other")].append(item)
    for category, items in sorted(grouped.items()):
        findings.append(f"<h2>{escape(category)}</h2>")
        for item in items:
            color = COLORS.get(item.get("severity", "Info"), "#58A6FF")
            findings.append(f'<article><span class="chip" style="background:{color}">{escape(item["severity"])}</span><h3>{escape(item["id"])} · {escape(item["title"])}</h3><p><b>Evidence</b>: <code>{escape(json.dumps(item.get("evidence", {}), sort_keys=True))}</code></p><p><b>Possibility</b>: {escape(item["exploitation"])}</p><p><b>Mitigation</b>: {escape(item["mitigation"])}</p><p><b>References</b>: {" · ".join(escape(url) for url in item.get("references", []))}</p></article>')
    coverage_rows = "".join(f"<tr><td>{escape(name)}</td><td>{escape(value.get('status',''))}</td><td>{escape(value.get('reason',''))}</td></tr>" for name, value in data.get("coverage", {}).items())
    banner = '<p class="banner">SIMULATED KERNEL VERSION — demonstration value; not the running host kernel.</p>' if meta.get("simulated_kernel") else ""
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Security scan report</title><style>
body{{margin:0;background:#0E1116;color:#E6EDF3;font:15px/1.55 Segoe UI,Arial,sans-serif}}main{{max-width:1100px;margin:36px auto;padding:0 24px}}header,article,.card{{background:#161B22;border:1px solid #30363D;border-radius:12px;padding:20px}}header{{border-top:4px solid #3FB950}}h1{{margin:0 0 8px}}h2{{margin-top:32px}}h3{{display:inline-block;margin:0 0 14px 10px}}.muted{{color:#8B949E}}.cards{{display:flex;gap:12px;flex-wrap:wrap;margin:20px 0}}.card{{min-width:100px;display:flex;flex-direction:column}}.card b{{font-size:26px}}article{{margin:12px 0}}.chip{{font-size:12px;border-radius:99px;color:#0E1116;font-weight:700;padding:3px 9px}}code{{font-family:Consolas,monospace;overflow-wrap:anywhere}}table{{border-collapse:collapse;width:100%}}td,th{{border-bottom:1px solid #30363D;text-align:left;padding:9px}}.banner{{color:#F85149;font-weight:700}}
</style></head><body><main><header><h1>Linux privilege audit</h1><div class="muted">{escape(str(meta.get('label','scan')))} · {escape(str(meta.get('hostname','unknown')))} · {escape(str(data.get('created_at','')))}</div><p>Overall risk: <b>{escape(str(summary.get('overall_risk','unknown')))}</b> · {summary.get('total',0)} findings</p>{banner}</header><section class="cards">{cards}</section>{''.join(findings)}<h2>Coverage</h2><table><thead><tr><th>Check</th><th>Status</th><th>Reason</th></tr></thead><tbody>{coverage_rows}</tbody></table></main></body></html>'''


def write_reports(result: ScanResult, output_dir: str | Path, stem: str) -> dict[str, Path]:
    data = result.to_dict()
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    targets = {"json": root / f"{stem}.json", "md": root / f"{stem}.md", "html": root / f"{stem}.html"}
    write_json(result, targets["json"])
    targets["md"].write_text(render_markdown(data), encoding="utf-8")
    targets["html"].write_text(render_html(data), encoding="utf-8")
    return targets


def render_console(data: dict[str, Any], no_color: bool = False) -> str:
    summary = data.get("summary", {})
    meta = data.get("meta", {})
    prefix = "" if no_color else "\x1b[1;32m"
    reset = "" if no_color else "\x1b[0m"
    lines = [f"{prefix}Linux Privilege Escalation Automation Toolkit{reset}", f"Host: {meta.get('hostname','?')} · User: {meta.get('user','?')} ({meta.get('privilege','?')}) · Kernel: {meta.get('kernel','?')}"]
    if meta.get("simulated_kernel"):
        lines.append("*** SIMULATED KERNEL VERSION ***")
    lines.append(f"Risk: {summary.get('overall_risk','?')} · Findings: {summary.get('total',0)}")
    for severity, count in summary.get("by_severity", {}).items():
        lines.append(f"  {severity:<8} {count}")
    for item in data.get("findings", []):
        lines.append(f"[{item['severity'].upper():8}] {item['id']} {item['title']}")
    return "\n".join(lines)
