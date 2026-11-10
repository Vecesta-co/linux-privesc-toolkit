# Linux Test Guide (Kali Linux & WSL)

This document provides quick reference instructions for executing and evaluating the **Linux Privilege Escalation Automation Toolkit** on real Linux systems.

---

## Primary Testing Target: Kali Linux VirtualBox VM

The designated environment is the Kali Linux 2026.3 VirtualBox VM (stored on host at `C:\CyberSecurity\kali-linux-2026.3-virtualbox-amd64`).

For complete, step-by-step instructions on transferring the handoff package, running evidence collection, and retrieving the results, see:
👉 **[`docs/KALI_HANDOFF_GUIDE.md`](KALI_HANDOFF_GUIDE.md)**

### Fast Copy-Paste Commands (Inside Kali VM)

```bash
# 1. Download handoff package from Windows host (run: python -m http.server 8000 --directory dist on Windows)
mkdir -p ~/linux-privesc-toolkit
cd ~/linux-privesc-toolkit
wget http://10.0.2.2:8000/linux-privesc-toolkit-handoff.zip
unzip -q linux-privesc-toolkit-handoff.zip

# 2. Run the automated all-in-one evidence collector
bash lab/collect_evidence.sh --yes

# 3. The bundle is created at ~/privesc_evidence_bundle_<timestamp>.zip
# Copy it to your Windows host project's incoming/ directory.
```

---

## Secondary Alternative: Ubuntu on Windows WSL

If WSL is installed on your Windows machine:
```bash
# Inside WSL terminal:
cd ~
cp -r /mnt/c/Users/.../dist/linux-privesc-toolkit-handoff.zip .
unzip -q linux-privesc-toolkit-handoff.zip -d linux-privesc-toolkit
cd linux-privesc-toolkit
bash lab/collect_evidence.sh --yes
cp ~/privesc_evidence_bundle_*.zip /mnt/c/Users/.../incoming/
```

---

## Verification on Windows

After placing the evidence bundle in `incoming/`, run:
```powershell
python tools/ingest_evidence.py incoming/privesc_evidence_bundle_<timestamp>.zip
```
This automatically verifies hashes, unpacks evidence, executes `verify_all.py`, renders terminal screenshots, and produces `evidence/INGEST_REPORT.md`.
