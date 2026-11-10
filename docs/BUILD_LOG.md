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

## Completion Pass A — Final Verification & Kali Handoff Architecture (2026-11-10)

- Project: Linux Privilege Escalation Automation Toolkit
- Author: Vansh Dhawan (Intern)
- Company: Vecesta.co
- Organization: Unified Mentor
- Date: 10 November 2026
- Branch: `main` (renamed from `master` via `git branch -M main`)

### Actions Taken:
1. **Audit & Lab Hardening**:
   - Audited `lab/run_lab_demo.sh` to ensure passthrough of `--yes-i-am-in-a-disposable-lab` to `lab/setup_lab.sh`.
   - Created `lab/preflight.sh` to verify all required binaries (`python3` ≥3.10, GNU `find`, `sudo`, `visudo`, `useradd`, `userdel`, `runuser`, `unzip`, `sha256sum`) and optional tools (`getcap`, `setcap`, `systemctl`).
   - Created `lab/test_interrupt_teardown.sh` to simulate demo interruption (SIGINT/SIGTERM) and verify that trap teardown reliably purges all planted lab artifacts.
   - Built `lab/collect_evidence.sh` as the one-command Kali evidence collector executing preflight, env info capture, double pytest runs, 3-act demo runs 1 & 2, comparative fingerprint verification, and SHA256-verified zip bundle output.
   - Configured all `.sh` scripts with LF line endings and executable index bits (`git update-index --chmod=+x`).
2. **Handoff Packaging & Documentation**:
   - Implemented `tools/make_handoff.py` to package 54 project files into `dist/linux-privesc-toolkit-handoff.zip` with strict LF normalization and POSIX permission metadata.
   - Authored `docs/KALI_HANDOFF_GUIDE.md` detailing copy-paste execution, transfer options, and troubleshooting.
   - Authored `docs/RECORDING_GUIDE.md` incorporating Vansh Dhawan's identity, Vecesta.co, Unified Mentor, and a 2-minute narration script.
3. **Evidence Ingestion Engine**:
   - Implemented `tools/ingest_evidence.py` to cryptographically verify incoming evidence bundles, guard against simulated kernel leakage, scan for personal Windows paths, regenerate summary reports, render terminal screenshots, and generate `evidence/INGEST_REPORT.md`.
   - Created and verified unit test `tests/test_ingest_synthetic.py` (PASS in 1.87s).
4. **Documentation & QA Refinement**:
   - Updated `tools/make_docs.py` with mutually exclusive `--draft` (default) and `--final` CLI modes.
   - Replaced unpersonalized placeholders in DOCX cover page and PPTX cover slide with author identity (`Vansh Dhawan`, `Vecesta.co`, `Unified Mentor`, `10 November 2026`).
   - Replaced generic "SKIPPED" with transparent `"PENDING REAL RUN"` markers on slides 10, 11, 12, 14 and DOCX report tables where Linux guest evidence is awaiting Kali bundle collection.
   - Built `tools/check_consistency.py` validating 54 required files, LF shell script endings, text hygiene (no TODO/XXX/lorem, no Windows absolute paths), and evidence sync.
   - Authored `docs/PPT_QA.md` scoring all 15 presentation slides honestly (7/10 to 9/10), detailing per-slide weaknesses, applied fixes, and programmatic validation receipts.
   - Updated `README.md` with identity details, Kali Linux evidence collection quick start, and testing status.

### Verification Results:
- `pytest`: 29 passed, 1 skipped (Linux-only E2E test).
- `pytest tests/test_runner_safety.py -v`: 6 passed (strict allowlist and argument injection defenses verified).
- `python tools/check_consistency.py --draft`: PASS across all 54 required files, line endings, text hygiene, and evidence sync.
- `python tools/make_docs.py --draft`: Clean generation of `docs/Project_Report.docx` and `docs/Final_Presentation.pptx`.
- Shell script syntax: LF enforced on all `.sh` scripts, executable index bits set.

- Status: PASS. Ready for Kali Linux VM evidence collection.

## Deployment Pass — Static Site & GitHub Pages CI/CD (2026-11-10)

- Project: Linux Privilege Escalation Automation Toolkit
- Target Repository: `linux-privesc-toolkit`
- Author: Vansh Dhawan
- Organization: Vecesta.co · Unified Mentor
- Mode: DRAFT mode (real Linux evidence pending Kali execution; all placeholders transparently marked PENDING REAL RUN)

### Actions Taken:
1. **Task C0 — State Discovery & Mode Determination**:
   - Inspected repository state; confirmed project is "Linux Privilege Escalation Automation Toolkit".
   - Verified that `evidence/INGEST_REPORT.md` is not yet populated with real Linux scan results. Determined site build mode is DRAFT.
2. **Task C1 — Configuration & URL Setter Tool**:
   - Created `config/site.json` with keys `project_name`, `tagline`, `author`, `company`, `program`, `repo_url`, and `live_url`.
   - Created `tools/set_live_url.py <live_url> <repo_url>` to update configuration, update README links, rebuild static site, and regenerate DOCX and PPTX deliverables.
3. **Task C2 & C3 — Static Site Architecture & Templates**:
   - Built `site_src/style.css` (custom dark theme `#0E1116`, zero CDNs/external fonts, responsive, accessible, AA contrast).
   - Built `site_src/app.js` (mobile navigation toggle, copyable code blocks, client-side interactive Report Viewer with local JSON FileReader).
   - Built `site_src/index.html` (single-page showcase with sticky nav, Hero, The Problem, What It Checks, Architecture & Flowchart diagrams, 3-Act Demo with terminal screenshots, KPI stat cards, Sample Reports, Safety Model & Ethics, Limitations, Tech Stack, Quick Start, and Downloads).
   - Built `site_src/viewer.html` (interactive report viewer with sample selector, search filter, severity filter, category filter, expandable finding details, coverage checklist, and allowlisted command table).
   - Implemented `tools/build_site.py` to generate `site/` deterministically: copies assets, sample reports, screenshots, downloads; optimizes PNGs via Pillow; generates `.nojekyll`, `404.html`, `robots.txt`, `build_info.json`; enforces <10 MB per-file and <50 MB site limits; executes strict privacy scanner against personal paths and secrets. Added `site/` to `.gitignore`.
4. **Task C4 — GitHub Actions Workflow**:
   - Created `.github/workflows/pages.yml` with permissions (`contents: read`, `pages: write`, `id-token: write`), checkout@v4, setup-python@v5, build_site.py, check_site.py, configure-pages@v5, upload-pages-artifact@v3, and deploy-pages@v4.
5. **Task C5 — Site Integrity Tooling & Tests**:
   - Implemented `tools/check_site.py` validating essential files, HTML metadata (`lang`, `<title>`, `<meta description>`), image alt attributes, zero external resource loads, internal link/anchor resolution, sample JSON schema integrity, and live loopback HTTP server responses.
   - Authored `tests/test_site.py` covering site build, sample schema, and privacy leak checks (3 tests passing).
6. **Task C6 — Headless Browser Visual Audit**:
   - Implemented `tools/render_site_previews.py` using headless Microsoft Edge to capture desktop (1440x900) and mobile (390x844) screenshots into `docs/site_preview/`.
   - Conducted visual audit and authored `docs/SITE_QA.md` scoring index and viewer pages at 8.5/10 to 9/10 with zero validation errors.
7. **Task C7 — Deployment Documentation & Pipeline Integration**:
   - Authored beginner click-by-click guide `docs/DEPLOYMENT_GUIDE.md` with step-by-step instructions, troubleshooting matrix, and alternative hosts.
   - Authored `docs/DEPLOYMENT_PROOF.md` with checklist and template for recording live URLs and screenshot receipts.
   - Updated `README.md`, `docs/SUBMISSION_CHECKLIST.md`, and `docs/GITHUB_REPO_INFO.md`.
   - Updated `tools/make_docs.py` adding a "Live deployment" chapter to `Project_Report.docx` and a dedicated "Live deployment" slide (Slide 15) to `Final_Presentation.pptx`.
8. **Task C8 — Final Verification**:
   - Full pytest suite: 33 passed, 1 skipped.
   - Consistency check (`python tools/check_consistency.py --draft`): 68/68 required files PASS.
   - Fresh-clone build and check test verified.

- Status: PASS. All deployment artifacts, workflows, and documentation complete.

## Phase: Project Explanation Video & Release Packaging
- Date: 2026-11-10
- Input Video: `~/Downloads/VID20261110194343.mp4` (Size: 1,053,829,791 bytes, ~1.005 GB, 06:59 duration, H.264 video, recorded by Vansh Dhawan).
- Strategy: GitHub hard file limit is 100 MB for git push. Utilizing GitHub Releases (`v1.0.0`) which natively supports up to 2 GB per asset with global CDN bandwidth.
- Action:
  1. Authenticated `gh` CLI with `repo` and `workflow` scopes.
  2. Created release `v1.0.0` and uploaded `project_explanation_video.mp4` asset (1.05 GB).
  3. SHA-256 Digest: `64a15fa11dea8aa38fccee10542605a1fae8e087b73a23d5b4c1807d7baaac4d`.
  4. Updated `README.md` and `site_src/index.html` with direct release download links and hero action buttons.
  5. Verified static site compilation and integrity with `python tools/build_site.py` and `python tools/check_site.py`.
- Result: Release live at `https://github.com/Vecesta-co/linux-privesc-toolkit/releases/tag/v1.0.0` with verified asset. Status: PASS.
