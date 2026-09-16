"""ZAVA on the assessor: its own recall / precision, gating its authority."""

from compliance_spine.llm import NullAssessor, evaluate
from compliance_spine.llm.assessor_eval import assessor_cases


def test_stand_in_assessor_meets_thresholds():
    report = evaluate()
    assert report.passed
    assert report.recall == 1.0
    assert report.fpr == 0.0


def test_null_assessor_fails_recall():
    report = evaluate(NullAssessor())
    assert not report.passed
    assert report.recall < 1.0  # catches nothing on the extended violations


def test_eval_runs_on_the_assessor_domain_only():
    cases = assessor_cases()
    assert all("covered" not in tags for (_id, _exp, _ch, tags) in cases)
    assert len(cases) >= 4
