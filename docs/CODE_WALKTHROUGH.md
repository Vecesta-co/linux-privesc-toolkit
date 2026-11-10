# Code Walkthrough

**Author:** Vansh Dhawan
**Company:** Vecesta.co
**Internship:** Unified Mentor
**Date:** 10 November 2026
**Project:** Linux Privilege Escalation Automation Toolkit

---

## Scanner source

### `privesc_scan.py`

- Defines the `scan`, `compare`, and `render` command-line actions.
- Checks the platform before starting a Linux scan.
- Normalizes the report label so it is safe to use in filenames.
- Loads JSON for rendering and comparison on any operating system.
- Prints a clear error code when a scan cannot run on Windows.

### `privesc/models.py`

- Defines the `Finding` and `ScanResult` data classes.
- Keeps finding evidence separate from human-readable advice.
- Calculates a stable fingerprint from a rule ID and key evidence.
- Counts findings by severity and category for report summaries.
- Converts results to and from the JSON report structure.

### `privesc/runner.py`

- Is the only scanner module that starts external programs.
- Validates command names and arguments against a small allowlist.
- Rejects risky `find` actions and any sudo request that could prompt.
- Always uses an argument list, a timeout, and `shell=False`.
- Records each command's arguments, exit status, duration, and skip reason.

### `privesc/scan.py`

- Calls the selected collectors and records their coverage status.
- Keeps module failures as skipped coverage instead of crashing the scan.
- Adds visible metadata when a kernel version is simulated.
- Runs the pure analysis rules after collection.
- Writes scan events and High/Critical alert lines to the chosen log folder.

### `privesc/analysis.py`

- Converts collected system facts into stable finding IDs.
- Uses small rules for SUID, permissions, sudo, cron, services, capabilities, and kernels.
- Adds an impact explanation, mitigation, confidence, and references to each finding.
- Ignores known standard SUID paths and sticky temporary directories.
- Does not invoke commands or modify the inspected system.

### `privesc/report.py`

- Writes structured JSON with metadata, findings, coverage, and command records.
- Renders the same data as Markdown and self-contained HTML.
- Escapes HTML text before adding it to the report.
- Groups HTML findings by category and colors severity labels.
- Prints a compact console summary with optional ANSI color.

### `privesc/compare.py`

- Loads two JSON reports and matches findings by rule ID and fingerprint.
- Lists findings as NEW, FIXED, or UNCHANGED.
- Writes a Markdown comparison with counts and evidence keys.
- Works on Windows because it only reads report files.
- Does not compare transient timestamps or machine-specific report metadata.

## Collectors and parsers

### `privesc/modules/common.py`

- Reads a bounded amount of text from a known configuration path.
- Records path, mode, owner IDs, symlink state, and file size.
- Returns read errors as evidence instead of raising them to the CLI.
- Imports POSIX identity calls only when a Linux collector needs them.
- Centralizes small filesystem helpers used by other collectors.

### `privesc/modules/sysinfo.py`

- Parses `/etc/os-release` without requiring Linux-only imports.
- Collects account and group information when called on Linux.
- Gets the running kernel through the safe command runner.
- Detects WSL and container markers for report context.
- States the visibility limits of a scan run by a limited account.

### `privesc/modules/suid.py`

- Parses NUL-delimited `find` output into mode, owner, group, and path fields.
- Runs `find` with a permission-only query for SUID and SGID files.
- Supports a fast scan root set and explicit excluded paths.
- Leaves binary classification to the analysis rule catalog.
- Does not open or execute discovered binaries.

### `privesc/modules/perms.py`

- Finds world-writable files and directories with `find` permission predicates.
- Checks account databases, sudo policy, home directories, and PATH directories.
- Parses file metadata rather than relying on the scanner's effective access.
- Ignores special directories in analysis when applying the sticky-bit guard.
- Returns raw records for the rule engine to interpret.

### `privesc/modules/services.py`

- Reads systemd unit files directly instead of requiring systemd to run.
- Parses the `Service` section for `User`, `ExecStart`, and `Environment`.
- Defaults an omitted service user to root for review.
- Records the unit and executable metadata for permission checks.
- Skips symlinked units to reduce duplicate or unexpected traversal.

### `privesc/modules/sudo.py`

- Parses sudoers file rules and non-interactive `sudo -n -l` output.
- Identifies `NOPASSWD`, broad `ALL` grants, and high-risk programs.
- Reads local policy files when permitted and otherwise tries the safe listing command.
- Never prompts for a password or attempts a listed privilege.
- Reports unreadable policy as a coverage limitation.

### `privesc/modules/cron.py`

- Parses system crontab lines into schedule, user, and command fields.
- Reads `/etc/crontab`, `/etc/cron.d`, periodic directories, and readable user spools.
- Uses `crontab -l` only through the command runner.
- Records metadata for absolute scripts invoked by root jobs.
- Flags writable scripts, wildcard archive commands, and relative command paths.

### `privesc/modules/caps.py`

- Parses `getcap` output as file paths and capability strings.
- Scans standard system and user roots recursively.
- Treats a missing `getcap` program as a skipped coverage item.
- Leaves capability risk mapping to `dangerous_caps.json` and analysis rules.
- Never launches a binary that has a capability.

### `privesc/modules/kernel.py`

- Parses the numeric major, minor, and patch prefix from kernel strings.
- Compares versions against explicit advisory ranges.
- Separates upstream-series policy from CVE version matching.
- Handles vendor suffixes without treating them as upstream version components.
- Describes range matches as advisory because distributions backport patches.

## Rule data and tools

### `privesc/data/gtfobins.json`

- Lists common binary names and the contexts in which to review them.
- Links to the public GTFOBins reference page for each binary.
- Contains no payload or command string.
- Is loaded by the analysis rules for SUID, sudo, and capability findings.
- Can be updated independently from the collector code.

### `privesc/data/suid_standard.json`

- Lists common package-managed SUID/SGID paths and their purpose.
- Helps avoid flagging ordinary system binaries as unusual.
- Matches full paths so a copied binary remains non-standard.
- Should be checked against the target distribution before expansion.
- Is a review aid, not a proof that a listed binary is safe.

### `privesc/data/dangerous_caps.json`

- Maps capability names to short defensive risk descriptions.
- Keeps capability policy readable and data-driven.
- Provides no instructions for using capabilities to gain access.
- Is consulted only when `getcap` returns a matching capability.
- Can be extended as a review rule with authoritative references.

### `privesc/data/kernel_cves.json`

- Stores the verified upstream ranges used for the included kernel advisories.
- Links each entry to its NVD record and records verification notes.
- Warns that distribution backports can make a version-only result inaccurate.
- Has only the ranges supported by the checked NVD descriptions.
- Does not include exploit instructions or test payloads.

### `privesc/data/kernel_eol.json`

- Records the upstream series support policy and compile date.
- Uses kernel.org release information as its source.
- States separately that distributions may maintain patched kernels.
- Keeps the default old-series rule visible and reviewable.
- Should be refreshed when upstream long-term release dates change.

### `tools/verify_all.py`

- Reads the generated demo reports and supporting evidence files.
- Checks required rule IDs, simulated-kernel results, comparisons, and safety hashes.
- Fails when expected files are missing or teardown evidence contains a failure.
- Prints one PASS/FAIL line for each check.
- Does not alter the evidence folder.

### `tools/make_docs.py`

- Reads the final JSON evidence to obtain report counts and finding details.
- Builds the DOCX, editable PowerPoint, architecture diagrams, and previews.
- Marks unavailable Linux evidence as SKIPPED rather than inventing values.
- Uses pinned development packages from the project virtual environment.
- Can be rerun after new evidence is copied into `evidence/run1` or `evidence/run2`.

### `tools/render_terminal_png.py`

- Draws a plain-text transcript in a readable terminal-style frame.
- Uses Pillow and a monospace font for consistent output.
- Can select relevant transcript lines with a keyword filter.
- Creates screenshots only from supplied real transcript files.
- Does not fabricate scanner output or report findings.

### `tools/render_pdf_pages.py`

- Opens the PDF exported from the DOCX report.
- Renders every PDF page to a PNG using a fixed DPI.
- Writes previews into the requested QA folder.
- Does not modify the source PDF.
- Uses the pinned documentation-only PyMuPDF dependency.

### `tools/render_office.ps1`

- Uses the already installed Microsoft Word to export the DOCX to PDF.
- Uses the already installed PowerPoint to export every slide as a PNG.
- Runs both Office applications without displaying their windows.
- Writes previews only to the paths supplied to the script.
- Does not alter the project source or system settings.

## Shell scripts

### `run_scan.sh`

- Finds the project root relative to its own location.
- Checks for `python3` before starting the scanner.
- Passes all supplied options to the CLI scan action.
- Runs the same Python entry point documented in the README.
- Does not elevate privileges automatically.

### `lab/setup_lab.sh`

- Requires root and a clear disposable-lab confirmation flag.
- Refuses to overwrite lab paths or an existing `privlab` account.
- Validates the temporary sudoers file with `visudo` before installing it.
- Records created paths in `/opt/privesc-lab/manifest.txt`.
- Creates dormant, tracked weaknesses and never starts the service.

### `lab/teardown_lab.sh`

- Requires root and reads only the lab manifest.
- Accepts only the expected lab paths and account name.
- Removes exact files and empty directories without recursive path deletion.
- Removes the lab account and its home when the manifest lists it.
- Verifies that the created paths and account are gone and is safe to repeat.

### `lab/run_lab_demo.sh`

- Runs baseline, lab, limited-user, simulated-kernel, and fixed scans in order.
- Hashes key account and sudo files before and after each scan.
- Captures independent Linux checks while planted weaknesses are active.
- Uses an exit trap to run manifest-based teardown after errors or interruption.
- Writes transcripts, scan reports, comparisons, and checks under `--out`.

## Tests

### `tests/test_parsers.py`

- Exercises parsers with fixture output that resembles Linux commands and files.
- Covers system release data, SUID output, sudo, cron, units, capabilities, and kernels.
- Checks kernel suffix parsing and exclusive upper bounds.
- Avoids Linux-only collectors so it can run on Windows.
- Uses small assertions that identify parser regressions.

### `tests/test_analysis.py`

- Supplies structured records directly to the rule engine.
- Covers positive and negative cases for every finding family.
- Checks standard SUID and sticky-directory false-positive guards.
- Confirms the expected simulated kernel advisory rules.
- Runs without a Linux host.

### `tests/test_runner_safety.py`

- Verifies the accepted read-only command forms.
- Confirms shell, dangerous `find`, and interactive sudo arguments are rejected.
- Scans implementation sources for prohibited execution or mutation calls.
- Tests validation without launching any system command.
- Keeps the safety policy visible in the test names.

### `tests/test_reports_cli.py`

- Checks required JSON keys and report creation.
- Confirms Markdown and HTML contain report content.
- Exercises NEW, FIXED, and UNCHANGED comparison states.
- Uses temporary output folders outside the project reports directory.
- Does not require a Linux system.

### `tests/test_cli.py`

- Confirms a Windows scan exits with status 2 and a clear message.
- Confirms report rendering still works on Windows.
- Uses a temporary JSON file for re-rendering.
- Does not scan or change the host.
- Checks that generated output files exist.

### `tests/test_linux_e2e.py`

- Runs a small real scan when the operating system is Linux.
- Checks key system metadata and coverage records.
- Skips itself on Windows with an explicit reason.
- Uses a temporary log directory for the runner records.
- Provides one end-to-end check in addition to parser fixtures.
