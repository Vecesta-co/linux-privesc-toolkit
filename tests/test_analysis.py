from privesc.analysis import analyze


def base():
    return {
        "suid": [], "perms": {"world_files": [], "world_dirs": [], "sensitive": [], "homes": []},
        "sudo": [], "cron": [], "services": [], "caps": [], "kernel": {"version": "6.6.87", "simulated": False},
    }


def ids(collected):
    return {finding.id for finding in analyze(collected)}


def test_suid_rules_flag_unknown_and_gtfo_binary_but_ignore_standard():
    data = base()
    data["suid"] = [
        {"mode": "4755", "uid": "0", "gid": "0", "path": "/opt/privesc-lab/find_suid"},
        {"mode": "4755", "uid": "0", "gid": "0", "path": "/usr/bin/passwd"},
    ]
    findings = analyze(data)
    assert [item.id for item in findings].count("SUID-001") == 1
    assert [item.id for item in findings].count("SUID-002") == 1


def test_permission_rules_include_sticky_directory_guard_and_sensitive_home():
    data = base()
    data["perms"] = {
        "world_files": [{"path": "/opt/open.conf", "mode": "0666", "uid": 0}],
        "world_dirs": [{"path": "/tmp", "mode": "1777", "uid": 0}, {"path": "/opt/open", "mode": "0777", "uid": 0}],
        "sensitive": [{"path": "/etc/passwd", "mode": "0666", "uid": 0}],
        "homes": [{"path": "/home/privlab", "mode": "0777", "uid": 1000}],
    }
    result = analyze(data)
    assert {"PERM-001", "PERM-002", "PERM-003", "PERM-004"}.issubset({item.id for item in result})
    assert not any(item.evidence.get("path") == "/tmp" for item in result)


def test_permission_rule_finds_writable_path_directory():
    data = base()
    data["perms"]["path_dirs"] = [{"path": "/usr/local/bin", "mode": "0777", "uid": 0, "gid": 0}]
    assert "PERM-005" in ids(data)


def test_sudo_rules_distinguish_passwordless_all_and_gtfo():
    data = base()
    data["sudo"] = [
        {"subject": "privlab", "runas": "root", "nopasswd": True, "commands": ["/usr/bin/find"], "raw": "fixture"},
        {"subject": "privlab", "runas": "root", "nopasswd": True, "commands": ["ALL"], "raw": "fixture"},
    ]
    assert {"SUDO-001", "SUDO-002", "SUDO-003"}.issubset(ids(data))


def test_cron_rules_find_writable_script_wildcards_and_relative_command():
    data = base()
    data["cron"] = [
        {"user": "root", "schedule": "@yearly", "command": "/opt/privesc-lab/backup.sh", "source": "cron fixture", "target_record": {"path": "/opt/privesc-lab/backup.sh", "mode": "0777", "uid": 0}},
        {"user": "root", "schedule": "@yearly", "command": "tar -cf /tmp/archive *", "source": "cron fixture"},
        {"user": "root", "schedule": "@yearly", "command": "backup-relative.sh", "source": "cron fixture"},
    ]
    assert {"CRON-001", "CRON-002", "CRON-003"}.issubset(ids(data))


def test_cron_rule_finds_user_controlled_configuration_file():
    data = base()
    data["cron"] = [{"user": "root", "command": "/usr/bin/true", "source": "/etc/cron.d/lab", "source_record": {"path": "/etc/cron.d/lab", "mode": "0666", "uid": 0, "gid": 0}}]
    assert "CRON-004" in ids(data)


def test_service_rules_and_safe_path_guard():
    data = base()
    data["services"] = [{
        "path": "/etc/systemd/system/lab.service", "file": {"path": "/etc/systemd/system/lab.service", "mode": "0666", "uid": 0},
        "parsed": {"user": "root", "exec_start": [{"executable": "/opt/lab/task.sh"}], "environment": ["PATH=/tmp:/usr/bin:/bin"]},
        "target_records": [{"path": "/opt/lab/task.sh", "mode": "0777", "uid": 0}],
    }]
    assert {"SVC-001", "SVC-002", "SVC-003"}.issubset(ids(data))


def test_capabilities_and_kernel_rules():
    data = base()
    data["caps"] = [{"path": "/opt/privesc-lab/python_cap", "capabilities": "cap_setuid+ep"}]
    data["kernel"] = {"version": "4.4.0-210-generic", "simulated": True}
    assert {"CAP-001", "CAP-002", "KERN-001", "KERN-002"}.issubset(ids(data))
