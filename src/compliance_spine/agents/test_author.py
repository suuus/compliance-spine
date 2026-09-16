"""Test-author agent — proposes the compliance tests a change should carry, based on the
context it declares. Deterministic: it maps the applicable gates to pytest stubs the team
keeps as regression tests. Advisory only.
"""

from __future__ import annotations

from compliance_spine.agents.base import Agent, AgentResult
from compliance_spine.change import Change

# Gates that apply to every change (code-level scans).
_ALWAYS = ("no-pii-in-logs", "encryption-required", "pii-access-boundary")


def _applicable(change: Change) -> list[str]:
    m = change.metadata or {}
    gates = list(_ALWAYS)
    if m.get("data_category") in {"personal", "special"}:
        gates += ["lawful-basis-required", "retention-ttl", "cross-border-transfer"]
    if m.get("data_category") == "special":
        gates.append("special-category")
    if m.get("automated_decision"):
        gates.append("automated-decision")
    if m.get("ai_feature"):
        gates.append("ai-act-risk-tier")
    if m.get("ai_feature") or m.get("model_change"):
        gates.append("model-governance")
    return sorted(dict.fromkeys(gates))


def _stub(gate: str, change_id: str) -> tuple[str, str]:
    fn = f"test_compliant_{gate.replace('-', '_')}"
    code = (
        f"def {fn}():\n"
        f"    from compliance_spine.change import Change\n"
        f"    from compliance_spine.gates.runner import enforce\n"
        f'    change = Change.from_json_file("changes/{change_id}.json")\n'
        f'    result = enforce(change, emit_evidence=False, only={{"{gate}"}})\n'
        f"    assert result.allowed, result.summary()\n"
    )
    return fn, code


class TestAuthorAgent(Agent):
    name = "test-author"

    def run(self, change: Change) -> AgentResult:
        from compliance_spine.agents.test_templates import TEMPLATES, select

        gates = _applicable(change)
        stubs: dict[str, str] = {}
        items: list[str] = []
        for gate in gates:
            fn, code = _stub(gate, change.id)
            stubs[fn] = code
            items.append(f"{fn}  (covers {gate})")

        templates = {key: TEMPLATES[key] for key in select(change)}
        for key in templates:
            items.append(f"behavioural template: {key}")

        verdict = (
            f"{len(gates)} gate test(s) + {len(templates)} behavioural template(s) recommended"
        )
        return AgentResult(
            self.name,
            change.id,
            True,
            verdict,
            items,
            {"gates": gates, "stubs": stubs, "templates": templates},
        )
