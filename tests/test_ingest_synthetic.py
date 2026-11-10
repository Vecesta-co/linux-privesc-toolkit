"""Unit test for evidence ingestion tool against a synthetic mini-bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

import pytest


def test_ingest_synthetic_bundle_passes():
    """Verify ingest_evidence.py against a synthetic fixture bundle in a temp directory."""
    root = Path(__file__).resolve().parents[1]
    ingest_script = root / "tools" / "ingest_evidence.py"

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        ev_dir = tmp / "bundle_src" / "evidence"
        ev_dir.mkdir(parents=True)

        # Create synthetic env info
        (ev_dir / "env_info.txt").write_text("Synthetic Kali Linux x86_64\n", encoding="utf-8")
        (ev_dir / "pytest_linux_run1.txt").write_text("30 passed in 0.5s\n", encoding="utf-8")
        (ev_dir / "pytest_linux_run2.txt").write_text("30 passed in 0.5s\n", encoding="utf-8")

        # Create valid synthetic lab run structures for run1 and run2
        for r_name in ("run1", "run2"):
            r_dir = ev_dir / r_name
            r_dir.mkdir()
            (r_dir / "console_transcript.txt").write_text("ACT 1\nClean\nACT 2\nLab\nACT 3\nFixed\n", encoding="utf-8")
            (r_dir / "safety_proof.txt").write_text(
                "SCAN act1_clean\nBEFORE\nhash1\nAFTER\nhash1\nSTATUS PASS\n"
                "SCAN act2_lab\nBEFORE\nhash1\nAFTER\nhash1\nSTATUS PASS\n"
                "SCAN act2_lab_limited\nBEFORE\nhash1\nAFTER\nhash1\nSTATUS PASS\n"
                "SCAN act2_kernel_sim\nBEFORE\nhash1\nAFTER\nhash1\nSTATUS PASS\n"
                "SCAN act3_fixed\nBEFORE\nhash1\nAFTER\nhash1\nSTATUS PASS\n",
                encoding="utf-8"
            )
            (r_dir / "teardown_check.txt").write_text("PASS absent /opt/privesc-lab\nPASS user removed\n", encoding="utf-8")
            (r_dir / "independent_check.txt").write_text(
                "find_suid world_writable.conf open_dir backup.sh privesc-lab.service /home/privlab NOPASSWD python_cap\n",
                encoding="utf-8"
            )
            (r_dir / "lab_manifest.txt").write_text("/opt/privesc-lab/find_suid\nSKIPPED python capability\n", encoding="utf-8")
            (r_dir / "compare_act2_lab_vs_act3_fixed.md").write_text("- FIXED: 14\n", encoding="utf-8")

            # Create mock scan reports for each act
            for label in ("act1_clean", "act2_lab", "act2_lab_limited", "act2_kernel_sim", "act3_fixed"):
                sub_dir = r_dir / label
                sub_dir.mkdir()
                sim_kernel = (label == "act2_kernel_sim")
                
                # Lab findings for act2
                if label in ("act2_lab", "act2_lab_limited"):
                    findings = [
                        {"id": "SUID-001", "fingerprint": "SUID-001:/opt/privesc-lab/find_suid", "evidence": {"path": "/opt/privesc-lab/find_suid"}},
                        {"id": "SUID-002", "fingerprint": "SUID-002:/opt/privesc-lab/find_suid", "evidence": {"path": "/opt/privesc-lab/find_suid"}},
                        {"id": "PERM-001", "fingerprint": "PERM-001:/opt/privesc-lab/world_writable.conf", "evidence": {"path": "/opt/privesc-lab/world_writable.conf"}},
                        {"id": "PERM-002", "fingerprint": "PERM-002:/opt/privesc-lab/open_dir", "evidence": {"path": "/opt/privesc-lab/open_dir"}},
                        {"id": "PERM-004", "fingerprint": "PERM-004:/home/privlab", "evidence": {"path": "/home/privlab"}},
                        {"id": "CRON-001", "fingerprint": "CRON-001:/opt/privesc-lab/backup.sh", "evidence": {"path": "/opt/privesc-lab/backup.sh", "source": "/etc/cron.d/privesc-lab"}},
                        {"id": "CRON-002", "fingerprint": "CRON-002:tar", "evidence": {"source": "/etc/cron.d/privesc-lab"}},
                        {"id": "CRON-003", "fingerprint": "CRON-003:relative", "evidence": {"command": "backup-relative.sh", "source": "/etc/cron.d/privesc-lab"}},
                        {"id": "SUDO-001", "fingerprint": "SUDO-001:privlab", "evidence": {"subject": "privlab"}},
                        {"id": "SUDO-002", "fingerprint": "SUDO-002:privlab", "evidence": {"subject": "privlab"}},
                        {"id": "SUDO-003", "fingerprint": "SUDO-003:privlab", "evidence": {"subject": "privlab"}},
                        {"id": "SVC-001", "fingerprint": "SVC-001:privesc-lab", "evidence": {"unit": "privesc-lab.service"}},
                        {"id": "SVC-002", "fingerprint": "SVC-002:privesc-lab", "evidence": {"unit": "privesc-lab.service"}},
                        {"id": "SVC-003", "fingerprint": "SVC-003:privesc-lab", "evidence": {"unit": "privesc-lab.service"}},
                    ]
                elif label == "act2_kernel_sim":
                    findings = [
                        {"id": "KERN-001", "fingerprint": "KERN-001:CVE-2016-5195", "evidence": {}},
                        {"id": "KERN-002", "fingerprint": "KERN-002:4.4", "evidence": {}}
                    ]
                else:
                    findings = []

                data = {
                    "schema_version": 1,
                    "meta": {"label": label, "simulated_kernel": sim_kernel},
                    "summary": {"total": len(findings)},
                    "findings": findings,
                    "coverage": {},
                    "commands": []
                }
                (sub_dir / f"scan_{label}.json").write_text(json.dumps(data), encoding="utf-8")
                (sub_dir / f"scan_{label}.md").write_text(f"# Report {label}\n", encoding="utf-8")
                (sub_dir / f"scan_{label}.html").write_text(f"<html><body>{label}</body></html>\n", encoding="utf-8")

        # Generate SHA256SUMS for the synthetic bundle
        sums = []
        for f in ev_dir.rglob("*"):
            if f.is_file():
                h = hashlib.sha256(f.read_bytes()).hexdigest()
                rel = f.relative_to(ev_dir).as_posix()
                sums.append(f"{h}  {rel}")
        (ev_dir / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")

        # Package into zip
        synthetic_zip = tmp / "synthetic_bundle.zip"
        with zipfile.ZipFile(synthetic_zip, "w") as zf:
            for f in ev_dir.rglob("*"):
                if f.is_file():
                    arc = "evidence/" + f.relative_to(ev_dir).as_posix()
                    zf.write(f, arc)

        # Ingest against an isolated staging directory in temp
        isolated_dest = tmp / "ingested_evidence"
        cmd = [sys.executable, str(ingest_script), str(synthetic_zip), "--dest", str(isolated_dest)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode == 0, f"ingest_evidence failed: {res.stderr}\n{res.stdout}"
        assert "Overall Ingest Result: ALL CHECKS PASSED" in res.stdout or (isolated_dest / "INGEST_REPORT.md").read_text(encoding="utf-8").find("ALL CHECKS PASSED") != -1

