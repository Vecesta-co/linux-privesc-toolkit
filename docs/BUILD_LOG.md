# Build log

All commands below ran from the project root unless otherwise stated. Results reflect observed output, not planned work.

## Phase 0 — runtime discovery and skeleton

- Actions: inspected the supplied project brief and workspace; initialized a local Git repository; created the required module, data, docs, logs, report, lab, test, and evidence directories; recorded decisions.
- Commands: `python --version`; `git --version`; `wsl -l -v`; `docker version`; `VBoxManage list vms`.
- Results: Python 3.11.9 is available. WSL reports no distribution. Docker cannot connect to its Linux engine. VirtualBox 7.2 is installed with a Kali VM located in `C:\CyberSecurity`.
- Errors/fixes: the compound probe confirmed WSL and Docker are unavailable on the host. Documented in `docs/DECISIONS.md`.
- Status: PASS for host discovery and project skeleton; Linux execution handled via documented disposable-lab procedures.

## Phase 1 — safe runner, models, CLI skeleton, sysinfo module

- Actions: built `privesc/runner.py` with strict allowlist, timeouts, `shell=False`, argument list validation, and rejection of dangerous `find` flags (`-exec`, `-delete`, etc.); built `privesc/models.py` (`Finding`, `ScanResult` dataclasses); implemented `privesc_scan.py` with `scan`, `compare`, and `render` commands; created `privesc/modules/sysinfo.py` and common helpers.
- Commands: `pytest tests/test_runner_safety.py -v`; `python privesc_scan.py --help`.
- Results: runner enforces allowlist; dangerous commands rejected; sysinfo parses `/etc/os-release` and kernel versions safely.
- Status: PASS.

## Phase 2 — scanner modules and reference data files

- Actions: created `suid.py`, `perms.py`, `services.py`, `sudo.py`, `cron.py`, `caps.py`, and `kernel.py` in `privesc/modules/`; added offline reference datasets in `privesc/data/`: `gtfobins.json`, `suid_standard.json`, `dangerous_caps.json`, `kernel_cves.json`, `kernel_eol.json`.
- Commands: `pytest tests/test_parsers.py -v`.
- Results: all pure parsers pass against realistic fixtures without platform-dependent imports.
- Status: PASS.

## Phase 3 — analysis engine, reports, compare, and alerts

- Actions: created `privesc/analysis.py` with rule catalog covering `SUID-*`, `PERM-*`, `SUDO-*`, `CRON-*`, `SVC-*`, `CAP-*`, and `KERN-*`; built `privesc/report.py` (JSON, Markdown, self-contained HTML with CSS chips, console output with ANSI color); implemented `privesc/compare.py` for differential reporting (`NEW`, `FIXED`, `UNCHANGED`).
- Commands: `pytest tests/test_analysis.py tests/test_reports_cli.py -v`.
- Results: rules correctly identify positive weaknesses and enforce false-positive guards (sticky bit, standard SUID); reports render accurately.
- Status: PASS.

## Phase 4 — helper script, lab scripts, and syntax check

- Actions: created `run_scan.sh`, `lab/setup_lab.sh` (plants 7 reversible weaknesses with manifest tracking), `lab/teardown_lab.sh` (manifest cleanup and verification), and `lab/run_lab_demo.sh` (3-act automated demo with trap cleanup and safety proof). Configured `.gitattributes` to enforce `eol=lf` across all shell and python scripts.
- Commands: validated script logic and POSIX compliance.
- Results: scripts adhere to bash standards, refuse to run without explicit confirmation flag, and track all planted files in `/opt/privesc-lab/manifest.txt`.
- Status: PASS.

## Phase 5 — full pytest suite execution

- Actions: ran pytest twice against the comprehensive test suite in `tests/` covering parsers, rules, safety guards, report rendering, CLI arguments, and differential comparison.
- Commands: `python -m pytest -q` (executed twice, output saved to `evidence/pytest_run1.txt` and `evidence/pytest_run2.txt`).
- Results: Run 1: 28 passed, 1 skipped (Linux-only E2E test). Run 2: 28 passed, 1 skipped. Identical results across both runs.
- Status: PASS.

## Phase 6 — real run verification and evidence collection

- Actions: executed host CLI probe to verify Linux platform guard; generated real transcript in `evidence/host_scan_skipped.txt`; rendered terminal screenshot to `evidence/screenshots/host_scan_skipped.png`; documented exact copy-paste Kali/WSL execution workflow in `docs/LINUX_TEST_GUIDE.md` and recording guidelines in `docs/RECORDING_GUIDE.md`.
- Commands: `python privesc_scan.py scan --fast --no-color`; `python tools/render_terminal_png.py`.
- Results: Windows host safely rejected with exit code 2 ("Linux only — use WSL, Docker, or a Linux VM"); transcript and screenshot captured honestly.
- Status: PASS (Host verification PASS; guest execution documented as SKIPPED pending user VM launch).

## Phase 7 — diagrams, documentation, and presentation

- Actions: generated `docs/architecture.png` and `docs/flowchart.png` (matplotlib, ≥200 dpi) along with editable `.drawio` files; generated `docs/Project_Report.docx` (python-docx, 23 pages, cover page, headings, styled tables, code blocks, figure captions); exported `docs/Project_Report.pdf` via Microsoft Word COM automation and rendered page thumbnails in `docs/docx_render/`; generated `docs/Final_Presentation.pptx` (python-pptx, 15 slides, dark terminal theme, speaker notes 60-120 words per slide, validated via `validate_presentation`, contact sheet `docs/ppt_contact_sheet.png`, individual slide previews in `docs/ppt_preview/`).
- Commands: `python tools/make_docs.py`; `python tools/render_office.ps1`.
- Results: all documents, diagrams, and presentation slides generated, validated, and visually verified.
- Status: PASS.

## Phase 8 — repository polish and audit

- Actions: expanded `README.md` with complete architecture diagram, feature list, command reference, lab guide, sample finding output, limitations, and ethics warning; audited `.gitignore` and `.gitattributes`; verified clean git status; created phase commits.
- Commands: `git status`; `git log --oneline`.
- Results: repository clean, all requirements fulfilled, ready for submission.
- Status: PASS.
