"""Regulatory framework packs.

A *framework pack* groups the gates (and, through them, the never-delegate principles, ZAVA
cases, and article mappings) that enforce one regulation — so a framework is a first-class,
queryable, pluggable unit rather than an implicit property of the gate list.

Ships GDPR + EU AI Act. An adopter adds a pack by declaring it in ``spine/frameworks.yaml`` and
adding its gates (each with an intent principle + ZAVA cases + article references). See
``docs/FRAMEWORKS.md``. The customer's own sector regulations are added privately, this way,
without touching the core.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache

import yaml

from compliance_spine.config import paths
from compliance_spine.gates.builtins import GATE_CLASSES

# Built-in default packs, used when spine/frameworks.yaml is absent.
_DEFAULT: dict[str, dict] = {
    "gdpr": {
        "name": "GDPR",
        "description": "EU General Data Protection Regulation (2016/679)",
        "gates": [
            "no-pii-in-logs",
            "lawful-basis-required",
            "special-category",
            "retention-ttl",
            "cross-border-transfer",
            "encryption-required",
            "automated-decision",
            "pii-access-boundary",
            "consent-default",
            "weak-password-hash",
            "pii-in-url",
            "insecure-transport",
            "permissive-cors",
            "error-leakage",
            "secret-file-committed",
        ],
    },
    "eu-ai-act": {
        "name": "EU AI Act",
        "description": "EU Artificial Intelligence Act (2024/1689)",
        "gates": ["ai-act-risk-tier", "model-governance"],
    },
}


@dataclass(frozen=True)
class Framework:
    key: str
    name: str
    description: str
    gates: tuple[str, ...]

    @property
    def implemented(self) -> int:
        return sum(1 for g in self.gates if g in GATE_CLASSES)


@cache
def load_frameworks() -> tuple[Framework, ...]:
    data = _DEFAULT
    try:
        fp = paths().root / "spine" / "frameworks.yaml"
        if fp.is_file():
            loaded = yaml.safe_load(fp.read_text(encoding="utf-8")) or {}
            data = loaded.get("frameworks") or _DEFAULT
    except Exception:  # noqa: BLE001 — a missing/broken file must not break framework reporting
        data = _DEFAULT
    return tuple(
        Framework(
            key=key,
            name=str(spec.get("name", key)),
            description=str(spec.get("description", "")),
            gates=tuple(spec.get("gates", []) or []),
        )
        for key, spec in data.items()
    )


def framework_of(gate: str) -> str | None:
    """The framework a gate belongs to (first match), or None if unassigned."""
    for fw in load_frameworks():
        if gate in fw.gates:
            return fw.key
    return None


def orphan_gates() -> list[str]:
    """Implemented gates that no framework pack claims."""
    claimed = {g for fw in load_frameworks() for g in fw.gates}
    return sorted(name for name in GATE_CLASSES if name not in claimed)


def render() -> str:
    lines = ["Regulatory framework packs", "=" * 26]
    for fw in load_frameworks():
        lines.append(f"[{fw.name}] ({fw.key}) — {fw.implemented}/{len(fw.gates)} gates implemented")
        lines.append(f"    {fw.description}")
        lines.append(f"    gates: {', '.join(fw.gates)}")
    orphans = orphan_gates()
    if orphans:
        lines.append(f"\nunassigned gates (no framework): {', '.join(orphans)}")
    return "\n".join(lines)
