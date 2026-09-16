"""A reasoned (non-deterministic) finding must become its own adjudicable ledger event —
so an agent's finding gets a real evt_* id, not just a report label.
"""

from compliance_spine.evidence.ledger import Ledger
from compliance_spine.learning import adjudicate, learning_report, record_finding


def test_record_finding_creates_an_adjudicable_event(tmp_path):
    led = Ledger(path=tmp_path / "ledger.jsonl")
    rec = record_finding(
        "automated-decision",
        "auto-declines with no human path (Art 22)",
        change="assess-1",
        file="risk/service.js",
        line=116,
        confidence=0.8,
        severity="high",
        model="reasoning-agent",
        ledger=led,
    )
    assert rec["id"].startswith("evt_")
    assert rec["rule_id"] == "llm/automated-decision"
    assert rec["confidence"] == 0.8
    assert rec["findings"][0] == {
        "file": "risk/service.js",
        "line": 116,
        "message": "auto-declines with no human path (Art 22)",
    }
    assert rec["actor"] == {"type": "llm", "id": "reasoning-agent"}


def test_recorded_finding_is_adjudicable_and_shows_in_learn(tmp_path):
    led = Ledger(path=tmp_path / "ledger.jsonl")
    rec = record_finding("pii-in-response", "returns raw PII", change="c", ledger=led)

    adjudicate(rec["id"], "confirmed", human_id="dpo", signature="s", ledger=led)
    report = learning_report(ledger=led)
    assert len(report.confirmed) == 1


def test_record_finding_without_location_is_valid(tmp_path):
    led = Ledger(path=tmp_path / "ledger.jsonl")
    rec = record_finding("purpose-creep", "reused analytics data", change="c", ledger=led)
    assert rec["findings"][0]["file"] is None
    assert rec["findings"][0]["line"] is None
