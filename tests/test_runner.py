"""Enforcement runner: fail-closed verdicts, evidence emission, override downgrade."""

from compliance_spine import human
from compliance_spine.change import Change, ChangeFile
from compliance_spine.evidence.ledger import Ledger
from compliance_spine.gates.runner import enforce
from compliance_spine.overrides import OverrideStore


def _violation() -> Change:
    return Change(
        id="pr-v",
        files=[ChangeFile("a.py", "logger.info(f'{user.email}')")],
        metadata={"data_category": "personal"},
    )


def _clean() -> Change:
    return Change(id="pr-c", files=[ChangeFile("a.py", "logger.info('ok')")])


def test_violation_blocks_and_emits(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    result = enforce(_violation(), ledger=led)
    assert result.decision == "block"
    assert not result.allowed
    assert led.verify().count >= 1


def test_clean_change_allowed(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    assert enforce(_clean(), ledger=led).allowed


def test_override_downgrades_block(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    store = OverrideStore(tmp_path / "ov.json")
    human.request_override(
        _violation(), "no-pii-in-logs", "incident hotfix",
        signers={"spine_author": "su", "dpo": "jane"}, signature="sig",
        ledger=led, store=store,
    )
    # isolate to the silenced gate: a personal-data change also trips basis/retention/encryption
    result = enforce(_violation(), ledger=led, overrides=store, only={"no-pii-in-logs"})
    assert result.allowed
    assert result.overrides_applied == ["no-pii-in-logs"]


def test_all_gates_now_enforced(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    result = enforce(_clean(), ledger=led)
    assert result.unenforced == []  # every configured gate is implemented
