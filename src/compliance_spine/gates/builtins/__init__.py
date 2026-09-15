"""Registry of implemented gate classes, keyed by their gate-config.yaml name."""

from compliance_spine.gates.builtins.no_pii_in_logs import NoPiiInLogsGate

GATE_CLASSES = {
    NoPiiInLogsGate.name: NoPiiInLogsGate,
}

__all__ = ["GATE_CLASSES", "NoPiiInLogsGate"]
