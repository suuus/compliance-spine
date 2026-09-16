from compliance_spine.frameworks import (
    framework_of,
    load_frameworks,
    orphan_gates,
    render,
)
from compliance_spine.matrix import build_matrix


def test_ships_gdpr_and_ai_act_packs():
    keys = {f.key for f in load_frameworks()}
    assert {"gdpr", "eu-ai-act"} <= keys


def test_every_implemented_gate_belongs_to_a_pack():
    assert orphan_gates() == []


def test_framework_of_maps_gates_to_packs():
    assert framework_of("no-pii-in-logs") == "gdpr"
    assert framework_of("ai-act-risk-tier") == "eu-ai-act"
    assert framework_of("model-governance") == "eu-ai-act"
    assert framework_of("does-not-exist") is None


def test_gdpr_pack_is_fully_implemented():
    by_key = {f.key: f for f in load_frameworks()}
    gdpr = by_key["gdpr"]
    assert gdpr.implemented == len(gdpr.gates) == 15


def test_matrix_framework_filter_scopes_rows():
    matrix = build_matrix(framework="eu-ai-act")
    assert {r.gate for r in matrix.rows} == {"ai-act-risk-tier", "model-governance"}


def test_render_lists_both_packs():
    out = render()
    assert "GDPR" in out
    assert "EU AI Act" in out
