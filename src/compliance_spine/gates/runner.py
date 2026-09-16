"""Enforcement runner — evaluate every gate against a change, emit Evidence for every
decision, apply active overrides, and aggregate a fail-closed verdict.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from compliance_spine import __version__ as SPINE_VERSION
from compliance_spine.change import Change
from compliance_spine.evidence.ledger import Ledger
from compliance_spine.evidence.record import DecisionRecord, structure_findings
from compliance_spine.gates.base import ALLOW, BLOCK, HALT, GateResult, worst
from compliance_spine.gates.registry import build_gates
from compliance_spine.overrides import OverrideStore


def emit(
    ledger: Ledger,
    change: Change,
    gate: str,
    intent_ref: str,
    severity: str,
    action: str,
    actor: dict,
    owner: dict | None = None,
    override: dict | None = None,
    findings: tuple[str, ...] = (),
) -> dict:
    record = DecisionRecord(
        action=action,
        rule_id=f"spine/policies/{gate}",
        intent_ref=intent_ref,
        severity=severity,
        inputs_hash=change.payload_hash(),
        actor=actor,
        subject={
            "change": change.id,
            "data_category": change.data_category,
            "ai_feature": change.metadata.get("ai_feature"),
        },
        owner=owner,
        override=override,
        spine_version=SPINE_VERSION,
        findings=structure_findings(findings) or None,
    )
    return ledger.append(record)


@dataclass
class EnforcementResult:
    change_id: str
    phase: str
    results: list[GateResult]
    unenforced: list[str]
    overrides_applied: list[str]

    @property
    def decision(self) -> str:
        return worst([r.decision for r in self.results]) if self.results else ALLOW

    @property
    def allowed(self) -> bool:
        """A change may proceed only on a clean, non-escalated, non-blocked verdict."""
        return self.decision == ALLOW

    def summary(self) -> str:
        head = f"[{self.decision.upper()}] change '{self.change_id}' ({self.phase})"
        lines = [head]
        for r in self.results:
            mark = "ok" if r.compliant else r.decision
            lines.append(f"  - {r.gate}: {mark} — {r.reason}")
            for f in r.findings:
                lines.append(f"      · {f}")
        if self.overrides_applied:
            lines.append(f"  overrides applied: {', '.join(self.overrides_applied)}")
        if self.unenforced:
            lines.append(f"  unenforced (not yet implemented): {', '.join(self.unenforced)}")
        return "\n".join(lines)


def enforce(
    change: Change,
    phase: str = "build",
    ledger: Ledger | None = None,
    overrides: OverrideStore | None = None,
    config: dict | None = None,
    emit_evidence: bool = True,
    only: set[str] | None = None,
) -> EnforcementResult:
    gates, unenforced = build_gates(config, only=only)
    ledger = ledger if ledger is not None else Ledger()
    results: list[GateResult] = []
    applied: list[str] = []

    for gate, spec in gates:
        res = gate.evaluate(change, spec, phase)
        active = (
            overrides.active(spec.name)
            if overrides is not None and res.decision in (BLOCK, HALT)
            else None
        )
        if active is not None:
            if emit_evidence:
                emit(
                    ledger, change, res.gate, res.intent_ref, res.severity,
                    action="override",
                    actor={"type": "human", "id": active.human_id},
                    owner=active.owner,
                    override=active.to_evidence(),
                    findings=res.findings,
                )
            applied.append(spec.name)
            res = replace(
                res, decision=ALLOW, reason=f"silenced by active override until {active.expires}"
            )
        elif emit_evidence:
            emit(
                ledger, change, res.gate, res.intent_ref, res.severity,
                action=res.decision,
                actor={"type": "gate", "id": res.gate},
                findings=res.findings,
            )
        results.append(res)

    return EnforcementResult(change.id, phase, results, unenforced, applied)
