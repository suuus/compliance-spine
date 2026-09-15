"""Diagnostics + governance operations."""

from compliance_spine.change import Change, ChangeFile
from compliance_spine.diagnostics import diagnose
from compliance_spine.evidence.ledger import Ledger
from compliance_spine.gates.runner import enforce
from compliance_spine.governance import export_change, governance_report
from compliance_spine.overrides import OverrideStore


def test_diagnose_reports_four_isee_dimensions():
    diag = diagnose(run_evals=False)
    assert [d.name for d in diag.dimensions] == ["Intent", "Structure", "Execution", "Evidence"]
    structure = next(d for d in diag.dimensions if d.name == "Structure")
    assert structure.ok  # all configured gates implemented, no traceability errors


def test_export_change_bundles_records(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    change = Change(
        id="pr-42",
        files=[ChangeFile("a.py", "logger.info(f'{user.email}')")],
        metadata={"data_category": "none"},
    )
    enforce(change, ledger=led, only={"no-pii-in-logs"})
    bundle = export_change("pr-42", ledger=led)
    assert bundle["count"] >= 1
    assert all(r["subject"]["change"] == "pr-42" for r in bundle["records"])


def test_governance_flags_unassigned_owners(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    report = governance_report(store=OverrideStore(tmp_path / "o.json"), ledger=led)
    assert report["intent_owners_unassigned"]  # seed constitution has placeholder owners
    assert report["ledger_ok"]
    assert report["active_overrides"] == []
