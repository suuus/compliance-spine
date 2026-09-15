"""Gate registry — resolve gate-config.yaml (+ defaults) into specs and instantiate the
implemented gates. Gates named in config but not yet implemented are reported as
*unenforced* rather than silently ignored.
"""

from __future__ import annotations

import yaml

from compliance_spine.config import paths
from compliance_spine.gates.base import Gate, GateSpec
from compliance_spine.gates.builtins import GATE_CLASSES

_KNOWN_KEYS = {"intent_ref", "severity", "build_time", "run_time", "silence"}


def load_config(path=None) -> dict:
    p = path or paths().gate_config
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def resolve_specs(config: dict) -> dict[str, GateSpec]:
    defaults = config.get("defaults", {}) or {}
    default_silence = defaults.get("silence", {}) or {}
    specs: dict[str, GateSpec] = {}
    for name, raw in (config.get("gates") or {}).items():
        raw = raw or {}
        specs[name] = GateSpec(
            name=name,
            intent_ref=raw.get("intent_ref", ""),
            severity=raw.get("severity", "high"),
            build_time=raw.get("build_time", defaults.get("default_decision", "block")),
            run_time=raw.get("run_time", defaults.get("default_decision", "block")),
            silence={**default_silence, **(raw.get("silence") or {})},
            extra={k: v for k, v in raw.items() if k not in _KNOWN_KEYS},
        )
    return specs


def build_gates(
    config: dict | None = None, only: set[str] | None = None
) -> tuple[list[tuple[Gate, GateSpec]], list[str]]:
    config = config if config is not None else load_config()
    specs = resolve_specs(config)
    enforced: list[tuple[Gate, GateSpec]] = []
    unenforced: list[str] = []
    for name, spec in specs.items():
        if only is not None and name not in only:
            continue
        cls = GATE_CLASSES.get(name)
        if cls is None:
            unenforced.append(name)
        else:
            enforced.append((cls(), spec))
    return enforced, unenforced
