"""Governance operations — the DPO-facing surface.

- :func:`export_change` builds an audit / DSAR bundle: every Evidence record for a change.
- :func:`governance_report` surfaces governance gaps: unassigned Intent owners, active and
  soon-to-expire overrides, ledger integrity, and any ghost decisions.
"""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

from compliance_spine.evidence.detector import scan
from compliance_spine.evidence.ledger import Ledger
from compliance_spine.intent import IntentRegistry
from compliance_spine.overrides import OverrideStore, _now, _parse


def export_change(
    change_id: str, out: str | Path | None = None, ledger: Ledger | None = None
) -> dict:
    """Return (and optionally write) all Evidence records for a change."""
    led = ledger if ledger is not None else Ledger()
    records = [r for r in led.read_all() if (r.get("subject") or {}).get("change") == change_id]
    bundle = {"change": change_id, "count": len(records), "records": records}
    if out is not None:
        Path(out).write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")
    return bundle


def governance_report(
    store: OverrideStore | None = None,
    ledger: Ledger | None = None,
    expiring_within_days: int = 3,
) -> dict:
    registry = IntentRegistry.load()
    unassigned = [r.slug for r in registry.rules if not r.owner]

    store = store if store is not None else OverrideStore()
    active = [o for o in store.load() if o.is_active()]
    soon = _now() + timedelta(days=expiring_within_days)
    expiring = [o.gate for o in active if _parse(o.expires) < soon]

    led = ledger if ledger is not None else Ledger()
    verify = led.verify()
    ghosts = scan(led)

    return {
        "intent_owners_unassigned": unassigned,
        "active_overrides": [
            {"gate": o.gate, "expires": o.expires, "signed_by": o.signed_by} for o in active
        ],
        "expiring_overrides": expiring,
        "ledger_ok": verify.ok,
        "ledger_count": verify.count,
        "ghosts": [g.render() for g in ghosts],
    }
