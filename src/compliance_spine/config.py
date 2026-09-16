"""Locate the spine repository and expose the canonical file paths.

The spine governs a repository, so everything is resolved relative to a *root* that
contains ``spine/``. Resolution order:

1. An explicitly pinned root — the ``start`` argument or ``$COMPLIANCE_SPINE_ROOT`` — is
   authoritative and only has to contain ``spine/``, so the spine drops into any project
   (Python or not) without needing a ``pyproject.toml`` marker.
2. Otherwise walk upward from the current working directory for a dir with ``spine/`` +
   ``pyproject.toml``.
3. Fall back to the installed package's repository root.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import cache
from pathlib import Path


def find_root(start: str | os.PathLike[str] | None = None) -> Path:
    # A pinned root (argument or $COMPLIANCE_SPINE_ROOT) is authoritative: it lets the spine
    # govern a non-Python project, which has no pyproject.toml to anchor auto-discovery.
    pinned = start if start is not None else os.environ.get("COMPLIANCE_SPINE_ROOT")
    if pinned is not None:
        root = Path(pinned).resolve()
        if (root / "spine").is_dir():
            return root
        raise FileNotFoundError(f"pinned spine root {root} has no 'spine/' directory")
    # Otherwise auto-discover: walk up for a repo that carries the spine + a Python manifest.
    base = Path.cwd().resolve()
    for d in (base, *base.parents):
        if (d / "spine").is_dir() and (d / "pyproject.toml").is_file():
            return d
    # Fallback: repo root is two levels above this file (src/compliance_spine/config.py).
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Paths:
    """Canonical locations the spine reads and writes."""

    root: Path

    @property
    def spine_dir(self) -> Path:
        return self.root / "spine"

    @property
    def intent_file(self) -> Path:
        return self.spine_dir / "intent" / "never-delegate.md"

    @property
    def gate_config(self) -> Path:
        return self.spine_dir / "gates" / "gate-config.yaml"

    @property
    def data_catalogue(self) -> Path:
        return self.spine_dir / "data-catalogue.yaml"

    @property
    def access_boundaries(self) -> Path:
        return self.spine_dir / "access-boundaries.yaml"

    @property
    def evidence_dir(self) -> Path:
        return self.root / "evidence"

    @property
    def evidence_schema(self) -> Path:
        return self.evidence_dir / "schema" / "decision-record.schema.json"

    @property
    def ledger_dir(self) -> Path:
        return self.evidence_dir / "ledger"

    @property
    def ledger_file(self) -> Path:
        return self.ledger_dir / "decisions.ledger.jsonl"

    @property
    def zava_dir(self) -> Path:
        return self.root / "zava"


@cache
def paths(start: str | None = None) -> Paths:
    return Paths(root=find_root(start))
