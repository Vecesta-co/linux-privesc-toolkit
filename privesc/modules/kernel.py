"""Kernel version parsing and advisory CVE/EOL matching."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any


def version_tuple(value: str) -> tuple[int, int, int] | None:
    match = re.match(r"^\s*(\d+)\.(\d+)(?:\.(\d+))?", value)
    if not match:
        return None
    return tuple(int(part or 0) for part in match.groups())


def in_range(version: tuple[int, int, int] | None, low: str, high: str) -> bool:
    lower, upper = version_tuple(low), version_tuple(high)
    return bool(version is not None and lower is not None and upper is not None and lower <= version < upper)


def load_data(name: str) -> Any:
    return json.loads((Path(__file__).parents[1] / "data" / name).read_text(encoding="utf-8"))


def match_cves(kernel: str, entries: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    version = version_tuple(kernel)
    entries = entries if entries is not None else load_data("kernel_cves.json")
    matches = []
    for item in entries:
        if any(in_range(version, low, high) for low, high in item.get("affected_ranges", [])):
            matches.append(item)
    return matches


def eol_series(kernel: str) -> tuple[str, bool] | None:
    version = version_tuple(kernel)
    if version is None:
        return None
    return f"{version[0]}.{version[1]}", version < (5, 10, 0)
