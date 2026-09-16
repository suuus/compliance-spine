"""The unit a gate evaluates: a proposed change (PR / commit / plan) plus its declared
compliance context. Deterministic canonicalisation gives every change a stable hash so
Evidence records are reproducible and tamper-evident.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


def canonical_json(obj: object) -> str:
    """Stable JSON serialisation used for all hashing (sorted keys, no whitespace)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ChangeFile:
    path: str
    content: str


@dataclass
class Change:
    """A proposed change and the compliance context declared for it.

    ``metadata`` is the declared context gates rely on, e.g.::

        {"data_category": "personal" | "special" | "none",
         "region": "eu", "ai_feature": "risk-scoring",
         "automated_decision": true, "lawful_basis": "contract"}
    """

    id: str
    files: list[ChangeFile] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    #: LLM-drafted compliance context, awaiting human confirmation (never binding on its own).
    proposed_metadata: dict = field(default_factory=dict)

    def payload_hash(self) -> str:
        return sha256_hex(canonical_json(asdict(self)))

    @property
    def data_category(self) -> str:
        return str(self.metadata.get("data_category", "unknown"))

    @classmethod
    def from_dict(cls, data: dict) -> Change:
        files = [ChangeFile(**f) for f in data.get("files", [])]
        return cls(
            id=data["id"],
            files=files,
            metadata=data.get("metadata", {}),
            proposed_metadata=data.get("proposed_metadata", {}),
        )

    @classmethod
    def from_json_file(cls, path: str | Path) -> Change:
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
