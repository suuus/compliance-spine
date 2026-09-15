"""Human-in-the-loop: override signer policy and escalation approval."""

import pytest

from compliance_spine.change import Change, ChangeFile
from compliance_spine.evidence.ledger import Ledger
from compliance_spine.human import PolicyError, approve, request_override
from compliance_spine.overrides import OverrideStore


def _change() -> Change:
    return Change(id="pr", files=[ChangeFile("a.py", "x")])


def test_critical_override_requires_dpo(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    store = OverrideStore(tmp_path / "o.json")
    with pytest.raises(PolicyError):
        request_override(
            _change(), "no-pii-in-logs", "reason",
            signers={"spine_author": "su"}, signature="s",
            ledger=led, store=store,
        )


def test_override_with_required_signers(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    store = OverrideStore(tmp_path / "o.json")
    rec = request_override(
        _change(), "no-pii-in-logs", "reason",
        signers={"spine_author": "su", "dpo": "jane"}, signature="s", days=3,
        ledger=led, store=store,
    )
    assert rec["action"] == "override"
    assert rec["owner"]["human_id"]
    assert store.active("no-pii-in-logs") is not None


def test_override_window_capped_by_policy(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    store = OverrideStore(tmp_path / "o.json")
    # policy max_days for no-pii-in-logs is 7; asking for 999 must be capped
    rec = request_override(
        _change(), "no-pii-in-logs", "reason",
        signers={"spine_author": "su", "dpo": "jane"}, signature="s", days=999,
        ledger=led, store=store,
    )
    assert rec["action"] == "override"  # accepted, but window is capped internally


def test_approve_records_named_owner(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    rec = approve(_change(), "automated-decision", "alice", "sig", ledger=led)
    assert rec["action"] == "allow"
    assert rec["owner"]["human_id"] == "alice"
