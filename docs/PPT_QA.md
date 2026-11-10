# PowerPoint Deck Quality Assurance Audit (PPT_QA.md)

**Project:** Linux Privilege Escalation Automation Toolkit  
**Author:** Vansh Dhawan  
**Organization / Internship:** Vecesta.co · Unified Mentor  
**Date:** 10 November 2026  
**Deck File:** `docs/Final_Presentation.pptx` (15 slides, 16:9 widescreen, dark theme `#0E1116`)

---

## Executive Summary

An exhaustive per-slide audit was conducted against `docs/Final_Presentation.pptx` and the rendered 1080p preview images in `docs/ppt_preview/`. Each slide was evaluated for:
1. Visual hierarchy and typography (minimum 12pt font, Segoe UI / Consolas).
2. Spacing, alignment, margin overflow, and contrast against dark slate background.
3. Native shapes and editable elements (no static raster slides).
4. Speaker notes quality (60–120 words per slide).
5. Transparency regarding real Linux evidence (`PENDING REAL RUN` vs verified local tests).

---

## Per-Slide QA Matrix

| Slide | Title | Weakness / Risk Identified | Remediation / Fix Applied | Score (1–10) |
|---|---|---|---|:---:|
| **01** | Cover | Generic `[Your Name]` placeholders risked presenting unpersonalized internship material. | Replaced placeholders with real student identity (`Vansh Dhawan · Vecesta.co · Supervisor: [Supervisor] · 10 November 2026`); preserved prominent `READ ONLY` accent badge. | 9/10 |
| **02** | Privilege Escalation Ladder | Diagonal connector arrow between Limited User and Root could overlap text on smaller renders. | Adjusted connector start/end coordinates to `(5.5, 2.4)` -> `(8.0, 4.6)`, centering text between cards with ample clearance. | 8/10 |
| **03** | Objectives | Cards had slight horizontal asymmetry on 13.33" widescreen canvas. | Normalized card widths to `3.65"` with equal `0.35"` gutters and centered footer caption. | 8/10 |
| **04** | What It Checks | 2x3 grid of check categories had tight vertical line spacing in body text. | Added paragraph spacing (`space_after = Pt(4)`) and normalized accent badges across categories. | 8/10 |
| **05** | Architecture | Process boundary between command runner and collectors was described only in small footer text. | Elevated command runner centrality in speaker notes and added prominent contrast border to pipeline cards. | 9/10 |
| **06** | Scan Workflow | Arrowheads between 8 workflow boxes in 2x4 layout could look crowded on 720p projections. | Adjusted box margins (`2.7" x 1.0"`) and connector endpoints to keep arrowheads sharp and uncluttered. | 8/10 |
| **07** | Safety Model: Detection Only | Right-hand "NO EXPLOITATION" warning box had excessive empty padding. | Re-centered text frame with bold crimson accent border (`#F85149`) and centered 27pt header. | 9/10 |
| **08** | The Disposable Lab | Seven lab weakness cards in 2x4 grid left an empty cell at slot 8. | Balanced layout by spanning centered subtitle across full bottom grid width, explaining tracked manifest lifecycle. | 7/10 |
| **09** | Demo in Three Acts | Sequential transition between Act 1, Act 2, and Act 3 lacked numbered emphasis. | Added high-contrast accent numbers (`01`, `02`, `03`) in 29pt colored glyphs with horizontal connectors. | 9/10 |
| **10** | Results | Prior draft showed generic "SKIPPED" which could be mistaken for failed test execution. | Updated placeholder labels to explicit `"PENDING REAL RUN"` in amber; added clear notice that charts populate dynamically upon ingest of Kali evidence bundle. | 8/10 |
| **11** | Findings in Action | Lack of Linux terminal screenshot risked empty right pane. | Placed authenticated host guard screenshot with descriptive alt text (`descr`), explicitly clarifying Linux finding captures are pending real Kali run. | 8/10 |
| **12** | Before / After Comparison | Comparison card layout had potential text wrap clipping on long fingerprint names. | Limited preview character slice to 900 characters in monospaced Consolas with top vertical alignment. | 8/10 |
| **13** | Mitigation Highlights | Checklist rows looked uniform without visual grouping. | Added distinctive green checkmark badges (`✓`) in individual accent boxes alongside remediation directives. | 9/10 |
| **14** | Testing and Verification | Multiple status lines risked ambiguity between Windows fixture results and Linux e2e status. | Color-coded status lines individually (`#3FB950` green for PASS, `#D29922` amber for PENDING REAL RUN). | 8/10 |
| **15** | Limitations & Q&A | Split card format between Limitations and Next Work left bottom quarter sparse. | Added centered 31pt "Questions" banner with ample breathing room for viva/defense dialogue. | 9/10 |

---

## Technical Validation Receipt

The deck was validated programmatically by `validate_presentation()` in `tools/make_docs.py` with the following output in `docs/ppt_validation.json`:
- **Total Slides:** 15 / 15
- **Notes Count:** 15 (every slide contains 60–120 words of speaker notes)
- **Minimum Font Size:** 12.0 pt (meets or exceeds readability threshold)
- **Allowed Fonts:** Segoe UI, Consolas, Calibri (no non-standard font fallbacks)
- **Alt Text:** Present on embedded terminal pictures (`nvPicPr.cNvPr.descr`)
- **Canvas Boundaries:** Zero shapes out of canvas bounds
- **Validation Errors:** 0
