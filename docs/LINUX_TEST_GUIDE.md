# Linux test guide

The current host has no configured WSL distribution. The supplied Kali VirtualBox guest is powered off when this project is delivered because its Guest Additions control session was unavailable before a user logged in. The lab remains unrun until you open the Kali VM, log in as `kali`, and run the commands below in a terminal inside the guest.

The repository must be copied to the guest's ext4 home directory before the lab runs. Do not run the lab directly from a VirtualBox shared folder: the lab and its scans must be on a Linux filesystem with real ownership and permission bits. After copying the folder into `~/linux-privesc-toolkit`, use:

```bash
cd ~/linux-privesc-toolkit
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
python3 -m pytest -q
bash lab/run_lab_demo.sh --out evidence/run1 --pace 3
python3 tools/verify_all.py evidence/run1
bash lab/run_lab_demo.sh --out evidence/run2 --pace 3
python3 tools/verify_all.py evidence/run2
python3 run_scan.sh --help
bash run_scan.sh --label manual --fast --output-dir reports/manual
```

The demo refuses to plant the lab unless it runs as root and supplies the explicit disposable-lab confirmation flag internally. It tears down the lab on exit and writes the command transcript, reports, comparisons, before/after hashes, independent checks, and teardown check under the chosen evidence directory. Verify both runs before bringing them back. A second demo starts from the guest's clean state after the first demo's teardown.

## Optional WSL setup

If you prefer WSL instead of the Kali VM, install Ubuntu through Windows' documented WSL setup, complete its first-run account setup, then copy this repository into the WSL ext4 home (not `/mnt/c`). Open Ubuntu, `cd` into that copy, and run the same Linux commands above. This project does not install WSL or Docker for you.

If guest control becomes available after logging into Kali, host-side copy and evidence transfer can use VirtualBox Guest Control. `VBoxManage guestcontrol` supports recursive `copyto` and `copyfrom`; use the Kali VM name shown in VirtualBox and the `kali` account. Keep the project inside `/home/kali` while running scans and copy the resulting evidence folder back to the Windows project after teardown.
