"""Art 22 gate: no solely-automated decision with legal or significant effect without a
human-intervention path and a contestable explanation. Non-compliance *escalates* to a
human (build-time), rather than hard-blocking — the design needs a person, not a veto.
"""

from __future__ import annotations

from compliance_spine.gates.base import Gate, GateSpec


class AutomatedDecisionGate(Gate):
    name = "automated-decision"

    def check(self, change, spec: GateSpec) -> tuple[bool, list[str], dict]:
        subject = {"change": change.id, "data_category": change.data_category}
        m = change.metadata or {}
        if not m.get("automated_decision"):
            return True, [], subject
        if not m.get("significant_effect", True):
            return True, [], subject
        findings: list[str] = []
        if not m.get("human_intervention"):
            findings.append(
                "solely-automated decision with significant effect and no "
                "human-intervention path (Art 22)"
            )
        if not (m.get("explanation") or m.get("contestable")):
            findings.append("automated decision without a contestable explanation (Art 22)")
        return (not findings, findings, subject)
