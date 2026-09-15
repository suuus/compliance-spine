"""MCP server: tools are registered, callable, and return the spine's verdicts."""

import asyncio
import shutil

import pytest

pytest.importorskip("mcp")

from compliance_spine import mcp_server as m
from compliance_spine.config import paths

_PII = {
    "id": "pr-x",
    "files": [{"path": "a.py", "content": "logger.info(f'{user.email}')"}],
    "metadata": {"data_category": "none"},
}
_CLEAN = {
    "id": "pr-y",
    "files": [{"path": "a.py", "content": "logger.info('ok')"}],
    "metadata": {"data_category": "none"},
}


@pytest.fixture(autouse=True)
def _clean_ledger():
    yield
    shutil.rmtree(paths().ledger_dir, ignore_errors=True)


def test_tools_registered():
    names = {t.name for t in asyncio.run(m.server.list_tools())}
    assert {
        "check_change", "advise", "recommend_tests", "review", "classify_ai_act_risk",
        "verify_ledger", "scan_ghosts", "run_evals", "list_intent",
    } <= names


def test_check_change_blocks_pii():
    out = m.check_change(_PII)
    assert out["decision"] == "block"
    assert out["allowed"] is False


def test_advise_clean_ok():
    assert m.advise(_CLEAN)["ok"] is True


def test_list_intent_returns_constitution():
    assert len(m.list_intent()) == 9


def test_run_evals_passes():
    out = m.run_evals()
    assert out["passed"] and out["recall"] == 1.0
