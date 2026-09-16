"""LLM proposals: advisory-only, non-binding, and still checked by the deterministic gates."""

from compliance_spine.change import Change, ChangeFile
from compliance_spine.evidence.detector import detect_ghosts
from compliance_spine.evidence.ledger import Ledger
from compliance_spine.proposals import propose, record_proposal


def _change(**proposed) -> Change:
    return Change(id="pr", files=[ChangeFile("a.py", "db.store(x)")], proposed_metadata=proposed)


def test_proposal_is_advisory_emit_by_llm(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    rec = record_proposal(_change(data_category="personal"), led, model_ref="copilot/gpt")
    assert rec["action"] == "emit"
    assert rec["actor"] == {"type": "llm", "id": "copilot/gpt"}
    assert led.verify().ok


def test_proposal_is_not_a_ghost(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    record_proposal(_change(data_category="personal"), led)
    assert detect_ghosts(led.read_all()) == []  # an advisory emit needs no human owner


def test_preview_runs_gates_on_proposed_metadata(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    incomplete = propose(_change(data_category="personal", lawful_basis="contract"), ledger=led)
    assert not incomplete.would_allow  # retention missing -> gates would block

    complete = propose(
        _change(
            data_category="personal",
            lawful_basis="contract",
            retention_days=90,
            encryption={"at_rest": True, "in_transit": True},
        ),
        ledger=led,
    )
    assert complete.would_allow


def test_preview_writes_no_binding_evidence(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    propose(_change(data_category="personal"), ledger=led)
    # only the advisory proposal is recorded; no gate allow/block decisions leak into the ledger
    assert [r["action"] for r in led.read_all()] == ["emit"]
