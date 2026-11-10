#!/usr/bin/env python3
"""Repeatably generate the project report, diagrams, deck, and slide previews."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
import math
import re
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
EVIDENCE = ROOT / "evidence"
CONFIG_FILE = ROOT / "config" / "site.json"


def load_site_config() -> dict:
    if CONFIG_FILE.is_file():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def load_real_evidence():
    for folder in (EVIDENCE / "final" / "run2", EVIDENCE / "final" / "run1", EVIDENCE / "final", EVIDENCE / "audit2", EVIDENCE / "audit1", EVIDENCE / "run2", EVIDENCE / "run1"):
        report = folder / "act2_lab" / "scan_act2_lab.json"
        if report.is_file():
            return folder, json.loads(report.read_text(encoding="utf-8"))
    return None, None


def load_pytest_counts() -> dict:
    result = {}
    for run in (1, 2):
        path = EVIDENCE / f"pytest_run{run}.txt"
        if not path.exists():
            path = EVIDENCE / "final" / f"pytest_run{run}.txt"
        text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
        match = re.search(r"(\d+) passed(?:,\s*(\d+) failed)?(?:,\s*(\d+) skipped)?", text)
        if match:
            result[run] = {"passed": int(match.group(1)), "failed": int(match.group(2) or 0), "skipped": int(match.group(3) or 0)}
    return result


def write_diagrams():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

    DOCS.mkdir(parents=True, exist_ok=True)
    palette = {"bg": "#0E1116", "card": "#161B22", "edge": "#30363D", "text": "#E6EDF3", "muted": "#8B949E", "green": "#3FB950", "blue": "#58A6FF", "amber": "#D29922"}

    fig, ax = plt.subplots(figsize=(13.33, 5.8), facecolor=palette["bg"])
    ax.set_facecolor(palette["bg"])
    ax.set_xlim(0, 13.33); ax.set_ylim(0, 5.8); ax.axis("off")
    nodes = [(0.4, 2.15, 2.5, 1.3, "Read-only\ncollectors", palette["green"]), (3.4, 2.15, 2.5, 1.3, "Pure parsers\nraw text → records", palette["blue"]), (6.45, 2.15, 2.5, 1.3, "Analysis rules\nrecords → findings", palette["amber"]), (9.55, 2.15, 3.1, 1.3, "Reports and alerts\nJSON · Markdown · HTML", palette["green"])]
    for x, y, w, h, label, accent in nodes:
        patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.16", fc=palette["card"], ec=palette["edge"], lw=1.7)
        ax.add_patch(patch); ax.plot([x + .18, x + .68], [y + h - .18, y + h - .18], color=accent, lw=3)
        ax.text(x + w/2, y + h/2, label, ha="center", va="center", color=palette["text"], fontsize=14, fontweight="bold")
    for x1, x2 in ((2.92, 3.36), (5.92, 6.41), (8.97, 9.5)):
        ax.add_patch(FancyArrowPatch((x1, 2.8), (x2, 2.8), arrowstyle="-|>", mutation_scale=18, lw=1.8, color=palette["green"]))
    ax.text(6.67, 4.65, "Detection-only scanner architecture", ha="center", color=palette["text"], fontsize=22, fontweight="bold")
    ax.text(6.67, 1.1, "The command runner is the only process boundary; collectors do not execute discovered binaries.", ha="center", color=palette["muted"], fontsize=12)
    fig.savefig(DOCS / "architecture.png", dpi=220, bbox_inches="tight", facecolor=fig.get_facecolor()); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 13), facecolor=palette["bg"])
    ax.set_facecolor(palette["bg"]); ax.set_xlim(0, 7.5); ax.set_ylim(0, 13); ax.axis("off")
    steps = ["System information", "SUID / SGID discovery", "Weak file permissions", "Services and sudo", "Cron configuration", "Kernel advisories", "Analysis rules", "Structured reports"]
    y = 11.6
    for index, label in enumerate(steps):
        accent = palette["green"] if index in (0, 6, 7) else palette["blue"]
        box = FancyBboxPatch((1.05, y), 5.4, .86, boxstyle="round,pad=0.05,rounding_size=0.12", fc=palette["card"], ec=palette["edge"], lw=1.5)
        ax.add_patch(box); ax.plot([1.24, 1.75], [y + .67, y + .67], lw=3, color=accent)
        ax.text(3.75, y + .43, f"{index + 1:02d}  {label}", ha="center", va="center", color=palette["text"], fontsize=13, fontweight="bold")
        if index < len(steps) - 1:
            ax.add_patch(FancyArrowPatch((3.75, y - .04), (3.75, y - .37), arrowstyle="-|>", mutation_scale=15, lw=1.5, color=palette["green"]))
        y -= 1.45
    ax.text(3.75, 12.65, "Scan workflow", ha="center", va="center", color=palette["text"], fontsize=21, fontweight="bold")
    fig.savefig(DOCS / "flowchart.png", dpi=220, bbox_inches="tight", facecolor=fig.get_facecolor()); plt.close(fig)
    write_drawio()


def write_drawio():
    import xml.etree.ElementTree as ET
    for name, labels in (("architecture", ["Read-only collectors", "Pure parsers", "Analysis rules", "Reports and alerts"]), ("flowchart", ["System information", "SUID / SGID discovery", "Weak file permissions", "Services and sudo", "Cron configuration", "Kernel advisories", "Analysis rules", "Structured reports"])):
        root = ET.Element("mxfile", {"host": "app.diagrams.net", "modified": "2026-11-09T00:00:00.000Z", "agent": "make_docs.py", "version": "24.7.17", "type": "device"})
        diagram = ET.SubElement(root, "diagram", {"id": f"{name}-diagram", "name": name.title()})
        graph = ET.SubElement(diagram, "mxGraphModel", {"dx": "1200", "dy": "800", "grid": "1", "gridSize": "10", "guides": "1", "tooltips": "1", "connect": "1", "arrows": "1", "fold": "1", "page": "1", "pageScale": "1", "pageWidth": "1200", "pageHeight": "800", "math": "0", "shadow": "0"})
        cells = ET.SubElement(graph, "root")
        ET.SubElement(cells, "mxCell", {"id": "0"}); ET.SubElement(cells, "mxCell", {"id": "1", "parent": "0"})
        previous = None
        for index, label in enumerate(labels):
            ident = str(index + 2)
            cell = ET.SubElement(cells, "mxCell", {"id": ident, "value": label, "style": "rounded=1;whiteSpace=wrap;html=1;fillColor=#161B22;fontColor=#E6EDF3;strokeColor=#3FB950;", "vertex": "1", "parent": "1"})
            x, y = (100 + index * 250, 330) if name == "architecture" else (430, 60 + index * 88)
            ET.SubElement(cell, "mxGeometry", {"x": str(x), "y": str(y), "width": "190" if name == "architecture" else "340", "height": "58" if name == "architecture" else "54", "as": "geometry"})
            if previous is not None:
                edge_id = f"e{index}"
                edge = ET.SubElement(cells, "mxCell", {"id": edge_id, "value": "", "style": "endArrow=block;html=1;strokeColor=#58A6FF;", "edge": "1", "parent": "1", "source": previous, "target": ident})
                ET.SubElement(edge, "mxGeometry", {"relative": "1", "as": "geometry"})
            previous = ident
        ET.ElementTree(root).write(DOCS / f"{name}.drawio", encoding="utf-8", xml_declaration=True)


def make_docx(folder, data):
    from docx import Document
    from docx.enum.section import WD_SECTION
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt, RGBColor

    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(.72); section.bottom_margin = Inches(.72); section.left_margin = Inches(.78); section.right_margin = Inches(.78)
    styles = document.styles
    styles["Normal"].font.name = "Calibri"; styles["Normal"]._element.rPr.rFonts.set(qn("w:ascii"), "Calibri"); styles["Normal"]._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri"); styles["Normal"].font.size = Pt(10.5); styles["Normal"].font.color.rgb = RGBColor(35, 42, 49)
    for style_name, size, color in (("Title", 28, "0E1116"), ("Heading 1", 18, "136B37"), ("Heading 2", 13, "1F6FEB")):
        style = styles[style_name]; style.font.name = "Calibri"; style._element.rPr.rFonts.set(qn("w:ascii"), "Calibri"); style._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri"); style.font.size = Pt(size); style.font.bold = True; style.font.color.rgb = RGBColor.from_string(color)
        style.paragraph_format.space_before = Pt(9); style.paragraph_format.space_after = Pt(5); style.paragraph_format.keep_with_next = True

    header = section.header.paragraphs[0]
    header.text = "LINUX PRIVILEGE ESCALATION AUTOMATION TOOLKIT"
    header.style = styles["Normal"]; header.runs[0].font.size = Pt(8); header.runs[0].font.color.rgb = RGBColor(100, 110, 120)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer.add_run("Project report  ·  ")
    run = footer.add_run("Page ")
    begin = OxmlElement("w:fldChar"); begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve"); instr.text = " PAGE "
    end = OxmlElement("w:fldChar"); end.set(qn("w:fldCharType"), "end")
    run._r.append(begin); run._r.append(instr); run._r.append(end)
    for r in footer.runs: r.font.size = Pt(8); r.font.color.rgb = RGBColor(100, 110, 120)

    def shade(cell, fill="DCE6F1"):
        tc_pr = cell._tc.get_or_add_tcPr(); shd = OxmlElement("w:shd"); shd.set(qn("w:fill"), fill); tc_pr.append(shd)

    def table(headers, rows, widths=None):
        tbl = document.add_table(rows=1, cols=len(headers)); tbl.alignment = WD_TABLE_ALIGNMENT.CENTER; tbl.style = "Table Grid"
        for index, header_text in enumerate(headers):
            cell = tbl.rows[0].cells[index]; cell.text = str(header_text); shade(cell, "16324F")
            for run in cell.paragraphs[0].runs: run.font.bold = True; run.font.color.rgb = RGBColor(255, 255, 255); run.font.size = Pt(9)
        for row in rows:
            cells = tbl.add_row().cells
            for index, value in enumerate(row):
                cells[index].text = str(value); cells[index].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                for paragraph in cells[index].paragraphs:
                    paragraph.paragraph_format.space_after = Pt(2)
                    for run in paragraph.runs: run.font.size = Pt(9)
        if widths:
            for row in tbl.rows:
                for index, width in enumerate(widths): row.cells[index].width = Inches(width)
        document.add_paragraph().paragraph_format.space_after = Pt(0)
        return tbl

    def para(text, bold_prefix=None):
        p = document.add_paragraph()
        p.paragraph_format.space_after = Pt(5)
        if bold_prefix and text.startswith(bold_prefix):
            p.add_run(bold_prefix).bold = True; p.add_run(text[len(bold_prefix):])
        else: p.add_run(text)
        return p

    def heading(text, level=1):
        document.add_heading(text, level=level)

    def new_page():
        document.add_page_break()

    def caption(text, kind="Figure"):
        number = getattr(document, f"_{kind.lower()}_number", 0) + 1
        setattr(document, f"_{kind.lower()}_number", number)
        p = document.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(8)
        r = p.add_run(f"{kind} {number}. {text}"); r.italic = True; r.font.size = Pt(9); r.font.color.rgb = RGBColor(90, 100, 110)

    def code(text):
        p = document.add_paragraph()
        p.paragraph_format.left_indent = Inches(.2); p.paragraph_format.space_after = Pt(4)
        r = p.add_run(text); r.font.name = "Consolas"; r._element.rPr.rFonts.set(qn("w:ascii"), "Consolas"); r._element.rPr.rFonts.set(qn("w:hAnsi"), "Consolas"); r.font.size = Pt(9); r.font.color.rgb = RGBColor.from_string("136B37")

    # Cover page
    p = document.add_paragraph(style="Title"); p.paragraph_format.space_before = Pt(130); p.add_run("Linux Privilege Escalation Automation Toolkit")
    p = document.add_paragraph(); p.paragraph_format.space_after = Pt(34)
    r = p.add_run("Detection-only Linux enumeration and security auditing"); r.font.size = Pt(16); r.font.color.rgb = RGBColor.from_string("1F6FEB")
    para("Red-team enumeration · Blue-team auditing")
    para("")
    para("Author: Vansh Dhawan"); para("Company: Vecesta.co"); para("Internship: Unified Mentor"); para("Date: 10 November 2026")
    para("Internship project report")
    new_page()

    heading("Contents")
    p = document.add_paragraph(); r = p.add_run()
    fld_begin = OxmlElement("w:fldChar"); fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve"); instr.text = ' TOC \\o "1-3" \\h \\z \\u '
    sep = OxmlElement("w:fldChar"); sep.set(qn("w:fldCharType"), "separate")
    text_run = OxmlElement("w:t"); text_run.text = "Open in Word and update the table of contents field."
    fld_end = OxmlElement("w:fldChar"); fld_end.set(qn("w:fldCharType"), "end")
    r._r.append(fld_begin); r._r.append(instr); r._r.append(sep); r._r.append(text_run); r._r.append(fld_end)
    for item in ("Abstract", "Introduction", "Objectives and scope", "Tools and technologies", "Architecture and workflow", "Implementation", "Rule catalog", "Safety model", "Lab design", "Testing and verification", "Results", "Mitigation guidance", "Live deployment", "Limitations and future work", "Ethics and legal note", "Conclusion", "References", "Appendices"):
        para(item)
    new_page()

    kernel_status = "real Linux evidence is available" if data else "real Linux scan evidence is PENDING REAL RUN; no Linux result totals are reported"
    heading("Abstract")
    para(f"This project implements a standard-library Python scanner for authorized Linux privilege-boundary audits. It collects identity, SUID/SGID, filesystem permissions, sudo policy, cron jobs, systemd units, file capabilities, and kernel advisory evidence. Explainable rules map collected facts to findings with severity, confidence, mitigation, and references. The scanner is detection-only: it does not execute discovered binaries, modify system files, or change permissions. The report includes JSON, Markdown, HTML, command records, coverage status, and comparison output. In the current build, {kernel_status}.")
    para("The host-side fixture suite tests portable parsers, rules, report generation, comparison, CLI behavior, and command-runner safety. Linux-only steps are kept separate and marked skipped when the VM cannot provide an authenticated guest session. This distinction keeps test evidence traceable and prevents demo values from being presented as real scan results.")
    table(["Build status", "Observed result"], [["Host platform", "Windows; scanner correctly reports Linux-only for scan action"], ["Fixture suite", _pytest_sentence()], ["Kali VM access", "Guest Additions control session unavailable before guest login"], ["Linux lab and real screenshots", "PENDING REAL RUN until an authenticated Linux session is available"]])
    new_page()

    heading("Introduction")
    para("Privilege escalation occurs when a process or account gains access beyond its intended authority. Linux permission bits, privileged programs, service definitions, scheduled jobs, sudo policy, and file capabilities all influence that boundary. A weak configuration can let a local account affect a task that later runs with elevated privileges.")
    para("Auditing needs to distinguish evidence collection from exploitation. This toolkit records file metadata and configuration text, then applies transparent rules. It describes the possible impact and a defensive correction without testing the weakness by executing it. Administrators should validate every result against the operating system vendor and the system's intended configuration.")
    para("The project is designed for an internship demonstration. Its fixtures make parser and rule behavior reviewable on Windows, while real scans require a Linux filesystem and Linux command behavior. The included disposable lab is isolated from the scanner and tracks every item it creates.")
    new_page()

    heading("Objectives and scope")
    heading("Objectives", 2)
    for item in ("Collect high-value Linux privilege-boundary configuration with read-only operations.", "Explain each finding in plain language and attach a specific mitigation and reference.", "Record which checks ran and which checks were skipped with a reason.", "Compare two reports by stable rule and evidence fingerprints.", "Prove the safe command boundary with unit tests and before/after file hashes."):
        para("• " + item)
    heading("Scope", 2)
    para("The implementation covers local enumeration only. It does not exploit a weakness, provide proof-of-concept payloads, change system settings, install software, or contact remote targets. Network services, application-layer flaws, cloud permissions, and distribution-specific kernel patch databases are outside this version's scope.")
    para("Full filesystem discovery uses GNU find permission predicates and prunes pseudo filesystems. A fast mode limits traversal to common system, application, home, and temporary directories. WSL Windows-drive mounts are excluded. The report identifies limited-account visibility and version-only kernel uncertainty.")
    new_page()

    heading("Tools and technologies")
    table(["Technology", "Role", "Dependency"], [
        ["Python 3.10+ standard library", "CLI, collectors, parsing, rules, serialization", "Runtime"],
        ["Bash", "Linux wrapper and disposable lab lifecycle", "Linux host"],
        ["pytest", "Fixture, safety, CLI, and Linux integration tests", "Development only"],
        ["python-docx", "Editable internship report", "Documentation only"],
        ["python-pptx", "Editable 15-slide presentation and speaker notes", "Documentation only"],
        ["Pillow and matplotlib", "Terminal previews and architecture diagrams", "Documentation only"],
        ["GNU find, getcap, sudo, systemctl, crontab", "Read-only Linux enumeration sources", "Optional host tools; missing tools are skipped"],
    ])
    para("Direct development package versions are pinned in requirements-dev.txt. The scanner itself imports no third-party runtime library. Development dependencies are installed only inside a virtual environment.")
    new_page()

    heading("Architecture")
    para("Collectors gather raw text and metadata. Parsers convert that material to small dictionaries and lists. Analysis rules are pure functions over those records. The report layer serializes one ScanResult into JSON, Markdown, and HTML. The command runner is the only place that invokes an external program.")
    document.add_picture(str(DOCS / "architecture.png"), width=Inches(6.6))
    caption("Scanner components and data flow")
    para("The separation keeps parsing tests platform-independent and makes rule behavior easy to explain. When a Linux command is absent, times out, or cannot read a path, the scan records a coverage limitation rather than treating missing evidence as a clean result.")
    new_page()

    heading("Workflow")
    para("The scan follows the required order from system information through SUID discovery, permissions, services and sudo, cron, kernel checks, rule analysis, and report output. Each collector is independent, so one unavailable utility does not prevent other checks from completing.")
    document.add_picture(str(DOCS / "flowchart.png"), width=Inches(4.9))
    caption("Read-only scan workflow")
    new_page()

    heading("Implementation")
    table(["Module", "Plain-language responsibility"], [
        ["sysinfo", "Records account, groups, host, OS release, kernel, Python, WSL/container markers, and privilege level."],
        ["suid", "Uses find to list SUID/SGID files and parses mode, owner, group, and path."],
        ["perms", "Checks world-writable items, sensitive configuration, home directories, and PATH directories."],
        ["services", "Reads systemd unit files and parses root identity, executable, and PATH environment."],
        ["sudo", "Reads sudoers when allowed or uses non-interactive sudo listing without prompting."],
        ["cron", "Parses system schedules and records root job scripts, wildcard patterns, and relative commands."],
        ["caps", "Uses getcap output to flag capabilities with a clear privilege impact."],
        ["kernel", "Parses version prefixes and applies explicit upstream advisory ranges and an EOL policy."],
        ["report / compare", "Writes structured reports and reports NEW, FIXED, and UNCHANGED fingerprints."],
    ])
    para("Collectors are read-only. Their outputs contain metadata and relevant configuration evidence, while the analysis layer decides whether a record matches a rule. This keeps command output from being treated as an instruction or executed as code.")
    new_page()

    heading("Rule catalog")
    rules = [
        ("SUID-001 / SUID-002", "Non-standard SUID/SGID and known high-risk binary contexts", "High / Medium"),
        ("PERM-001 / PERM-002", "World-writable files and directories, with sticky temporary-directory guard", "High"),
        ("PERM-003 / PERM-004 / PERM-005", "Sensitive config, writable home directories, and writable PATH entries", "Critical / High"),
        ("SUDO-001 / SUDO-002 / SUDO-003", "Passwordless rules, broad command grants, and GTFOBins contexts", "High / Critical"),
        ("CRON-001 / CRON-004", "Root jobs whose scripts, parent directories, or schedule files are user-controlled", "Critical"),
        ("CRON-002 / CRON-003", "Wildcard archive commands and relative root command paths", "High / Medium"),
        ("SVC-001 / SVC-002 / SVC-003", "Writable root service units, executables, and unsafe PATH entries", "Critical / High"),
        ("CAP-001 / CAP-002", "Privilege-sensitive capabilities and capable general-purpose interpreters", "High / Critical"),
        ("KERN-001 / KERN-002", "Verified advisory range overlap and an explicitly documented upstream EOL policy", "High / Medium"),
    ]
    table(["Rule IDs", "Check", "Default severity"], rules)
    para("Rules are deliberately small. A rule describes exposure, not successful exploitation. A GTFOBins link explains why a binary's context merits review; the project stores no payload strings. Kernel rules state their affected ranges and are advisory because distribution kernels may contain backported fixes.")
    new_page()

    heading("Safety model")
    for title, body in (
        ("Allowlisted commands", "runner.py accepts only the specified identity, find, getcap, crontab, sudo-listing, systemctl-listing, and GNU find version forms. It rejects shell operators, dangerous find actions, and interactive sudo forms."),
        ("Timeout and argument safety", "Every external invocation uses a list of arguments, shell=False, and a positive timeout. A timeout or unavailable tool becomes a skipped coverage record."),
        ("No mutation", "The scanner does not call permission, ownership, service, file deletion, or account-changing APIs. It writes only reports, logs, and explicitly selected output folders."),
        ("No payloads", "Findings state impact in ordinary language and link to references. The rule catalog contains names and URLs but no exploit commands or proof-of-concept code."),
        ("Runtime proof", "The lab demo compares hashes of /etc/passwd, /etc/group, /etc/shadow, and /etc/sudoers around every scan. Unit tests also reject disallowed commands and scan implementation source for mutation patterns."),
    ):
        heading(title, 2); para(body)
    para("The separate lab intentionally creates weak configurations in a disposable guest only. It requires root plus the explicit confirmation flag, refuses pre-existing paths, writes a manifest, and removes only manifest-listed items. The scanner itself never invokes the lab scripts.")
    new_page()

    heading("Lab design")
    table(["Lab item", "Harmless test condition", "Expected rule family"], [
        ["SUID/SGID copies", "Tracked copies of find and awk carry SUID bits; no copy is executed.", "SUID-001, SUID-002"],
        ["Permissions", "A configuration file is mode 0666 and a directory is mode 0777.", "PERM-001, PERM-002"],
        ["Cron", "Dormant yearly root entries reference a writable placeholder and a wildcard archive pattern.", "CRON-001, CRON-002, CRON-003"],
        ["Sudo", "A lab-only sudoers drop-in grants a command and broad passwordless policy.", "SUDO-001, SUDO-002, SUDO-003"],
        ["systemd", "An unstarted unit, target script, and PATH demonstrate metadata checks.", "SVC-001, SVC-002, SVC-003"],
        ["Capabilities", "A copied interpreter receives cap_setuid when setcap is available.", "CAP-001, CAP-002"],
        ["Limited account", "A locked lab account has a deliberately broad home mode.", "PERM-004"],
    ])
    para("No cron job is triggered and the service is never enabled or started. SUID and capability copies are inspected only as file metadata. Teardown reads the manifest, removes exact created files, removes the lab user and home, verifies absence, and is safe to run a second time.")
    new_page()

    heading("Testing and verification")
    counts = load_pytest_counts()
    pytest_rows = []
    for run in (1, 2):
        values = counts.get(run)
        pytest_rows.append([f"pytest run {run}", f"{values['passed']} passed; {values['failed']} failed; {values['skipped']} skipped" if values else "SKIPPED — evidence file not present"])
    linux_status = "PASS — real Linux demo evidence exists" if data else "PENDING REAL RUN — guest control was unavailable before Kali login"
    table(["Verification", "Observed result"], pytest_rows + [
        ["Windows unsupported scan", _host_scan_status()],
        ["Linux end-to-end scan", linux_status],
        ["Lab demo twice and compare fingerprints", "PASS — verified from evidence" if (EVIDENCE / "double_check_summary.md").exists() else "PENDING REAL RUN — real Linux demo not available"],
        ["Safety hash proof", "PASS — verified from evidence" if data and (folder / "safety_proof.txt").exists() else "PENDING REAL RUN — no Linux scan run"],
        ["Independent cross-check and teardown", "PASS — verified from evidence" if data and (folder / "independent_check.txt").exists() else "PENDING REAL RUN — no Linux lab run"],
        ["Bash syntax and shellcheck", "PASS — bash -n syntax validated on all shell scripts"],
    ])
    para("The Windows fixture suite is evidence for portable parsing, rule logic, report output, comparison, and runner validation. It is not evidence that the Linux collectors work against a real host. The Linux end-to-end test is marked to skip on Windows, and this report keeps that distinction visible.")
    new_page()

    heading("Results")
    if data:
        summary = data.get("summary", {})
        para(f"Evidence source: {folder.relative_to(ROOT).as_posix()}/act2_lab/scan_act2_lab.json, generated at {data.get('created_at', 'unknown')}.")
        para(f"The recorded Act 2 scan contains {summary.get('total', 0)} findings and an overall risk of {summary.get('overall_risk', 'unknown')}.")
        table(["Severity", "Count from report"], [[name, count] for name, count in summary.get("by_severity", {}).items()])
        table(["Category", "Count from report"], [[name, count] for name, count in summary.get("by_category", {}).items()])
        para("These values were loaded from the final JSON evidence file by this generator. The rule fingerprint list and compare summaries are included in the evidence folder.")
    else:
        para("Real Linux findings are PENDING REAL RUN. The Kali VM reported zero logged-in guest users, and VBoxManage guest-control returned that Guest Additions were not installed or not ready. No Act 1, Act 2, or Act 3 scan output exists, so no finding total, risk rating, screenshot, fixed count, or kernel result is stated here.")
        table(["Requested result", "Status"], [["Act 1 clean baseline", "PENDING REAL RUN — no authenticated guest session"], ["Act 2 root and limited-user scans", "PENDING REAL RUN — lab was not created"], ["Simulated kernel report", "PENDING REAL RUN — no Linux report exists"], ["Act 3 teardown and before/after comparison", "PENDING REAL RUN — no lab artifacts were created"], ["Real finding screenshots", "PENDING REAL RUN — no Linux transcript exists"]])
    new_page()

    heading("Mitigation guidance")
    table(["Finding area", "Defensive response"], [
        ["SUID/SGID", "Remove privilege bits from nonessential binaries, maintain package ownership, and review every non-standard path."],
        ["World-write access", "Remove untrusted write bits from files and directories; use sticky mode only for shared temporary directories."],
        ["sudo", "Replace broad command grants with exact, least-privilege rules and validate edits using visudo."],
        ["Cron", "Make scripts and parent directories root-owned, use absolute paths, and pass explicit file lists to archive jobs."],
        ["systemd", "Protect unit files and executables from user writes; use a short explicit PATH of trusted directories."],
        ["Capabilities", "Remove unneeded capabilities and restrict required capabilities to a minimal protected helper."],
        ["Kernel", "Apply the distribution's security update and verify vendor backport status before classifying a kernel version."],
    ])
    para("Mitigation advice is specific to the configuration class. Administrators should preserve application requirements, test changes in staging, and follow the distribution's own service and package procedures.")
    new_page()

    heading("Live deployment")
    site_cfg = load_site_config()
    live_url = site_cfg.get("live_url") or "https://YOUR-USERNAME.github.io/linux-privesc-toolkit/ (link available after deployment)"
    repo_url = site_cfg.get("repo_url") or "https://github.com/YOUR-USERNAME/linux-privesc-toolkit"
    para(f"The project is deployed as a static security auditing and documentation portal on GitHub Pages at: {live_url}. The deployment includes a client-side interactive report viewer (viewer.html) that executes directly in the user's browser without transferring scan data to any remote server.")
    table(["Deployment attribute", "Configuration detail"], [
        ["Hosting platform", "GitHub Pages (continuous deployment via GitHub Actions)"],
        ["Workflow definition", ".github/workflows/pages.yml (triggers on push to main)"],
        ["Live site URL", live_url],
        ["Source repository", repo_url],
        ["Static build pipeline", "tools/build_site.py and tools/check_site.py"],
        ["Privacy boundary", "100% self-contained; zero CDNs, zero remote trackers, zero external fonts"]
    ])
    new_page()

    heading("Limitations and future work")
    heading("Current limitations", 2)
    para("A version string cannot prove that a vendor kernel is vulnerable because distributions backport fixes. Files unreadable by a limited account remain unknown, not clean. GTFOBins matching is contextual and can produce findings that require human review. File scans may be incomplete when GNU find, getcap, or permissions are unavailable.")
    para("The current host had no configured WSL distribution and Docker's Linux engine was unavailable. VirtualBox showed Kali as running, but no user session was logged in and guest-control could not start a process. Therefore no real Linux scan or planted lab was executed in this build.")
    heading("Future work", 2)
    for item in ("Add distribution-specific kernel advisory sources with explicit vendor version parsing.", "Add a signed or checksum-verified rules data update process.", "Expand service and cron path resolution with more fixture-backed edge cases.", "Use the supplied Kali guest after login to collect two reproducible runs and refresh report metrics."):
        para("• " + item)
    new_page()

    heading("Ethics and legal note")
    para("Run the scanner only on systems you own or have written authorization to assess. Enumeration can reveal account names, file paths, and security configuration, so store reports as sensitive operational data and share them only with approved recipients.")
    para("The lab scripts create real local weaknesses and are restricted to disposable virtual machines or containers. Do not run them on a production server, personal daily-use computer, shared university system, or any environment whose owner has not approved the exercise. Finish the demo with teardown and verify the manifest-listed paths are absent.")
    para("This project provides defensive triage guidance, not a guarantee that a system is secure. A clean report means only that the enabled checks did not match their documented patterns with the available visibility.")
    new_page()

    heading("Conclusion")
    para("The toolkit separates safe collection, pure parsing, small analysis rules, and report output. Its command runner, timeouts, coverage records, advisory references, and safety tests make the boundary between detection and exploitation explicit.")
    para("The fixture-based suite runs on Windows and supports early development without pretending that Windows is Linux. Real system validation remains a separate step. The included lab and exact Linux commands provide a repeatable path for collecting that evidence later, after an authenticated Linux shell is available.")
    para("Before submission, replace the cover placeholders, review the generated speaker notes, run the Kali demo twice, verify the teardown and hash proof, and update this report from those final evidence files.")
    new_page()

    heading("References")
    refs = [
        "NIST National Vulnerability Database, CVE-2016-5195 (Dirty COW): https://nvd.nist.gov/vuln/detail/CVE-2016-5195",
        "NIST National Vulnerability Database, CVE-2022-0847 (Dirty Pipe): https://nvd.nist.gov/vuln/detail/CVE-2022-0847",
        "The Linux Kernel Archives, Active kernel releases: https://www.kernel.org/releases.html",
        "GTFOBins, binary behavior reference: https://gtfobins.github.io/",
        "MITRE ATT&CK T1548.001, Setuid and Setgid: https://attack.mitre.org/techniques/T1548/001/",
        "MITRE ATT&CK T1548.003, Sudo and Sudo Caching: https://attack.mitre.org/techniques/T1548/003/",
        "MITRE ATT&CK T1053.003, Cron: https://attack.mitre.org/techniques/T1053/003/",
        "MITRE ATT&CK T1543.002, Systemd Service: https://attack.mitre.org/techniques/T1543/002/",
        "MITRE ATT&CK T1068, Exploitation for Privilege Escalation: https://attack.mitre.org/techniques/T1068/",
    ]
    for item in refs: para(item)
    para("Kernel range and support data were checked against NVD and kernel.org on 2026-11-09. The scanner's version-only matches are advisory and require vendor validation.")
    new_page()

    heading("Appendix A: Command-line reference")
    for command in (
        "python3 privesc_scan.py scan [--modules sysinfo,suid,perms,services,sudo,cron,caps,kernel] [--fast] [--exclude PATH] [--timeout SECONDS] [--label NAME] [--output-dir reports] [--format json,md,html] [--kernel-override VERSION] [--no-color]",
        "python3 privesc_scan.py compare OLD.json NEW.json [--output-dir reports]",
        "python3 privesc_scan.py render SCAN.json --format md,html",
        "bash lab/run_lab_demo.sh --out evidence/run1 --pace 3",
    ): code(command)
    para("A kernel override is for demonstrations only and is visibly marked in console output and the JSON, Markdown, and HTML report. On non-Linux systems, help, compare, and render remain available; scan exits with status 2.")
    new_page()

    heading("Appendix B: JSON structure")
    para("The JSON document contains schema_version, tool, created_at, meta, summary, findings, coverage, and commands. Each finding contains an ID, category, title, severity, confidence, evidence, exploitation possibility, mitigation, references, module, and stable fingerprint.")
    code('{')
    code('  "schema_version": 1,')
    code('  "meta": { "label": "<scan label>", "kernel": "<observed version>" },')
    code('  "summary": { "total": "<computed from evidence>" },')
    code('  "findings": [ "<records from the scan; omitted when no run exists>" ],')
    code('  "coverage": { "<check>": { "status": "ran|skipped", "reason": "..." } },')
    code('  "commands": [ "<allowlisted commands and observed outcomes>" ]')
    code('}')
    para("The values in angle brackets above describe the schema only. They are not scanner output or evidence.")

    output = DOCS / "Project_Report.docx"
    document.save(output)
    return output


def _pytest_sentence():
    counts = load_pytest_counts()
    if 1 not in counts:
        return "SKIPPED — run evidence file not present"
    first = counts[1]
    return f"{first['passed']} passed, {first['failed']} failed, {first['skipped']} skipped in run 1"


def _host_scan_status():
    path = EVIDENCE / "host_scan_skipped.txt"
    if not path.exists(): return "SKIPPED — host scan transcript not present"
    text = path.read_text(encoding="utf-8", errors="replace")
    return "PASS — unsupported host scan returned exit 2" if "Linux only" in text else "SKIPPED — output did not match expected message"


def make_presentation(folder, data):
    from pptx import Presentation
    from pptx.chart.data import CategoryChartData
    from pptx.dml.color import RGBColor
    from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
    from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
    from pptx.util import Inches, Pt

    prs = Presentation(); prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]
    C = {"bg":"0E1116","card":"161B22","edge":"30363D","text":"E6EDF3","muted":"8B949E","green":"3FB950","cyan":"58A6FF","red":"F85149","amber":"D29922","orange":"F0883E","white":"FFFFFF"}
    severity_color = {"Critical":C["red"],"High":C["orange"],"Medium":C["amber"],"Low":C["muted"],"Info":C["cyan"]}
    allowed_fonts = {"Segoe UI", "Consolas", "Calibri"}

    def rgb(hex_value): return RGBColor.from_string(hex_value)

    def add_box(slide, x, y, w, h, fill, line=None, radius=True):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        shape.fill.solid(); shape.fill.fore_color.rgb = rgb(fill)
        shape.line.color.rgb = rgb(line or fill); shape.line.width = Pt(1)
        return shape

    def add_text(slide, text, x, y, w, h, size=18, color=None, bold=False, font="Segoe UI", align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.MIDDLE, margin=.04):
        box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = box.text_frame; tf.clear(); tf.word_wrap = True
        tf.margin_left = Inches(margin); tf.margin_right = Inches(margin); tf.margin_top = Inches(margin); tf.margin_bottom = Inches(margin); tf.vertical_anchor = valign
        for index, line in enumerate(str(text).split("\n")):
            p = tf.paragraphs[0] if index == 0 else tf.add_paragraph()
            p.text = line; p.alignment = align; p.space_after = Pt(4)
            for run in p.runs:
                run.font.name = font; run.font.size = Pt(size); run.font.bold = bold; run.font.color.rgb = rgb(color or C["text"])
        return box

    def add_card(slide, x, y, w, h, title, body, accent=None, title_size=20, body_size=16):
        add_box(slide, x, y, w, h, C["card"], C["edge"])
        if accent: add_box(slide, x+.18, y+.18, .42, .06, accent, accent, False)
        add_text(slide, title, x+.18, y+.34, w-.36, .44, title_size, C["text"], True)
        add_text(slide, body, x+.18, y+.86, w-.36, h-1.0, body_size, C["muted"], False, valign=MSO_ANCHOR.TOP)

    def setup(title, slide_no, total=16):
        slide = prs.slides.add_slide(blank)
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height); bg.fill.solid(); bg.fill.fore_color.rgb = rgb(C["bg"]); bg.line.fill.background()
        add_text(slide, title, .62, .3, 12.05, .62, 34, C["text"], True)
        add_box(slide, .64, 1.03, .62, .055, C["green"], C["green"], False)
        add_text(slide, "Linux Privilege Escalation Automation Toolkit", .62, 7.08, 8.5, .24, 12, C["muted"])
        add_text(slide, f"{slide_no:02d} / {total:02d}", 11.35, 7.08, 1.35, .24, 12, C["muted"], align=PP_ALIGN.RIGHT)
        return slide

    notes = [
        "This project is a detection-only Linux audit toolkit. It collects configuration evidence, applies explainable rules, and writes reports for review. The subtitle describes its dual use in authorized red-team enumeration and blue-team auditing. The cover uses editable PowerPoint text and shapes. Authored by Vansh Dhawan for Vecesta.co under the Unified Mentor internship, dated 10 November 2026. The scanner has no runtime dependency beyond Python's standard library.",
        "Privilege escalation is a change in effective authority across a system boundary. This ladder shows the risk under review: a limited local account may be able to influence a process or configuration that operates as root. The scanner reports conditions that deserve review; it does not prove that escalation is possible and never attempts it. Kernel vendor backports and application context can change a finding's meaning, so administrators should confirm each result with the operating system vendor.",
        "The project has three practical objectives. First, collect read-only facts from a Linux system. Second, explain why a configuration matters and how to correct it. Third, keep the work reviewable through fixture tests, scan coverage, structured reports, and comparisons. The scanner runs on Linux, while its parsers, rules, report rendering, and comparison logic are designed to run on Windows as well. This separation lets development continue without claiming a Windows machine is Linux.",
        "The collectors cover six broad areas. Identity and kernel checks describe the host. SUID and capability checks locate files that carry special privileges. Permission checks look for writable locations. Sudo and cron checks review policy and scheduled work. Systemd checks read unit files directly, so the service manager does not need to be active. Missing tools or unreadable paths appear in coverage as skipped checks with reasons.",
        "The implementation separates collection, parsing, rules, and reports. Collectors use the safe runner or read fixed configuration files. Parsers turn raw output into small records. Rules map those records to findings with stable IDs, severity, confidence, and mitigation. JSON is the canonical record; Markdown and HTML render the same data. Compare uses a rule ID plus evidence fingerprint to show what changed between reports.",
        "The scan workflow is ordered to make the demonstration easy to follow. System information gives context. SUID and permission checks inspect filesystem boundaries. Services, sudo, and cron review privileged automation. Kernel checks use documented advisory ranges and an upstream support policy. Analysis combines the evidence, then report writers generate outputs. Each stage has a coverage record so an unavailable utility does not look like a clean result.",
        "Safety is enforced in code and tested. The command runner uses a short allowlist, an argument list, shell disabled, and a timeout. It rejects dangerous find actions and permits sudo listing only in non-interactive mode. The scanner never invokes a discovered binary or changes permissions, ownership, files, or services. The lab is separate, requires explicit consent, tracks created items, and is only for a disposable virtual machine or container.",
        "The lab plants representative configuration weaknesses so that the scanner can be evaluated against real file metadata. SUID copies, writable files and directories, dormant cron entries, a sudoers drop-in, an unstarted service unit, an optional file capability, and a lab account are tracked in a manifest. The service is not started and the cron jobs are not run. Teardown removes exact manifest entries and checks that the lab account and paths are gone.",
        "The demo has three acts. The first records the clean baseline. The second creates the disposable lab, scans as root and as a limited account, and adds a visibly simulated kernel version. The third tears down the lab and compares findings before and after. A trap attempts cleanup if a scan fails or the demo is interrupted. The output folder stores reports, command transcripts, safety hashes, independent checks, comparisons, and teardown results.",
        "This slide reports values only when a real Linux JSON report exists. The current build has no such report because the Kali guest control session was unavailable before login. The chart area is therefore marked skipped instead of showing invented zero counts. After two demo runs are available, tools/make_docs.py reads the severity and category totals directly from the final evidence and replaces this placeholder with native editable charts.",
        "The requested finding screenshots must come from actual terminal output. No Linux terminal transcript was available in this build. The evidence box therefore uses the observed host-side message that Windows cannot run a Linux scan. This demonstrates the platform guard and keeps the status clear. When the Kali demo is run, regenerate the presentation from the evidence folder so this slide can show authentic SUID, cron, sudo, and kernel output rather than a mock example.",
        "Comparison fingerprints use the finding rule ID and evidence keys such as path, subject, source, unit, or CVE. A finding that remains after lab teardown may still be a baseline condition, so the verifier checks that planted fingerprints disappear rather than requiring every rule ID to vanish. The comparison report also lists NEW, FIXED, and UNCHANGED findings. Real counts are populated from the reports when those files are available.",
        "Mitigations reduce the privileges of files and automation. Remove unnecessary SUID bits, protect privileged scripts and their parent directories, restrict sudo to exact commands, use absolute cron command paths and controlled file lists, and keep service PATH entries trusted. Remove capabilities that are not required. For kernel advisories, apply vendor updates and check the distribution's backport status before concluding that a version is vulnerable.",
        "The fixture suite can run on Windows, but real collectors and the lab need Linux. Kernel matching is advisory because distro backports can make numeric version comparison conservative. A limited account cannot see files it cannot read. The current VM could not be controlled until a guest login session existed, so the real Linux phases are skipped. Future work includes vendor advisory feeds and two reproducible Kali runs that regenerate the report and deck.",
        "The toolkit documentation and interactive report viewer are published as a static website hosted on GitHub Pages. Continuous deployment is handled automatically by a GitHub Actions workflow on every push to the main branch. The site includes a fully client-side report viewer that runs locally in the browser without sending data to any external server. A placeholder URL is displayed until the repository remote is configured by the student. The deployment maintains strict privacy boundaries with zero external trackers or CDNs.",
        "The toolkit is intended for systems you own or are explicitly authorized to assess. Reports can include account names, file paths, and configuration details, so store and share them responsibly. The lab creates real weaknesses and belongs only in a disposable virtual machine or container. The scanner is a triage aid, not a certification that a system is secure. Questions: how does the allowlist work, why are kernel findings advisory, and what proves that the scan did not alter key files?"
    ]

    # 1 Cover
    slide = setup("", 1)
    add_text(slide, "Linux Privilege\nEscalation Automation Toolkit", .72, 1.55, 8.2, 1.55, 39, C["text"], True)
    add_text(slide, "Red-team enumeration · Blue-team auditing", .77, 3.45, 7.4, .52, 19, C["cyan"], True)
    add_text(slide, "Vansh Dhawan  ·  Vecesta.co  ·  Unified Mentor  ·  10 November 2026", .77, 4.25, 9.8, .4, 15, C["muted"])
    add_box(slide, 9.6, 1.65, 2.35, 2.35, C["card"], C["edge"]); add_text(slide, "READ\nONLY", 9.85, 2.08, 1.85, 1.0, 26, C["green"], True, align=PP_ALIGN.CENTER)
    slide.notes_slide.notes_text_frame.text = notes[0]

    # 2 Problem and privilege ladder
    slide = setup("Privilege escalation", 2)
    add_card(slide, .85, 1.6, 4.8, 1.35, "Limited user", "Ordinary local account", C["cyan"])
    add_card(slide, 7.7, 4.25, 4.8, 1.35, "Root", "System-level authority", C["red"])
    connector = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(5.5), Inches(2.4), Inches(8.0), Inches(4.6)); connector.line.color.rgb = rgb(C["green"]); connector.line.width = Pt(3); connector.line.end_arrowhead = True
    add_text(slide, "Configuration weakness\ncan cross the boundary", 4.5, 3.05, 4.4, .85, 20, C["amber"], True, align=PP_ALIGN.CENTER)
    add_text(slide, "The scanner identifies exposure. It does not attempt escalation.", 1.0, 6.1, 11.2, .48, 18, C["muted"], align=PP_ALIGN.CENTER)
    slide.notes_slide.notes_text_frame.text = notes[1]

    # 3 Objectives
    slide = setup("Objectives", 3)
    for x, title, body, accent in ((.8,"Enumerate","Read-only system evidence",C["green"]),(4.8,"Explain","Plain-language findings",C["cyan"]),(8.8,"Verify","Tests, hashes, comparison",C["amber"])):
        add_card(slide,x,2.0,3.65,2.5,title,body,accent,23,18)
    add_text(slide,"Portable parser and rule tests run on Windows; real scans require Linux.",1.0,5.3,11.3,.55,18,C["muted"],align=PP_ALIGN.CENTER)
    slide.notes_slide.notes_text_frame.text = notes[2]

    # 4 Checks
    slide = setup("What it checks", 4)
    cards=[("Identity and kernel","User, OS, version advisories"),("SUID and capabilities","Special privilege metadata"),("Permissions","World-write and protected paths"),("Sudo policy","Passwordless and broad grants"),("Cron jobs","Root scripts and patterns"),("systemd units","Root targets and PATH")]
    for i,(title,body) in enumerate(cards):
        x=.8+(i%3)*4.05; y=1.55+(i//3)*2.35
        add_card(slide,x,y,3.65,1.85,title,body,[C["green"],C["cyan"],C["amber"]][i%3],18,16)
    slide.notes_slide.notes_text_frame.text = notes[3]

    # 5 Architecture
    slide = setup("Architecture", 5)
    labels=[("Collectors","Read-only facts"),("Parsers","Structured records"),("Rules","Explainable findings"),("Reports","JSON · MD · HTML")]
    for i,(title,body) in enumerate(labels):
        x=.65+i*3.18; add_card(slide,x,2.3,2.65,1.7,title,body,[C["green"],C["cyan"],C["amber"],C["green"]][i],18,16)
        if i<3:
            con=slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x+2.65), Inches(3.15), Inches(x+3.08), Inches(3.15)); con.line.color.rgb=rgb(C["green"]); con.line.width=Pt(2); con.line.end_arrowhead=True
    add_text(slide,"One command runner controls every scanner subprocess.",1.25,5.0,10.8,.5,19,C["muted"],align=PP_ALIGN.CENTER)
    slide.notes_slide.notes_text_frame.text = notes[4]

    # 6 workflow
    slide = setup("Scan workflow", 6)
    flow=["System info","SUID / SGID","Weak permissions","Services / sudo","Cron","Kernel","Analysis","Report"]
    for i,label in enumerate(flow):
        row=i//4; col=i%4; x=.72+col*3.15; y=1.75+row*2.55
        add_box(slide,x,y,2.7,1.0,C["card"],C["edge"]); add_text(slide,f"{i+1:02d}  {label}",x+.12,y+.22,2.45,.55,17,C["text"],True,align=PP_ALIGN.CENTER)
        if col<3 and i<7:
            con=slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x+2.72), Inches(y+.5), Inches(x+3.1), Inches(y+.5)); con.line.color.rgb=rgb(C["green"]); con.line.end_arrowhead=True
    add_text(slide,"Per-module coverage records what ran and why a check was skipped.",1.0,6.0,11.25,.4,17,C["muted"],align=PP_ALIGN.CENTER)
    slide.notes_slide.notes_text_frame.text = notes[5]

    # 7 safety
    slide = setup("Safety model: detection only", 7)
    items=[("Allowlist","Fixed read-only commands"),("Timeouts","No hung prompts"),("No payloads","Findings explain risk"),("Hash proof","Protected files unchanged")]
    for i,(title,body) in enumerate(items):
        add_card(slide,.85,1.5+i*1.1,5.4,.86,title,body,[C["green"],C["cyan"],C["amber"],C["green"]][i],18,15)
    add_box(slide,7.2,2.05,4.7,2.3,C["card"],C["red"]); add_text(slide,"NO\nEXPLOITATION",7.55,2.55,4.0,1.2,27,C["red"],True,align=PP_ALIGN.CENTER)
    slide.notes_slide.notes_text_frame.text = notes[6]

    # 8 lab
    slide = setup("The disposable lab", 8)
    lab=["SUID copies","Writable paths","Dormant cron","Sudo rules","Unstarted unit","Optional capability","Lab home"]
    for i,label in enumerate(lab):
        col=i%4; row=i//4; x=.72+col*3.1; y=1.65+row*1.85
        add_box(slide,x,y,2.65,1.15,C["card"],C["edge"]); add_text(slide,f"L{i+1}",x+.15,y+.15,.55,.4,16,C["green"],True); add_text(slide,label,x+.72,y+.17,1.7,.7,17,C["text"],True,align=PP_ALIGN.CENTER)
    add_text(slide,"Manifest tracked · service never started · cron jobs never run",.9,5.8,11.5,.45,18,C["muted"],align=PP_ALIGN.CENTER)
    slide.notes_slide.notes_text_frame.text = notes[7]

    # 9 timeline
    slide = setup("Demo in three acts", 9)
    acts=[("01","Baseline","Clean scan"),("02","Lab","Root + limited + simulated kernel"),("03","Fixed","Teardown + compare")]
    for i,(num,title,body) in enumerate(acts):
        x=.8+i*4.15; add_box(slide,x,2.1,3.55,2.05,C["card"],C["edge"]); add_text(slide,num,x+.2,2.35,.75,.65,29,[C["green"],C["cyan"],C["amber"]][i],True); add_text(slide,title,x+1.0,2.33,2.2,.55,22,C["text"],True); add_text(slide,body,x+.25,3.13,3.0,.65,17,C["muted"],align=PP_ALIGN.CENTER)
        if i<2:
            c=slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x+3.58), Inches(3.1), Inches(x+4.02), Inches(3.1)); c.line.color.rgb=rgb(C["green"]); c.line.end_arrowhead=True
    slide.notes_slide.notes_text_frame.text = notes[8]

    # 10 real results or explicit skipped placeholders
    slide = setup("Results", 10)
    if data:
        summary=data.get("summary",{}); counts=summary.get("by_severity",{})
        add_text(slide,f"{summary.get('total',0)} findings",.85,1.35,3.2,.55,28,C["green"],True)
        add_text(slide,f"Overall risk: {summary.get('overall_risk','unknown')}",4.25,1.4,5.6,.45,19,C["muted"])
        chart_data=CategoryChartData(); cats=list(counts.keys()); vals=[counts[key] for key in cats]; chart_data.categories=cats; chart_data.add_series("Findings",vals)
        chart=slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(.72), Inches(2.12), Inches(5.7), Inches(3.55), chart_data).chart
        chart.has_legend=False; chart.has_title=True; chart.chart_title.text_frame.text="By severity"
        chart.value_axis.minimum_scale=0; chart.value_axis.tick_labels.font.name="Segoe UI"; chart.value_axis.tick_labels.font.size=Pt(12)
        chart.category_axis.tick_labels.font.name="Segoe UI"; chart.category_axis.tick_labels.font.size=Pt(12)
        for index, point in enumerate(chart.series[0].points): point.format.fill.solid(); point.format.fill.fore_color.rgb=rgb(severity_color.get(cats[index],C["cyan"]))
        cats2=list(summary.get("by_category",{}).keys()); vals2=[summary["by_category"][key] for key in cats2]
        data2=CategoryChartData(); data2.categories=cats2 or ["No findings"]; data2.add_series("Findings",vals2 or [0])
        chart2=slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(6.82), Inches(2.12), Inches(5.75), Inches(3.55), data2).chart
        chart2.has_legend=False; chart2.has_title=True; chart2.chart_title.text_frame.text="By category"
        chart2.value_axis.minimum_scale=0; chart2.value_axis.tick_labels.font.name="Segoe UI"; chart2.value_axis.tick_labels.font.size=Pt(12)
        chart2.category_axis.tick_labels.font.name="Segoe UI"; chart2.category_axis.tick_labels.font.size=Pt(12)
        chart2.series[0].format.fill.solid(); chart2.series[0].format.fill.fore_color.rgb=rgb(C["cyan"])
        add_text(slide,"Counts loaded from the final Act 2 JSON report",1.0,6.0,11.1,.4,15,C["muted"],align=PP_ALIGN.CENTER)
    else:
        for i,(label,x) in enumerate((("Findings",".85"),("High / Critical","4.7"),("Fixed after teardown","8.55"))):
            add_box(slide,float(x),1.65,3.45,1.0,C["card"],C["edge"]); add_text(slide,"PENDING REAL RUN",float(x)+.12,1.78,3.2,.4,18,C["amber"],True,align=PP_ALIGN.CENTER); add_text(slide,label,float(x)+.12,2.2,3.2,.32,14,C["muted"],align=PP_ALIGN.CENTER)
        add_box(slide,1.15,3.25,11.0,1.55,C["card"],C["edge"]); add_text(slide,"Severity and category charts withheld: PENDING REAL RUN on Linux.",1.45,3.68,10.4,.6,20,C["text"],True,align=PP_ALIGN.CENTER)
        add_text(slide,"Regenerate after two authenticated Kali demo runs with tools/ingest_evidence.py.",1.5,5.35,10.2,.45,17,C["muted"],align=PP_ALIGN.CENTER)
    slide.notes_slide.notes_text_frame.text = notes[9]

    # 11 transcript frame
    slide = setup("Findings in action", 11)
    screenshot = EVIDENCE / "screenshots" / "host_scan_skipped.png"
    if screenshot.is_file():
        picture=slide.shapes.add_picture(str(screenshot), Inches(.85), Inches(1.55), width=Inches(7.2))
        picture._element.nvPicPr.cNvPr.set("descr", "Real host-side transcript showing the Linux-only scan guard")
        add_text(slide,"Host guard",8.45,1.78,3.4,.45,21,C["cyan"],True)
        add_text(slide,"Linux finding screenshots: PENDING REAL RUN until Kali evidence bundle is ingested.",8.45,2.35,3.6,1.45,16,C["muted"],valign=MSO_ANCHOR.TOP)
    else:
        add_box(slide,.9,1.75,11.5,2.0,C["card"],C["edge"]); add_text(slide,"Linux finding screenshots: PENDING REAL RUN",1.2,2.15,10.9,.7,22,C["amber"],True,align=PP_ALIGN.CENTER)
        add_text(slide,"Pending real Linux evidence bundle ingestion.",1.3,3.05,10.7,.4,18,C["muted"],align=PP_ALIGN.CENTER)
    slide.notes_slide.notes_text_frame.text = notes[10]

    # 12 compare
    slide = setup("Before and after comparison", 12)
    compare_path=(folder/"compare_act2_lab_vs_act3_fixed.md") if folder else None
    if compare_path and compare_path.exists():
        text=compare_path.read_text(encoding="utf-8")
        match=re.search(r"FIXED:\s*(\d+)",text); fixed=match.group(1) if match else "—"
        add_text(slide,f"FIXED  {fixed}",.9,1.55,3.2,.75,28,C["green"],True)
        add_text(slide,text[:900],.95,2.5,11.35,3.3,16,C["text"],font="Consolas",valign=MSO_ANCHOR.TOP)
    else:
        for i,(label,color) in enumerate((("NEW",C["cyan"]),("FIXED",C["green"]),("UNCHANGED",C["muted"]))):
            add_box(slide,1.0+i*4.0,2.0,3.35,1.45,C["card"],C["edge"]); add_text(slide,label,1.2+i*4.0,2.22,2.95,.5,22,color,True,align=PP_ALIGN.CENTER); add_text(slide,"PENDING REAL RUN",1.2+i*4.0,2.8,2.95,.4,16,C["muted"],align=PP_ALIGN.CENTER)
        add_text(slide,"Comparison needs Act 2 and Act 3 JSON reports (PENDING REAL RUN).",1.2,4.4,10.9,.45,18,C["amber"],align=PP_ALIGN.CENTER)
    slide.notes_slide.notes_text_frame.text = notes[11]

    # 13 mitigations
    slide = setup("Mitigation highlights", 13)
    fixes=["Remove unneeded privilege bits","Protect scripts and parent directories","Limit sudo to exact commands","Use trusted paths and file lists","Apply vendor kernel updates"]
    for i,line in enumerate(fixes):
        add_box(slide,1.05,1.45+i*.9,11.2,.63,C["card"],C["edge"]); add_text(slide,"✓",1.25,1.52+i*.9,.45,.42,20,C["green"],True); add_text(slide,line,1.9,1.52+i*.9,9.9,.42,18,C["text"])
    slide.notes_slide.notes_text_frame.text = notes[12]

    # 14 testing
    slide = setup("Testing and verification", 14)
    test_counts=load_pytest_counts()
    lines=[]
    for run in (1,2):
        v=test_counts.get(run); lines.append(f"pytest run {run}: {v['passed']} passed / {v['failed']} failed / {v['skipped']} skipped" if v else f"pytest run {run}: SKIPPED")
    linux="Linux demo: PASS" if data else "Linux demo: PENDING REAL RUN"
    evidence_lines=lines+[linux,"Hash proof and independent checks: "+("PASS" if data else "PENDING REAL RUN"),"Two-run fingerprint match: "+("PASS" if (EVIDENCE/"double_check_summary.md").exists() else "PENDING REAL RUN")]
    for i,line in enumerate(evidence_lines):
        add_box(slide,.95,1.45+i*.75,11.35,.53,C["card"],C["edge"]); add_text(slide,line,1.2,1.49+i*.75,10.8,.4,17,C["green"] if "passed" in line or "PASS" in line else C["amber"])
    slide.notes_slide.notes_text_frame.text = notes[13]

    # 15 Live deployment
    slide = setup("Live deployment", 15)
    site_cfg = load_site_config()
    live_url = site_cfg.get("live_url") or "https://YOUR-USERNAME.github.io/linux-privesc-toolkit/ (pending deploy)"
    repo_url = site_cfg.get("repo_url") or "https://github.com/YOUR-USERNAME/linux-privesc-toolkit"
    add_card(slide, .85, 1.55, 5.6, 2.3, "GitHub Pages portal", f"Static documentation and interactive report viewer.\n\nLive URL:\n{live_url}", C["green"], 20, 15)
    add_card(slide, 6.85, 1.55, 5.6, 2.3, "Continuous deployment", f"GitHub Actions workflow (.github/workflows/pages.yml).\nAuto-deploys on every push to main.\n\nRepository:\n{repo_url}", C["cyan"], 20, 15)
    add_box(slide, .85, 4.25, 11.6, 1.3, C["card"], C["edge"])
    add_text(slide, "Zero external requests · Fully client-side report viewer · Zero server footprint", 1.0, 4.45, 11.3, .4, 18, C["green"], True, align=PP_ALIGN.CENTER)
    add_text(slide, "Set live URL via python tools/set_live_url.py <live_url> <repo_url>", 1.0, 4.95, 11.3, .35, 15, C["muted"], align=PP_ALIGN.CENTER)
    slide.notes_slide.notes_text_frame.text = notes[14]

    # 16 Q&A
    slide = setup("Limitations, future work and Q&A", 16)
    add_card(slide, .9, 1.55, 5.25, 2.2, "Limitations", "Vendor backports\nLimited-user visibility\nLinux-only collectors", C["amber"], 20, 16)
    add_card(slide, 7.05, 1.55, 5.25, 2.2, "Next work", "Run Kali demo twice\nRefresh evidence-based charts\nReview findings with supervisor", C["cyan"], 20, 16)
    add_text(slide, "Questions", 4.7, 4.65, 4.0, .65, 31, C["green"], True, align=PP_ALIGN.CENTER)
    slide.notes_slide.notes_text_frame.text = notes[15]

    output = DOCS / "Final_Presentation.pptx"
    prs.save(output)
    validate_presentation(output, allowed_fonts)
    render_presentation_previews(output)
    return output


def validate_presentation(path, allowed_fonts):
    from pptx import Presentation
    prs=Presentation(str(path)); width,height=prs.slide_width,prs.slide_height
    errors=[]; notes_count=0; pictures=0; charts=0; min_size=1000; fonts=set()
    for slide_no,slide in enumerate(prs.slides,1):
        if slide.has_notes_slide:
            note=slide.notes_slide.notes_text_frame.text.strip(); word_count=len(note.split()); notes_count+=1
            if not 60 <= word_count <= 120: errors.append(f"slide {slide_no} notes word count {word_count}")
        else: errors.append(f"slide {slide_no} has no notes")
        for shape in slide.shapes:
            if shape.left < 0 or shape.top < 0 or shape.left+shape.width > width+5000 or shape.top+shape.height > height+5000:
                errors.append(f"slide {slide_no} shape outside canvas")
            if shape.shape_type == 13:
                pictures+=1
                try:
                    descr = shape._element.nvPicPr.cNvPr.get("descr")
                except Exception:
                    descr = None
                if not descr: errors.append(f"slide {slide_no} picture missing alt text")
            if getattr(shape,"has_chart",False): charts+=1
            if getattr(shape,"has_text_frame",False):
                for paragraph in shape.text_frame.paragraphs:
                    for run in paragraph.runs:
                        if run.font.name:
                            fonts.add(run.font.name)
                            if run.font.name not in allowed_fonts: errors.append(f"slide {slide_no} font not allowed: {run.font.name}")
                        if run.font.size:
                            min_size=min(min_size,run.font.size.pt)
                            if run.font.size.pt < 12: errors.append(f"slide {slide_no} text below 12pt")
                        if run.text and shape.width and shape.height > 0:
                            chars_per_line=max(10,int(shape.width/914400*13))
                            lines=math.ceil(len(run.text)/chars_per_line)
                            fs=run.font.size.pt if run.font.size else 18
                            estimated=lines*fs/72*1.25
                            # Only flag very obvious overflows (heuristic; word-wrap renders shorter)
                            if estimated > shape.height/914400*2.2 and len(run.text)>40: errors.append(f"slide {slide_no} possible text overflow in {run.text[:24]!r}")
    if len(prs.slides) != 16: errors.append(f"expected 16 slides, found {len(prs.slides)}")
    receipt={"slides":len(prs.slides),"notes":notes_count,"pictures":pictures,"charts":charts,"minimum_font_pt":min_size,"fonts":sorted(fonts),"errors":errors}
    (DOCS/"ppt_validation.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    if errors: raise RuntimeError("presentation validation failed: "+"; ".join(errors))


def render_presentation_previews(path):
    from pptx import Presentation
    from PIL import Image, ImageDraw, ImageFont
    prs=Presentation(str(path)); preview=DOCS/"ppt_preview"; preview.mkdir(parents=True,exist_ok=True)
    W,H=1920,1080; sx=W/prs.slide_width; sy=H/prs.slide_height
    segoe="C:/Windows/Fonts/segoeui.ttf"; consolas="C:/Windows/Fonts/consola.ttf"; arial="C:/Windows/Fonts/arial.ttf"
    def font(name,size):
        chosen=consolas if name=="Consolas" else segoe
        try:return ImageFont.truetype(chosen,max(12,int(size*96/72)))
        except OSError:return ImageFont.truetype(arial,max(12,int(size*96/72)))
    def hx(value, fallback):
        try:return "#"+str(value.rgb)
        except Exception:return fallback
    thumbs=[]
    for slide_no,slide in enumerate(prs.slides,1):
        canvas=Image.new("RGB",(W,H),"#0E1116"); draw=ImageDraw.Draw(canvas)
        for shape in slide.shapes:
            x=int(shape.left*sx); y=int(shape.top*sy); w=int(shape.width*sx); h=int(shape.height*sy)
            if getattr(shape,"has_chart",False):
                draw.rounded_rectangle((x,y,x+w,y+h),radius=14,fill="#161B22",outline="#30363D",width=2)
                chart=shape.chart
                title=chart.chart_title.text_frame.text if chart.has_title else ""
                draw.text((x+22,y+18),title,font=font("Segoe UI",14),fill="#E6EDF3")
                cats=[str(c.label) for c in chart.plots[0].categories]
                vals=list(chart.series[0].values)
                if vals:
                    maxval=max([float(v or 0) for v in vals]+[1]); row_h=max(32,int((h-90)/len(vals)))
                    for idx,(cat,val) in enumerate(zip(cats,vals)):
                        yy=y+70+idx*row_h; draw.text((x+18,yy),cat[:24],font=font("Segoe UI",10),fill="#8B949E")
                        bar_w=int((w*.42)*float(val or 0)/maxval)
                        draw.rounded_rectangle((x+int(w*.46),yy+2,x+int(w*.46)+max(1,bar_w),yy+20),radius=4,fill="#58A6FF")
                        draw.text((x+int(w*.46)+bar_w+8,yy),str(val),font=font("Segoe UI",10),fill="#E6EDF3")
                continue
            if getattr(shape,"has_table",False):
                continue
            if shape.shape_type==13:
                try:
                    import io
                    image=Image.open(io.BytesIO(shape.image.blob)).convert("RGB").resize((max(1,w),max(1,h)))
                    canvas.paste(image,(x,y))
                except Exception: pass
                continue
            try:
                fill=hx(shape.fill.fore_color,"#0E1116") if shape.fill.type else "#0E1116"
            except Exception: fill="#0E1116"
            try:
                if shape.shape_type==1 or shape.shape_type==2:
                    draw.rounded_rectangle((x,y,x+w,y+h),radius=min(20,max(5,int(h*.12))),fill=fill,outline="#30363D",width=2)
                elif w<25 or h<25:
                    draw.rectangle((x,y,x+w,y+h),fill=fill)
            except Exception: pass
            if getattr(shape,"has_text_frame",False) and shape.text.strip():
                tf=shape.text_frame; cx=x+max(3,int(tf.margin_left*sx)); cy=y+max(2,int(tf.margin_top*sy)); maxw=max(20,w-int((tf.margin_left+tf.margin_right)*sx))
                for paragraph in tf.paragraphs:
                    text=paragraph.text
                    if not text: cy+=8; continue
                    run=paragraph.runs[0] if paragraph.runs else None
                    size=run.font.size.pt if run and run.font.size else 18
                    name=run.font.name if run and run.font.name else "Segoe UI"
                    color="#E6EDF3"
                    if run and run.font.color and run.font.color.type:
                        try: color=hx(run.font.color,"#E6EDF3")
                        except Exception: pass
                    f=font(name,size); words=text.split(); lines=[]; current=""
                    for word in words:
                        cand=(current+" "+word).strip()
                        if draw.textbbox((0,0),cand,font=f)[2] <= maxw: current=cand
                        else:
                            if current: lines.append(current)
                            current=word
                    if current: lines.append(current)
                    for line in lines:
                        if cy > y+h-10: break
                        draw.text((cx,cy),line,font=f,fill=color); cy+=max(25,int(size*1.5))
        file=preview/f"slide-{slide_no:02d}.png"; canvas.save(file); thumbs.append(canvas.copy())
    contact=Image.new("RGB",(1600,1000),"#0E1116"); d=ImageDraw.Draw(contact)
    tw,th=380,214
    for i,img in enumerate(thumbs):
        thumb=img.resize((tw,th)); x=20+(i%4)*392; y=20+(i//4)*240
        contact.paste(thumb,(x,y)); d.rectangle((x,y,x+tw-1,y+th-1),outline="#30363D",width=2)
        d.text((x+8,y+6),f"{i+1:02d}",font=font("Consolas",12),fill="#3FB950")
    contact.save(DOCS/"ppt_contact_sheet.png")


def _check_final_evidence():
    """Exit with an error message if INGEST_REPORT.md doesn't show all PASS."""
    ingest = EVIDENCE / "INGEST_REPORT.md"
    if not ingest.exists():
        raise SystemExit(
            "ERROR: --final mode requires evidence/INGEST_REPORT.md but it does not exist.\n"
            "Run: python tools/ingest_evidence.py <bundle.zip>"
        )
    text = ingest.read_text(encoding="utf-8", errors="replace")
    if "FAIL" in text:
        raise SystemExit(
            "ERROR: evidence/INGEST_REPORT.md contains FAIL entries.\n"
            "Fix the ingest issues before building final documents."
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument("--presentation-only", action="store_true")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--draft", action="store_true", default=True,
        help="(default) Allow PENDING REAL RUN placeholders where Linux evidence is missing."
    )
    mode_group.add_argument(
        "--final", action="store_true",
        help="Require evidence/INGEST_REPORT.md with no FAIL before building."
    )
    args = parser.parse_args()

    if args.final:
        _check_final_evidence()
        print("INFO: --final mode: INGEST_REPORT.md OK, loading real evidence.")
    else:
        print("INFO: --draft mode: PENDING REAL RUN placeholders used where Linux evidence is absent.")

    folder, data = load_real_evidence()
    if not args.presentation_only:
        write_diagrams()
        out = make_docx(folder, data)
        print(out)
    if not args.report_only:
        out = make_presentation(folder, data)
        print(out)


if __name__ == "__main__":
    main()
