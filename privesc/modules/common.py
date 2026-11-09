"""Small helpers for safe, read-only Linux file inspection."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def read_text(path: str | Path, limit: int = 256_000) -> tuple[str, str]:
    try:
        with Path(path).open("r", encoding="utf-8", errors="replace") as stream:
            return stream.read(limit), ""
    except OSError as exc:
        return "", str(exc)


def file_record(path: str | Path) -> dict[str, Any]:
    item = Path(path)
    try:
        stat = item.lstat()
        return {"path": str(item), "mode": f"{stat.st_mode & 0o7777:04o}", "uid": stat.st_uid, "gid": stat.st_gid, "is_symlink": item.is_symlink(), "size": stat.st_size}
    except OSError as exc:
        return {"path": str(item), "error": str(exc)}


def writable_by_nonroot(record: dict[str, Any]) -> bool:
    try:
        mode = int(record["mode"], 8)
        uid = int(record["uid"])
        return uid != 0 and bool(mode & 0o222) or uid == 0 and bool(mode & 0o002)
    except (KeyError, TypeError, ValueError):
        return False


def linux_memberships() -> tuple[int, set[int]]:
    """Import POSIX-only identity helpers lazily."""
    import os
    return os.getuid(), set(os.getgroups()) | {os.getgid()}
