import platform

import pytest

from privesc.scan import scan


@pytest.mark.skipif(platform.system() != "Linux", reason="real scanner run requires Linux")
def test_real_scan_returns_structured_result(tmp_path):
    result = scan(label="pytest_e2e", fast=True, modules=["sysinfo", "kernel"], log_dir=tmp_path / "logs")
    assert result.meta["kernel"]
    assert set(result.coverage) >= {"sysinfo", "kernel", "gnu_find"}
