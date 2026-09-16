"""ZAVA (via DeepEval) on the assessor — the LLM/ceiling layer's own efficacy, deterministic
metric, no LLM judge. Run against any assessor; the shipped stand-in must catch the long-tail
violations it's responsible for without crying wolf on clean changes.
"""

from __future__ import annotations

import os

os.environ.setdefault("DEEPEVAL_TELEMETRY_OPT_OUT", "YES")
os.environ.setdefault("DEEPEVAL_UPDATE_WARNING_OPT_OUT", "YES")

import pytest

deepeval = pytest.importorskip("deepeval")

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

from compliance_spine.llm import HeuristicAssessor
from compliance_spine.llm.assessor_eval import assessor_cases, assessor_predict


class AssessorEfficacyMetric(BaseMetric):
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
        return "Assessor Efficacy"


_CASES = assessor_cases()


@pytest.mark.parametrize("case", _CASES, ids=[c[0] for c in _CASES])
def test_assessor_efficacy(case):
    _id, expected, change, _tags = case
    predicted = assessor_predict(HeuristicAssessor(), change)
    test_case = LLMTestCase(input=_id, actual_output=predicted, expected_output=expected)
    metric = AssessorEfficacyMetric()
    metric.measure(test_case)
    assert metric.is_successful(), metric.reason
