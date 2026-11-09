# Traceability matrix

| Requirement | Feature | Test | Evidence |
|---|---|---|---|
| Detection only; safe command runner | `privesc/runner.py` allowlist and fixed argument validation | Runner allowlist and dangerous `find` argument tests | `evidence/safety_proof.txt` (Linux only) |
| System identity and OS details | `privesc/modules/sysinfo.py` | Parser and collector behavior tests | Scan JSON `meta` |
| SUID, permissions, services, sudo, cron, capabilities | Small independent collectors and pure parsers | Fixture parser and analysis-rule tests | Scan findings and coverage |
| Kernel version checks | Advisory data and version parser | Version/range/EOL tests | Simulated-kernel scan |
| JSON, Markdown, HTML, compare | `privesc/report.py`, `privesc/compare.py` | Serialization and compare tests | `reports/` and `evidence/run*/` |
| Lab finds planted issues and teardown removes them | Manifest-driven scripts | Linux integration demo and `verify_all.py` | `evidence/run*/` |
| User documentation and presentation | `tools/make_docs.py` | Artifact reopen/structure checks | `docs/Project_Report.docx`, `docs/Final_Presentation.pptx` |
