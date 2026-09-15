"""ZAVA dataset — labelled compliance cases the gates must get right."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from compliance_spine.change import Change
from compliance_spine.config import paths


@dataclass
class ZavaCase:
    id: str
    expected: str  # "block" (a violation the gate must stop) | "allow" (a clean change)
    change: Change
    tags: list[str] = field(default_factory=list)
    gate: str | None = None  # isolate evaluation to this gate (defaults from filename)


def _from_dict(d: dict, default_gate: str | None = None) -> ZavaCase:
    return ZavaCase(
        id=d["id"],
        expected=d["expected"],
        change=Change.from_dict(d["change"]),
        tags=list(d.get("tags", [])),
        gate=d.get("gate", default_gate),
    )


def load_cases(path: str | Path | None = None) -> list[ZavaCase]:
    root = Path(path) if path else paths().zava_dir / "datasets"
    files = [root] if root.is_file() else sorted(root.glob("*.jsonl"))
    cases: list[ZavaCase] = []
    for fp in files:
        default_gate = fp.stem.replace("_", "-")
        for line in fp.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("//"):
                cases.append(_from_dict(json.loads(line), default_gate))
    return cases
