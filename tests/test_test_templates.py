"""Test-author agent recommends behavioural compliance templates by declared context."""

import ast

from compliance_spine.agents.test_author import TestAuthorAgent
from compliance_spine.agents.test_templates import TEMPLATES
from compliance_spine.change import Change


def _templates(meta: dict) -> set[str]:
    change = Change.from_dict({"id": "x", "files": [], "metadata": meta})
    return set(TestAuthorAgent().run(change).detail["templates"])


def test_special_category_change_gets_behavioural_templates():
    t = _templates({"data_category": "special", "analytics": True, "automated_decision": True})
    assert {
        "encryption-at-rest-and-in-transit",
        "rbac-negative-access",
        "dsar-access-and-portability",
        "dsar-erasure",
        "retention-enforcement",
        "audit-log-immutable",
    } <= t
    assert "consent-opt-in" in t
    assert "automated-decision-human-override" in t


def test_non_personal_change_gets_no_behavioural_templates():
    assert _templates({"data_category": "none"}) == set()


def test_every_template_is_valid_python():
    for code in TEMPLATES.values():
        ast.parse(code)
