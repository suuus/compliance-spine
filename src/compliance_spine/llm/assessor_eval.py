"""ZAVA for the assessor — measure the LLM / ceiling layer's *own* recall and precision, with
thresholds, so you can gate how much authority it earns. This complements the scorecard (which
measures the union's recall lift) with a component-level eval of the assessor by itself.

The assessor's responsibility is the *long tail* — the violations the deterministic gates don't
cover — so its dataset is the scorecard's cases minus the ones already tagged ``covered``.
"""

from __future__ import annotations

from dataclasses import dataclass

from compliance_spine.llm.reviewer import Assessor, HeuristicAssessor
from compliance_spine.llm.scorecard import load_cases
from compliance_spine.zava.metrics import Confusion

DEFAULT_THRESHOLDS = {"recall_min": 1.0, "fpr_max": 0.0}


def assessor_predict(assessor: Assessor, change) -> str:
    """The assessor 'blocks' if it produces any finding for the change, else 'allow'."""
    return "block" if assessor.assess(change) else "allow"


def assessor_cases(cases=None):
    """The assessor's domain: scorecard cases the deterministic gates don't already cover."""
    source = cases if cases is not None else load_cases()
    return [(i, e, ch, t) for (i, e, ch, t) in source if "covered" not in t]


@dataclass
class AssessorReport:
    assessor: str
    n: int
    confusion: Confusion
    thresholds: dict

    @property
    def recall(self) -> float:
        return self.confusion.recall

    @property
    def fpr(self) -> float:
        return self.confusion.false_positive_rate

    @property
    def precision(self) -> float:
        return self.confusion.precision

    @property
    def passed(self) -> bool:
        return (
            self.recall >= self.thresholds["recall_min"]
            and self.fpr <= self.thresholds["fpr_max"]
        )

    def render(self) -> str:
        verdict = "PASS" if self.passed else "FAIL"
        return (
            f"ZAVA (assessor '{self.assessor}') [{verdict}] n={self.n} "
            f"recall={self.recall:.2f} (min {self.thresholds['recall_min']:.2f}) "
            f"fpr={self.fpr:.2f} (max {self.thresholds['fpr_max']:.2f}) "
            f"precision={self.precision:.2f}"
        )


def evaluate(assessor: Assessor | None = None, cases=None, thresholds=None) -> AssessorReport:
    assessor = assessor or HeuristicAssessor()
    cases = assessor_cases(cases)
    thresholds = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    confusion = Confusion()
    for _id, expected, change, _tags in cases:
        confusion.add(expected, assessor_predict(assessor, change))
    return AssessorReport(assessor.name, len(cases), confusion, thresholds)
