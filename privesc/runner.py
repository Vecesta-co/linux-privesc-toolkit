"""The single, timeout-bounded entry point for external commands."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import time
from typing import Sequence


class RunnerError(ValueError):
    """Raised when a requested external command is outside the safe allowlist."""


@dataclass
class CommandResult:
    argv: list[str]
    returncode: int | None
    stdout: str
    stderr: str
    elapsed_seconds: float
    skipped_reason: str = ""


def _validate(argv: Sequence[str]) -> None:
    if not argv or any(not isinstance(arg, str) for arg in argv):
        raise RunnerError("command must be a non-empty list of strings")
    command, args = argv[0], list(argv[1:])
    if command == "id":
        if args not in ([], ["-u"], ["-g"], ["-nG"], ["-un"]):
            raise RunnerError("id arguments are not allowed")
    elif command == "uname":
        if args not in (["-r"], ["-a"], ["-m"]):
            raise RunnerError("uname arguments are not allowed")
    elif command == "find":
        if args == ["--version"]:
            return
        lower = [arg.lower() for arg in args]
        forbidden = {"-exec", "-execdir", "-ok", "-okdir", "-delete", "-fprint", "-fprint0", "-fls"}
        if any(arg in forbidden or arg.startswith(("-fprint", "-fls")) for arg in lower):
            raise RunnerError("dangerous find action is forbidden")
        if not args or not args[0].startswith("/"):
            raise RunnerError("find root must be an absolute Linux path")
        if any(arg in (";", "|", ">", "<", "&&", "||") for arg in args):
            raise RunnerError("shell operators are not valid find arguments")
        if not any(arg in ("-perm",) for arg in args) or not any(arg in ("-type",) for arg in args):
            raise RunnerError("find is limited to permission and type scans")
        if "-printf" not in args:
            raise RunnerError("find must emit structured read-only output")
        if not any(arg in ("/6000", "-0002") for arg in args):
            raise RunnerError("find permission predicate is not allowed")
    elif command == "getcap":
        if len(args) < 2 or args[0] != "-r" or any(not arg.startswith("/") for arg in args[1:]):
            raise RunnerError("getcap is limited to recursive scans of absolute paths")
    elif command == "crontab":
        if args != ["-l"]:
            raise RunnerError("only crontab -l is allowed")
    elif command == "sudo":
        if args == ["-n", "-l"]:
            return
        if len(args) == 4 and args[:3] == ["-n", "-l", "-U"] and args[3].replace("_", "").isalnum():
            return
        raise RunnerError("sudo is limited to non-interactive listing")
    elif command == "systemctl":
        if args != ["list-unit-files", "--type=service"]:
            raise RunnerError("systemctl is limited to listing service unit files")
    else:
        raise RunnerError(f"command is not allowlisted: {command}")


def run(argv: Sequence[str], timeout: float = 8.0, log_path: str | Path | None = None) -> CommandResult:
    """Run an allowlisted argv without a shell; unavailable tools are skipped."""
    _validate(argv)
    if timeout <= 0:
        raise RunnerError("timeout must be positive")
    start = time.monotonic()
    try:
        resolved = shutil.which(argv[0])
        if resolved is None:
            result = CommandResult(list(argv), None, "", "", 0.0, f"tool not installed: {argv[0]}")
        else:
            proc = subprocess.run(list(argv), capture_output=True, text=True, timeout=timeout, check=False, shell=False)
            result = CommandResult(list(argv), proc.returncode, proc.stdout, proc.stderr, time.monotonic() - start)
    except subprocess.TimeoutExpired as exc:
        result = CommandResult(list(argv), None, (exc.stdout or "") if isinstance(exc.stdout, str) else "", "", time.monotonic() - start, f"timeout after {timeout:g}s")
    except OSError as exc:
        result = CommandResult(list(argv), None, "", "", time.monotonic() - start, f"command unavailable: {exc}")
    if log_path:
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {"argv": list(argv), "display": shlex.join(argv), "returncode": result.returncode, "elapsed_seconds": round(result.elapsed_seconds, 3), "skipped_reason": result.skipped_reason}
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")
    return result
