"""LLM metadata proposals — the "propose" half of *LLMs propose, gates dispose*.

A model (your Copilot model, or an optional headless one — see docs/LLM-LAYER.md) reads a
change and drafts its compliance context into ``change.proposed_metadata``. This module
records that draft as an **advisory** Evidence entry (``action: emit``, ``actor.type: llm``)
and previews what the deterministic gates *would* decide if a human confirmed it. Nothing here
is binding: a proposal never allows, blocks, or escalates anything. A human confirms by
promoting ``proposed_metadata`` to ``metadata`` and running ``check``/``review`` — that
decision is deterministic and human-owned.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from compliance_spine import __version__ as SPINE_VERSION
from compliance_spine.change import Change
from compliance_spine.evidence.ledger import Ledger
from compliance_spine.evidence.record import DecisionRecord
from compliance_spine.gates.runner import EnforcementResult, enforce


def record_proposal(change: Change, ledger: Ledger, model_ref: str = "copilot") -> dict:
    """Append an advisory record of an LLM's drafted metadata. Non-binding."""
    record = DecisionRecord(
        action="emit",
        rule_id="agents/metadata-proposal",
        intent_ref="advisory/llm-proposal",
        severity="info",
        inputs_hash=change.payload_hash(),
        actor={"type": "llm", "id": model_ref},
        subject={
            "change": change.id,
            "data_category": str((change.proposed_metadata or {}).get("data_category", "unknown")),
        },
        spine_version=SPINE_VERSION,
    )
    return ledger.append(record)


@dataclass
class ProposalPreview:
    proposal_id: str
    proposed_metadata: dict
    result: EnforcementResult  # what the gates WOULD say — a preview, not a decision

    @property
    def would_allow(self) -> bool:
        return self.result.allowed


def propose(
    change: Change, ledger: Ledger | None = None, model_ref: str = "copilot"
) -> ProposalPreview:
    """Record the LLM proposal, then preview the gates against the proposed metadata."""
    ledger = ledger if ledger is not None else Ledger()
    record = record_proposal(change, ledger, model_ref)
    # Preview only: run the gates as if the proposed metadata were confirmed. No binding
    # Evidence is written for this preview — the human's later `check` is the real decision.
    preview_change = replace(
        change, metadata={**(change.metadata or {}), **(change.proposed_metadata or {})}
    )
    result = enforce(preview_change, emit_evidence=False)
    return ProposalPreview(record["id"], dict(change.proposed_metadata or {}), result)
