import json
from pathlib import Path

from privesc.compare import compare_data
from privesc.models import Finding, ScanResult
from privesc.report import render_html, render_markdown, write_reports


def finding(rule, path):
    return Finding(rule, "File permissions", f"Finding {rule}", "High", "High", {"path": path}, "Potential impact.", "Fix permissions.", ["CWE-732"], "perms")


def test_json_markdown_and_html_reports(tmp_path):
    result = ScanResult(meta={"label": "sample", "hostname": "lab", "user": "root", "privilege": "root", "kernel": "6.6.1"}, findings=[finding("PERM-001", "/tmp/example")], coverage={"perms": {"status": "ran", "reason": ""}})
    paths = write_reports(result, tmp_path, "scan_sample")
    data = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert set(data) >= {"schema_version", "meta", "summary", "findings", "coverage", "commands"}
    assert "Exploitation possibility" in render_markdown(data)
    assert "<!doctype html>" in render_html(data)
    assert all(path.exists() for path in paths.values())


def test_compare_reports_new_fixed_and_unchanged():
    old = {"findings": [finding("A", "/a").to_dict(), finding("B", "/b").to_dict()]}
    new = {"findings": [finding("A", "/a").to_dict(), finding("C", "/c").to_dict()]}
    delta = compare_data(old, new)
    assert [item["id"] for item in delta["new"]] == ["C"]
    assert [item["id"] for item in delta["fixed"]] == ["B"]
    assert [item["id"] for item in delta["unchanged"]] == ["A"]
