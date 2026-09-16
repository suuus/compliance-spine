"""Compliance matrix — regulation / article -> requirement -> enforcing gate -> coverage status.

Generated from the never-delegate intent, the gate configuration, the implemented gates, and the
evidence ledger. Turns "which gates exist" into an accountable, regulator-facing coverage view
(the artefact a real compliance team maintains by hand — here it is derived from the spine).
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass

import yaml

from compliance_spine.config import paths
from compliance_spine.evidence.ledger import Ledger
from compliance_spine.gates.builtins import GATE_CLASSES
from compliance_spine.intent import IntentRegistry

_ART_RE = re.compile(r"\bArt(?:icle)?\.?\s*(\d+(?:\s*\([0-9a-z]+\))*(?:\s*[\u2013-]\s*\d+)?)", re.I)
_CHAP_RE = re.compile(r"\bChap(?:ter)?\.?\s+([IVXLC]+)\b", re.I)
_ANNEX_RE = re.compile(r"\bAnnex\s+([IVXLC]+)\b", re.I)

_STATUS_ICON = {"enforced": "\u2705", "unenforced": "\U0001f7e0", "no-gate": "\u26aa"}


def _regulation(text: str) -> str:
    return "EU AI Act" if re.search(r"ai act", text, re.I) else "GDPR"


def _articles(text: str) -> list[str]:
    found: list[str] = []
    for m in _ART_RE.finditer(text):
        found.append("Art " + re.sub(r"\s+", "", m.group(1)))
    for m in _CHAP_RE.finditer(text):
        found.append("Chapter " + m.group(1).upper())
    for m in _ANNEX_RE.finditer(text):
        found.append("Annex " + m.group(1).upper())
    seen: set[str] = set()
    uniq: list[str] = []
    for a in found:
        if a not in seen:
            seen.add(a)
            uniq.append(a)
    return uniq


@dataclass
class MatrixRow:
    rank: int
    requirement: str
    regulation: str
    articles: list[str]
    gate: str | None
    status: str  # enforced | unenforced | no-gate
    evidence_count: int


@dataclass
class Matrix:
    rows: list[MatrixRow]

    @property
    def enforced(self) -> int:
        return sum(1 for r in self.rows if r.status == "enforced")

    @property
    def evidenced(self) -> int:
        return sum(1 for r in self.rows if r.evidence_count)

    @property
    def with_article(self) -> int:
        return sum(1 for r in self.rows if r.articles)

    def _summary(self) -> str:
        n = len(self.rows)
        return (
            f"**Coverage:** {self.enforced}/{n} principles enforced by a gate \u00b7 "
            f"{self.with_article}/{n} mapped to an article \u00b7 "
            f"{self.evidenced}/{n} with evidence in the ledger."
        )

    def render_markdown(self) -> str:
        lines = [
            "# Compliance matrix",
            "",
            "Derived from the never-delegate intent, the gate configuration, and the evidence "
            "ledger. Status: **enforced** (a gate implements it), **unenforced** (configured but "
            "not yet implemented), **no-gate** (enforced by the detector / agents, not a gate).",
            "",
            "| # | Requirement | Regulation | Article(s) | Enforcing gate | Status | Evidence |",
            "|---|---|---|---|---|---|---|",
        ]
        for r in self.rows:
            arts = ", ".join(r.articles) or "\u2014"
            gate = f"`{r.gate}`" if r.gate else "\u2014"
            icon = _STATUS_ICON.get(r.status, "")
            ev = str(r.evidence_count) if r.evidence_count else "\u2014"
            lines.append(
                f"| {r.rank} | {r.requirement} | {r.regulation} | {arts} | {gate} | "
                f"{icon} {r.status} | {ev} |"
            )
        lines += ["", self._summary()]
        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps(
            {
                "principles": [asdict(r) for r in self.rows],
                "summary": {
                    "total": len(self.rows),
                    "enforced": self.enforced,
                    "with_article": self.with_article,
                    "evidenced": self.evidenced,
                },
            },
            indent=2,
        )


def build_matrix(config: dict | None = None, framework: str | None = None) -> Matrix:
    registry = IntentRegistry.load()
    cfg = config if config is not None else yaml.safe_load(
        paths().gate_config.read_text(encoding="utf-8")
    ) or {}
    gates_cfg = cfg.get("gates", {}) or {}

    # Reverse map: never-delegate rule -> the gate that enforces it.
    rule_to_gate: dict[str, str] = {}
    for name, spec in gates_cfg.items():
        rule = registry.resolve((spec or {}).get("intent_ref", ""))
        if rule is not None:
            rule_to_gate.setdefault(rule.slug, name)

    # Evidence counts per gate (records carry rule_id = "spine/policies/<gate>").
    ev_count: dict[str, int] = {}
    try:
        for rec in Ledger().read_all():
            rid = rec.get("rule_id", "")
            if rid.startswith("spine/policies/"):
                gate = rid.rsplit("/", 1)[-1]
                ev_count[gate] = ev_count.get(gate, 0) + 1
    except Exception:  # noqa: BLE001 — a missing/broken ledger must not break the report
        pass

    rows: list[MatrixRow] = []
    for rule in sorted(registry.rules, key=lambda r: r.rank):
        text = f"{rule.title} {rule.body}"
        gate = rule_to_gate.get(rule.slug)
        if gate is None:
            status = "no-gate"
        elif gate in GATE_CLASSES:
            status = "enforced"
        else:
            status = "unenforced"
        rows.append(
            MatrixRow(
                rank=rule.rank,
                requirement=" ".join(rule.title.split()),
                regulation=_regulation(text),
                articles=_articles(text),
                gate=gate,
                status=status,
                evidence_count=ev_count.get(gate or "", 0),
            )
        )
    if framework:
        from compliance_spine.frameworks import framework_of

        rows = [r for r in rows if r.gate and framework_of(r.gate) == framework]
    return Matrix(rows)
