#!/usr/bin/env bash
# End-to-end demo of the compliance spine's governed loop.
# Intent -> fail-closed gate -> human override -> Evidence -> integrity -> ghosts -> ZAVA.
set -euo pipefail
cd "$(dirname "$0")/.."

rm -f evidence/ledger/decisions.ledger.jsonl evidence/ledger/overrides.json

rule() { printf '\n\033[1m== %s ==\033[0m\n' "$1"; }

rule "1. Intent — the never-delegate list"
compliance-spine intent

rule "2. Structure serves Intent — every gate traces to a principle"
compliance-spine doctor

rule "3. Check a VIOLATION — PII in a log line (blocks, fail-closed)"
compliance-spine check examples/change-violation.json || true

rule "4. Check a CLEAN change (allowed)"
compliance-spine check examples/change-clean.json

rule "5. Human override — DPO + spine author co-sign, bounded window"
compliance-spine override examples/change-violation.json no-pii-in-logs \
  --reason "incident hotfix" \
  --signer spine_author:suzanne --signer dpo:jane \
  --signature sig-001 --days 3 \
  --compensating-control "log scrubber deployed"

rule "6. Re-check the violation — now silenced by the active override"
compliance-spine check examples/change-violation.json

rule "7. Evidence — the append-only decision trail"
compliance-spine evidence

rule "8. Integrity — verify the hash-chain (tamper-evident)"
compliance-spine verify

rule "9. Ghost-decision scan — any consequential decision without a named owner?"
compliance-spine ghosts

rule "10. ZAVA — prove the gate actually catches violations"
compliance-spine eval

rule "11. Coding-advisor — remediation guidance for the violation"
compliance-spine advise examples/change-violation.json

rule "12. AI feature — default to high-risk until assessed (Art 9-15 checklist)"
compliance-spine ai-act examples/change-ai.json || true

rule "13. Quality-reviewer — refuses to auto-approve a never-delegate escalation"
compliance-spine review examples/change-ai.json || true

rule "14. ISEE diagnostic — coverage across Intent / Structure / Execution / Evidence"
compliance-spine diagnose --no-evals
