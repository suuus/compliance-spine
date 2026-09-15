"""Human-in-the-loop gate: the two places a *person* enters an Evidence decision.

- :func:`approve` resolves an escalation — a human takes ownership of an ``allow``.
- :func:`request_override` silences a blocking gate for a bounded window, enforcing the
  signer roles the gate's silence policy requires (e.g. spine_author + dpo for critical).
"""

from __future__ import annotations

from datetime import timedelta

from compliance_spine import __version__ as SPINE_VERSION
from compliance_spine.change import Change
from compliance_spine.evidence.ledger import Ledger
from compliance_spine.evidence.record import DecisionRecord
from compliance_spine.gates.registry import load_config, resolve_specs
from compliance_spine.overrides import Override, OverrideStore, _now


class PolicyError(PermissionError):
    """Raised when a human action violates the gate's silence / approval policy."""


def _spec(gate_name: str, config: dict | None):
    specs = resolve_specs(config if config is not None else load_config())
    if gate_name not in specs:
        raise KeyError(f"unknown gate '{gate_name}'")
    return specs[gate_name]


def approve(
    change: Change,
    gate_name: str,
    human_id: str,
    signature: str,
    config: dict | None = None,
    ledger: Ledger | None = None,
) -> dict:
    """A named human takes ownership of an escalated decision (records an ``allow``)."""
    spec = _spec(gate_name, config)
    ledger = ledger if ledger is not None else Ledger()
    record = DecisionRecord(
        action="allow",
        rule_id=f"spine/policies/{gate_name}",
        intent_ref=spec.intent_ref,
        severity=spec.severity,
        inputs_hash=change.payload_hash(),
        actor={"type": "human", "id": human_id},
        subject={"change": change.id, "data_category": change.data_category},
        owner={"human_id": human_id, "signature": signature},
        spine_version=SPINE_VERSION,
    )
    return ledger.append(record)


def request_override(
    change: Change,
    gate_name: str,
    reason: str,
    signers: dict[str, str],
    signature: str,
    days: int | None = None,
    compensating_control: str | None = None,
    config: dict | None = None,
    ledger: Ledger | None = None,
    store: OverrideStore | None = None,
) -> dict:
    """Silence a blocking gate for a bounded window. Enforces required signer roles."""
    spec = _spec(gate_name, config)
    silence = spec.silence or {}
    if not silence.get("allowed", True):
        raise PolicyError(f"gate '{gate_name}' cannot be silenced")

    required = set(silence.get("requires") or ["spine_author"])
    missing = required - set(signers)
    if missing:
        raise PolicyError(
            f"override for '{gate_name}' requires signer role(s): {', '.join(sorted(missing))}"
        )

    max_days = int(silence.get("max_days", 30))
    window = min(int(days) if days else max_days, max_days)
    expires = (_now() + timedelta(days=window)).isoformat()
    signed_by = [f"{role}:{signers[role]}" for role in sorted(signers)]
    human_id = signers.get("spine_author") or sorted(signers.values())[0]

    override = Override(
        gate=gate_name,
        reason=reason,
        expires=expires,
        signed_by=signed_by,
        human_id=human_id,
        signature=signature,
        compensating_control=compensating_control,
    )
    (store if store is not None else OverrideStore()).add(override)

    ledger = ledger if ledger is not None else Ledger()
    record = DecisionRecord(
        action="override",
        rule_id=f"spine/policies/{gate_name}",
        intent_ref=spec.intent_ref,
        severity=spec.severity,
        inputs_hash=change.payload_hash(),
        actor={"type": "human", "id": human_id},
        subject={"change": change.id, "data_category": change.data_category},
        owner=override.owner,
        override=override.to_evidence(),
        spine_version=SPINE_VERSION,
    )
    return ledger.append(record)
