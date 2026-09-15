"""ZAVA native runner: the seed dataset must prove the gate works (no DeepEval needed)."""

from compliance_spine.zava import load_cases, run
from compliance_spine.zava.metrics import Confusion


def test_seed_dataset_passes_thresholds():
    report = run()
    assert report.passed, report.summary()
    assert report.recall == 1.0
    assert report.fpr == 0.0


def test_dataset_has_both_labels():
    labels = {c.expected for c in load_cases()}
    assert labels == {"block", "allow"}


def test_confusion_math():
    c = Confusion()
    c.add("block", "block")  # tp
    c.add("block", "allow")  # fn
    c.add("allow", "block")  # fp
    c.add("allow", "allow")  # tn
    assert c.recall == 0.5
    assert c.false_positive_rate == 0.5
    assert c.accuracy == 0.5
