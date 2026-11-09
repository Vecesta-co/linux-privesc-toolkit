from pathlib import Path

from privesc.modules.caps import parse_getcap
from privesc.modules.cron import parse_crontab
from privesc.modules.kernel import eol_series, in_range, match_cves, version_tuple
from privesc.modules.perms import parse_find_output as parse_writable_find_output
from privesc.modules.services import parse_unit
from privesc.modules.sudo import parse_sudo_list, parse_sudoers
from privesc.modules.suid import parse_find_output
from privesc.modules.sysinfo import parse_os_release


FIXTURES = Path(__file__).parent / "fixtures"


def read(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_os_release_parser_handles_quotes_and_comments():
    parsed = parse_os_release(read("os-release") + "\n# ignored\nEMPTY=\n")
    assert parsed["PRETTY_NAME"] == "Kali GNU/Linux Rolling"
    assert parsed["EMPTY"] == ""
    assert "# ignored" not in parsed


def test_suid_parser_accepts_nul_delimited_find_format():
    rows = parse_find_output(read("find_suid.txt").replace("\n", "\0"))
    assert rows[0] == {"mode": "4755", "uid": "0", "gid": "0", "path": "/opt/privesc-lab/find_suid"}
    assert len(rows) == 3


def test_permissions_parser_reads_world_write_output():
    rows = parse_writable_find_output("0666:0:0:/opt/open.conf\0")
    assert rows == [{"mode": "0666", "uid": "0", "gid": "0", "path": "/opt/open.conf"}]


def test_sudo_parsers_cover_policy_and_list_output():
    rules = parse_sudoers(read("sudoers"))
    assert rules[0]["subject"] == "privlab"
    assert rules[0]["nopasswd"] is True
    assert rules[0]["commands"] == ["/usr/bin/find"]
    listing = parse_sudo_list(read("sudo_list.txt"))
    assert ["ALL"] == listing[-1]["commands"]
    assert listing[0]["nopasswd"] is True


def test_cron_parser_extracts_system_user_and_command():
    entries = parse_crontab(read("crontab"), "/etc/cron.d/example")
    assert entries[0]["schedule"] == "@yearly"
    assert entries[0]["user"] == "root"
    assert entries[1]["command"].endswith("*")
    assert entries[2]["user"] == "backup-user"


def test_systemd_parser_defaults_to_root_and_extracts_target_and_path():
    parsed = parse_unit(read("service.service"))
    assert parsed["user"] == "root"
    assert parsed["exec_start"][0]["executable"] == "/opt/privesc-lab/service_task.sh"
    assert parsed["environment"] == ["PATH=/tmp:/usr/bin:/bin"]


def test_getcap_parser_and_empty_input():
    parsed = parse_getcap(read("getcap.txt"))
    assert parsed[1]["capabilities"] == "cap_setuid=ep"
    assert parse_getcap("no capabilities found\n") == []


def test_kernel_version_parsing_and_advisory_ranges():
    assert version_tuple("6.6.87.2-microsoft-standard-WSL2") == (6, 6, 87)
    assert version_tuple("4.4.0-210-generic") == (4, 4, 0)
    assert version_tuple("unknown") is None
    assert in_range((5, 15, 20), "5.15.0", "5.15.25")
    assert not in_range((5, 15, 25), "5.15.0", "5.15.25")
    assert "CVE-2016-5195" in {x["cve"] for x in match_cves("4.4.0-210-generic")}
    assert eol_series("4.4.0-210-generic") == ("4.4", True)
    assert eol_series("6.6.87.2-microsoft-standard-WSL2") == ("6.6", False)
