# MCP server — the spine as a tool

Expose the spine over MCP so any coding-agent surface (GitHub Copilot App, IDE agents, CI)
can call it. The MCP server is how Execution reaches Structure + Evidence.

## Tools

### `get_spine_context`
Return the constraints an agent must respect for a change. Read-only.
- **in:** `{ change_ref, paths[] }`
- **out:** `{ never_delegate[], data_categories[], active_policies[], region }`
- Use: the Privacy-Guidance agent calls this to inject constraints before code is written.

### `check_change`
Evaluate a change against the spine gates. The core enforcement call.
- **in:** `{ change_ref, diff, context }`
- **out:**
  ```json
  {
    "decision": "allow | block | escalate",
    "violations": [
      { "rule_id": "spine/policies/no-pii-in-logs", "intent_ref": "...",
        "severity": "critical", "evidence_id": "evt_...", "detail": "..." }
    ],
    "fail_closed": true          // true when blocked because compliance could not be proven
  }
  ```
- **Fail-closed:** if analysis is incomplete, returns `block` — never `allow` by default.

### `classify_ai_risk`
Run the AI Act Baseline classifier.
- **in:** `{ feature_description, model_usage, decision_effect }`
- **out:** `{ tier: "prohibited|high|limited|minimal", role: "provider|deployer",
  obligations[], artifacts_needed[], default_caution_applied: bool }`

### `emit_evidence`
Append an Evidence record (validated + hash-chained).
- **in:** a record matching `evidence/schema/decision-record.schema.json`
- **out:** `{ evidence_id, prev_hash, chain_ok: true }`
- The server computes `prev_hash`, validates the schema, and requires `owner.signature` for
  gated/override actions.

### `run_evals` (optional)
Trigger a ZAVA eval set and return the scorecard.
- **in:** `{ eval_ids[] | "all" }`
- **out:** `{ results[], regressions[], gate_action: "close|none" }`

## Contract rules
- Every mutating decision (`check_change` block, `classify_ai_risk`, `emit_evidence`) writes
  Evidence — no silent decisions.
- `check_change` and `emit_evidence` are the load-bearing calls; build them first.
- Keep the server stateless about *content* — it reads the spine, writes Evidence, and
  returns decisions; it does not hold personal data.

## Wiring
- **GitHub Copilot App:** register as an MCP server; the four agents call these tools; use
  Canvas as the human review-gate surface (README §7).
- **CI:** call `check_change` on every PR; a `block` fails the build.
