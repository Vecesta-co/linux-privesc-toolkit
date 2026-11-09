"""SUID/SGID inventory parsing and collection."""

from __future__ import annotations

from pathlib import Path

from ..runner import CommandResult, run


def parse_find_output(raw: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for row in raw.replace("\x00", "\n").splitlines():
        row = row.strip()
        if not row:
            continue
        pieces = row.split(":", 3)
        if len(pieces) == 4 and pieces[0].isdigit():
            mode, uid, gid, path = pieces
            entries.append({"mode": mode.zfill(4), "uid": uid, "gid": gid, "path": path})
    return entries


def collect(fast: bool = False, timeout: float = 8.0, log_path: str | Path | None = None, exclude: list[str] | None = None) -> tuple[list[dict[str, str]], CommandResult]:
    roots = ["/etc", "/usr", "/bin", "/sbin", "/lib", "/lib64", "/opt", "/home", "/var", "/srv", "/root", "/tmp"] if fast else ["/"]
    args = ["find", *roots, "-xdev"]
    excluded = list(dict.fromkeys(["/proc", "/sys", "/dev", "/run", *(exclude or [])]))
    if excluded:
        args.extend(["("])
        for path in excluded:
            args.extend(["-path", path, "-o"])
        args[-1] = ")"
        args.extend(["-prune", "-o"])
    args.extend(["-type", "f", "-perm", "/6000", "-printf", "%m:%U:%G:%p\\0"])
    result = run(args, timeout, log_path)
    return parse_find_output(result.stdout), result
