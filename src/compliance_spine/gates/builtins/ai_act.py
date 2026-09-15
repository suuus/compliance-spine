"""EU AI Act gate: classify an AI feature's risk tier and require the obligations that tier
carries. Fail-closed by *defaulting to high-risk until assessed* (Art references only —
never sector-named examples; the risk categories live in the Act's annexes by reference).

Tiers: prohibited (Art 5) · high (Art 9-15) · limited (Art 50 transparency) · minimal.
"""

from __future__ import annotations

from compliance_spine.gates.base import Gate, GateSpec

VALID_TIERS = {"prohibited", "high", "limited", "minimal"}


class AiActRiskTierGate(Gate):
    name = "ai-act-risk-tier"

    def check(self, change, spec: GateSpec) -> tuple[bool, list[str], dict]:
        m = change.metadata or {}
        feature = m.get("ai_feature")
        subject = {
            "change": change.id,
            "data_category": change.data_category,
            "ai_feature": feature,
        }
        if not feature:
            return True, [], subject

        default_caution = (spec.extra or {}).get("default_caution", "high_risk")
        tier = m.get("ai_risk_tier") or ("high" if default_caution == "high_risk" else "minimal")
        findings: list[str] = []

        if tier == "prohibited":
            findings.append(f"AI feature '{feature}' is a prohibited practice (Art 5)")
        elif tier not in VALID_TIERS:
            findings.append(
                f"AI feature '{feature}' has an unrecognised risk tier '{tier}' "
                "(defaulting to high-risk until assessed)"
            )
        elif tier == "high":
            if not m.get("ai_act_baseline"):
                findings.append(
                    f"high-risk AI feature '{feature}' without declared baseline "
                    "obligations (Art 9-15)"
                )
            if not m.get("human_oversight"):
                findings.append(
                    f"high-risk AI feature '{feature}' without human oversight (Art 14)"
                )
        elif tier == "limited":
            if not m.get("transparency"):
                findings.append(
                    f"limited-risk AI feature '{feature}' without transparency disclosure (Art 50)"
                )
        return (not findings, findings, subject)
