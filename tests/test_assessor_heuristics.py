"""HeuristicAssessor (LLM-ceiling stand-in) — long-tail heuristics surfaced by the demo app."""

from compliance_spine.change import Change
from compliance_spine.llm.reviewer import HeuristicAssessor


def _kinds(content: str) -> set[str]:
    change = Change.from_dict(
        {"id": "c", "files": [{"path": "x.py", "content": content}], "metadata": {}}
    )
    return {f.kind for f in HeuristicAssessor().assess(change)}


def test_pii_in_response_projection_flagged():
    kinds = _kinds('return {"medical_notes": claim.medical_notes}')
    assert "pii-in-response" in kinds


def test_automated_decision_flagged():
    assert "automated-decision" in _kinds('decision = "declined" if score < 540 else "approved"')


def test_egress_still_flagged():
    assert "undeclared-transfer" in _kinds('requests.post(URL, json={"email": customer.email})')


def test_clean_record_return_not_flagged():
    # returning non-personal record fields (id, status) must not be flagged
    assert _kinds('return {"id": claim.id, "status": claim.status}') == set()
