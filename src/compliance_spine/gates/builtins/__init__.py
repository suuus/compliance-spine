"""Registry of implemented gate classes, keyed by their gate-config.yaml name."""

from compliance_spine.gates.builtins.ai_act import AiActRiskTierGate
from compliance_spine.gates.builtins.automated_decision import AutomatedDecisionGate
from compliance_spine.gates.builtins.gdpr import (
    ConsentDefaultGate,
    CrossBorderTransferGate,
    EncryptionRequiredGate,
    LawfulBasisGate,
    RetentionTtlGate,
    SpecialCategoryGate,
)
from compliance_spine.gates.builtins.model_governance import ModelGovernanceGate
from compliance_spine.gates.builtins.no_pii_in_logs import NoPiiInLogsGate
from compliance_spine.gates.builtins.pii_access_boundary import PiiAccessBoundaryGate
from compliance_spine.gates.builtins.security_hygiene import (
    ErrorLeakageGate,
    InsecureTransportGate,
    PermissiveCorsGate,
    PiiInUrlGate,
    SecretFileCommittedGate,
    WeakPasswordHashGate,
)

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
    ConsentDefaultGate,
    WeakPasswordHashGate,
    PiiInUrlGate,
    InsecureTransportGate,
    PermissiveCorsGate,
    ErrorLeakageGate,
    SecretFileCommittedGate,
)

GATE_CLASSES = {g.name: g for g in _ALL}

__all__ = [
    "GATE_CLASSES",
    "AiActRiskTierGate",
    "AutomatedDecisionGate",
    "ConsentDefaultGate",
    "CrossBorderTransferGate",
    "EncryptionRequiredGate",
    "ErrorLeakageGate",
    "InsecureTransportGate",
    "LawfulBasisGate",
    "ModelGovernanceGate",
    "NoPiiInLogsGate",
    "PermissiveCorsGate",
    "PiiAccessBoundaryGate",
    "PiiInUrlGate",
    "RetentionTtlGate",
    "SecretFileCommittedGate",
    "SpecialCategoryGate",
    "WeakPasswordHashGate",
]
