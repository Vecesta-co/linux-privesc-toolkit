"""World-writeable and sensitive-path checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import file_record
from ..runner import CommandResult, run


SENSITIVE = ("/etc/passwd", "/etc/shadow", "/etc/group", "/etc/sudoers", "/etc/sudoers.d")
FAST_ROOTS = ("/etc", "/usr", "/bin", "/sbin", "/lib", "/lib64", "/opt", "/home", "/var", "/srv", "/root", "/tmp")


def _find(kind: str, fast: bool, timeout: float, log_path: str | Path | None, exclude: list[str] | None = None) -> CommandResult:
    roots = list(FAST_ROOTS) if fast else ["/"]
    args = ["find", *roots, "-xdev"]
    excluded = list(dict.fromkeys(["/proc", "/sys", "/dev", "/run", *(exclude or [])]))
    if excluded:
        args.append("(")
        for path in excluded:
            args.extend(["-path", path, "-o"])
        args[-1] = ")"
        args.extend(["-prune", "-o"])
    args.extend(["-type", kind, "-perm", "-0002", "-printf", "%m:%U:%G:%p\\0"])
    return run(args, timeout, log_path)


def parse_find_output(raw: str) -> list[dict[str, str]]:
    result = []
    for row in raw.replace("\x00", "\n").splitlines():
        pieces = row.strip().split(":", 3)
        if len(pieces) == 4 and pieces[0].isdigit():
            result.append({"mode": pieces[0].zfill(4), "uid": pieces[1], "gid": pieces[2], "path": pieces[3]})
    return result


def collect(fast: bool = False, timeout: float = 8.0, log_path: str | Path | None = None, exclude: list[str] | None = None) -> tuple[dict[str, Any], list[CommandResult]]:
    file_result = _find("f", fast, timeout, log_path, exclude)
    dir_result = _find("d", fast, timeout, log_path, exclude)
    sensitive = [file_record(path) for path in SENSITIVE if Path(path).exists()]
    homes = [file_record(path) for path in (Path("/home").glob("*") if Path("/home").exists() else [])]
    if Path("/root").exists():
        homes.append(file_record("/root"))
    path_dirs = [entry for entry in ("/usr/local/sbin", "/usr/local/bin", "/usr/sbin", "/usr/bin", "/sbin", "/bin") if entry in __import__("os").environ.get("PATH", "").split(":")]
    path_records = [file_record(path) for path in path_dirs]
    return {"world_files": parse_find_output(file_result.stdout), "world_dirs": parse_find_output(dir_result.stdout), "sensitive": sensitive, "homes": homes, "path_dirs": path_records}, [file_result, dir_result]
