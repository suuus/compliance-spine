"""ZAVA via DeepEval — the chosen eval runner.

Each labelled case becomes a DeepEval ``LLMTestCase`` whose ``actual_output`` is the gate's
verdict. ``ZavaGateEfficacyMetric`` scores it deterministically (no LLM judge), so the suite
is fast, offline, and reproducible while still running through DeepEval's assertion machinery.
It wraps the same :func:`compliance_spine.zava.predict` as the native runner, so the two
can never disagree.
"""

from __future__ import annotations

import os

os.environ.setdefault("DEEPEVAL_TELEMETRY_OPT_OUT", "YES")
os.environ.setdefault("DEEPEVAL_UPDATE_WARNING_OPT_OUT", "YES")

import pytest

deepeval = pytest.importorskip("deepeval")

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

from compliance_spine.zava import load_cases, predict_case


class ZavaGateEfficacyMetric(BaseMetric):
    """Passes when the gate's verdict matches the case's expected label."""

    def __init__(self, threshold: float = 1.0) -> None:
        self.threshold = threshold
        self.score = 0.0
        self.success = False
        self.reason = ""

    def measure(self, test_case: LLMTestCase) -> float:
        self.score = 1.0 if test_case.actual_output == test_case.expected_output else 0.0
        self.success = self.score >= self.threshold
        self.reason = (
            f"expected '{test_case.expected_output}', gate produced '{test_case.actual_output}'"
        )
        return self.score

    async def a_measure(self, test_case: LLMTestCase, *args, **kwargs) -> float:
        return self.measure(test_case)

    def is_successful(self) -> bool:
        return self.success

    @property
    def __name__(self) -> str:
        return "ZAVA Gate Efficacy"


_CASES = load_cases()


@pytest.mark.parametrize("case", _CASES, ids=[c.id for c in _CASES])
def test_zava_gate_efficacy(case):
    predicted = predict_case(case)
    test_case = LLMTestCase(
        input=case.id, actual_output=predicted, expected_output=case.expected
    )
    metric = ZavaGateEfficacyMetric()
    metric.measure(test_case)
    assert metric.is_successful(), metric.reason
