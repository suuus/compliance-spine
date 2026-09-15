"""ISEE coverage & maturity diagnostic — a read-only health report across the four
dimensions (Intent · Structure · Execution · Evidence). Deterministic: it scores each
dimension from observable signals in the repo, reusing the isee-advisor maturity idea
without any model call.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import yaml

from compliance_spine.agents import AGENTS
from compliance_spine.config import paths
from compliance_spine.evidence.detector import scan
from compliance_spine.evidence.ledger import Ledger
from compliance_spine.gates.builtins import GATE_CLASSES
from compliance_spine.gates.registry import resolve_specs
from compliance_spine.intent import IntentRegistry, validate_traceability
from compliance_spine.zava import run as zava_run


@dataclass
class Dimension:
    name: str
    ok: bool
    signals: list[str] = field(default_factory=list)


@dataclass
class Diagnostic:
    dimensions: list[Dimension]

    @property
    def healthy(self) -> bool:
        return all(d.ok for d in self.dimensions)

    def render(self) -> str:
        lines = ["ISEE compliance-spine diagnostic", "=" * 34]
        for d in self.dimensions:
            lines.append(f"[{'ok' if d.ok else 'GAP'}] {d.name}")
            lines.extend(f"      · {s}" for s in d.signals)
        lines.append("-" * 34)
        lines.append(f"overall: {'healthy' if self.healthy else 'gaps present'}")
        return "\n".join(lines)


def diagnose(run_evals: bool = True) -> Diagnostic:
    registry = IntentRegistry.load()
    config = yaml.safe_load(paths().gate_config.read_text(encoding="utf-8")) or {}
    specs = resolve_specs(config)

    owners = sum(1 for r in registry.rules if r.owner)
    intent = Dimension(
        "Intent",
        len(registry.rules) >= 3,
        [
            f"{len(registry.rules)} never-delegate principles",
            f"owners assigned: {owners}/{len(registry.rules)}",
        ],
    )

    findings = validate_traceability(registry, config)
    trace_errors = sum(1 for f in findings if f.level == "error")
    implemented = [n for n in specs if n in GATE_CLASSES]
    structure = Dimension(
        "Structure",
        len(implemented) == len(specs) and trace_errors == 0,
        [
            f"gates configured: {len(specs)}",
            f"gates implemented: {len(implemented)}/{len(specs)}",
            f"traceability errors: {trace_errors}",
        ],
    )

    execution = Dimension(
        "Execution",
        len(AGENTS) >= 4,
        [f"agents: {len(AGENTS)} ({', '.join(sorted(AGENTS))})"],
    )
    if run_evals:
        report = zava_run()
        execution.signals.append(
            f"ZAVA: {'PASS' if report.passed else 'FAIL'} "
            f"(recall {report.recall:.2f}, fpr {report.fpr:.2f}, n={len(report.results)})"
        )
        execution.ok = execution.ok and report.passed

    ledger = Ledger()
    verify = ledger.verify()
    ghosts = scan(ledger)
    evidence = Dimension(
        "Evidence",
        verify.ok and not ghosts,
        [
            f"ledger records: {verify.count}",
            f"chain intact: {verify.ok}",
            f"ghost decisions: {len(ghosts)}",
        ],
    )

    return Diagnostic([intent, structure, execution, evidence])
