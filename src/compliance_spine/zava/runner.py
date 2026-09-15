"""ZAVA native runner — run labelled cases through the real gate pipeline and score them.

This runner needs no third-party dependency, so it always works in CI. The DeepEval
integration in ``zava/test_zava.py`` wraps the very same :func:`predict` function, so the
chosen runner and the native one can never disagree.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from compliance_spine.change import Change
from compliance_spine.gates.runner import enforce
from compliance_spine.zava.dataset import ZavaCase, load_cases
from compliance_spine.zava.metrics import Confusion

DEFAULT_THRESHOLDS = {"recall_min": 1.0, "fpr_max": 0.0}


def predict(change: Change, config: dict | None = None) -> str:
    """Run the fail-closed pipeline (no evidence writes) and return 'allow' or 'block'."""
    result = enforce(change, emit_evidence=False, config=config)
    return "allow" if result.allowed else "block"


@dataclass
class CaseResult:
    id: str
    expected: str
    predicted: str
    passed: bool
    tags: list[str] = field(default_factory=list)


@dataclass
class ZavaReport:
    results: list[CaseResult]
    confusion: Confusion
    thresholds: dict

    @property
    def recall(self) -> float:
        return self.confusion.recall

    @property
    def fpr(self) -> float:
        return self.confusion.false_positive_rate

    @property
    def passed(self) -> bool:
        return (
            self.recall >= self.thresholds["recall_min"]
            and self.fpr <= self.thresholds["fpr_max"]
        )

    @property
    def failures(self) -> list[CaseResult]:
        return [r for r in self.results if not r.passed]

    def summary(self) -> str:
        verdict = "PASS" if self.passed else "FAIL"
        head = (
            f"ZAVA [{verdict}] n={len(self.results)} "
            f"recall={self.recall:.2f} (min {self.thresholds['recall_min']:.2f}) "
            f"fpr={self.fpr:.2f} (max {self.thresholds['fpr_max']:.2f}) "
            f"acc={self.confusion.accuracy:.2f}"
        )
        lines = [head]
        for r in self.failures:
            tags = ",".join(r.tags)
            lines.append(f"  MISS {r.id}: expected {r.expected}, got {r.predicted} [{tags}]")
        return "\n".join(lines)


def run(
    cases: list[ZavaCase] | None = None,
    config: dict | None = None,
    thresholds: dict | None = None,
) -> ZavaReport:
    cases = cases if cases is not None else load_cases()
    thresholds = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    confusion = Confusion()
    results: list[CaseResult] = []
    for case in cases:
        predicted = predict(case.change, config=config)
        confusion.add(case.expected, predicted)
        results.append(
            CaseResult(case.id, case.expected, predicted, predicted == case.expected, case.tags)
        )
    return ZavaReport(results, confusion, thresholds)
