# GitHub Pages Deployment Guide

**Project:** Linux Privilege Escalation Automation Toolkit  
**Author:** Vansh Dhawan  
**Organization / Internship:** Vecesta.co · Unified Mentor  
**Date:** 10 November 2026  
**Target Repository Name:** `linux-privesc-toolkit`

---

## Click-by-Click Deployment Instructions

### Step 1: Create a Public GitHub Repository
1. Log in to your GitHub account at [https://github.com](https://github.com).
2. In the top-right corner, click **+** (plus icon) and select **New repository**.
3. Set **Repository name** to: `linux-privesc-toolkit`
4. Set visibility to **Public** (required for GitHub Pages on free GitHub plans).
5. **IMPORTANT:** Do **NOT** initialize with a README, `.gitignore`, or license (the local repository already contains complete versions of all three).
6. Click **Create repository**.

---

### Step 2: Push Local Commits to GitHub
Open PowerShell in the project root directory and run:

```powershell
# Set working directory to project root
cd path\to\linux-privesc-toolkit

# Add the remote origin (replace YOUR-USERNAME with your actual GitHub username)
git remote add origin https://github.com/YOUR-USERNAME/linux-privesc-toolkit.git

# Verify branch is main
git branch -M main

# Push all commits to GitHub
git push -u origin main
```

---

### Step 3: Enable GitHub Pages with GitHub Actions
1. Navigate to your repository on GitHub: `https://github.com/YOUR-USERNAME/linux-privesc-toolkit`
2. Click **Settings** (tab at the top right of the repo).
3. In the left sidebar, under **Code and automation**, click **Pages**.
4. Under **Build and deployment** → **Source**, click the dropdown and select:
   👉 **GitHub Actions**
5. Navigate to the **Actions** tab. You will see the **Deploy GitHub Pages** workflow triggered automatically.
6. Wait approximately 60–90 seconds until the workflow displays a green checkmark (`✔`).
7. Return to **Settings** → **Pages**. Your live site URL will be displayed at the top:
   `https://YOUR-USERNAME.github.io/linux-privesc-toolkit/`

---

### Step 4: Configure Live URLs in Local Repository
Run the automated URL setter tool to inject your live URLs into `config/site.json`, update `README.md`, rebuild the static site, and regenerate the project documentation:

```powershell
# Run tools/set_live_url.py <live_url> <repo_url>
python tools/set_live_url.py https://YOUR-USERNAME.github.io/linux-privesc-toolkit https://github.com/YOUR-USERNAME/linux-privesc-toolkit

# Commit and push the updated URLs
git add config/site.json README.md docs/
git commit -m "chore(deploy): set live deployment and repository URLs"
git push origin main
```

---

### Step 5: Verify the Live Deployment
1. **Desktop:** Open `https://YOUR-USERNAME.github.io/linux-privesc-toolkit/` in Chrome or Edge.
   - Verify all sections render cleanly (Hero, Architecture, Checks, Results, Downloads).
   - Click **Report Viewer** and test the interactive search and accordion findings.
2. **Mobile:** Open the URL on your mobile phone or browser DevTools device emulation (390px).
   - Test navigation menu toggle, responsive stat cards, and touch-friendly accordion.

---

## Troubleshooting Guide

| Issue / Symptom | Root Cause | Exact Resolution |
|---|---|---|
| **404 Not Found** on live URL | GitHub Pages DNS takes 1–2 minutes after the initial deployment to propagate globally. | Wait 2 minutes, hard refresh (`Ctrl + F5` or `Cmd + Shift + R`). Confirm in **Settings → Pages** that Source is set to **GitHub Actions**. |
| **Workflow Failed:** *Permission denied to GITHUB_TOKEN* | Default repository Actions permissions are set to read-only. | Go to **Settings** → **Actions** → **General** → scroll to **Workflow permissions** → select **Read and write permissions** → Save. Then re-run the failed job. |
| **"Pages not available"** in Settings | Repository was created as Private on a free account. | Go to **Settings** → scroll to **Danger Zone** → click **Change visibility** → select **Make public**. |
| **CI Build Failure** in `check_site.py` | Local modified file introduced broken link or external resource load. | Run `python tools/build_site.py` followed by `python tools/check_site.py` locally to see the exact line/tag error. |

---

## Alternative Cloud Hosting Platforms (Zero-Config)

If GitHub Pages is not used, the site can be published in one click on any static host:

- **Netlify:** Import the repository, set Build command to `python tools/build_site.py`, and Publish directory to `site`.
- **Cloudflare Pages:** Connect repository, set Build command to `python tools/build_site.py`, Output directory to `site`.
- **Vercel:** Import repository, set Output directory to `site`.
