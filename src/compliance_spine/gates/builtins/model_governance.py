"""Gate: no model or AI change ships without validation, documentation, and a recorded change
(never-delegate #10). Generic model-change control that satisfies EU AI Act Art 11-12
(technical documentation + record-keeping) and standard model-governance practice.

Applies when a change is a *model change* — it declares an AI feature or ``model_change``,
or it touches a model artifact (``models/`` or ``ml/`` path, or a model file extension). Then
it fails closed unless the change declares:

  - ``model_validation``     — reference to a validation / eval run (e.g. a ZAVA report id)
  - ``model_documentation``  — reference to technical documentation / a model card
  - ``model_version``        — a version / change-record id (change control)

The gate's Evidence record is the model-change record: it ties the decision to a change whose
hashed inputs include the version, validation, and documentation references.
"""

from __future__ import annotations

import re

from compliance_spine.gates.base import Gate, GateSpec

_MODEL_PATH = re.compile(
    r"(?:^|/)(?:models?|ml)/"
    r"|\.(?:pkl|onnx|pt|pth|h5|hdf5|joblib|pb|safetensors|ckpt)$",
    re.IGNORECASE,
)


def _is_model_change(change) -> bool:
    m = change.metadata or {}
    if m.get("model_change") or m.get("ai_feature"):
        return True
    return any(_MODEL_PATH.search(f.path) for f in change.files)


class ModelGovernanceGate(Gate):
    name = "model-governance"

    def check(self, change, spec: GateSpec) -> tuple[bool, list[str], dict]:
        subject = {"change": change.id, "ai_feature": (change.metadata or {}).get("ai_feature")}
        if not _is_model_change(change):
            return True, [], subject

        m = change.metadata or {}
        findings: list[str] = []
        if not m.get("model_validation"):
            findings.append("model change without a validation / eval reference (Art 15)")
        if not m.get("model_documentation"):
            findings.append("model change without technical documentation (Art 11)")
        if not m.get("model_version"):
            findings.append("model change without a recorded version / change record")
        return (not findings, findings, subject)
