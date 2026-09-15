"""Phase-2 GDPR + AI-Act gates: key behaviours beyond the ZAVA datasets."""

from compliance_spine.change import Change, ChangeFile
from compliance_spine.gates.base import ALLOW, BLOCK, ESCALATE, GateSpec
from compliance_spine.gates.builtins.ai_act import AiActRiskTierGate
from compliance_spine.gates.builtins.automated_decision import AutomatedDecisionGate
from compliance_spine.gates.builtins.gdpr import EncryptionRequiredGate, LawfulBasisGate
from compliance_spine.gates.builtins.pii_access_boundary import PiiAccessBoundaryGate


def _c(meta, content="process()") -> Change:
    return Change(id="c", files=[ChangeFile("a.py", content)], metadata=meta)


def test_lawful_basis_rejects_invalid_value():
    spec = GateSpec("lawful-basis-required", "i", "critical", build_time="block")
    change = _c({"data_category": "personal", "lawful_basis": "vibes"})
    assert LawfulBasisGate().evaluate(change, spec).decision == BLOCK


def test_encryption_placeholder_not_flagged():
    spec = GateSpec("encryption-required", "i", "high", build_time="block")
    change = _c({"data_category": "none"}, "password = 'changeme'")
    assert EncryptionRequiredGate().evaluate(change, spec).decision == ALLOW


def test_encryption_real_secret_blocks():
    spec = GateSpec("encryption-required", "i", "high", build_time="block")
    res = EncryptionRequiredGate().evaluate(
        _c({"data_category": "none"}, "token = 'ghp_abcdef123456'"), spec
    )
    assert res.decision == BLOCK


def test_automated_decision_escalates():
    spec = GateSpec("automated-decision", "i", "critical", build_time="escalate")
    res = AutomatedDecisionGate().evaluate(_c({"automated_decision": True}), spec)
    assert res.decision == ESCALATE


def test_ai_act_defaults_to_high_until_assessed():
    spec = GateSpec(
        "ai-act-risk-tier", "i", "critical", build_time="escalate",
        extra={"default_caution": "high_risk"},
    )
    # ai_feature present but no tier assessed -> treated as high-risk -> not compliant
    res = AiActRiskTierGate().evaluate(_c({"ai_feature": "scoring"}), spec)
    assert res.decision == ESCALATE


def test_pii_access_boundary_blocks_restricted_component():
    spec = GateSpec("pii-access-boundary", "i", "high", build_time="block")
    restricted = Change(id="c", files=[ChangeFile("src/analytics/report.py", "x = user.email")])
    assert PiiAccessBoundaryGate().evaluate(restricted, spec).decision == BLOCK


def test_pii_access_boundary_allows_unrestricted_component():
    spec = GateSpec("pii-access-boundary", "i", "high", build_time="block")
    ok = Change(id="c", files=[ChangeFile("src/core/service.py", "x = user.email")])
    assert PiiAccessBoundaryGate().evaluate(ok, spec).decision == ALLOW
