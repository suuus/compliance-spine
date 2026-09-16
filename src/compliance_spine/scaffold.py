"""`compliance-spine init` — scaffold a working ``spine/`` policy folder into a target repo.

The engine is regulation-generic; a repo becomes governed by dropping in a ``spine/`` folder
(intent + gates + the data catalogue + access boundaries) and the evidence schema. ``init``
writes a functional starter set — every gate already traces to a principle, so ``doctor`` passes
immediately — that the adopter then tunes (owners/signatures, their field names, their
components). The templates are shipped as package data so this works from any install.
"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

# Files written into the target repo, relative to both the package's scaffold/ bundle and dest.
_TEMPLATES: tuple[str, ...] = (
    "spine/intent/never-delegate.md",
    "spine/gates/gate-config.yaml",
    "spine/data-catalogue.yaml",
    "spine/access-boundaries.yaml",
    "spine/frameworks.yaml",
    "spine/scan-ignore",
    "evidence/schema/decision-record.schema.json",
)


def _template_bytes(rel: str) -> bytes:
    return (files("compliance_spine") / "scaffold" / rel).read_bytes()


def scaffold_spine(dest: str | Path, force: bool = False) -> list[str]:
    """Write the starter ``spine/`` + evidence schema under ``dest``.

    Returns the repo-relative paths written. Existing files are left untouched unless ``force``
    is set — so re-running ``init`` never clobbers a tuned policy by accident.
    """
    root = Path(dest).resolve()
    written: list[str] = []
    for rel in _TEMPLATES:
        target = root / rel
        if target.exists() and not force:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(_template_bytes(rel))
        written.append(rel)
    return written


def next_steps(root: str | Path) -> str:
    root = Path(root)
    return "\n".join(
        [
            f"Scaffolded a starter spine into {root}/",
            "",
            "Next (this is the real work — tune, don't ship the defaults):",
            "  1. spine/intent/never-delegate.md  — assign real owners + signatures (your DPO).",
            "  2. spine/data-catalogue.yaml        — your personal / special-category fields.",
            "  3. spine/access-boundaries.yaml     — your components that must not touch raw PII.",
            "  4. spine/gates/gate-config.yaml     — severities / silence / circuit-breaker.",
            "",
            "Verify + enforce:",
            "  compliance-spine doctor              # every gate traces to a principle",
            "  compliance-spine matrix              # article -> gate -> coverage",
            "  pre-commit install                   # block violations on every commit",
            "  # CI: run `compliance-spine scan-diff --base origin/<base>` on the PR diff.",
            "",
            "See docs/PILOT.md for the full runbook.",
        ]
    )
