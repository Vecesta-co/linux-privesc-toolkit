"""systemd unit parsing and read-only file inventory."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from .common import file_record, read_text


UNIT_ROOTS = (Path("/etc/systemd/system"), Path("/lib/systemd/system"), Path("/usr/lib/systemd/system"))


def parse_unit(raw: str) -> dict[str, Any]:
    values: dict[str, list[str]] = {"User": [], "ExecStart": [], "Environment": []}
    section = ""
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1]
        elif section == "Service" and "=" in stripped and not stripped.startswith("#"):
            key, value = stripped.split("=", 1)
            if key in values:
                values[key].append(value.strip())
    starts = []
    for entry in values["ExecStart"]:
        command = re.sub(r"^[-@:+!]+", "", entry).split(";", 1)[0].strip()
        pieces = command.split()
        if pieces:
            starts.append({"raw": entry, "executable": pieces[0], "arguments": pieces[1:]})
    return {"user": values["User"][-1] if values["User"] else "root", "exec_start": starts, "environment": values["Environment"]}


def collect() -> list[dict[str, Any]]:
    result = []
    seen: set[str] = set()
    for root in UNIT_ROOTS:
        if not root.exists():
            continue
        for path in root.glob("*.service"):
            key = str(path)
            if key in seen or path.is_symlink():
                continue
            seen.add(key)
            raw, error = read_text(path)
            parsed = parse_unit(raw)
            targets = []
            for start in parsed["exec_start"]:
                executable = start["executable"]
                if executable.startswith("/"):
                    target = file_record(executable)
                    target["parent_record"] = file_record(Path(executable).parent)
                    targets.append(target)
            result.append({"path": key, "file": file_record(path), "parent_record": file_record(path.parent), "parsed": parsed, "target_records": targets, "error": error})
    return result
