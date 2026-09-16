# Assessing a repo + collecting evidence

A practical, command-by-command guide to running the spine against a repository and producing
an auditable trail. Pair it with [PILOT.md](./PILOT.md) (how to stand up a pilot) and
[LLM-LAYER.md](./LLM-LAYER.md) (the floor/ceiling model).

> **Mental model:** `scan-diff` = the gate (fast, blocks, no record) · `llm-review` / `check` /
> `review` / `ai-act` = the assessors that **produce evidence** · `evidence` / `verify` / `export`
> = the audit trail · `adjudicate` / `override` = the human decisions.

## 0. One-time setup (per repo)
```bash
cd yourrepo
python3 -m venv .venv && source .venv/bin/activate
pip install "compliance-spine[mcp] @ git+https://github.com/suuus/compliance-spine"
compliance-spine init                     # scaffolds spine/ + evidence/schema
# tune spine/data-catalogue.yaml, spine/access-boundaries.yaml, spine/intent/never-delegate.md
export COMPLIANCE_SPINE_ROOT="$(pwd)"     # only needed if the repo has no pyproject.toml
```

## 1. Confirm the policy is sound
```bash
compliance-spine doctor          # every gate traces to a signed principle
compliance-spine frameworks      # which packs are active (GDPR, EU AI Act)
compliance-spine matrix          # regulation -> article -> gate -> coverage (regulator-facing)
```

## 2. Assess the repo — deterministic floor (fast, fail-closed, no evidence)
```bash
EMPTY=$(git hash-object -t tree /dev/null)
compliance-spine scan-diff --base "$EMPTY"        # whole repo
compliance-spine scan-diff --base origin/main     # a branch / PR delta
compliance-spine scan-diff --staged               # what's staged (pre-commit)
```

## 3. Assess the repo — LLM ceiling (**this records evidence**)
```bash
compliance-spine llm-review --base "$EMPTY"       # floor ∪ assessor over the whole repo
compliance-spine llm-review --base origin/main    # over a PR delta
```
Each advisory finding prints an evidence id, e.g. `pii-in-response [flag] conf=0.55 … [evt_1b03…]`.

## 4. LLM-agent assessment via Copilot
Open a Copilot session in the repo and invoke the callable agents:
```
/agent compliance-spine        → "Assess this repo for GDPR + EU AI Act risk; cite files/lines."
/agent compliance-reviewer     → "Review the diff against origin/main for a merge verdict."
/agent ai-act-baseline         → "Classify the risk engine under the EU AI Act."
/agent compliance-advisor      → "How do I fix the PII-in-logs findings safely?"
```
Or call the MCP tools directly: `check_change`, `review`, `classify_ai_act_risk`, `scan_ghosts`,
`verify_ledger`, `run_evals`, `recommend_tests`, `advise`, `record_finding`, `list_intent`.

**Give each reasoned finding its own ledger id.** The offline assessor's findings already get
individual `evt_*` ids via `llm-review`. When *you* (or an agent) assess with reasoning, record
each finding so it is individually adjudicable instead of a report-only `ND-*` label:
```bash
compliance-spine record-finding --kind automated-decision \
    --message "risk engine auto-declines with no human path (Art 22)" \
    --file risk-service/src/services/riskCalculationService.js --line 116 \
    --confidence 0.8 --severity high --change my-assessment
# -> recorded evt_2dee7325 … then: compliance-spine adjudicate evt_2dee7325 --outcome …
```
(The `compliance-reviewer` agent does this automatically and cites the `evt_*` id.)

## 5. Deep, per-change assessment (a declared change → **records evidence**)
Write a `change.json` (see [`examples/`](../examples)) — the files plus a `metadata` block declaring
`data_category`, `lawful_basis`, `retention_days`, `transfers`, `ai_feature`, `encryption`, …
```bash
compliance-spine check    change.json           # run the gates, record Evidence
compliance-spine review   change.json           # quality-reviewer verdict, record Evidence
compliance-spine ai-act   change.json           # AI Act risk tier + Art 9–15 checklist, record Evidence
compliance-spine advise   change.json           # remediation guidance (advisory)
compliance-spine tests    change.json --emit-stubs   # compliance test scaffolds
```

## 6. Collect + verify the evidence
```bash
compliance-spine evidence --detail            # records + the findings (file:line: message) behind each
compliance-spine verify                       # hash-chain integrity (tamper check)
compliance-spine export <CHANGE_ID> --out bundle.json   # audit / DSAR bundle for one change
compliance-spine governance                   # owners, active overrides, ghosts, ledger status
compliance-spine ghosts                       # decisions with no named human owner
```
Every record carries the **findings that produced it** — `{file, line, message}` — so a decision is
traceable to source. The ledger lives at `evidence/ledger/` (keep it out of git; the scaffold
gitignores it).

## 7. Adjudicate ceiling findings (human-in-the-loop + learning)
Take an `evt_…` id from step 3/4 (`llm-review` findings, or a `record-finding` you logged):
```bash
compliance-spine adjudicate <FINDING_ID> --outcome confirmed \
    --human "Jordan Lee (DPO)" --signature <sig> --reason "real Art 22 gap"
compliance-spine adjudicate <FINDING_ID> --outcome dismissed \
    --human "you" --signature <sig> --reason "first-party call, not a transfer"
compliance-spine learn                        # confirmed / dismissed / pending
```

## 8. Grant a bounded exception (override a blocking gate)
```bash
compliance-spine override change.json <gate> \
  --reason "legacy path, remediation ticket JIRA-123" \
  --signer spine_author:you --signer dpo:jlee --signature <sig> \
  --days 30 --compensating-control "field-level encryption in place"
```

## 9. Prove the controls actually work
```bash
compliance-spine eval        # ZAVA: recall / false-positive-rate per gate
compliance-spine scorecard   # recall lift of ceiling vs. gates-only
compliance-spine diagnose    # ISEE coverage & maturity
```

## Recurring enforcement
- **Pre-commit:** `scan-diff --staged` blocks violations at commit time.
- **CI (`.github/workflows/compliance-gate.yml`):** floor `scan-diff` blocks the PR; ceiling
  `llm-review` advises — on every PR.

---

> **Not legal advice.** The spine assists and *evidences* compliance; a qualified human (DPO/legal)
> owns the sign-off.
