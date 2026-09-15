"""EU AI Act gate + shared classification. Fail-closed by *defaulting to high-risk until
assessed*. Everything here is expressed by **article reference and generic obligation
category** — never by sector-named example; the risk categories live in the Act's annexes
by reference, so faithful reproduction stays out of the code.

Tiers: prohibited (Art 5) · high (Art 9-15) · limited (Art 50 transparency) · minimal.
"""

from __future__ import annotations

from compliance_spine.gates.base import Gate, GateSpec

VALID_TIERS = {"prohibited", "high", "limited", "minimal"}

# High-risk obligations, by article and generic category (Art 9-15).
HIGH_RISK_OBLIGATIONS = (
    ("Art 9", "risk management system"),
    ("Art 10", "data and data governance"),
    ("Art 11", "technical documentation"),
    ("Art 12", "record-keeping and logging"),
    ("Art 13", "transparency and information to deployers"),
    ("Art 14", "human oversight"),
    ("Art 15", "accuracy, robustness and cybersecurity"),
)


def classify_tier(metadata: dict | None, default_caution: str = "high_risk") -> str | None:
    """Return the risk tier for a change, or None when it declares no AI feature.

    An unrecognised declared tier returns ``"invalid"``; an *absent* tier defaults to
    high-risk (fail-closed) unless configured otherwise.
    """
    meta = metadata or {}
    if not meta.get("ai_feature"):
        return None
    tier = meta.get("ai_risk_tier")
    if tier in VALID_TIERS:
        return tier
    if tier:
        return "invalid"
    return "high" if default_caution == "high_risk" else "minimal"


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
        tier = classify_tier(m, default_caution)
        findings: list[str] = []

        if tier == "prohibited":
            findings.append(f"AI feature '{feature}' is a prohibited practice (Art 5)")
        elif tier == "invalid":
            findings.append(
                f"AI feature '{feature}' has an unrecognised risk tier "
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
