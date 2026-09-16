"""Evidence records must be traceable to their source: every finding that produced a decision
is captured as {file, line, message}, so an auditor can see *where* it came from.
"""

from compliance_spine.change import Change
from compliance_spine.evidence.ledger import Ledger
from compliance_spine.evidence.record import (
    DecisionRecord,
    finding_at,
    structure_findings,
)
from compliance_spine.gates.registry import code_scanning_gate_names
from compliance_spine.gates.runner import enforce


def test_structure_findings_parses_path_line_message():
    out = structure_findings(
        ["src/a.py:12: logs personal-data attribute 'email'", "no location on this one"]
    )
    assert out[0] == {
        "file": "src/a.py",
        "line": 12,
        "message": "logs personal-data attribute 'email'",
    }
    assert out[1] == {"file": None, "line": None, "message": "no location on this one"}


def test_finding_at_parses_location():
    assert finding_at("x/y.ts:3", "returned in a response") == {
        "file": "x/y.ts",
        "line": 3,
        "message": "returned in a response",
    }
    assert finding_at("", "no location") == {"file": None, "line": None, "message": "no location"}


def test_record_with_findings_validates_against_schema():
    rec = DecisionRecord(
        action="block",
        rule_id="spine/policies/no-pii-in-logs",
        intent_ref="intent/never-delegate#no-pii-in-logs",
        severity="critical",
        inputs_hash="deadbeef",
        actor={"type": "gate", "id": "no-pii-in-logs"},
        findings=[{"file": "a.py", "line": 1, "message": "logs email"}],
    )
    data = rec.to_dict()
    assert data["findings"][0]["file"] == "a.py"
    rec.validate()  # must not raise — schema declares `findings`


def test_record_without_findings_omits_the_field():
    rec = DecisionRecord(
        action="allow",
        rule_id="spine/policies/x",
        intent_ref="i",
        severity="info",
        inputs_hash="h",
        actor={"type": "gate", "id": "x"},
    )
    assert "findings" not in rec.to_dict()


def test_enforce_records_findings_with_file_and_line(tmp_path):
    change = Change.from_dict(
        {
            "id": "pr-1",
            "files": [{"path": "svc/auth.py", "content": "logger.info(f'{user.email}')"}],
            "metadata": {"data_category": "personal"},
        }
    )
    led = Ledger(path=tmp_path / "ledger.jsonl")
    enforce(change, ledger=led, overrides=None, only=code_scanning_gate_names())

    blocks = [r for r in led.read_all() if r["action"] == "block"]
    assert blocks, "expected a fail-closed block"
    findings = blocks[0].get("findings")
    assert findings, "the blocking record must carry its findings"
    assert findings[0]["file"] == "svc/auth.py"
    assert isinstance(findings[0]["line"], int)
    assert "email" in findings[0]["message"] or "user" in findings[0]["message"]
