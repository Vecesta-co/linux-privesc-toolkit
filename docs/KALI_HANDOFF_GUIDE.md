# Kali Linux Live Evidence Collection & Handoff Guide

This guide describes the complete procedure for deploying, running, and collecting live evidence for the **Linux Privilege Escalation Automation Toolkit** inside your Kali Linux VirtualBox VM.

---

## 1. Safety & Preparation: Take a VM Snapshot

> [!IMPORTANT]
> The automated validation lab intentionally plants real, reversible security weaknesses (SUID copies, world-writable files, dormant cron jobs, sudoers rules).
> While the demo scripts strictly track and remove every created artifact, **always take a VirtualBox snapshot before beginning** so you can revert the VM to a 100% pristine state in one click.

1. In VirtualBox Manager, select your Kali Linux VM (`kali-linux-2026.3-virtualbox-amd64`).
2. Click **Machine** → **Take Snapshot...** (Name: `Pre-Audit-Baseline`).
3. Power on the VM and log in as `kali` (default password: `kali`).

---

## 2. Transfer the Toolkit Handoff Archive into Kali

The clean handoff archive is located on your Windows host at:
`dist/linux-privesc-toolkit-handoff.zip`

Choose **any one** of the following transfer methods:

### Method A: Local HTTP Server over NAT (Recommended & Fastest)
VirtualBox NAT networking exposes the Windows host to the guest at IP `10.0.2.2`.

1. **On Windows (PowerShell in project root):**
   ```powershell
   python -m http.server 8000 --directory dist
   ```
2. **Inside Kali Linux Terminal:**
   ```bash
   cd ~
   wget http://10.0.2.2:8000/linux-privesc-toolkit-handoff.zip
   ```
3. Stop the Python server on Windows (`Ctrl+C`).

### Method B: VirtualBox Shared Folder
1. In VirtualBox VM window: **Devices** → **Shared Folders** → **Shared Folder Settings...**
2. Add a transient share mapping to your Windows project `dist` folder.
3. In Kali:
   ```bash
   sudo mkdir -p /media/sf_dist
   sudo mount -t vboxsf dist /media/sf_dist 2>/dev/null || sudo mount -t 9p -o trans=virtio dist /media/sf_dist
   cp /media/sf_dist/linux-privesc-toolkit-handoff.zip ~/
   ```

### Method C: Private Git Clone
If your host project is pushed to a private GitHub repo:
```bash
git clone <your-repo-url> ~/linux-privesc-toolkit
```

---

## 3. Extract and Execute the Collector

Inside Kali Linux terminal:

```bash
# 1. Prepare directory and extract
mkdir -p ~/linux-privesc-toolkit
cd ~/linux-privesc-toolkit
unzip -q ~/linux-privesc-toolkit-handoff.zip

# 2. Run the one-command automated collector
bash lab/collect_evidence.sh
```

*(Optional: Use `bash lab/collect_evidence.sh --yes` to skip the interactive confirmation prompt).*

### What the Collector Does
1. Runs `lab/preflight.sh` to verify all required dependencies.
2. Captures host environment information (`uname -a`, `/etc/os-release`, Python, GNU find, user identity, virtual environment).
3. Executes pytest twice on Linux (verifying that the Linux-only end-to-end test passes).
4. Executes the 3-act disposable lab demo twice from scratch (`run1` and `run2`).
5. Generates two-run fingerprint consistency comparisons (`double_check_summary.md`).
6. Executes full filesystem scans (normal user and root) with recorded execution durations.
7. Performs the interrupt-safety test (`lab/test_interrupt_teardown.sh`) verifying SIGINT cleanup.
8. Performs final clean-state verification.
9. Computes cryptographic hashes and creates the bundle: `~/privesc_evidence_bundle_<timestamp>.zip`.

**Expected Duration:** Approximately 2 to 4 minutes.

---

## 4. Expected Output (Success Example)

Upon successful completion, the script prints:

```
========================================================================
                   EVIDENCE COLLECTION COMPLETE                         
========================================================================
Bundle Archive: /home/kali/privesc_evidence_bundle_20261110_123456Z.zip
Bundle SHA256:  a1b2c3d4e5f6...

Summary of Steps:
Preflight                      | PASS     | All required tools verified
Environment Info               | PASS     | evidence/env_info.txt written
pytest Linux Run 1             | PASS     | 30 passed (Linux e2e PASSED)
pytest Linux Run 2             | PASS     | 30 passed (Linux e2e PASSED)
Demo Run 1                     | PASS     | All lab checks verified
Demo Run 2                     | PASS     | All lab checks verified
Two-Run Comparison             | PASS     | double_check_summary.md written
Full Scans                     | PASS     | Durations recorded in evidence/full_scan
Interrupt Safety               | PASS     | Trap verified teardown on SIGINT
Clean State Proof              | PASS     | Zero leftover lab artifacts
========================================================================
```

---

## 5. Transfer the Evidence Bundle Back to Windows

Copy `~/privesc_evidence_bundle_*.zip` from Kali to your Windows project's `incoming/` directory:

1. **Via VirtualBox Shared Folder:**
   ```bash
   cp ~/privesc_evidence_bundle_*.zip /media/sf_shared/incoming/
   ```
2. **Via Drag & Drop (Guest Additions enabled):**
   Drag the zip file from the Kali file manager into the Windows `incoming/` folder.
3. **Via Local SCP/SSH (if SSH is enabled):**
   ```powershell
   scp kali@<VM_IP>:~/privesc_evidence_bundle_*.zip .\incoming\
   ```

Once placed in `incoming/`, run on Windows:
```powershell
python tools/ingest_evidence.py incoming/privesc_evidence_bundle_<timestamp>.zip
```

---

## 6. Restore VirtualBox Snapshot

Once the evidence zip is safely copied back to Windows:
1. Power off the Kali VM.
2. In VirtualBox Manager, select the snapshot `Pre-Audit-Baseline` and click **Restore**.
3. Your Kali VM is immediately restored to its pristine pre-lab state.

---

## 7. Troubleshooting & Common Questions

| Issue | Cause | Solution |
|---|---|---|
| `^M: bad interpreter` | Windows CRLF line endings | Run `sed -i 's/\r$//' lab/*.sh` in Kali. (Note: `make_handoff.py` automatically strips CRLF). |
| `getcap: command not found` | `libcap2-bin` package not installed | Run `sudo apt-get install -y libcap2-bin`. (Preflight allows this to degrade gracefully to SKIPPED if missing). |
| `pytest: command not found` | Virtual environment or pytest not installed | The script automatically sets up a `.venv` or installs `python3-pytest`. Or run `sudo apt-get install -y python3-pytest`. |
| `sudo: a password is required` | User does not have passwordless sudo | Run `bash lab/collect_evidence.sh`; it prompts for sudo once at startup and keeps credentials alive. |
| `systemd not running` | WSL 1 or minimal container environment | The toolkit parses systemd unit files directly from `/etc/systemd/system` and `/lib/systemd/system`. Systemd daemon is NOT required. |
| Offline / No Internet | Host or VM has no network | The toolkit runtime uses **Python standard library only** (0 pip packages). The entire scan and lab run 100% offline. |

---

## 8. Alternative: Ubuntu in WSL Setup

If you prefer WSL instead of VirtualBox:
1. Open PowerShell on Windows:
   ```powershell
   wsl --install -d Ubuntu
   ```
2. In Ubuntu terminal:
   ```bash
   sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pytest libcap2-bin
   mkdir -p ~/toolkit && cd ~/toolkit
   unzip /mnt/c/Users/.../dist/linux-privesc-toolkit-handoff.zip
   bash lab/collect_evidence.sh
   cp ~/privesc_evidence_bundle_*.zip /mnt/c/Users/.../incoming/
   ```

---

## 9. Screen Video Recording Guide (for Internship Viva)

To record your demonstration video:
1. Open terminal in Kali (or Ubuntu):
   ```bash
   bash lab/run_lab_demo.sh --out /tmp/demo_rec --pace 3
   ```
2. On Windows, press `Win + Alt + R` (Windows Game Bar) or use OBS to record the VM window.
3. Follow the 2-minute spoken narration script in [`docs/RECORDING_GUIDE.md`](file:///c:/Users/pc/OneDrive/Desktop/Unified%20Mentor(Intership%20journey)/Projects%20made%20under%20this%20internship/Project-2/docs/RECORDING_GUIDE.md).

