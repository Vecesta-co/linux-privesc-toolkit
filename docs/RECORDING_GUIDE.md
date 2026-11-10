# Screen Video Recording Guide

**Intern Name:** Vansh Dhawan  
**Company:** Vecesta.co  
**Internship Organization:** Unified Mentor  
**Date:** 10 November 2026  
**Project:** Linux Privilege Escalation Automation Toolkit  

---

## 1. Setup & Tools

You can record your real screen demonstration using any of the following:
- **Windows Game Bar (Built-in & Fastest):** Press `Win + Alt + R` to start/stop recording the focused window (VirtualBox or terminal).
- **OBS Studio (Recommended for advanced presentation):** Configure a Window Capture source targeting the Kali Linux VirtualBox window with your microphone active.
- **Snipping Tool (Windows 11):** Press `Win + Shift + S` or open Snipping Tool and switch to video recording mode.

---

## 2. Running the Visual Paced Demonstration

Inside your Kali Linux VirtualBox VM (or WSL terminal):

```bash
cd ~/linux-privesc-toolkit
bash lab/run_lab_demo.sh --out /tmp/demo_rec --pace 3
```

The `--pace 3` argument introduces a 3-second pause between each major action and act header, allowing you to narrate smoothly as the console displays colored output.

---

## 3. Two-Minute Spoken Narration Script

Use this talk track while recording:

> *"Hello, my name is Vansh Dhawan. As part of my internship at Unified Mentor, working under Vecesta.co, I have developed the **Linux Privilege Escalation Automation Toolkit**.*
> 
> *(Act 1 begins on screen)*  
> *Here in **Act 1**, the toolkit scans a pristine Linux system. The scanner is strictly detection-only: it uses Python's standard library, enforces a strict read-only command allowlist, contains zero exploit payloads, and never alters system state. Before and after every scan, SHA-256 hashes of critical configuration files are verified to prove zero mutation.*
> 
> *(Act 2 begins on screen)*  
> *In **Act 2**, we evaluate our automated, reversible test lab. It plants controlled, manifest-tracked security weaknesses: an SUID copy of find, world-writable files, a dormant root cron job with a wildcard expansion vector, passwordless sudo permissions, a systemd unit with an insecure PATH, and an interpreter capability.*
> *The scanner is executed first as root, and then with dropped privileges as our limited user, privlab, highlighting the visibility boundary between administrative and restricted accounts. We also demonstrate simulated kernel matching against known CVE advisories.*
> 
> *(Act 3 begins on screen)*  
> *In **Act 3**, the lab's automated manifest-driven teardown executes. Every planted file, directory, and the test user are permanently removed. The post-teardown scan and differential comparison confirm that all planted vulnerabilities are resolved with zero leftover artifacts.*
> 
> *The toolkit outputs structured reports in JSON, Markdown, and self-contained HTML. All findings, severity ratings, exploitation vectors, and hardening mitigations are fully documented.*
> 
> *Thank you."*

---

## 4. Post-Recording Verification Checklist

- [ ] Video shows clear 1080p resolution without blurred text.
- [ ] Terminal colors and act banners are clearly legible.
- [ ] Narration cleanly matches the on-screen execution.
- [ ] Final teardown PASS lines are clearly visible at the end of the recording.
