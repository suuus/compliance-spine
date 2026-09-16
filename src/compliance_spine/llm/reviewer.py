"""Layered reviewer — deterministic gates as a fail-closed FLOOR, unioned with a pluggable
ASSESSOR (the ceiling) that catches what the fixed rules miss.

The union is **fail-closed**: the assessor may *add* findings and *raise* the verdict, but it
can never clear a gate's block. So you get the assessor's recall (catch more) without a floor
that regresses or that a prompt-injected input can erode.

Assessors are pluggable:
  - ``HeuristicAssessor`` — a deterministic stand-in used offline and in tests/CI. It catches a
    few real patterns the core gates don't, so the architecture and the scorecard are
    exercised without a model. It is **not** an LLM.
  - ``CallableAssessor`` — wraps any model callable ``(prompt) -> json`` (your Copilot model,
    GitHub Models, or an Azure AI Foundry endpoint). This is where real probabilistic recall
    comes from. See docs/LLM-LAYER.md.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

from compliance_spine import __version__ as SPINE_VERSION
from compliance_spine.change import Change
from compliance_spine.evidence.ledger import Ledger
from compliance_spine.evidence.record import DecisionRecord
from compliance_spine.gates.base import ALLOW, BLOCK, ESCALATE, worst
from compliance_spine.gates.runner import EnforcementResult, enforce

# assessor finding decision -> spine decision
_DECISION = {"block": BLOCK, "flag": ESCALATE, "allow": ALLOW}


@dataclass
class Finding:
    kind: str
    decision: str  # "block" (high-confidence) | "flag" (candidate -> escalate)
    rationale: str
    location: str = ""
    confidence: float = 0.6  # assessor's probability this is a real violation (0-1)

    @property
    def spine_decision(self) -> str:
        return _DECISION.get(self.decision, ESCALATE)


class Assessor(Protocol):
    name: str

    def assess(self, change: Change, context: str = "") -> list[Finding]: ...


# ---------------------------------------------------------------------------
# Reference stand-in assessor (deterministic; NOT an LLM)
# ---------------------------------------------------------------------------

_PII = (
    "email", "ssn", "bsn", "nino", "full_name", "first_name", "last_name", "surname",
    "phone", "dob", "birthdate", "iban", "passport", "diagnosis", "medical_history",
    "health_record", "ip_address", "address", "biometric",
)
_PII_RE = re.compile(rf"\b(?:{'|'.join(_PII)})\b", re.I)
_MODEL_CALL = re.compile(
    r"\bprompt\s*=|\.(?:complete|chat|generate|invoke|predict)\s*\(|\b(?:openai|llm|model)\b",
    re.I,
)
_OUTBOUND = re.compile(
    r"\brequests?\.|httpx|urllib|\bfetch\s*\(|\.post\s*\(|\.put\s*\(|https?://", re.I
)


class HeuristicAssessor:
    """Deterministic stand-in for a model — catches a few things the core gates miss."""

    name = "heuristic-stand-in"

    def assess(self, change: Change, context: str = "") -> list[Finding]:
        findings: list[Finding] = []
        for f in change.files:
            for lineno, line in enumerate(f.content.splitlines(), start=1):
                loc = f"{f.path}:{lineno}"
                code, _, comment = line.partition("#")
                if not _PII_RE.search(line):
                    continue
                if comment and _PII_RE.search(comment):
                    findings.append(Finding(
                        "pii-in-comment", "flag",
                        "personal data referenced in a comment / TODO", loc, confidence=0.55))
                if _MODEL_CALL.search(code) and _PII_RE.search(code):
                    findings.append(Finding(
                        "pii-to-model", "block",
                        "personal data sent to a model / prompt (Art 5, minimisation)", loc,
                        confidence=0.9))
                elif _OUTBOUND.search(code) and _PII_RE.search(code):
                    findings.append(Finding(
                        "undeclared-transfer", "flag",
                        "personal data in an outbound call — possible undeclared transfer", loc,
                        confidence=0.7))
        return findings


class NullAssessor:
    name = "none"

    def assess(self, change: Change, context: str = "") -> list[Finding]:
        return []


class CallableAssessor:
    """Wrap a real model. ``fn(prompt) -> str`` returning JSON findings; parse failures are
    treated as *no findings* (fail-closed floor still applies)."""

    def __init__(self, fn: Callable[[str], str], name: str = "model", context: str = "") -> None:
        self._fn = fn
        self.name = name
        self._context = context

    def _prompt(self, change: Change) -> str:
        files = "\n\n".join(f"# {cf.path}\n{cf.content}" for cf in change.files)
        return (
            "You are a GDPR / EU AI Act code reviewer. Return a JSON list of findings; each "
            '{"kind","decision":"block|flag","rationale","location"}. Flag personal data sent '
            "to logs/models/third parties, missing lawful basis/retention, and access-boundary "
            f"or purpose-limitation issues.\n\nCONTEXT:\n{self._context}\n\nCHANGE:\n{files}"
        )

    def assess(self, change: Change, context: str = "") -> list[Finding]:
        try:
            raw = self._fn(self._prompt(change))
            data = json.loads(raw)
            return [
                Finding(
                    kind=str(d.get("kind", "llm-finding")),
                    decision=str(d.get("decision", "flag")),
                    rationale=str(d.get("rationale", "")),
                    location=str(d.get("location", "")),
                    confidence=float(d.get("confidence", 0.5)),
                )
                for d in data
            ]
        except Exception:  # noqa: BLE001 - a broken/injected model output must not weaken the floor
            return []


# ---------------------------------------------------------------------------
# The layered reviewer
# ---------------------------------------------------------------------------

_SEVERITY_RANK = {"critical": 3, "high": 2, "medium": 1, "info": 0}


@dataclass
class ReviewResult:
    change_id: str
    gate_result: EnforcementResult
    findings: list[Finding] = field(default_factory=list)

    @property
    def decision(self) -> str:
        return worst([self.gate_result.decision, *(f.spine_decision for f in self.findings)])

    @property
    def allowed(self) -> bool:
        return self.decision == ALLOW

    def summary(self) -> str:
        lines = [f"[{self.decision.upper()}] change '{self.change_id}' (layered review)"]
        lines.append(f"  floor (gates): {self.gate_result.decision}")
        if self.findings:
            lines.append("  assessor findings (ceiling):")
            for f in self.findings:
                lines.append(f"    - {f.kind} [{f.decision}] {f.location}: {f.rationale}")
        else:
            lines.append("  assessor findings (ceiling): none")
        return "\n".join(lines)


class LayeredReviewer:
    def __init__(self, assessor: Assessor | None = None) -> None:
        self.assessor = assessor or HeuristicAssessor()

    def review(
        self, change: Change, ledger: Ledger | None = None, config: dict | None = None
    ) -> ReviewResult:
        gate_result = enforce(change, emit_evidence=False, config=config)
        findings = self.assessor.assess(change)
        result = ReviewResult(change.id, gate_result, findings)

        if ledger is not None:
            self._emit(ledger, change, result)
        return result

    def _emit(self, ledger: Ledger, change: Change, result: ReviewResult) -> None:
        # advisory record per assessor finding (captures the rationale + confidence for audit)
        for f in result.findings:
            ledger.append(DecisionRecord(
                action="emit",
                rule_id=f"llm/{f.kind}",
                intent_ref="advisory/llm-review",
                severity="info",
                inputs_hash=change.payload_hash(),
                actor={"type": "llm", "id": self.assessor.name},
                subject={"change": change.id, "note": f.rationale, "kind": f.kind},
                confidence=f.confidence,
                spine_version=SPINE_VERSION,
            ))
        # one combined verdict record
        contributed = bool(result.findings)
        ledger.append(DecisionRecord(
            action=result.decision,
            rule_id="agents/layered-reviewer",
            intent_ref="advisory/llm-review",
            severity="high" if result.decision != ALLOW else "info",
            inputs_hash=change.payload_hash(),
            actor={"type": "llm" if contributed else "agent", "id": "layered-reviewer"},
            subject={"change": change.id, "model": self.assessor.name},
            spine_version=SPINE_VERSION,
        ))
