"""Compare two JSON scan reports by stable rule-and-evidence fingerprints."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _key(item: dict[str, Any]) -> tuple[str, str]:
    fingerprint = item.get("fingerprint")
    if not fingerprint:
        from .models import Finding
        candidate = Finding(**{key: item[key] for key in Finding.__dataclass_fields__})
        fingerprint = candidate.fingerprint
    return item.get("id", ""), fingerprint


def compare_data(old: dict[str, Any], new: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    left = {_key(item): item for item in old.get("findings", [])}
    right = {_key(item): item for item in new.get("findings", [])}
    return {"new": [right[k] for k in sorted(right.keys() - left.keys())], "fixed": [left[k] for k in sorted(left.keys() - right.keys())], "unchanged": [right[k] for k in sorted(right.keys() & left.keys())]}


def render_compare(old_path: str | Path, new_path: str | Path, output_dir: str | Path) -> tuple[Path, str]:
    old_data = json.loads(Path(old_path).read_text(encoding="utf-8"))
    new_data = json.loads(Path(new_path).read_text(encoding="utf-8"))
    delta = compare_data(old_data, new_data)
    old_label = Path(old_path).stem.removeprefix("scan_")
    new_label = Path(new_path).stem.removeprefix("scan_")
    lines = [f"# Scan comparison: {old_label} vs {new_label}", "", f"- NEW: {len(delta['new'])}", f"- FIXED: {len(delta['fixed'])}", f"- UNCHANGED: {len(delta['unchanged'])}", ""]
    for status in ("new", "fixed", "unchanged"):
        lines += [f"## {status.upper()}", ""]
        if not delta[status]:
            lines.append("None.")
        for item in delta[status]:
            lines.append(f"- `{item['id']}` {item['title']} — {item.get('evidence', {}).get('path', item.get('evidence', {}).get('command', 'finding'))}")
        lines.append("")
    target = Path(output_dir) / f"compare_{old_label}_vs_{new_label}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")
    console = f"NEW {len(delta['new'])} · FIXED {len(delta['fixed'])} · UNCHANGED {len(delta['unchanged'])}"
    return target, console
