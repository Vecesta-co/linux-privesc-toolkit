"""System identity collection and portable OS-release parsing."""

from __future__ import annotations

import os
from pathlib import Path
import platform
import socket
import sys
from typing import Any

from .common import read_text
from ..runner import run


def parse_os_release(raw: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in raw.splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def collect(timeout: float = 8.0, log_path: str | Path | None = None) -> dict[str, Any]:
    uid = os.getuid()
    gid = os.getgid()
    try:
        import pwd
        user = pwd.getpwuid(uid).pw_name
        groups = [pwd.getpwuid(uid).pw_name] if False else []
        import grp
        groups = [grp.getgrgid(group).gr_name for group in os.getgroups()]
    except (ImportError, KeyError):
        user, groups = str(uid), []
    release_text, release_error = read_text("/etc/os-release")
    release = parse_os_release(release_text)
    kernel = run(["uname", "-r"], timeout, log_path)
    version_text, _ = read_text("/proc/version", 4096)
    lower_version = version_text.lower()
    return {
        "user": user, "uid": uid, "gid": gid, "groups": groups,
        "privilege": "root" if uid == 0 else "limited",
        "visibility_note": "A limited scan can only report files and configuration readable by this account." if uid != 0 else "Root-level visibility; kernel and vendor backport checks remain advisory.",
        "hostname": socket.gethostname(), "os": release.get("PRETTY_NAME", platform.platform()),
        "os_id": release.get("ID", "unknown"), "kernel": kernel.stdout.strip() if kernel.returncode == 0 else platform.release(),
        "python": platform.python_version(), "wsl": "microsoft" in lower_version or "WSL_INTEROP" in os.environ,
        "container": Path("/.dockerenv").exists() or "container=" in Path("/proc/1/cgroup").read_text(errors="ignore") if Path("/proc/1/cgroup").exists() else False,
        "os_release_error": release_error,
    }
