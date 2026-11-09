"""Coordinates read-only collectors, analysis rules, and scan metadata."""

from __future__ import annotations

from datetime import datetime, timezone
import platform
from pathlib import Path
import time
from typing import Any

from .analysis import analyze
from .models import ScanResult
from .modules import caps, cron, kernel, perms, services, sudo, suid, sysinfo
from .runner import CommandResult, run


MODULES = ("sysinfo", "suid", "perms", "services", "sudo", "cron", "caps", "kernel")


def _command_record(result: CommandResult) -> dict[str, Any]:
    import shlex
    return {"argv": result.argv, "display": shlex.join(result.argv), "returncode": result.returncode, "elapsed_seconds": round(result.elapsed_seconds, 3), "skipped_reason": result.skipped_reason}


def scan(label: str = "scan", fast: bool = False, modules: list[str] | None = None, timeout: float = 8.0, kernel_override: str | None = None, log_dir: str | Path = "logs", exclude: list[str] | None = None) -> ScanResult:
    if platform.system() != "Linux":
        raise OSError("Linux only — use WSL, Docker, or a Linux VM")
    selected = modules or list(MODULES)
    unknown = set(selected) - set(MODULES)
    if unknown:
        raise ValueError(f"unknown scan modules: {', '.join(sorted(unknown))}")
    logs = Path(log_dir)
    logs.mkdir(parents=True, exist_ok=True)
    command_log = logs / "commands_run.log"
    command_log.write_text("", encoding="utf-8")
    started = time.monotonic()
    collected: dict[str, Any] = {}
    coverage: dict[str, dict[str, str]] = {}
    commands: list[CommandResult] = []

    if "sysinfo" in selected:
        try:
            collected["sysinfo"] = sysinfo.collect(timeout, command_log)
            coverage["sysinfo"] = {"status": "ran", "reason": ""}
        except Exception as exc:
            coverage["sysinfo"] = {"status": "skipped", "reason": str(exc)}
            collected["sysinfo"] = {}
        # sysinfo performs the kernel release query.
        try:
            import json
            commands.extend(_load_command_records(command_log))
        except OSError:
            pass

    def execute(name: str, function: Any, *args: Any) -> Any:
        try:
            response = function(*args, timeout=timeout, log_path=command_log)
            notes: list[str] = []
            if len(response) == 3:
                value, results, notes = response
            else:
                value, results = response
            commands.extend(results if isinstance(results, list) else [results])
            reason = ""
            if any(item.skipped_reason for item in (results if isinstance(results, list) else [results])):
                reason = "; ".join(item.skipped_reason for item in (results if isinstance(results, list) else [results]) if item.skipped_reason)
            if notes:
                reason = "; ".join(filter(None, [reason, "; ".join(notes)]))
            coverage[name] = {"status": "skipped" if reason else "ran", "reason": reason}
            return value
        except Exception as exc:
            coverage[name] = {"status": "skipped", "reason": str(exc)}
            return [] if name in ("suid", "services", "sudo", "cron", "caps") else {}

    if "suid" in selected:
        collected["suid"] = execute("suid", suid.collect, fast, exclude=exclude or [])
    if "perms" in selected:
        collected["perms"] = execute("perms", perms.collect, fast, exclude=exclude or [])
    if "services" in selected:
        try:
            collected["services"] = services.collect()
            coverage["services"] = {"status": "ran", "reason": "Unit files read directly; no active systemd daemon required."}
        except Exception as exc:
            collected["services"] = []
            coverage["services"] = {"status": "skipped", "reason": str(exc)}
    if "sudo" in selected:
        collected["sudo"] = execute("sudo", sudo.collect)
    if "cron" in selected:
        collected["cron"] = execute("cron", cron.collect)
    if "caps" in selected:
        collected["caps"] = execute("caps", caps.collect, fast, exclude=exclude or [])

    if "kernel" in selected:
        check = run(["find", "--version"], timeout, command_log)
        commands.append(check)
        coverage["gnu_find"] = {"status": "ran" if check.returncode == 0 and "GNU findutils" in check.stdout else "skipped", "reason": "" if check.returncode == 0 and "GNU findutils" in check.stdout else check.skipped_reason or "GNU findutils is unavailable; file discovery may be incomplete."}
        sysctl = run(["systemctl", "list-unit-files", "--type=service"], timeout, command_log)
        commands.append(sysctl)
        coverage["systemctl"] = {"status": "ran" if sysctl.returncode == 0 else "skipped", "reason": sysctl.skipped_reason or (sysctl.stderr.strip() if sysctl.returncode else "")}
        real_kernel = collected.get("sysinfo", {}).get("kernel", platform.release())
        collected["kernel"] = {"version": kernel_override or real_kernel, "simulated": bool(kernel_override)}
        coverage["kernel"] = {"status": "ran", "reason": "Version range results are advisory; distribution backports may apply."}

    if "sudo" in selected and not collected.get("sudo"):
        coverage.setdefault("sudo", {"status": "skipped", "reason": "No readable sudo policy or non-interactive listing."})
    if "cron" in selected and not collected.get("cron"):
        coverage.setdefault("cron", {"status": "skipped", "reason": "No readable cron configuration was found."})

    findings = analyze(collected)
    info = collected.get("sysinfo", {})
    wsl = bool(info.get("wsl"))
    meta = {
        **info,
        "label": label,
        "fast": fast,
        "modules": selected,
        "simulated_kernel": bool(kernel_override),
        "exclusions": list(dict.fromkeys(["/proc", "/sys", "/dev", "/run", *( ["/mnt"] if wsl else []), *(exclude or [])])),
        "duration_seconds": round(time.monotonic() - started, 3),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    # Read the structured append-only runner log as the canonical command appendix.
    import json
    command_data = []
    for line in command_log.read_text(encoding="utf-8").splitlines():
        try:
            command_data.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    result = ScanResult(meta=meta, findings=findings, coverage=coverage, commands=command_data)
    event = {"timestamp": result.created_at, "label": label, "findings": result.summary(), "duration_seconds": meta["duration_seconds"]}
    with (logs / "scan.log").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, sort_keys=True) + "\n")
    with (logs / "alerts.log").open("a", encoding="utf-8") as stream:
        for finding in findings:
            if finding.severity in ("High", "Critical"):
                stream.write(f"{result.created_at} {finding.severity} {finding.id} {finding.title}\n")
    return result


def _load_command_records(path: Path) -> list[CommandResult]:
    """Return no live results; command appendix is read from the runner log."""
    return []
