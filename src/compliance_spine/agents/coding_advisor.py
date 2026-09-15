"""Coding-advisor agent — helps a coding agent write GDPR/AI-Act-compliant code by turning
gate findings into concrete, article-referenced remediation guidance. Advisory only: it
runs the gates but writes no Evidence and makes no decision.
"""

from __future__ import annotations

from compliance_spine.agents.base import Agent, AgentResult
from compliance_spine.change import Change
from compliance_spine.gates.runner import enforce

_GUIDANCE = {
    "no-pii-in-logs": (
        "Remove or redact personal data from the log/trace/prompt; log a non-personal "
        "correlation id, or wrap values in redact()/mask()."
    ),
    "lawful-basis-required": (
        "Declare a valid Art 6 lawful basis for this processing (and record it in the DPIA/ROPA)."
    ),
    "special-category": (
        "Special-category data needs an Art 9(2) condition, a DPIA reference, and a "
        "documented minimisation step."
    ),
    "retention-ttl": (
        "Declare a retention window (retention_days) and an erasure path for the stored "
        "personal data (Art 5(1)(e), Art 17)."
    ),
    "cross-border-transfer": (
        "Attach a valid Chapter V transfer mechanism (adequacy, SCCs, BCRs, or a documented "
        "derogation) to each transfer."
    ),
    "encryption-required": (
        "Remove hardcoded secrets (use a secrets manager / environment), and declare "
        "encryption at rest and in transit for stored personal data (Art 32)."
    ),
    "automated-decision": (
        "Add a human-intervention path and a contestable explanation for the automated "
        "decision (Art 22)."
    ),
    "ai-act-risk-tier": (
        "Assess and declare the EU AI Act risk tier; for high-risk features reference the "
        "baseline obligations (Art 9-15) and human oversight (Art 14)."
    ),
    "pii-access-boundary": (
        "This component must not access personal data directly (purpose limitation, "
        "Art 5(1)(b)). Consume de-identified / aggregated data, move the access behind an "
        "authorised service, or reclassify the component boundary in "
        "spine/access-boundaries.yaml."
    ),
}


class CodingAdvisorAgent(Agent):
    name = "coding-advisor"

    def run(self, change: Change) -> AgentResult:
        result = enforce(change, emit_evidence=False)
        items: list[str] = []
        issues = 0
        for r in result.results:
            if r.compliant:
                continue
            issues += 1
            items.append(f"{r.gate}: {_GUIDANCE.get(r.gate, r.reason)}")
            items.extend(f"    · {f}" for f in r.findings)
        ok = result.allowed
        verdict = (
            "no compliance issues found"
            if ok
            else f"{issues} issue(s) to address before merge"
        )
        return AgentResult(self.name, change.id, ok, verdict, items, {"decision": result.decision})
