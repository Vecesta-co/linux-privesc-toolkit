# Recording guide

I cannot record the user's physical desktop from this build. The demo script produces a real console transcript and screenshots from the Linux session when you run it inside Kali.

## Before recording

1. Open the Kali VM in VirtualBox and log in as `kali`.
2. Open a terminal in the Linux copy of this repository.
3. Confirm the lab is clean with `test ! -e /opt/privesc-lab && ! id privlab >/dev/null 2>&1`.
4. Start Windows Game Bar with `Win+Alt+R`, use Snipping Tool with `Win+Shift+S` for still images, or use OBS if you need scene or audio control.

## Capture command

```bash
cd ~/linux-privesc-toolkit
bash lab/run_lab_demo.sh --out evidence/recording --pace 3
```

The script pauses between acts, creates the disposable lab, scans as root and as the limited lab user, shows a simulated kernel version, removes the lab, and compares the reports. Do not leave the lab active after recording; let the final act finish and confirm `teardown_check.txt` contains only `PASS` lines.

## Two-minute narration

“This project audits Linux privilege boundaries using read-only enumeration. The scanner records the current account, system version, permissions, sudo policy, scheduled jobs, service units, capabilities, and kernel advisories. It does not run exploits or modify the operating system. The command runner accepts only a small list of read-only commands and applies timeouts.

“The first act records a baseline. In the second act, a disposable lab adds tracked SUID, writable-file, cron, sudo, service, capability, and home-directory weaknesses. We compare root and limited-user visibility and then show a simulated old kernel version. The simulated banner matters because it is not the VM's kernel. In the final act, the manifest-driven teardown removes each created item. The safety proof compares hashes of account and sudo configuration before and after every scan. The final comparison reports what was fixed. These results are a training demonstration; real systems need explicit authorization and vendor review.”
