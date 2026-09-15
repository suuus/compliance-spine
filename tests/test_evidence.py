"""Evidence: schema validation, hash-chain integrity, and tamper detection."""

import pytest
from jsonschema import ValidationError

from compliance_spine.evidence.ledger import Ledger
from compliance_spine.evidence.record import DecisionRecord


def _rec(**kw) -> DecisionRecord:
    base = dict(
        action="block",
        rule_id="spine/policies/no-pii-in-logs",
        intent_ref="intent/never-delegate#no-pii-in-logs",
        severity="critical",
        inputs_hash="a" * 64,
        actor={"type": "gate", "id": "no-pii-in-logs"},
        subject={"change": "pr-1"},
    )
    base.update(kw)
    return DecisionRecord(**base)


def test_valid_record_passes_schema():
    _rec().validate()  # must not raise


def test_override_requires_owner():
    # schema allOf: action == override implies owner + override present
    bad = _rec(action="override", override={"reason": "r", "expires": "2030-01-01T00:00:00+00:00",
                                            "signed_by": ["dpo:jane"]})
    with pytest.raises(ValidationError):
        bad.validate()


def test_append_and_verify(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    led.append(_rec(subject={"change": "pr-1"}))
    led.append(_rec(subject={"change": "pr-2"}))
    result = led.verify()
    assert result.ok and result.count == 2


def test_tamper_is_detected(tmp_path):
    path = tmp_path / "l.jsonl"
    led = Ledger(path)
    led.append(_rec(subject={"change": "pr-1"}))
    led.append(_rec(subject={"change": "pr-2"}))
    # tamper with the first line's content
    lines = path.read_text().splitlines()
    lines[0] = lines[0].replace("pr-1", "pr-X")
    path.write_text("\n".join(lines) + "\n")
    result = led.verify()
    assert not result.ok and result.errors


def test_chain_links_prev_hash(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    first = led.append(_rec())
    second = led.append(_rec())
    assert first["prev_hash"] == "0" * 64
    assert second["prev_hash"] != "0" * 64
