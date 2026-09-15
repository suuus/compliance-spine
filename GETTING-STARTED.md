# Getting started

This is the **running implementation** of the [README](./README.md) design: an installable
Python package (`compliance_spine`) with a CLI, an MCP server, and a ZAVA eval suite.

## Prerequisites
- Python 3.11+ and `pip`.
- CI that can fail a build and block a merge (a GitHub Actions workflow is included).
- A named human owner — **DPO / privacy engineer** — who signs the spine (`spine/intent/`).
- Optional: the coding-agent surface you're governing (GitHub Copilot App / MCP client).

## Install
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,zava,mcp]"     # core + tests + DeepEval + MCP server
```
Core install (`pip install -e .`) needs only `pyyaml` + `jsonschema`; DeepEval and the MCP
SDK are optional extras. ZAVA also has a native runner, so the eval suite works without
DeepEval.

## See the whole loop in 30 seconds
```bash
./scripts/demo.sh
```
This runs Intent → a fail-closed block → a clean allow → a co-signed human override →
the Evidence trail → hash-chain verification → the ghost scan → ZAVA.

## How the pieces connect
```
Intent (never-delegate)  →  Structure (fail-closed gates)
        │                                   │
        │ agents inherit                    │ enforce
        ▼                                   ▼
Execution (4 agents on real code)  →  Evidence (hash-chained log + detector)
                                            ▲
                                    ZAVA proves the gates actually close
```

## The CLI
```bash
compliance-spine intent            # the never-delegate list (Intent)
compliance-spine doctor            # every gate traces to a principle (Structure -> Intent)
compliance-spine check CHANGE.json # run the fail-closed gates, emit Evidence
compliance-spine advise CHANGE.json    # coding-advisor: remediation guidance
compliance-spine tests  CHANGE.json    # test-author: recommended compliance tests
compliance-spine review CHANGE.json    # quality-reviewer: verdict (+ Evidence)
compliance-spine ai-act CHANGE.json    # ai-act-baseline: risk tier + Art 9-15 checklist
compliance-spine override CHANGE.json GATE --reason R \
    --signer spine_author:you --signer dpo:them --signature SIG   # human-in-the-loop
compliance-spine evidence          # recent Evidence records
compliance-spine verify            # verify the hash-chain (tamper detection)
compliance-spine ghosts            # decisions with no named human owner
compliance-spine eval              # ZAVA: recall / false-positive-rate per gate
compliance-spine diagnose          # ISEE coverage & maturity
compliance-spine governance        # owners, overrides, ledger, ghosts
compliance-spine export CHANGE_ID --out bundle.json   # audit / DSAR bundle
compliance-spine scan-diff --staged                   # code gates on the staged diff
```
A **change** is a small JSON file — see [`examples/`](./examples). `metadata` declares the
compliance context (data category, lawful basis, retention, transfers, AI feature, ...);
the gates fire on what a change declares and fail closed when a required attestation is
missing.

## MCP (for the GitHub Copilot App / any MCP client)
```bash
compliance-spine-mcp        # stdio transport; tools: check_change, advise, review,
                            # recommend_tests, classify_ai_act_risk, verify_ledger,
                            # scan_ghosts, run_evals, list_intent
```

## Enforce on every commit
Instructions (`.github/copilot-instructions.md`) tell Copilot what to do; this makes it
*enforced*. Install the hook so the code-scanning gates run on every commit:
```bash
pip install pre-commit && pre-commit install
```
A commit that logs personal data, hardcodes a secret, or reads PII from a restricted
component is now blocked locally. CI runs the same check on the PR diff against its base
branch (`compliance-spine scan-diff --base origin/<base>`).

## What's implemented
- **9 fail-closed gates** — no-PII-in-logs, lawful basis, special category, retention,
  cross-border transfer, encryption/secrets, automated decision (Art 22), AI-Act risk tier,
  PII access-boundary (purpose limitation).
- **Evidence** — schema-validated, hash-chained ledger + ghost-decision detector.
- **4 agents** — coding-advisor, test-author, quality-reviewer, ai-act-baseline.
- **ZAVA** — 89-case suite (native + DeepEval), recall 1.00 / FPR 0.00, per-gate.
- **Confidentiality leak-guard** — hashed denylist; runs in pre-commit and CI.

## Make it yours
1. Edit [`spine/intent/never-delegate.md`](./spine/intent/never-delegate.md) — assign real
   owners and signatures.
2. Tune [`spine/gates/gate-config.yaml`](./spine/gates/gate-config.yaml) — severities,
   silence policy, circuit-breaker behaviour.
3. Add ZAVA cases under [`zava/datasets/`](./zava/datasets) for your own edge cases.

## Reuse
- **git-ape** -> gate / approval / drift-detection / evidence patterns.
- **ape-context** -> generate `never-delegate.md` from existing policies/DPAs.
- **isee-advisor** -> the `diagnose` maturity idea.

> **Not legal advice.** This assists and evidences compliance; a qualified human owns the
> sign-off. See README §13.
