"""Execution agents: guidance, test recommendations, review verdicts, AI-Act baseline."""

from compliance_spine.agents import (
    AiActBaselineAgent,
    CodingAdvisorAgent,
    QualityReviewerAgent,
    TestAuthorAgent,
)
from compliance_spine.change import Change, ChangeFile
from compliance_spine.evidence.ledger import Ledger


def _c(meta, content="process()") -> Change:
    return Change(id="c", files=[ChangeFile("a.py", content)], metadata=meta)


def test_coding_advisor_flags_and_guides():
    result = CodingAdvisorAgent().run(_c({"data_category": "none"}, "logger.info(f'{user.email}')"))
    assert not result.ok
    assert any("no-pii-in-logs" in item for item in result.items)


def test_coding_advisor_clean_is_ok():
    assert CodingAdvisorAgent().run(_c({"data_category": "none"}, "logger.info('ok')")).ok


def test_test_author_selects_applicable_gates():
    personal = TestAuthorAgent().run(_c({"data_category": "personal"}))
    assert "lawful-basis-required" in personal.detail["gates"]
    ai = TestAuthorAgent().run(_c({"ai_feature": "scoring"}))
    assert "ai-act-risk-tier" in ai.detail["gates"]
    none = TestAuthorAgent().run(_c({"data_category": "none"}))
    assert none.detail["gates"] == ["encryption-required", "no-pii-in-logs"]


def test_quality_reviewer_refuses_never_delegate(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    result = QualityReviewerAgent().run(_c({"automated_decision": True}), ledger=led)
    assert not result.ok
    assert "human sign-off" in result.verdict
    assert result.detail["decision"] == "escalate"
    assert led.verify().count == 1


def test_quality_reviewer_approves_clean(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    result = QualityReviewerAgent().run(_c({"data_category": "none"}), ledger=led)
    assert result.ok
    assert "approve" in result.verdict


def test_ai_act_baseline_unassessed_is_high(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    result = AiActBaselineAgent().run(_c({"ai_feature": "scoring"}), ledger=led)
    assert not result.ok
    assert result.detail["tier"] == "high"


def test_ai_act_baseline_complete(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    meta = {
        "ai_feature": "scoring",
        "ai_risk_tier": "high",
        "ai_act_obligations": {f"Art {n}": True for n in (9, 10, 11, 12, 13, 15)},
        "human_oversight": True,
    }
    result = AiActBaselineAgent().run(_c(meta), ledger=led)
    assert result.ok
    assert "complete" in result.verdict


def test_ai_act_baseline_prohibited():
    result = AiActBaselineAgent().run(_c({"ai_feature": "x", "ai_risk_tier": "prohibited"}))
    assert not result.ok
    assert "PROHIBITED" in result.verdict


def test_ai_act_baseline_not_applicable():
    result = AiActBaselineAgent().run(_c({"data_category": "none"}))
    assert result.ok
    assert "not applicable" in result.verdict
