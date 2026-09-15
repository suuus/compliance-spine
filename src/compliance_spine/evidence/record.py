"""Evidence record — one append-only entry per consequential decision.

The record mirrors ``evidence/schema/decision-record.schema.json`` exactly and is validated
against it, so the code and the published schema cannot drift.
"""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass, field
from datetime import UTC
from functools import cache

from jsonschema import Draft7Validator

from compliance_spine.change import canonical_json, sha256_hex
from compliance_spine.config import paths

GENESIS_PREV = "0" * 64


@cache
def _validator() -> Draft7Validator:
    schema = json.loads(paths().evidence_schema.read_text(encoding="utf-8"))
    return Draft7Validator(schema)


def new_id() -> str:
    return "evt_" + secrets.token_hex(4)


def record_hash(record: dict) -> str:
    """Content hash of a stored record (includes its own ``prev_hash``)."""
    return sha256_hex(canonical_json(record))


@dataclass
class DecisionRecord:
    """A single Evidence entry. Build via :meth:`for_gate` or directly, then append to a Ledger."""

    action: str
    rule_id: str
    intent_ref: str
    severity: str
    inputs_hash: str
    actor: dict
    subject: dict = field(default_factory=dict)
    id: str = field(default_factory=new_id)
    ts: str | None = None
    owner: dict | None = None
    override: dict | None = None
    outputs_hash: str | None = None
    artifacts: list[str] | None = None
    spine_version: str | None = None
    prev_hash: str = GENESIS_PREV

    def to_dict(self) -> dict:
        from datetime import datetime

        data: dict = {
            "id": self.id,
            "ts": self.ts or datetime.now(UTC).isoformat(),
            "actor": self.actor,
            "action": self.action,
            "subject": {k: v for k, v in self.subject.items() if v is not None},
            "rule_id": self.rule_id,
            "intent_ref": self.intent_ref,
            "severity": self.severity,
            "inputs_hash": self.inputs_hash,
            "prev_hash": self.prev_hash,
        }
        if self.owner is not None:
            data["owner"] = self.owner
        if self.override is not None:
            data["override"] = self.override
        if self.outputs_hash is not None:
            data["outputs_hash"] = self.outputs_hash
        if self.artifacts:
            data["artifacts"] = self.artifacts
        if self.spine_version is not None:
            data["spine_version"] = self.spine_version
        return data

    def validate(self) -> None:
        """Raise jsonschema.ValidationError if this record violates the published schema."""
        _validator().validate(self.to_dict())
