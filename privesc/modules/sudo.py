"""Sudo rule parsing and safe read-only collection."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from .common import read_text
from ..runner import CommandResult, run


def parse_sudoers(raw: str) -> list[dict[str, Any]]:
    entries = []
    for original in raw.splitlines():
        line = original.split("#", 1)[0].strip()
        if not line or "=" not in line or line.startswith("Defaults"):
            continue
        left, right = line.split("=", 1)
        if " ALL" not in left and not re.search(r"\S+\s+ALL(?:\s|$)", left):
            continue
        subject = left.split()[0]
        nopasswd = "NOPASSWD:" in right.replace(" ", "") or "NOPASSWD:" in right
        runas = re.findall(r"\(([^)]*)\)", right)
        command_part = right.split(")", 1)[-1] if runas else right
        command_part = command_part.replace("NOPASSWD:", "").replace("PASSWD:", "")
        commands = [item.strip() for item in command_part.split(",") if item.strip()]
        entries.append({"subject": subject, "nopasswd": nopasswd, "runas": runas[-1] if runas else "root", "commands": commands, "raw": original.strip()})
    return entries


def parse_sudo_list(raw: str) -> list[dict[str, Any]]:
    result = []
    for original in raw.splitlines():
        line = original.strip()
        if not line or line.startswith(("Matching Defaults", "User ", "Sudoers", "RunAsUsers")) or "may run the following commands" in line:
            continue
        if "(" not in line and "=" not in line:
            continue
        right = line
        if "=" in right:
            right = right.split("=", 1)[-1].strip()
        runas = re.findall(r"\(([^)]*)\)", right)
        if ")" in right:
            right = right.split(")", 1)[-1].strip()
        nopasswd = "NOPASSWD:" in right
        right = right.replace("NOPASSWD:", "").replace("PASSWD:", "").strip()
        commands = [item.strip() for item in right.split(",") if item.strip()]
        result.append({"subject": "current-user", "nopasswd": nopasswd, "runas": runas[-1] if runas else "root", "commands": commands, "raw": line})
    return result


def collect(timeout: float = 8.0, log_path: str | Path | None = None) -> tuple[list[dict[str, Any]], list[CommandResult], list[str]]:
    entries: list[dict[str, Any]] = []
    results: list[CommandResult] = []
    notes = []
    if Path("/etc/sudoers").exists():
        raw, err = read_text("/etc/sudoers")
        if raw:
            entries.extend(parse_sudoers(raw))
        elif err:
            notes.append(f"/etc/sudoers unreadable: {err}")
    drop = Path("/etc/sudoers.d")
    if drop.is_dir():
        for path in drop.glob("*"):
            if path.is_file() and not path.is_symlink():
                raw, err = read_text(path)
                if raw:
                    entries.extend(parse_sudoers(raw))
                elif err:
                    notes.append(f"{path} unreadable: {err}")
    if not entries or not Path("/etc/sudoers").is_file():
        listing = run(["sudo", "-n", "-l"], timeout, log_path)
        results.append(listing)
        if listing.returncode == 0:
            entries.extend(parse_sudo_list(listing.stdout))
        elif listing.skipped_reason:
            notes.append(listing.skipped_reason)
        elif "password" in listing.stderr.lower():
            notes.append("cannot determine: sudo requires authentication")
        elif listing.stderr:
            notes.append(listing.stderr.strip())
    return entries, results, notes
