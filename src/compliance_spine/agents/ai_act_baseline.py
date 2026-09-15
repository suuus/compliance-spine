"""AI-Act-baseline agent — classifies an AI feature's risk tier and produces the baseline
obligation checklist that tier carries, by **article reference and generic category only**.
Fail-closed: an unassessed feature is treated as high-risk. Writes a conformance record to
Evidence when given a ledger.
"""

from __future__ import annotations

from compliance_spine.agents.base import Agent, AgentResult
from compliance_spine.change import Change
from compliance_spine.evidence.ledger import Ledger
from compliance_spine.gates.builtins.ai_act import HIGH_RISK_OBLIGATIONS, classify_tier
from compliance_spine.gates.runner import emit

# Resolves via alias to the ai-act-risk-tier principle.
_INTENT = "intent/never-delegate#ai-act"


def _declared_obligations(metadata: dict) -> set[str]:
    obligations = metadata.get("ai_act_obligations") or {}
    declared: set[str] = {art for art, ok in obligations.items() if ok}
    if metadata.get("human_oversight"):
        declared.add("Art 14")
    return declared


class AiActBaselineAgent(Agent):
    name = "ai-act-baseline"

    def run(
        self, change: Change, ledger: Ledger | None = None, default_caution: str = "high_risk"
    ) -> AgentResult:
        m = change.metadata or {}
        tier = classify_tier(m, default_caution)
        items: list[str] = []
        ok = True
        action = "emit"

        if tier is None:
            verdict = "no AI feature declared — EU AI Act baseline not applicable"
        elif tier == "prohibited":
            ok, action = False, "escalate"
            verdict = "PROHIBITED practice (Art 5) — must not ship"
            items = ["Art 5: prohibited practice — stop and escalate."]
        elif tier == "minimal":
            verdict = "minimal risk — no mandatory baseline (voluntary codes, Art 95)"
        elif tier == "limited":
            declared = bool(m.get("transparency"))
            ok = declared
            action = "emit" if declared else "escalate"
            items = [f"Art 50 transparency disclosure: {'declared' if declared else 'MISSING'}"]
            verdict = "limited risk — transparency baseline " + (
                "complete" if declared else "incomplete"
            )
        else:  # high (or invalid, treated as high under default caution)
            declared = _declared_obligations(m)
            for art, category in HIGH_RISK_OBLIGATIONS:
                items.append(f"{art} {category}: {'declared' if art in declared else 'MISSING'}")
            missing = [art for art, _ in HIGH_RISK_OBLIGATIONS if art not in declared]
            ok = not missing
            action = "emit" if ok else "escalate"
            label = "high-risk" if tier == "high" else "unassessed (treated as high-risk)"
            verdict = f"{label} — baseline " + (
                "complete" if ok else f"missing {len(missing)} obligation(s)"
            )

        detail = {"tier": tier, "action": action}
        if ledger is not None:
            record = emit(
                ledger, change,
                gate=self.name,
                intent_ref=_INTENT,
                severity="critical",
                action=action,
                actor={"type": "agent", "id": self.name},
            )
            detail["evidence_id"] = record["id"]

        return AgentResult(self.name, change.id, ok, verdict, items, detail)
