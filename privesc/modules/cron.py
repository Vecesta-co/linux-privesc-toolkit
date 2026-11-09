"""System cron inventory and simple schedule-line parsing."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from .common import file_record, read_text
from ..runner import CommandResult, run


def parse_crontab(raw: str, source: str = "unknown") -> list[dict[str, Any]]:
    entries = []
    for original in raw.splitlines():
        line = original.strip()
        if not line or line.startswith("#") or line.startswith(("SHELL=", "PATH=", "MAILTO=")):
            continue
        parts = line.split()
        if line.startswith("@") and len(parts) >= 3:
            schedule, user, command = parts[0], parts[1], " ".join(parts[2:])
        elif len(parts) >= 7:
            schedule, user, command = " ".join(parts[:5]), parts[5], " ".join(parts[6:])
        elif len(parts) >= 6:
            schedule, user, command = " ".join(parts[:5]), "current-user", " ".join(parts[5:])
        else:
            continue
        entries.append({"source": source, "schedule": schedule, "user": user, "command": command, "raw": line})
    return entries


def collect(timeout: float = 8.0, log_path: str | Path | None = None) -> tuple[list[dict[str, Any]], list[CommandResult], list[str]]:
    entries: list[dict[str, Any]] = []
    results: list[CommandResult] = []
    notes: list[str] = []
    fixed_files = [Path("/etc/crontab")]
    if Path("/etc/cron.d").is_dir():
        fixed_files.extend(Path("/etc/cron.d").glob("*"))
    for root in (Path("/etc/cron.hourly"), Path("/etc/cron.daily"), Path("/etc/cron.weekly"), Path("/etc/cron.monthly")):
        if root.is_dir():
            for path in root.iterdir():
                if path.is_file() and not path.is_symlink():
                    entries.append({"source": str(path), "schedule": root.name, "user": "root", "command": str(path), "raw": str(path)})
    for path in fixed_files:
        if not path.is_file() or path.is_symlink():
            continue
        raw, error = read_text(path)
        if raw:
            entries.extend(parse_crontab(raw, str(path)))
        elif error:
            notes.append(f"{path}: {error}")
    spool = Path("/var/spool/cron/crontabs")
    if spool.is_dir():
        for path in spool.iterdir():
            raw, error = read_text(path)
            if raw:
                entries.extend(parse_crontab(raw, str(path)))
            elif error:
                notes.append(f"{path}: {error}")
    listing = run(["crontab", "-l"], timeout, log_path)
    results.append(listing)
    if listing.returncode == 0:
        entries.extend(parse_crontab(listing.stdout, "crontab -l"))
    elif listing.skipped_reason:
        notes.append(listing.skipped_reason)
    for entry in entries:
        if entry.get("user", "").lower() != "root":
            continue
        source = entry.get("source", "")
        if source.startswith("/") and Path(source).is_file():
            entry["source_record"] = file_record(source)
        paths = re.findall(r"(?<![\w.-])(/[A-Za-z0-9_./+-]+)", entry.get("command", ""))
        target = next((Path(item) for item in paths if Path(item).is_file()), None)
        if target:
            try:
                stat = target.stat()
                entry["target_record"] = {"path": str(target), "mode": f"{stat.st_mode & 0o7777:04o}", "uid": stat.st_uid, "gid": stat.st_gid, "parent_record": file_record(target.parent)}
            except OSError as exc:
                notes.append(f"{target}: {exc}")
    return entries, results, notes
