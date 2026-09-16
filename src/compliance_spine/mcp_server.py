"""MCP server — exposes the compliance spine to the GitHub Copilot App or any MCP client.

Each tool is a thin wrapper over the same primitives the CLI uses, so an agent in the
Copilot App can plan, delegate, and review changes through the spine while every
consequential decision still lands in the tamper-evident Evidence ledger.

Run:  compliance-spine-mcp        (stdio transport)
Requires the optional MCP extra:  pip install -e ".[mcp]"
"""

from __future__ import annotations

from typing import Any

from compliance_spine.agents import (
    AiActBaselineAgent,
    CodingAdvisorAgent,
    QualityReviewerAgent,
    TestAuthorAgent,
)
from compliance_spine.change import Change
from compliance_spine.evidence.detector import scan
from compliance_spine.evidence.ledger import Ledger
from compliance_spine.gates.runner import enforce
from compliance_spine.intent import IntentRegistry
from compliance_spine.overrides import OverrideStore
from compliance_spine.zava import run as zava_run

try:
    from mcp.server.mcpserver import MCPServer
except ModuleNotFoundError as exc:  # pragma: no cover - import guard
    raise SystemExit("MCP SDK not installed. Install with:  pip install -e '.[mcp]'") from exc

server = MCPServer("compliance-spine")


@server.tool()
def check_change(change: dict[str, Any]) -> dict[str, Any]:
    """Run the fail-closed compliance gates over a change and emit Evidence for every decision."""
    result = enforce(Change.from_dict(change), overrides=OverrideStore())
    return {
        "decision": result.decision,
        "allowed": result.allowed,
        "summary": result.summary(),
        "unenforced": result.unenforced,
    }


@server.tool()
def advise(change: dict[str, Any]) -> dict[str, Any]:
    """Coding-advisor: article-referenced remediation guidance for a change (advisory)."""
    r = CodingAdvisorAgent().run(Change.from_dict(change))
    return {"ok": r.ok, "verdict": r.verdict, "guidance": r.items}


@server.tool()
def recommend_tests(change: dict[str, Any]) -> dict[str, Any]:
    """Test-author: the compliance tests a change should carry, with pytest stubs."""
    r = TestAuthorAgent().run(Change.from_dict(change))
    return {"gates": r.detail["gates"], "tests": r.items, "stubs": r.detail["stubs"]}


@server.tool()
def review(change: dict[str, Any]) -> dict[str, Any]:
    """Quality-reviewer verdict; refuses to auto-approve never-delegate items. Emits Evidence."""
    r = QualityReviewerAgent().run(Change.from_dict(change), ledger=Ledger())
    return {"ok": r.ok, "verdict": r.verdict, "findings": r.items, "detail": r.detail}


@server.tool()
def classify_ai_act_risk(change: dict[str, Any]) -> dict[str, Any]:
    """AI-Act-baseline: risk tier + Art 9-15 obligation checklist. Emits Evidence."""
    r = AiActBaselineAgent().run(Change.from_dict(change), ledger=Ledger())
    return {"ok": r.ok, "tier": r.detail["tier"], "verdict": r.verdict, "obligations": r.items}


@server.tool()
def verify_ledger() -> dict[str, Any]:
    """Verify the Evidence hash-chain (tamper detection)."""
    v = Ledger().verify()
    return {"ok": v.ok, "count": v.count, "errors": v.errors}


@server.tool()
def scan_ghosts() -> dict[str, Any]:
    """Find consequential decisions with no named human owner."""
    findings = scan(Ledger())
    return {"ok": not findings, "ghosts": [g.render() for g in findings]}


@server.tool()
def run_evals() -> dict[str, Any]:
    """Run the ZAVA compliance eval suite and return recall / false-positive-rate."""
    report = zava_run()
    return {
        "passed": report.passed,
        "recall": report.recall,
        "fpr": report.fpr,
        "n": len(report.results),
    }


@server.tool()
def record_finding(
    kind: str,
    message: str,
    file: str | None = None,
    line: int | None = None,
    confidence: float = 0.6,
    severity: str = "info",
    change: str = "reasoning-review",
    model: str = "reasoning",
) -> dict[str, Any]:
    """Record one reasoned (non-deterministic) finding as its own adjudicable Evidence event.

    Call this per finding when you assess with your own reasoning, so each becomes a real
    ``evt_*`` ledger id (not just a report label) that a human can pass to ``adjudicate``.
    Returns the ledger id and the finding's structured location.
    """
    from compliance_spine.learning import record_finding as _record

    rec = _record(
        kind, message, change=change, file=file, line=line,
        confidence=confidence, severity=severity, model=model,
    )
    return {
        "id": rec["id"],
        "rule_id": rec["rule_id"],
        "confidence": confidence,
        "finding": {"file": file, "line": line, "message": message},
    }


@server.tool()
def list_intent() -> list[dict[str, Any]]:
    """List the never-delegate rules (Intent)."""
    return [
        {"rank": r.rank, "slug": r.slug, "title": r.title, "owner": r.owner}
        for r in IntentRegistry.load().rules
    ]


def main() -> None:
    server.run()  # stdio transport


if __name__ == "__main__":
    main()
