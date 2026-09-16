"""no-pii-in-logs is catalogue-driven and covers special-category + bare-arg patterns.

Fields declared in spine/data-catalogue.yaml (not only the built-in defaults) are treated as
personal data in logs, so an adopter declares personal data once for both code gates.
"""

from compliance_spine.change import Change
from compliance_spine.gates.base import GateSpec
from compliance_spine.gates.builtins import GATE_CLASSES
from compliance_spine.gates.builtins import no_pii_in_logs as npl

SPEC = GateSpec(name="x", intent_ref="", severity="high")


def _blocks(content: str) -> bool:
    change = Change.from_dict(
        {"id": "c", "files": [{"path": "svc/x.py", "content": content}], "metadata": {}}
    )
    ok, _findings, _subject = GATE_CLASSES["no-pii-in-logs"]().check(change, SPEC)
    return not ok


def test_special_category_field_in_log_is_caught():
    assert _blocks('logger.info("conditions=%s", claim.health_conditions)')
    assert _blocks('log.info(f"notes {claim.medical_notes}")')


def test_bare_field_positional_arg_is_caught():
    assert _blocks('logger.info("id lookup %s", national_id)')


def test_catalogue_only_field_is_caught():
    # sexual_orientation is in spine/data-catalogue.yaml (special) but not the built-in defaults;
    # accessed via a non-container object so it can only be caught via the catalogue.
    assert "sexual_orientation" not in npl._DEFAULT_FIELDS
    assert _blocks('logger.warning("pref %s", row.sexual_orientation)')


def test_record_id_and_correlation_id_are_not_flagged():
    assert not _blocks('logger.info("claim %s status %s", claim.id, claim.status)')
    assert not _blocks('logger.info("request %s complete", correlation_id)')
