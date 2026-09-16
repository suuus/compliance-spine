"""scan-diff: git-diff -> Change adapter feeds the code-scanning gates."""

import subprocess

from compliance_spine.gates.registry import code_scanning_gate_names
from compliance_spine.gates.runner import enforce
from compliance_spine.gitdiff import build_change, collect_change


def _git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def test_code_scanning_set():
    assert code_scanning_gate_names() == {
        "no-pii-in-logs",
        "encryption-required",
        "pii-access-boundary",
        "weak-password-hash",
        "pii-in-url",
        "insecure-transport",
        "permissive-cors",
        "error-leakage",
        "secret-file-committed",
    }


def test_build_change_blocks_pii():
    change = build_change([("svc/a.py", "logger.info(f'{user.email}')")])
    result = enforce(change, emit_evidence=False, only=code_scanning_gate_names())
    assert not result.allowed


def test_build_change_allows_clean():
    change = build_change([("svc/a.py", "logger.info('request ok')")])
    result = enforce(change, emit_evidence=False, only=code_scanning_gate_names())
    assert result.allowed


def test_collect_staged_change(tmp_path, monkeypatch):
    _git("init", "-q", cwd=tmp_path)
    (tmp_path / "svc").mkdir()
    (tmp_path / "svc" / "a.py").write_text("logger.info(f'{user.email}')", encoding="utf-8")
    _git("add", "svc/a.py", cwd=tmp_path)
    monkeypatch.chdir(tmp_path)

    change = collect_change(staged=True)
    assert any(f.path == "svc/a.py" for f in change.files)
    result = enforce(change, emit_evidence=False, only=code_scanning_gate_names())
    assert not result.allowed
