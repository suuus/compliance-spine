# Evidence — the mechanism

Evidence is generated *by construction* (as a by-product of execution), append-only,
tamper-evident, and traceable. This doc is how you build and read it. See README §5 for the
design rationale.

## Components
```
evidence/
  schema/decision-record.schema.json   # the record contract (validate every event)
  log/                                 # append-only, hash-chained event log (jsonl)
  artifacts/                           # generated: ropa/, dpia/, annexIV/, logs/
  writer/                              # appends events; computes prev_hash; signs
  detector/                            # the ghost-decision detector
  surface/                             # queryable, hierarchical read API
```

## The writer (audit by construction)
- Every gate decision and every agent finding calls the writer with a record that validates
  against `schema/decision-record.schema.json`.
- The writer:
  1. sets `prev_hash` = hash of the previous record (genesis = all-zeroes) → **hash chain**;
  2. computes `inputs_hash` / `outputs_hash` over what was evaluated/produced;
  3. requires `owner.signature` when the record is a gated/human decision;
  4. appends (never updates or deletes) to `log/` as one JSON object per line.
- Tampering with any past record breaks the chain from that point → detectable.

## Evidence contract
Each agent + gate declares what it must emit, when, and in what shape (its section in the
schema). A signal that *should* have been emitted but wasn't is a **ghost signal** — the
detector finds it by comparing the contract to the log.

## The ghost-decision detector
Runs on the log + the change set. Flags a **ghost decision** when a compliance-relevant
change shipped with **no owner**, e.g.:
- a new personal-data field/sink with no Privacy-Guidance event;
- a gate that was `override`n with no valid silencing;
- a DSAR-relevant change with no Compliance-Testing event;
- an AI feature with no AI-Act classification.
Output: a flagged item on the Evidence surface (and, if `critical`, a gate input).
**Measured by recall** (a missed ghost is the failure that matters) — see ZAVA.

## The surface (reader-of-record)
- Hierarchical: per-change → per-cell → org. Readable at each altitude without the ones below.
- The **DPO** reads it. Provide: "show every decision on this data category", "every override
  and its expiry", "every unowned decision this week", "produce the RoPA / DPIA / Annex IV".
- Audit-readiness target: those artifacts are produced **on demand**, not reconstructed weeks
  later.

## Versioning & hygiene
- **Version Evidence alongside the spine** — record which policy version was in force, so you
  can reconstruct *why* a decision was allowed at the time.
- Evidence is itself sensitive: minimise (no raw personal data — store hashes/refs), secure,
  and retain per policy.

## Build order (MVP)
1. Validate + append with `prev_hash` (the chain).
2. Emit on the one fail-closed gate.
3. Detector: flag one seeded unowned change.
4. Surface: a simple query over `log/`.
Then add artifact generation (RoPA/DPIA/Annex IV) in later phases.
