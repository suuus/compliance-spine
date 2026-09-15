"""Intent layer: parsing, resolution, and gate traceability."""

import yaml

from compliance_spine.config import paths
from compliance_spine.intent import IntentRegistry, load_intent, validate_traceability
from compliance_spine.intent.loader import Finding


def test_parses_full_constitution():
    rules = load_intent()
    assert len(rules) == 9
    assert [r.rank for r in rules] == list(range(1, 10))
    slugs = {r.slug for r in rules}
    for expected in (
        "no-pii-in-logs",
        "special-category",
        "automated-decision",
        "cross-border-transfer",
        "encryption-required",
        "storage-limitation",
        "ai-act-risk-tier",
    ):
        assert expected in slugs


def test_resolve_direct_and_aliased():
    reg = IntentRegistry.load()
    assert reg.resolve("intent/never-delegate#no-pii-in-logs").slug == "no-pii-in-logs"
    # aliased anchors resolve to their fuller slug
    assert reg.resolve("intent/never-delegate#lawful-basis").slug == "lawful-basis-required"
    assert reg.resolve("intent/never-delegate#ai-act").slug == "ai-act-risk-tier"
    assert reg.resolve("intent/never-delegate#not-a-real-anchor") is None


def test_seed_gates_all_trace_to_intent():
    reg = IntentRegistry.load()
    cfg = yaml.safe_load(paths().gate_config.read_text(encoding="utf-8"))
    findings = validate_traceability(reg, cfg)
    errors = [f for f in findings if f.level == "error"]
    assert errors == [], f"seed gates must trace to intent, got: {errors}"


def test_unmapped_gate_is_detected():
    reg = IntentRegistry.load()
    synthetic = {"gates": {"rogue-gate": {"intent_ref": "intent/never-delegate#nowhere"}}}
    findings = validate_traceability(reg, synthetic)
    assert any(isinstance(f, Finding) and f.code == "gate-unmapped-intent" for f in findings)
