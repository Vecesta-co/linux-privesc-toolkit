"""Pure, explainable rules that map collected configuration into findings."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from .models import Finding
from .modules.kernel import eol_series, match_cves, version_tuple


DATA = Path(__file__).parent / "data"


def _json(name: str) -> Any:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def _finding(rule_id: str, category: str, title: str, severity: str, evidence: dict[str, Any], exploitation: str, mitigation: str, references: list[str], module: str, confidence: str = "High") -> Finding:
    return Finding(rule_id, category, title, severity, confidence, evidence, exploitation, mitigation, references, module)


def _user_controlled(record: dict[str, Any]) -> bool:
    try:
        mode = int(record.get("mode", "0"), 8)
        uid = int(record.get("uid", -1))
        gid = int(record.get("gid", 0))
    except (TypeError, ValueError):
        return False
    return bool((uid != 0 and mode & 0o200) or (gid != 0 and mode & 0o020) or (mode & 0o002))


def analyze(collected: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    gtfo = {item["name"]: item for item in _json("gtfobins.json")}
    standard = _json("suid_standard.json")
    dangerous_caps = _json("dangerous_caps.json")

    for item in collected.get("suid", []):
        path = item["path"]
        name = Path(path).name
        gtfo_name = name.removesuffix("_suid").removesuffix("-suid")
        mode = int(item.get("mode", "0"), 8)
        if mode & 0o4000 and path not in standard:
            findings.append(_finding("SUID-001", "SUID/SGID", "Non-standard SUID/SGID binary", "High", item, "A non-standard privilege-bearing binary runs with elevated identity; review its purpose and ownership.", "Remove the SUID/SGID bit where unnecessary and keep privileged binaries root-owned and package-managed.", ["MITRE ATT&CK T1548.001"], "suid"))
        if mode & 0o4000 and gtfo_name in gtfo and "suid" in gtfo[gtfo_name]["contexts"]:
            findings.append(_finding("SUID-002", "SUID/SGID", f"SUID binary has a known high-risk behavior: {gtfo_name}", "High", {**item, "reference": gtfo[gtfo_name]["url"]}, "This program has behavior that can be repurposed when run with elevated identity; the finding indicates exposure, not execution.", "Remove SUID where not required, restrict ownership and permissions, and review package guidance.", [gtfo[gtfo_name]["url"], "MITRE ATT&CK T1548.001"], "suid"))
        elif mode & 0o2000 and gtfo_name in gtfo and "suid" in gtfo[gtfo_name]["contexts"]:
            findings.append(_finding("SUID-002", "SUID/SGID", f"SGID binary has a known high-risk behavior: {gtfo_name}", "Medium", {**item, "reference": gtfo[gtfo_name]["url"]}, "This program may expose elevated group access if its behavior is reachable in this context.", "Remove SGID where not required and validate group ownership and access.", [gtfo[gtfo_name]["url"], "MITRE ATT&CK T1548.001"], "suid"))

    permissions = collected.get("perms", {})
    for item in permissions.get("world_files", []):
        findings.append(_finding("PERM-001", "File permissions", "World-writable file", "High", item, "Any local account may modify this file; privileged consumers can turn that access into a privilege boundary failure.", "Remove world-write permission and review the file's owner, group, and consumers.", ["CWE-732"], "perms"))
    for item in permissions.get("world_dirs", []):
        if item["path"] in ("/tmp", "/var/tmp", "/dev/shm") and int(item.get("mode", "0"), 8) & 0o1000:
            continue
        findings.append(_finding("PERM-002", "File permissions", "World-writable directory without a sticky-bit exception", "High", item, "Local users can create or replace entries in this directory; sensitive consumers should not trust its contents.", "Restrict write access; use a sticky bit only for shared temporary directories that require it.", ["CWE-732"], "perms"))
    for item in permissions.get("sensitive", []):
        try:
            world_write = _user_controlled(item)
        except ValueError:
            world_write = False
        if world_write:
            findings.append(_finding("PERM-003", "File permissions", "Sensitive account or sudo configuration is world-writable", "Critical", item, "Any local account could change authentication or privilege policy through this file.", "Restore vendor-appropriate root ownership and restrictive modes; validate sudo policy with visudo before use.", ["CWE-732", "MITRE ATT&CK T1548.003"], "perms"))
    for item in permissions.get("homes", []):
        try:
            world_write = bool(int(item.get("mode", "0"), 8) & 0o002)
        except ValueError:
            world_write = False
        if item.get("path", "").startswith("/home/") and world_write:
            findings.append(_finding("PERM-004", "File permissions", "Home directory is world-writable", "High", item, "Other local accounts can create or replace content in this user's home, which may affect trusted scripts or files.", "Set the home directory to owner-only or an approved group mode and review its contents.", ["CWE-732"], "perms"))
    for item in permissions.get("path_dirs", []):
        if _user_controlled(item):
            findings.append(_finding("PERM-005", "File permissions", "PATH directory may be writable by an untrusted account", "High", item, "A privileged command that resolves a program through this directory could select an untrusted file.", "Keep every PATH directory root-owned and non-writable by untrusted users; use explicit executable paths in privileged automation.", ["CWE-426"], "perms"))

    for entry in collected.get("sudo", []):
        for command in entry.get("commands", []):
            token = command.split()[0].lstrip("!") if command else ""
            name = Path(token).name
            evidence = {"subject": entry.get("subject"), "runas": entry.get("runas"), "command": command, "raw": entry.get("raw")}
            if entry.get("nopasswd"):
                findings.append(_finding("SUDO-001", "Sudo policy", "Sudo rule permits passwordless commands", "High", evidence, "An account can invoke the listed privileged command without an additional password prompt.", "Remove NOPASSWD where unnecessary and limit rules to exact commands and required arguments.", ["MITRE ATT&CK T1548.003"], "sudo"))
            if (command == "ALL" or command.endswith(": ALL")) and entry.get("subject") not in ("%sudo", "%wheel"):
                findings.append(_finding("SUDO-002", "Sudo policy", "Sudo rule grants unrestricted commands", "Critical", evidence, "The account is authorized to run an unrestricted command set as the configured run-as user.", "Replace broad grants with least-privilege command-specific rules and validate them with visudo.", ["MITRE ATT&CK T1548.003"], "sudo"))
            elif name in gtfo and "sudo" in gtfo[name]["contexts"]:
                findings.append(_finding("SUDO-003", "Sudo policy", f"Sudo grants a high-risk program: {name}", "High", {**evidence, "reference": gtfo[name]["url"]}, "The allowed program has behavior that may cross the intended privilege boundary; no command was executed.", "Remove the rule or constrain it with a wrapper and arguments that cannot start unrelated behavior.", [gtfo[name]["url"], "MITRE ATT&CK T1548.003"], "sudo"))

    for entry in collected.get("cron", []):
        command = entry.get("command", "")
        if entry.get("user", "").lower() == "root":
            record = entry.get("target_record", {})
            parent = record.get("parent_record", {})
            writable = _user_controlled(record) or _user_controlled(parent)
            if record and writable:
                findings.append(_finding("CRON-001", "Cron", "Root cron job invokes a user-controlled script or directory", "Critical", {"source": entry.get("source"), "schedule": entry.get("schedule"), "command": command, **record}, "A local account can change a script or replace its directory entry before a scheduled root job executes it.", "Make the script and its parent directories root-owned and non-writable by untrusted users; review the scheduled command.", ["MITRE ATT&CK T1053.003"], "cron"))
            source_record = entry.get("source_record", {})
            if source_record and _user_controlled(source_record):
                findings.append(_finding("CRON-004", "Cron", "System cron configuration is user-controlled", "Critical", {"source": source_record.get("path"), **source_record}, "A local account can change the scheduled command configuration loaded by cron.", "Restore root ownership and restrict write permission on the cron file and its parent directory.", ["MITRE ATT&CK T1053.003"], "cron"))
            if "*" in command and re.search(r"\b(tar|cpio|rsync)\b", command):
                findings.append(_finding("CRON-002", "Cron", "Root cron command expands a wildcard", "High", {"source": entry.get("source"), "schedule": entry.get("schedule"), "command": command}, "Wildcard expansion can include unexpected directory entries; review how privileged archive or copy jobs handle file names.", "Use an explicit, controlled file list and a dedicated root-owned working directory.", ["MITRE ATT&CK T1053.003"], "cron"))
            command_first = command.split()[0] if command.split() else ""
            if command_first and not command_first.startswith("/") and not command_first.startswith("{"):
                findings.append(_finding("CRON-003", "Cron", "Root cron job uses a relative command path", "Medium", {"source": entry.get("source"), "schedule": entry.get("schedule"), "command": command}, "Cron may resolve a relative executable differently than intended, depending on the job's environment and working directory.", "Use an absolute executable path and a restricted, explicit environment.", ["MITRE ATT&CK T1053.003"], "cron", "Medium"))

    for unit in collected.get("services", []):
        parsed, unit_file = unit.get("parsed", {}), unit.get("file", {})
        if parsed.get("user", "root") == "root":
            if _user_controlled(unit_file) or _user_controlled(unit.get("parent_record", {})):
                findings.append(_finding("SVC-001", "Systemd service", "Root service unit is writable by a non-root account", "Critical", {"path": unit.get("path"), **unit_file}, "A user-controlled unit can change the command or environment used by a root service when it is next started.", "Restore root ownership and remove untrusted write permissions from the unit and parent directory.", ["MITRE ATT&CK T1543.002"], "services"))
            for target in unit.get("target_records", []):
                writable = _user_controlled(target) or _user_controlled(target.get("parent_record", {}))
                if writable:
                    findings.append(_finding("SVC-002", "Systemd service", "Root service executes a user-writable target", "Critical", {"unit": unit.get("path"), **target}, "A local account can change a program that a root service executes.", "Make the executable and its parent directories root-owned and non-writable by untrusted users.", ["MITRE ATT&CK T1543.002"], "services"))
            for value in parsed.get("environment", []):
                if value.startswith("PATH=") and any(part in ("/tmp", ".", "") for part in value[5:].split(":")):
                    findings.append(_finding("SVC-003", "Systemd service", "Root service has an unsafe PATH entry", "High", {"unit": unit.get("path"), "environment": value}, "A privileged service may resolve a command from a location an unprivileged account can control.", "Set an explicit root-owned PATH containing only trusted, absolute directories.", ["MITRE ATT&CK T1543.002"], "services"))

    for item in collected.get("caps", []):
        name = Path(item["path"]).name
        matches = [cap for cap in dangerous_caps if cap in item["capabilities"]]
        if matches:
            findings.append(_finding("CAP-001", "Linux capabilities", "File has a privilege-sensitive capability", "High", {**item, "matched_capabilities": matches}, "A capability can grant a process a privileged operation without ordinary root identity.", "Remove unneeded capabilities and keep any required capability on a narrowly scoped, protected binary.", ["MITRE ATT&CK T1548"], "caps"))
            if name.startswith(("python", "perl", "ruby", "node", "php")) and "cap_setuid" in matches:
                findings.append(_finding("CAP-002", "Linux capabilities", "General-purpose interpreter has cap_setuid", "Critical", {**item, "matched_capabilities": matches}, "A capable interpreter gives its input unusually broad influence over process identity.", "Remove the capability from the interpreter; use a dedicated, minimal helper if this capability is required.", ["MITRE ATT&CK T1548"], "caps"))

    kernel = collected.get("kernel", {})
    version = kernel.get("version", "")
    for cve in match_cves(version):
        findings.append(_finding("KERN-001", "Kernel advisory", f"Kernel version overlaps advisory range for {cve['cve']} ({cve['name']})", "High", {"kernel": version, "cve": cve["cve"], "name": cve["name"], "affected_ranges": cve["affected_ranges"], "verified": cve["verified"], "simulated": kernel.get("simulated", False)}, "The version string overlaps a published local privilege-escalation advisory range; no exploit was run and vendor backports may change applicability.", "Apply the current distribution kernel security updates, reboot into the fixed kernel, and verify status with the vendor advisory.", [*cve["references"], "MITRE ATT&CK T1068"], "kernel", "Medium"))
    series = eol_series(version)
    if series and series[1]:
        findings.append(_finding("KERN-002", "Kernel advisory", "Kernel series is older than the supported upstream baseline", "Medium", {"kernel": version, "series": series[0], "policy": "series below 5.10 are treated as upstream EOL", "simulated": kernel.get("simulated", False)}, "An upstream end-of-life series may no longer receive upstream fixes; the distribution may still backport patches.", "Plan an upgrade to a vendor-supported kernel series and confirm support status with the distribution.", ["https://www.kernel.org/releases.html"], "kernel", "Medium"))

    return findings
