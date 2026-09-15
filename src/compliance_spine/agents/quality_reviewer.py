"""Quality-reviewer agent — a GDPR/AI-Act-aware review that runs the gates, forms a verdict,
and *refuses to auto-approve never-delegate items* (they escalate to a human). Writes a
single review record to Evidence when given a ledger.
"""

from __future__ import annotations

from compliance_spine.agents.base import Agent, AgentResult
from compliance_spine.change import Change
from compliance_spine.evidence.ledger import Ledger
from compliance_spine.gates.base import ALLOW, ESCALATE, GateResult
from compliance_spine.gates.runner import emit, enforce

_SEVERITY_RANK = {"critical": 3, "high": 2, "medium": 1, "info": 0}


def _worst_severity(results: list[GateResult]) -> str:
    if not results:
        return "info"
    return max(results, key=lambda r: _SEVERITY_RANK.get(r.severity, 0)).severity


class QualityReviewerAgent(Agent):
    name = "quality-reviewer"

    def run(self, change: Change, ledger: Ledger | None = None) -> AgentResult:
        result = enforce(change, emit_evidence=False)
        decision = result.decision
        noncompliant = [r for r in result.results if not r.compliant]

        if decision == ALLOW:
            verdict = "approve — compliant"
        elif decision == ESCALATE:
            verdict = "needs human sign-off (never-delegate) — not auto-approved"
        else:
            verdict = "changes requested (blocking)"

        items = [f"{r.gate} [{r.decision}]: {r.reason}" for r in noncompliant]
        detail = {"decision": decision}

        if ledger is not None:
            intent_ref = noncompliant[0].intent_ref if noncompliant else "intent/never-delegate"
            record = emit(
                ledger, change,
                gate=self.name,
                intent_ref=intent_ref,
                severity=_worst_severity(noncompliant),
                action=decision,
                actor={"type": "agent", "id": self.name},
            )
            detail["evidence_id"] = record["id"]

        return AgentResult(self.name, change.id, decision == ALLOW, verdict, items, detail)
