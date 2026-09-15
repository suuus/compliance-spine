"""Registry of implemented gate classes, keyed by their gate-config.yaml name."""

from compliance_spine.gates.builtins.ai_act import AiActRiskTierGate
from compliance_spine.gates.builtins.automated_decision import AutomatedDecisionGate
from compliance_spine.gates.builtins.gdpr import (
    CrossBorderTransferGate,
    EncryptionRequiredGate,
    LawfulBasisGate,
    RetentionTtlGate,
    SpecialCategoryGate,
)
from compliance_spine.gates.builtins.model_governance import ModelGovernanceGate
from compliance_spine.gates.builtins.no_pii_in_logs import NoPiiInLogsGate
from compliance_spine.gates.builtins.pii_access_boundary import PiiAccessBoundaryGate

_ALL = (
    NoPiiInLogsGate,
    LawfulBasisGate,
    SpecialCategoryGate,
    RetentionTtlGate,
    CrossBorderTransferGate,
    EncryptionRequiredGate,
    AutomatedDecisionGate,
    AiActRiskTierGate,
    PiiAccessBoundaryGate,
    ModelGovernanceGate,
)

GATE_CLASSES = {g.name: g for g in _ALL}

__all__ = [
    "GATE_CLASSES",
    "AiActRiskTierGate",
    "AutomatedDecisionGate",
    "CrossBorderTransferGate",
    "EncryptionRequiredGate",
    "LawfulBasisGate",
    "ModelGovernanceGate",
    "NoPiiInLogsGate",
    "PiiAccessBoundaryGate",
    "RetentionTtlGate",
    "SpecialCategoryGate",
]
