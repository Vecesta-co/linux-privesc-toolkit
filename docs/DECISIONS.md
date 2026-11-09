# Decisions

## Runtime and environment

- The scanner targets Python 3.10+ and uses only the standard library at runtime.
- Host discovery on 2026-11-09 found Windows 11, Python 3.11.9 (`python`), Git 2.56.0, and an installed Kali 2026.3 VirtualBox VM. WSL had no distro and Docker's Linux engine was not running.
- The user supplied `C:\CyberSecurity` specifically as an available Kali resource. The VM is registered in VirtualBox and is the selected real-Linux target. It is a VM, satisfying the disposable-environment boundary for the lab. Project source and delivered evidence remain in this repository; lab files are created only in the guest.
- The Kali VM description advertises the default `kali` login. Use guest-control or a private host-only transfer path; do not put the host's personal absolute paths in committed artifacts.

## Scope choices

- This is a detection-only scanner. It never invokes an exploit, modifies permissions or system files, enables services, or changes ownership. The separate lab scripts intentionally create tracked weaknesses only after an explicit disposable-lab confirmation flag and remove only manifest-listed artifacts.
- Kernel CVE matches are advisory version-range checks. Vendor backports make version-only matching prone to false positives; reports require administrator/vendor validation before remediation decisions.
- Upstream series status is checked against kernel.org during document generation. Distro kernels may continue receiving security fixes after upstream EOL.
- Development-only dependencies are pinned in `requirements-dev.txt`; runtime use requires no third-party packages.
- PyMuPDF is a documentation-only extra used to rasterize the PDF pages exported by the installed Microsoft Word. The bundled DOCX renderer was first attempted but lacked `pdf2image`; no LibreOffice install was available. The official PyMuPDF `Page.get_pixmap(dpi=...)` API provides the local page-image fallback.

## Availability limits

- A real Linux scan can run in the registered Kali VM if guest control and credentials work. If VM execution or file transfer fails, that phase and all environment-dependent evidence must be marked `SKIPPED` with the observed reason; Windows is not represented as Linux evidence.
- Recording the user's physical desktop is not possible from this build. A recording guide is supplied instead.
- PDF export depends on an available LibreOffice/Word installation. If neither is available, the DOCX remains the editable deliverable and export is documented as skipped.
