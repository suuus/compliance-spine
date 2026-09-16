"""Recall scorecard — put the deterministic floor next to the layered reviewer and let the
numbers decide. Measures gates-only recall vs. gates-∪-assessor recall on an *extended*
dataset that deliberately includes violations the fixed rules don't cover.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from compliance_spine.change import Change
from compliance_spine.config import paths
from compliance_spine.gates.runner import enforce
from compliance_spine.llm.reviewer import Assessor, LayeredReviewer
from compliance_spine.zava.metrics import Confusion


def load_cases(path: str | Path | None = None) -> list[tuple[str, str, Change, list[str]]]:
    root = Path(path) if path else paths().zava_dir / "scorecard"
    files = [root] if root.is_file() else sorted(root.glob("*.jsonl"))
    cases: list[tuple[str, str, Change, list[str]]] = []
    for fp in files:
        for line in fp.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("//"):
                d = json.loads(line)
                change = Change.from_dict(d["change"])
                cases.append((d["id"], d["expected"], change, d.get("tags", [])))
    return cases


@dataclass
class Scorecard:
    n: int
    assessor: str
    baseline: Confusion
    augmented: Confusion

    @property
    def lift(self) -> float:
        return self.augmented.recall - self.baseline.recall

    def render(self) -> str:
        return "\n".join([
            f"Recall scorecard — deterministic floor vs. + '{self.assessor}' (n={self.n})",
            f"  baseline  (gates only)      recall={self.baseline.recall:.2f}  "
            f"fpr={self.baseline.false_positive_rate:.2f}",
            f"  augmented (gates + assessor) recall={self.augmented.recall:.2f}  "
            f"fpr={self.augmented.false_positive_rate:.2f}",
            f"  recall lift: {self.lift:+.2f}   (false-positive rate must not rise)",
        ])


def score(assessor: Assessor | None = None, cases=None) -> Scorecard:
    cases = cases if cases is not None else load_cases()
    reviewer = LayeredReviewer(assessor)
    baseline, augmented = Confusion(), Confusion()
    for _id, expected, change, _tags in cases:
        baseline_pred = "allow" if enforce(change, emit_evidence=False).allowed else "block"
        augmented_pred = "allow" if reviewer.review(change).allowed else "block"
        baseline.add(expected, baseline_pred)
        augmented.add(expected, augmented_pred)
    return Scorecard(len(cases), reviewer.assessor.name, baseline, augmented)
