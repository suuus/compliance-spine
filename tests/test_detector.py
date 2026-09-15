"""Ghost-decision detector: consequential decisions must carry a named human owner."""

from compliance_spine.evidence.detector import detect_ghosts, detect_undocumented


def test_override_without_owner_is_ghost():
    records = [{"id": "e1", "action": "override", "actor": {"type": "human", "id": "x"}}]
    assert detect_ghosts(records)


def test_gate_allow_without_owner_is_not_ghost():
    records = [{"id": "e2", "action": "allow", "actor": {"type": "gate", "id": "g"}}]
    assert detect_ghosts(records) == []


def test_human_allow_without_owner_is_ghost():
    records = [{"id": "e3", "action": "allow", "actor": {"type": "human", "id": "h"}}]
    assert detect_ghosts(records)


def test_halt_without_owner_is_ghost():
    records = [{"id": "e4", "action": "halt", "actor": {"type": "gate", "id": "g"}}]
    assert detect_ghosts(records)


def test_undocumented_change_detected():
    records = [{"id": "e", "action": "allow", "subject": {"change": "pr-1"}}]
    assert detect_undocumented(["pr-1", "pr-2"], records)
    assert detect_undocumented(["pr-1"], records) == []
