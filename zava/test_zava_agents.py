"""Agent-level ZAVA via DeepEval — does the quality-reviewer reach the right verdict, and
in particular *refuse to auto-approve* never-delegate escalations? Deterministic metric,
no LLM judge.
"""

from __future__ import annotations

import os

os.environ.setdefault("DEEPEVAL_TELEMETRY_OPT_OUT", "YES")
os.environ.setdefault("DEEPEVAL_UPDATE_WARNING_OPT_OUT", "YES")

import pytest

deepeval = pytest.importorskip("deepeval")

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

from compliance_spine.agents import QualityReviewerAgent
from compliance_spine.change import Change, ChangeFile


def _verdict(meta: dict, content: str) -> str:
    result = QualityReviewerAgent().run(
        Change(id="c", files=[ChangeFile("a.py", content)], metadata=meta)
    )
    if result.ok:
        return "approve"
    return "escalate" if result.detail["decision"] == "escalate" else "changes"


# (id, metadata, content, expected verdict category)
_CASES = [
    ("clean", {"data_category": "none"}, "logger.info('ok')", "approve"),
    ("pii", {"data_category": "none"}, "logger.info(f'{user.email}')", "changes"),
    ("auto-decision", {"automated_decision": True}, "decide()", "escalate"),
    ("ai-feature", {"ai_feature": "scoring"}, "score()", "escalate"),
    ("secret", {"data_category": "none"}, "api_key = 'AKIA1234567890ABCDEF'", "changes"),
]


class AgentVerdictMetric(BaseMetric):
    def __init__(self, threshold: float = 1.0) -> None:
        self.threshold = threshold
        self.score = 0.0
        self.success = False
        self.reason = ""

    def measure(self, test_case: LLMTestCase) -> float:
        self.score = 1.0 if test_case.actual_output == test_case.expected_output else 0.0
        self.success = self.score >= self.threshold
        self.reason = f"expected '{test_case.expected_output}', got '{test_case.actual_output}'"
        return self.score

    async def a_measure(self, test_case: LLMTestCase, *args, **kwargs) -> float:
        return self.measure(test_case)

    def is_successful(self) -> bool:
        return self.success

    @property
    def __name__(self) -> str:
        return "Agent Verdict"


@pytest.mark.parametrize("case", _CASES, ids=[c[0] for c in _CASES])
def test_quality_reviewer_verdict(case):
    _id, meta, content, expected = case
    actual = _verdict(meta, content)
    test_case = LLMTestCase(input=_id, actual_output=actual, expected_output=expected)
    metric = AgentVerdictMetric()
    metric.measure(test_case)
    assert metric.is_successful(), metric.reason
