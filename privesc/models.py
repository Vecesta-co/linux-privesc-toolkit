"""Small data models shared by collectors, rules, and report writers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Any


@dataclass
class Finding:
    id: str
    category: str
    title: str
    severity: str
    confidence: str
    evidence: dict[str, Any]
    exploitation: str
    mitigation: str
    references: list[str]
    module: str

    @property
    def fingerprint(self) -> str:
        key_evidence = {k: self.evidence[k] for k in ("path", "command", "cve", "subject", "source", "unit") if k in self.evidence}
        raw = json.dumps([self.id, key_evidence], sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["fingerprint"] = self.fingerprint
        return result


@dataclass
class ScanResult:
    meta: dict[str, Any]
    findings: list[Finding] = field(default_factory=list)
    coverage: dict[str, dict[str, str]] = field(default_factory=dict)
    commands: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def summary(self) -> dict[str, Any]:
        severities = {name: 0 for name in ("Critical", "High", "Medium", "Low", "Info")}
        categories: dict[str, int] = {}
        for finding in self.findings:
            severities[finding.severity] = severities.get(finding.severity, 0) + 1
            categories[finding.category] = categories.get(finding.category, 0) + 1
        risk = "Critical" if severities["Critical"] else "High" if severities["High"] else "Medium" if severities["Medium"] else "Low" if self.findings else "Informational"
        return {"total": len(self.findings), "by_severity": severities, "by_category": dict(sorted(categories.items())), "overall_risk": risk}

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "tool": {"name": "Linux Privilege Escalation Automation Toolkit", "version": "1.0.0"},
            "created_at": self.created_at,
            "meta": self.meta,
            "summary": self.summary(),
            "findings": [item.to_dict() for item in self.findings],
            "coverage": self.coverage,
            "commands": self.commands,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScanResult":
        findings = [Finding(**{key: item[key] for key in Finding.__dataclass_fields__}) for item in data.get("findings", [])]
        return cls(meta=data.get("meta", {}), findings=findings, coverage=data.get("coverage", {}), commands=data.get("commands", []), created_at=data.get("created_at", ""))
