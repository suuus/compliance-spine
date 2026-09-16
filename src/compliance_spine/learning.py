"""The learning loop for probabilistic findings.

An assessor (LLM) finding is advisory — recorded with a confidence, but no *decision* yet.
:func:`adjudicate` records the **human's** decision on a finding (confirmed / dismissed),
even when no deterministic gate caught it, so the finding gains a named owner and a label.
:func:`learning_report` then turns those labels into signal: confirmed findings are candidates
to encode as a new gate + ZAVA case (recall you keep forever); dismissed ones are assessor
false positives to tune.
"""

from __future__ import annotations

from dataclasses import dataclass

from compliance_spine import __version__ as SPINE_VERSION
from compliance_spine.evidence.ledger import Ledger
from compliance_spine.evidence.record import DecisionRecord

_OUTCOMES = {"confirmed", "dismissed"}


def _by_id(records: list[dict], rid: str) -> dict | None:
    return next((r for r in records if r.get("id") == rid), None)


def adjudicate(
    finding_id: str,
    outcome: str,
    human_id: str,
    signature: str,
    reason: str | None = None,
    ledger: Ledger | None = None,
) -> dict:
    """Record a human's decision on an assessor finding. ``outcome`` is confirmed|dismissed."""
    if outcome not in _OUTCOMES:
        raise ValueError(f"outcome must be one of {sorted(_OUTCOMES)}")
    ledger = ledger if ledger is not None else Ledger()
    finding = _by_id(ledger.read_all(), finding_id)
    if finding is None:
        raise KeyError(f"no evidence record '{finding_id}'")

    subject = finding.get("subject", {}) or {}
    record = DecisionRecord(
        action="block" if outcome == "confirmed" else "allow",
        rule_id="human/adjudication",
        intent_ref="advisory/llm-review",
        severity="high" if outcome == "confirmed" else "info",
        inputs_hash=finding.get("inputs_hash", "0" * 64),
        actor={"type": "human", "id": human_id},
        owner={"human_id": human_id, "signature": signature},
        subject={
            "change": subject.get("change", "?"),
            "adjudicates": finding_id,
            "outcome": outcome,
            "kind": subject.get("kind", ""),
            "reason": reason or "",
        },
        spine_version=SPINE_VERSION,
    )
    return ledger.append(record)


@dataclass
class LearningReport:
    confirmed: list[dict]
    dismissed: list[dict]
    pending: list[dict]

    def render(self) -> str:
        lines = [
            "Learning from probabilistic findings",
            f"  confirmed (candidates for a new gate + ZAVA case): {len(self.confirmed)}",
            f"  dismissed (assessor false positives to tune):      {len(self.dismissed)}",
            f"  pending human review:                              {len(self.pending)}",
        ]
        for f in self.confirmed:
            s = f.get("subject", {})
            conf = f.get("confidence", "?")
            lines.append(f"    + encode: {s.get('kind', '?')} (conf {conf}) — {s.get('note', '')}")
        return "\n".join(lines)


def learning_report(ledger: Ledger | None = None) -> LearningReport:
    records = (ledger if ledger is not None else Ledger()).read_all()
    findings = [r for r in records if str(r.get("rule_id", "")).startswith("llm/")]
    verdict = {
        (r.get("subject") or {}).get("adjudicates"): (r.get("subject") or {}).get("outcome")
        for r in records
        if (r.get("subject") or {}).get("adjudicates")
    }
    confirmed, dismissed, pending = [], [], []
    for f in findings:
        outcome = verdict.get(f.get("id"))
        if outcome == "confirmed":
            confirmed.append(f)
        elif outcome == "dismissed":
            dismissed.append(f)
        else:
            pending.append(f)
    return LearningReport(confirmed, dismissed, pending)
