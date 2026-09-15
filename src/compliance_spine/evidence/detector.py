"""Ghost-decision detector — enforces never-delegate principle #9: *every consequential
decision has a named human owner in Evidence*.

A "ghost decision" is a consequential action that reached the ledger without a human owner
(an override or halt, or an allow attributed to a human but unsigned), or a change that
proceeded with no Evidence record at all.
"""

from __future__ import annotations

from dataclasses import dataclass

# Actions that require a named human owner to be legitimate.
OWNER_REQUIRED_ACTIONS = frozenset({"override", "halt"})


@dataclass(frozen=True)
class GhostFinding:
    record_id: str
    action: str
    reason: str

    def render(self) -> str:
        return f"{self.record_id} ({self.action}): {self.reason}"


def _needs_owner(record: dict) -> bool:
    action = record.get("action")
    actor = record.get("actor", {}) or {}
    if action in OWNER_REQUIRED_ACTIONS:
        return True
    return action == "allow" and actor.get("type") == "human"


def detect_ghosts(records: list[dict]) -> list[GhostFinding]:
    findings: list[GhostFinding] = []
    for rec in records:
        if _needs_owner(rec) and not rec.get("owner"):
            findings.append(
                GhostFinding(
                    rec.get("id", "?"),
                    rec.get("action", "?"),
                    "consequential decision without a named human owner in Evidence",
                )
            )
    return findings


def detect_undocumented(proceeded_change_ids: list[str], records: list[dict]) -> list[GhostFinding]:
    documented = {(r.get("subject") or {}).get("change") for r in records}
    return [
        GhostFinding("-", "proceed", f"change '{cid}' proceeded with no Evidence record")
        for cid in proceeded_change_ids
        if cid not in documented
    ]


def scan(ledger) -> list[GhostFinding]:
    """Scan a Ledger for ghost decisions."""
    return detect_ghosts(ledger.read_all())
