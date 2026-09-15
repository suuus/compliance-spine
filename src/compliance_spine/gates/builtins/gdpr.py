"""GDPR gates (Structure layer). Each is *conditional*: it applies when a change declares
(or reveals) the relevant personal-data context, and then fails closed if the required
attestation is absent.

Change ``metadata`` contract used here::

    data_category:  "none" | "personal" | "special"
    lawful_basis:   one of the Art 6 bases
    art9_condition: one of the Art 9(2) conditions       (special-category only)
    dpia:           reference/bool                        (special-category only)
    minimisation:   bool                                  (special-category only)
    persists:       bool (default true)                   (retention)
    retention_days: int > 0                               (retention)
    transfers:      [{"to": region, "mechanism": ...}]    (cross-border)
    encryption:     {"at_rest": bool, "in_transit": bool} (security)
"""

from __future__ import annotations

import re

from compliance_spine.gates.base import Gate, GateSpec

_PERSONAL = {"personal", "special"}

ART6_BASES = {
    "consent", "contract", "legal_obligation",
    "vital_interests", "public_task", "legitimate_interests",
}
ART9_CONDITIONS = {
    "explicit_consent", "employment_social_security", "vital_interests",
    "legitimate_activities", "made_public", "legal_claims",
    "substantial_public_interest", "health_care", "public_health",
    "archiving_research",
}
TRANSFER_MECHANISMS = {"adequacy", "scc", "bcr", "dpf", "derogation"}


def _meta(change) -> dict:
    return change.metadata or {}


def _touches_personal(change) -> bool:
    return _meta(change).get("data_category") in _PERSONAL


class LawfulBasisGate(Gate):
    """Art 6 / 9(1): no processing of personal data without a declared, valid lawful basis."""

    name = "lawful-basis-required"

    def check(self, change, spec: GateSpec) -> tuple[bool, list[str], dict]:
        subject = {"change": change.id, "data_category": change.data_category}
        if not _touches_personal(change):
            return True, [], subject
        basis = _meta(change).get("lawful_basis")
        if basis in ART6_BASES:
            return True, [], subject
        if basis:
            return False, [f"declared lawful_basis '{basis}' is not a valid Art 6 basis"], subject
        return False, ["personal data processed with no declared Art 6 lawful basis"], subject


class SpecialCategoryGate(Gate):
    """Art 9: special-category data needs an explicit condition, a DPIA, and minimisation."""

    name = "special-category"

    def check(self, change, spec: GateSpec) -> tuple[bool, list[str], dict]:
        subject = {"change": change.id, "data_category": change.data_category}
        if _meta(change).get("data_category") != "special":
            return True, [], subject
        m = _meta(change)
        findings: list[str] = []
        if m.get("art9_condition") not in ART9_CONDITIONS:
            findings.append("special-category data without a valid Art 9(2) condition")
        if not m.get("dpia"):
            findings.append("special-category data without a DPIA reference")
        if not m.get("minimisation"):
            findings.append("special-category data without a minimisation attestation")
        return (not findings, findings, subject)


class RetentionTtlGate(Gate):
    """Art 5(1)(e): stored personal data must declare a retention window."""

    name = "retention-ttl"

    def check(self, change, spec: GateSpec) -> tuple[bool, list[str], dict]:
        subject = {"change": change.id, "data_category": change.data_category}
        m = _meta(change)
        if not _touches_personal(change) or not m.get("persists", True):
            return True, [], subject
        days = m.get("retention_days")
        if isinstance(days, int) and days > 0:
            return True, [], subject
        return False, ["stored personal data with no declared retention window"], subject


class CrossBorderTransferGate(Gate):
    """Chapter V: personal data may not leave its region without a valid transfer mechanism."""

    name = "cross-border-transfer"

    def check(self, change, spec: GateSpec) -> tuple[bool, list[str], dict]:
        subject = {"change": change.id, "data_category": change.data_category}
        if not _touches_personal(change):
            return True, [], subject
        findings: list[str] = []
        for t in _meta(change).get("transfers", []) or []:
            dest = t.get("to", "?")
            if t.get("mechanism") not in TRANSFER_MECHANISMS:
                findings.append(f"transfer to '{dest}' has no valid Chapter V mechanism")
        return (not findings, findings, subject)


# Hardcoded-secret patterns (personal-adjacent security, Art 32).
_SECRET_PATTERNS = (
    ("aws access key id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    (
        "vendor token",
        re.compile(r"\b(?:ghp|gho|ghs|ghu|github_pat|xox[baprs]|sk|rk)[-_][A-Za-z0-9]{10,}"),
    ),
    (
        "hardcoded credential",
        re.compile(
            r"""(?ix)\b(?:password|passwd|secret|api[_-]?key|apikey|access[_-]?token|
            client[_-]?secret)\b\s*[=:]\s*['"][^'"\s]{6,}['"]"""
        ),
    ),
)
_PLACEHOLDER = re.compile(
    r"(?i)(changeme|placeholder|example|dummy|redacted"
    r"|\$\{|\{\{|<[^>]+>|os\.environ|getenv)"
)


class EncryptionRequiredGate(Gate):
    """Art 32: no secrets in source; stored personal data must be encrypted at rest + in transit."""

    name = "encryption-required"

    def check(self, change, spec: GateSpec) -> tuple[bool, list[str], dict]:
        subject = {"change": change.id, "data_category": change.data_category}
        findings: list[str] = []
        for f in change.files:
            for lineno, line in enumerate(f.content.splitlines(), start=1):
                for label, pattern in _SECRET_PATTERNS:
                    hit = pattern.search(line)
                    if hit and not _PLACEHOLDER.search(line):
                        findings.append(f"{f.path}:{lineno}: {label} in source")
        m = _meta(change)
        if _touches_personal(change) and m.get("persists", True):
            enc = m.get("encryption", {}) or {}
            if not (enc.get("at_rest") and enc.get("in_transit")):
                findings.append("stored personal data without encryption at rest and in transit")
        return (not findings, findings, subject)
