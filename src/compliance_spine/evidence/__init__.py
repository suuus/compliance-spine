"""Evidence layer — hash-chained decision ledger + ghost-decision detector."""

from compliance_spine.evidence.detector import (
    GhostFinding,
    detect_ghosts,
    detect_undocumented,
    scan,
)
from compliance_spine.evidence.ledger import Ledger, VerifyResult
from compliance_spine.evidence.record import (
    GENESIS_PREV,
    DecisionRecord,
    new_id,
    record_hash,
)

__all__ = [
    "GENESIS_PREV",
    "DecisionRecord",
    "GhostFinding",
    "Ledger",
    "VerifyResult",
    "detect_ghosts",
    "detect_undocumented",
    "new_id",
    "record_hash",
    "scan",
]
