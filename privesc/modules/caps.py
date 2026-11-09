"""Linux file capability collection and output parsing."""

from __future__ import annotations

from pathlib import Path

from ..runner import CommandResult, run


def parse_getcap(raw: str) -> list[dict[str, str]]:
    entries = []
    for line in raw.splitlines():
        if "=" not in line:
            continue
        path, capabilities = line.strip().split(None, 1)
        entries.append({"path": path, "capabilities": capabilities})
    return entries


def collect(fast: bool = False, timeout: float = 8.0, log_path: str | Path | None = None, exclude: list[str] | None = None) -> tuple[list[dict[str, str]], CommandResult]:
    roots = ["/etc", "/usr", "/bin", "/sbin", "/lib", "/lib64", "/opt", "/home", "/var", "/root", "/tmp"] if fast else ["/"]
    result = run(["getcap", "-r", *roots], timeout, log_path)
    entries = parse_getcap(result.stdout)
    excluded = exclude or []
    return [item for item in entries if not any(item["path"] == path or item["path"].startswith(path.rstrip("/") + "/") for path in excluded)], result
