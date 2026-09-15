"""Gate framework — Structure layer.

A gate proves that a change complies with one never-delegate principle. Gates are
**fail-closed**: if a gate cannot prove compliance — including when it raises — the
outcome is the configured non-compliant decision (block by default), never allow.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

# Decision vocabulary (subset of the Evidence ``action`` enum).
ALLOW = "allow"
BLOCK = "block"
ESCALATE = "escalate"
HALT = "halt"
QUARANTINE = "quarantine"

# How much a decision stops the world (higher = more stopping). Used to aggregate.
_SEVERITY_ORDER = {ALLOW: 0, ESCALATE: 1, QUARANTINE: 2, HALT: 3, BLOCK: 4}

# Map a config outcome keyword to a decision.
_OUTCOME_TO_DECISION = {
    "block": BLOCK,
    "escalate": ESCALATE,
    "circuit_breaker": HALT,
    "degrade": ESCALATE,
    "allow": ALLOW,
}


def worst(decisions: list[str]) -> str:
    return max(decisions, key=lambda d: _SEVERITY_ORDER.get(d, 4), default=ALLOW)


@dataclass(frozen=True)
class GateSpec:
    """A gate's enforcement configuration, resolved from gate-config.yaml + defaults."""

    name: str
    intent_ref: str
    severity: str
    build_time: str = "block"
    run_time: str = "block"
    silence: dict = field(default_factory=dict)
    extra: dict = field(default_factory=dict)

    def outcome_for(self, phase: str) -> str:
        keyword = self.build_time if phase == "build" else self.run_time
        return _OUTCOME_TO_DECISION.get(keyword, BLOCK)


@dataclass(frozen=True)
class GateResult:
    gate: str
    decision: str
    severity: str
    intent_ref: str
    reason: str
    findings: tuple[str, ...] = ()
    subject: dict = field(default_factory=dict)

    @property
    def compliant(self) -> bool:
        return self.decision == ALLOW


class Gate(ABC):
    """Base class for a single-principle gate.

    Subclasses implement :meth:`check`, returning ``(compliant, findings, subject)``.
    They never decide *what happens* on failure — that is the spec's job — so the same
    gate logic works at build-time and run-time.
    """

    #: stable id, must match a key in gate-config.yaml
    name: str = "gate"

    #: True if the gate inspects source directly (works on a raw diff, no declared metadata).
    scans_code: bool = False

    @abstractmethod
    def check(self, change, spec: GateSpec) -> tuple[bool, list[str], dict]:
        """Return (compliant, findings, subject-extra). Raise to fail closed."""
        raise NotImplementedError

    def evaluate(self, change, spec: GateSpec, phase: str = "build") -> GateResult:
        try:
            compliant, findings, subject = self.check(change, spec)
        except Exception as exc:  # noqa: BLE001 — fail-closed is the whole point
            return GateResult(
                gate=self.name,
                decision=BLOCK,
                severity=spec.severity,
                intent_ref=spec.intent_ref,
                reason=f"gate raised, failing closed: {exc}",
                findings=(f"{type(exc).__name__}: {exc}",),
                subject={"change": getattr(change, "id", "?")},
            )
        if compliant:
            return GateResult(
                gate=self.name,
                decision=ALLOW,
                severity=spec.severity,
                intent_ref=spec.intent_ref,
                reason="compliant",
                findings=tuple(findings),
                subject=subject,
            )
        return GateResult(
            gate=self.name,
            decision=spec.outcome_for(phase),
            severity=spec.severity,
            intent_ref=spec.intent_ref,
            reason="cannot prove compliance (fail-closed)",
            findings=tuple(findings),
            subject=subject,
        )
