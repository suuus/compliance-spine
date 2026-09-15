"""Gate framework — the Structure layer."""

from compliance_spine.gates.base import (
    ALLOW,
    BLOCK,
    ESCALATE,
    HALT,
    QUARANTINE,
    Gate,
    GateResult,
    GateSpec,
    worst,
)
from compliance_spine.gates.registry import build_gates, load_config, resolve_specs
from compliance_spine.gates.runner import EnforcementResult, emit, enforce

__all__ = [
    "ALLOW",
    "BLOCK",
    "ESCALATE",
    "HALT",
    "QUARANTINE",
    "EnforcementResult",
    "Gate",
    "GateResult",
    "GateSpec",
    "build_gates",
    "emit",
    "enforce",
    "load_config",
    "resolve_specs",
    "worst",
]
