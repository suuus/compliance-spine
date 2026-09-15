"""Time-boxed gate overrides (silences). An override lets a human accept a blocking gate
for a bounded window, with named signers and an expiry — recorded in Evidence as an
``override`` action. Absence of an active override means the gate stays fail-closed.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from compliance_spine.config import paths


def _now() -> datetime:
    return datetime.now(UTC)


def _parse(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts)
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


class Override:
    def __init__(
        self,
        gate: str,
        reason: str,
        expires: str,
        signed_by: list[str],
        human_id: str,
        signature: str,
        compensating_control: str | None = None,
    ) -> None:
        self.gate = gate
        self.reason = reason
        self.expires = expires
        self.signed_by = signed_by
        self.human_id = human_id
        self.signature = signature
        self.compensating_control = compensating_control

    def is_active(self, now: datetime | None = None) -> bool:
        return _parse(self.expires) > (now or _now())

    @property
    def owner(self) -> dict:
        return {"human_id": self.human_id, "signature": self.signature}

    def to_evidence(self) -> dict:
        ev = {"reason": self.reason, "expires": self.expires, "signed_by": list(self.signed_by)}
        if self.compensating_control:
            ev["compensating_control"] = self.compensating_control
        return ev

    def to_dict(self) -> dict:
        return {
            "gate": self.gate,
            "reason": self.reason,
            "expires": self.expires,
            "signed_by": self.signed_by,
            "human_id": self.human_id,
            "signature": self.signature,
            "compensating_control": self.compensating_control,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Override:
        return cls(
            gate=d["gate"],
            reason=d["reason"],
            expires=d["expires"],
            signed_by=list(d.get("signed_by", [])),
            human_id=d["human_id"],
            signature=d["signature"],
            compensating_control=d.get("compensating_control"),
        )


class OverrideStore:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else paths().ledger_dir / "overrides.json"

    def load(self) -> list[Override]:
        if not self.path.exists():
            return []
        return [Override.from_dict(d) for d in json.loads(self.path.read_text(encoding="utf-8"))]

    def save(self, overrides: list[Override]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps([o.to_dict() for o in overrides], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add(self, override: Override) -> None:
        self.save([*self.load(), override])

    def active(self, gate: str, now: datetime | None = None) -> Override | None:
        candidates = [o for o in self.load() if o.gate == gate and o.is_active(now)]
        return candidates[-1] if candidates else None
