"""Learning loop: confidence on findings, human adjudication, and the confirmed-candidate view."""

from compliance_spine.change import Change, ChangeFile
from compliance_spine.evidence.ledger import Ledger
from compliance_spine.learning import adjudicate, learning_report
from compliance_spine.llm import LayeredReviewer


def _pii_to_model_change() -> Change:
    return Change(
        id="pr-42",
        files=[ChangeFile("src/svc/s.py", "resp = model.complete(f'{patient.diagnosis}')")],
    )


def test_finding_records_confidence(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    LayeredReviewer().review(_pii_to_model_change(), ledger=led)
    finding = next(r for r in led.read_all() if r["rule_id"].startswith("llm/"))
    assert finding["confidence"] == 0.9
    assert finding["actor"]["type"] == "llm"


def test_adjudicate_records_human_decision(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    LayeredReviewer().review(_pii_to_model_change(), ledger=led)
    finding = next(r for r in led.read_all() if r["rule_id"].startswith("llm/"))
    rec = adjudicate(finding["id"], "confirmed", human_id="dpo", signature="s", ledger=led)
    assert rec["action"] == "block"
    assert rec["owner"]["human_id"] == "dpo"
    assert rec["subject"]["adjudicates"] == finding["id"]
    assert led.verify().ok


def test_learning_report_classifies(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    LayeredReviewer().review(_pii_to_model_change(), ledger=led)
    finding = next(r for r in led.read_all() if r["rule_id"].startswith("llm/"))

    assert len(learning_report(led).pending) == 1
    adjudicate(finding["id"], "confirmed", human_id="dpo", signature="s", ledger=led)
    report = learning_report(led)
    assert len(report.confirmed) == 1
    assert len(report.pending) == 0


def test_dismissed_is_a_false_positive(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    LayeredReviewer().review(_pii_to_model_change(), ledger=led)
    finding = next(r for r in led.read_all() if r["rule_id"].startswith("llm/"))
    adjudicate(finding["id"], "dismissed", human_id="dpo", signature="s", ledger=led)
    report = learning_report(led)
    assert len(report.dismissed) == 1
    assert len(report.confirmed) == 0
