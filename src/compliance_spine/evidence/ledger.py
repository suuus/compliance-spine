"""Hash-chained, append-only Evidence ledger.

Every consequential decision is appended as one JSON line. Each record's ``prev_hash``
is the content hash of the record before it (genesis = 64 zeroes), so any edit, deletion,
or reordering breaks the chain and is detected by :meth:`verify`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from compliance_spine.config import paths
from compliance_spine.evidence.record import (
    GENESIS_PREV,
    DecisionRecord,
    record_hash,
)


@dataclass
class VerifyResult:
    ok: bool
    count: int
    errors: list[str]


class Ledger:
    """Append-only JSONL ledger of decision records."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else paths().ledger_file

    # -- reading -----------------------------------------------------------
    def read_all(self) -> list[dict]:
        if not self.path.exists():
            return []
        records: list[dict] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                records.append(json.loads(line))
        return records

    def last_hash(self) -> str:
        records = self.read_all()
        return record_hash(records[-1]) if records else GENESIS_PREV

    # -- writing -----------------------------------------------------------
    def append(self, record: DecisionRecord) -> dict:
        """Chain, validate against the schema, and append. Returns the stored dict."""
        record.prev_hash = self.last_hash()
        record.validate()
        stored = record.to_dict()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(stored, sort_keys=True, ensure_ascii=False) + "\n")
        return stored

    # -- integrity ---------------------------------------------------------
    def verify(self) -> VerifyResult:
        records = self.read_all()
        errors: list[str] = []
        prev = GENESIS_PREV
        for i, rec in enumerate(records):
            if rec.get("prev_hash") != prev:
                errors.append(
                    f"record {i} ({rec.get('id', '?')}): broken chain — "
                    f"prev_hash {rec.get('prev_hash', '')[:12]}… != expected {prev[:12]}…"
                )
            try:
                DecisionRecord(  # schema re-validation of stored content
                    action=rec["action"],
                    rule_id=rec["rule_id"],
                    intent_ref=rec["intent_ref"],
                    severity=rec["severity"],
                    inputs_hash=rec["inputs_hash"],
                    actor=rec["actor"],
                    subject=rec.get("subject", {}),
                    id=rec["id"],
                    ts=rec["ts"],
                    owner=rec.get("owner"),
                    override=rec.get("override"),
                    outputs_hash=rec.get("outputs_hash"),
                    artifacts=rec.get("artifacts"),
                    spine_version=rec.get("spine_version"),
                    prev_hash=rec["prev_hash"],
                ).validate()
            except Exception as exc:  # noqa: BLE001
                errors.append(f"record {i} ({rec.get('id', '?')}): invalid — {exc}")
            prev = record_hash(rec)
        return VerifyResult(ok=not errors, count=len(records), errors=errors)
