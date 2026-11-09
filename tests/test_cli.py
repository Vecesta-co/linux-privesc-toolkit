import json

from privesc_scan import main


def test_scan_cli_reports_unsupported_os(monkeypatch, capsys):
    monkeypatch.setattr("privesc_scan.sys.platform", "win32")
    assert main(["scan", "--fast"]) == 2
    assert "Linux only" in capsys.readouterr().err


def test_report_rendering_works_on_any_os(tmp_path):
    source = tmp_path / "input.json"
    source.write_text(json.dumps({"created_at": "now", "meta": {"label": "test"}, "summary": {}, "findings": [], "coverage": {}, "commands": []}), encoding="utf-8")
    assert main(["render", str(source), "--format", "md,html", "--output-dir", str(tmp_path / "out")]) == 0
    assert (tmp_path / "out" / "input.md").exists()
    assert (tmp_path / "out" / "input.html").exists()
