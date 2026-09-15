"""No-PII-in-logs gate: violations blocked, clean allowed, redaction respected, fail-closed."""

from compliance_spine.change import Change, ChangeFile
from compliance_spine.gates.base import ALLOW, BLOCK, Gate, GateSpec
from compliance_spine.gates.builtins.no_pii_in_logs import NoPiiInLogsGate

_SPEC = GateSpec(name="no-pii-in-logs", intent_ref="intent/never-delegate#no-pii-in-logs",
                 severity="critical", build_time="block")


def _change(content: str) -> Change:
    return Change(id="c", files=[ChangeFile("a.py", content)])


def test_flags_interpolated_pii():
    gate = NoPiiInLogsGate()
    res = gate.evaluate(_change("logger.info(f'hi {user.email}')"), _SPEC)
    assert res.decision == BLOCK
    assert res.findings


def test_allows_prose_and_non_pii():
    gate = NoPiiInLogsGate()
    assert gate.evaluate(_change("logger.info('user logged in')"), _SPEC).decision == ALLOW
    assert gate.evaluate(_change("logger.info(f'req {request_id}')"), _SPEC).decision == ALLOW


def test_redaction_is_respected():
    gate = NoPiiInLogsGate()
    res = gate.evaluate(_change("logger.info(f'{redact(user.email)}')"), _SPEC)
    assert res.decision == ALLOW


def test_bare_container_first_arg_blocked():
    gate = NoPiiInLogsGate()
    assert gate.evaluate(_change("logging.debug(customer)"), _SPEC).decision == BLOCK


class _ExplodingGate(Gate):
    name = "boom"

    def check(self, change, spec):
        raise RuntimeError("kaboom")


def test_gate_fails_closed_on_error():
    res = _ExplodingGate().evaluate(_change("x"), GateSpec("boom", "i", "high"))
    assert res.decision == BLOCK
    assert "kaboom" in res.reason
