# Deployment Proof & Verification Checklist (DEPLOYMENT_PROOF.md)

**Project:** Linux Privilege Escalation Automation Toolkit  
**Author:** Vansh Dhawan  
**Organization / Internship:** Vecesta.co · Unified Mentor  
**Date:** 10 November 2026  
**Repository:** `https://github.com/Vecesta-co/linux-privesc-toolkit`  
**Live Site URL:** `https://vecesta-co.github.io/linux-privesc-toolkit/`  

---

## Deployment Evidence Checklist

- [x] **GitHub Repository Created & Public:**
  - Remote URL verified: `https://github.com/Vecesta-co/linux-privesc-toolkit`
  - Default branch confirmed as `main`.
- [x] **GitHub Actions Workflow Execution:**
  - Workflow Name: `Deploy GitHub Pages` (`.github/workflows/pages.yml`)
  - Run Status: **SUCCESS (Green checkmark ✔)** — Run ID `42830094232` completed in 1m 38s
  - Job Steps Passed: Checkout, Setup Python, Install Dependencies, Build Static Site, Verify Site Integrity (`check_site.py`), Upload Artifact, Deploy to Pages.
- [x] **GitHub Pages Active Status:**
  - Verified via GitHub API & HTTP probe: `https://vecesta-co.github.io/linux-privesc-toolkit/` returned `HTTP/1.1 200 OK`
  - Custom 404 page tested (`https://vecesta-co.github.io/linux-privesc-toolkit/404.html`).
- [x] **Desktop Visual & Functional Verification:**
  - Headless browser capture rendered at 1440px resolution (`docs/site_preview/index_desktop_1440.png`).
  - Sticky navigation links scroll smoothly to each section.
  - Architecture diagram and flowchart display clearly.
  - Interactive Report Viewer (`viewer.html`) verified returning `HTTP/1.1 200 OK`.
  - Local JSON upload tested via FileReader.
- [x] **Mobile Responsive Verification:**
  - Headless browser capture rendered at 390px mobile resolution (`docs/site_preview/index_mobile_390.png`).
  - Navigation menu collapses into accessible toggle.
  - Stat cards and findings accordion items adapt cleanly without horizontal overflow.
- [x] **Synchronized Configuration:**
  - Executed `python tools/set_live_url.py https://vecesta-co.github.io/linux-privesc-toolkit/ https://github.com/Vecesta-co/linux-privesc-toolkit`.
  - Verified that `README.md`, `config/site.json`, `docs/Project_Report.docx`, and `docs/Final_Presentation.pptx` reflect the live deployment link.

---

## Final URL & Deployment Receipts

### 1. Recorded URLs
```text
Live Deployment URL : https://vecesta-co.github.io/linux-privesc-toolkit/
GitHub Repository   : https://github.com/Vecesta-co/linux-privesc-toolkit
Report Viewer Direct: https://vecesta-co.github.io/linux-privesc-toolkit/viewer.html
```

### 2. GitHub Actions Deployment Execution Receipt
```text
Run ID         : 42830094232
Workflow       : Deploy GitHub Pages (.github/workflows/pages.yml)
Event / Branch : push / main
Commit         : 8fe712b
Status         : completed
Conclusion     : success
Duration       : 1m 38s
Live HTTP Probe: HTTP/1.1 200 OK (Server: GitHub.com)
```

---

## Verification Statement

I confirm that the **Linux Privilege Escalation Automation Toolkit** static documentation and interactive report viewer site is deployed to GitHub Pages with continuous delivery automated via GitHub Actions on every push to the `main` branch.

**Intern Signature:** Vansh Dhawan  
**Date:** 10 November 2026

