# Security scan — sample_lab_scan

- **Created:** 2026-11-10T12:57:13.061838+00:00
- **Host:** kali-disposable-lab (privlab, limited)
- **OS / kernel:** Debian GNU/Linux (Kali Linux) / `5.10.0-8-amd64`
- **Overall risk:** Critical

## Summary

| Severity | Count |
|---|---:|
| Critical | 2 |
| High | 7 |
| Medium | 0 |
| Low | 0 |
| Info | 0 |

## Findings

### CRON-001 · Root cron job executes user-writable script

**Severity:** Critical · **Confidence:** High · **Category:** cron

- **Evidence:** `{"owner": "privlab", "path": "/opt/privesc-lab/backup.sh", "source": "/etc/cron.d/privesc-lab", "user": "root"}`
- **Exploitation possibility:** A script executed periodically by root is writable by an unprivileged user. Any commands appended to the script will run with full root privileges on the next schedule.
- **Mitigation:** Change ownership of the script to root:root and set permissions to 0755 or 0700.
- **References:** https://attack.mitre.org/techniques/T1053/003/

### SVC-001 · Systemd service unit executes writable script as root

**Severity:** Critical · **Confidence:** High · **Category:** services

- **Evidence:** `{"exec": "/opt/privesc-lab/service.sh", "owner": "privlab", "unit": "privesc-lab.service"}`
- **Exploitation possibility:** The system service runs as root but executes a script owned or writable by an unprivileged account. Modifying the script gives root code execution upon service activation.
- **Mitigation:** Set root ownership on the service script and restrict file write permissions.
- **References:** https://attack.mitre.org/techniques/T1543/002/

### CAP-001 · Binary with elevated Linux capabilities found

**Severity:** High · **Confidence:** High · **Category:** caps

- **Evidence:** `{"capabilities": "cap_setuid+ep", "path": "/opt/privesc-lab/python_cap"}`
- **Exploitation possibility:** The capability cap_setuid allows the process to arbitrarily change its UID to 0 (root). If attached to an interpreter or utility, full root escalation is trivial.
- **Mitigation:** Remove unnecessary capabilities: setcap -r /opt/privesc-lab/python_cap
- **References:** https://man7.org/linux/man-pages/man7/capabilities.7.html

### KERN-001 · Running kernel version matches known advisory range (Advisory)

**Severity:** High · **Confidence:** Medium · **Category:** kernel

- **Evidence:** `{"cve": "CVE-2022-0847", "kernel": "5.10.0-8-amd64", "vulnerable_range": "5.8 <= version < 5.16.11"}`
- **Exploitation possibility:** Local privilege escalation flaw in the Linux kernel (Dirty Pipe). Notice: Distribution kernels may contain backported fixes; verify against distribution vendor errata.
- **Mitigation:** Update kernel packages via apt/dnf and reboot into the latest security release.
- **References:** https://nvd.nist.gov/vuln/detail/CVE-2022-0847

### PERM-001 · World-writable configuration file

**Severity:** High · **Confidence:** High · **Category:** perms

- **Evidence:** `{"mode": "-rw-rw-rw-", "owner": "root", "path": "/opt/privesc-lab/world_writable.conf"}`
- **Exploitation possibility:** Any local account can alter this configuration file, potentially redirecting application flow, injecting arguments, or tampering with parameters read by root.
- **Mitigation:** Restrict write permissions to root or authorized group: chmod o-w /opt/privesc-lab/world_writable.conf
- **References:** https://attack.mitre.org/techniques/T1222/002/

### PERM-002 · World-writable directory without sticky bit

**Severity:** High · **Confidence:** High · **Category:** perms

- **Evidence:** `{"mode": "drwxrwxrwx", "owner": "root", "path": "/opt/privesc-lab/open_dir"}`
- **Exploitation possibility:** Users can create, replace, or delete files owned by other users within this directory. If a privileged service relies on this directory, symlink or race attacks may occur.
- **Mitigation:** Apply the sticky bit (chmod +t) or remove world-write permissions (chmod o-w).
- **References:** https://attack.mitre.org/techniques/T1222/002/

### SUDO-001 · Sudo NOPASSWD grant detected

**Severity:** High · **Confidence:** High · **Category:** sudo

- **Evidence:** `{"commands": "/usr/bin/find, ALL", "subject": "privlab"}`
- **Exploitation possibility:** The specified user can run privileged commands without supplying a password. If broad or unconstrained, this allows immediate privilege boundary transitions.
- **Mitigation:** Require password authentication and scope sudo permissions to specific commands and parameters.
- **References:** https://attack.mitre.org/techniques/T1548/003/

### SUID-001 · Non-standard SUID binary found

**Severity:** High · **Confidence:** High · **Category:** suid

- **Evidence:** `{"group": "root", "mode": "-rwsr-xr-x", "owner": "root", "path": "/opt/privesc-lab/find_suid"}`
- **Exploitation possibility:** A non-standard SUID executable runs with root privileges. If it contains logic flaws, shell escapes, or relative library loads, a local user may escalate privileges.
- **Mitigation:** Remove the SUID bit if not required: chmod u-s /opt/privesc-lab/find_suid
- **References:** https://gtfobins.github.io/gtfobins/find/, https://attack.mitre.org/techniques/T1548/001/

### SUID-002 · SUID binary with known GTFOBins bypass found

**Severity:** High · **Confidence:** High · **Category:** suid

- **Evidence:** `{"binary": "find", "functions": ["suid", "sudo"], "path": "/opt/privesc-lab/find_suid"}`
- **Exploitation possibility:** The executable has documented command execution or shell breakout capabilities when invoked with elevated privileges.
- **Mitigation:** Review GTFOBins documentation for find and remove SUID bit or restrict execution permissions.
- **References:** https://gtfobins.github.io/gtfobins/find/

## Coverage

| Check | Status | Reason |
|---|---|---|
| sysinfo | ran |  |
| suid | ran |  |
| perms | ran |  |
| services | ran |  |
| sudo | ran |  |
| cron | ran |  |
| caps | ran |  |
| kernel | ran |  |
| shadow_read | skipped | Permission denied (unprivileged account) |

## Commands run

| Command | Exit | Time (s) | Status |
|---|---:|---:|---|
| `id -u; id -un; id -G -n` | 0 | 0.01 | ran |
| `uname -r` | 0 | 0.01 | ran |
| `find / -perm -4000 -o -perm -2000` | 0 | 0.42 | ran |
| `getcap -r /` | 0 | 0.15 | ran |
