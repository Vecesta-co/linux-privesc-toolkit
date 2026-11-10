# GitHub Repository Information

- Repository Name: `linux-privesc-toolkit`
- Description: Detection-only Linux privilege-escalation auditing toolkit with safe enumeration, structured reports, differential comparison, interactive report viewer, and automated GitHub Pages deployment.
- Topics: `linux`, `python`, `security-audit`, `privilege-escalation`, `blue-team`, `red-team`, `github-pages`, `internship-project`
- Author: Vansh Dhawan
- Organization: Vecesta.co · Unified Mentor
- Primary Branch: `main`

## Publication Steps

1. Create a new public repository named `linux-privesc-toolkit` on GitHub (do NOT initialize with a README).
2. Connect your local repository and push:
   ```bash
   git remote add origin https://github.com/YOUR-USERNAME/linux-privesc-toolkit.git
   git branch -M main
   git push -u origin main
   ```
3. Enable GitHub Pages in **Settings → Pages** → Source: **GitHub Actions**.
4. Configure live deployment URL locally:
   ```bash
   python tools/set_live_url.py https://YOUR-USERNAME.github.io/linux-privesc-toolkit https://github.com/YOUR-USERNAME/linux-privesc-toolkit
   git add config/site.json README.md docs/
   git commit -m "chore(deploy): set live deployment and repository URLs"
   git push origin main
   ```
5. Follow detailed instructions in [`docs/DEPLOYMENT_GUIDE.md`](file:///c:/Users/pc/OneDrive/Desktop/Unified%20Mentor(Intership%20journey)/Projects%20made%20under%20this%20internship/Project-2/docs/DEPLOYMENT_GUIDE.md).
