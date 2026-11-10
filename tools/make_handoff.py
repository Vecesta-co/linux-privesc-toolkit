#!/usr/bin/env python3
"""Build the clean handoff ZIP archive for deployment into Kali Linux / VM."""

from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"

# Patterns to include in handoff package
INCLUDE_PATTERNS = [
    "privesc_scan.py",
    "run_scan.sh",
    "pytest.ini",
    "requirements-dev.txt",
    "README.md",
    "LICENSE",
    ".gitattributes",
    "privesc/**/*.py",
    "privesc/data/*.json",
    "lab/*.sh",
    "tests/**/*.py",
    "tests/fixtures/*",
    "tools/*.py",
]

EXCLUDE_PARTS = {
    ".venv",
    ".venv*",
    "__pycache__",
    ".pytest_cache",
    ".git",
    "dist",
    "incoming",
    "docs",
    "evidence",
    "logs",
    "reports",
}


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def collect_files() -> list[Path]:
    matched: set[Path] = set()
    for pattern in INCLUDE_PATTERNS:
        for p in ROOT.glob(pattern):
            if p.is_file() and not any(part in p.parts for part in EXCLUDE_PARTS):
                matched.add(p)
    return sorted(matched)


def build_handoff_zip() -> tuple[Path, str]:
    DIST.mkdir(parents=True, exist_ok=True)
    zip_path = DIST / "linux-privesc-toolkit-handoff.zip"
    sha_path = DIST / "SHA256SUMS"

    files = collect_files()
    print(f"Packaging {len(files)} clean source and lab files into {zip_path.name}...")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            arcname = f.relative_to(ROOT).as_posix()
            data = f.read_bytes()

            # Enforce LF endings on text/script files
            if f.suffix in {".sh", ".py", ".json", ".md", ".txt", ".ini", ".gitattributes"} or f.name in {"LICENSE", "crontab", "sudoers", "os-release"}:
                data = data.replace(b"\r\n", b"\n")

            # Set standard POSIX permissions in zip header
            info = zipfile.ZipInfo(arcname)
            # If executable script (.sh or privesc_scan.py), set 0755; else 0644
            if f.suffix == ".sh" or f.name == "privesc_scan.py":
                info.external_attr = 0o100755 << 16
            else:
                info.external_attr = 0o100644 << 16

            zf.writestr(info, data)

    sha = compute_sha256(zip_path)
    sha_path.write_text(f"{sha}  {zip_path.name}\n", encoding="utf-8")
    print(f"Handoff archive built successfully: {zip_path}")
    print(f"SHA-256: {sha}")
    return zip_path, sha


if __name__ == "__main__":
    build_handoff_zip()

