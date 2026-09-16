"""llm-review accepts a change JSON *or* a git diff (--base/--staged), so the layered
floor+ceiling review runs on a real tree, not only a hand-authored change file.
"""

from compliance_spine.cli import build_parser, main
from compliance_spine.gitdiff import build_change


def test_parser_accepts_change_or_git_diff():
    p = build_parser()
    a = p.parse_args(["llm-review", "--base", "origin/main"])
    assert a.base == "origin/main" and a.change is None and a.staged is False
    b = p.parse_args(["llm-review", "change.json"])
    assert b.change == "change.json" and b.base is None


def test_no_input_returns_guidance():
    # neither a change file nor a diff selector -> non-zero guidance, no side effects
    assert main(["llm-review"]) == 2


def test_base_routes_to_git_diff_and_layers_run(monkeypatch):
    seen = {}

    def fake_collect(staged=True, base=None, head="HEAD"):
        seen["route"] = (staged, base, head)
        return build_change([("svc/a.py", "logger.info(f'{user.email}')")])

    class _FakeLedger:
        def append(self, record):
            return record

    monkeypatch.setattr("compliance_spine.gitdiff.collect_change", fake_collect)
    monkeypatch.setattr("compliance_spine.evidence.ledger.Ledger", _FakeLedger)

    rc = main(["llm-review", "--base", "abc123"])
    assert seen["route"] == (False, "abc123", "HEAD")
    assert rc == 1  # the PII-in-logs change blocks at the deterministic floor
