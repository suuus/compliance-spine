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

## Scaffold your policy folder
```bash
compliance-spine init          # writes a working spine/ + evidence/schema into the repo
compliance-spine doctor        # confirm every gate traces to a principle (passes out of the box)
```
`init` writes a *functional* starter you then tune (owners/signatures, your field names, your
components) — see **Make it yours** below. It never overwrites tuned files without `--force`.

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
compliance-spine init              # scaffold a starter spine/ into a repo (run this first)
compliance-spine intent            # the never-delegate list (Intent)
compliance-spine doctor            # every gate traces to a principle (Structure -> Intent)
compliance-spine check CHANGE.json # run the fail-closed gates, emit Evidence
compliance-spine propose CHANGE.json   # advisory LLM metadata proposal + non-binding preview
compliance-spine advise CHANGE.json    # coding-advisor: remediation guidance
compliance-spine tests  CHANGE.json    # test-author: recommended compliance tests
compliance-spine review CHANGE.json    # quality-reviewer: verdict (+ Evidence)
compliance-spine ai-act CHANGE.json    # ai-act-baseline: risk tier + Art 9-15 checklist
compliance-spine override CHANGE.json GATE --reason R \
    --signer spine_author:you --signer dpo:them --signature SIG   # human-in-the-loop
compliance-spine evidence          # recent Evidence records (--detail shows each finding's file:line)
compliance-spine verify            # verify the hash-chain (tamper detection)
compliance-spine ghosts            # decisions with no named human owner
compliance-spine eval              # ZAVA: recall / false-positive-rate per gate
compliance-spine diagnose          # ISEE coverage & maturity
compliance-spine matrix            # compliance matrix: article -> gate -> coverage status
compliance-spine frameworks        # regulatory framework packs (GDPR, EU AI Act) + coverage
compliance-spine governance        # owners, overrides, ledger, ghosts
compliance-spine export CHANGE_ID --out bundle.json   # audit / DSAR bundle
compliance-spine scan-diff --staged                   # code gates on the staged diff
compliance-spine llm-review --base origin/main        # floor (gates) ∪ ceiling (assessor) on a diff
compliance-spine scorecard                            # recall lift vs. gates-only
compliance-spine assess-eval                          # ZAVA on the assessor: its own recall / precision
compliance-spine record-finding --kind K --message "..." --file f --line N   # reasoned finding -> ledger evt_*
compliance-spine adjudicate FINDING_ID --outcome confirmed --human you --signature s
compliance-spine learn                                # findings: confirmed / dismissed / pending
```
A **change** is a small JSON file — see [`examples/`](./examples). `metadata` declares the
compliance context (data category, lawful basis, retention, transfers, AI feature, ...);
the gates fire on what a change declares and fail closed when a required attestation is
missing.

> For the full command-by-command flow — assess a repo, run the floor + LLM ceiling, and collect
> auditable evidence — see [docs/ASSESSING.md](./docs/ASSESSING.md).

## MCP (for the GitHub Copilot App / any MCP client)
```bash
compliance-spine-mcp        # stdio transport; tools: check_change, advise, review,
                            # recommend_tests, classify_ai_act_risk, verify_ledger,
                            # scan_ghosts, run_evals, record_finding, list_intent
```
The MCP server needs the **`[mcp]` extra** (`pip install "compliance-spine[mcp]"`) — without it
`compliance-spine-mcp` exits with "MCP SDK not installed" and the server silently won't load.
In your `.mcp.json`, point `command` at a **resolvable** `compliance-spine-mcp` (an absolute path,
or ensure the venv is on `PATH`). The `[mcp]` dependency tree (mcp / starlette) can clash with an
app's own web deps, so for an app you're governing, consider installing the spine tooling in a
**dedicated venv** (or via `pipx`) rather than the app's runtime environment.

## Enforce on every commit
Instructions (`.github/copilot-instructions.md`) tell Copilot what to do; this makes it
*enforced*. Install the hook so the code-scanning gates run on every commit:
```bash
pip install pre-commit && pre-commit install
```
A commit that logs personal data, hardcodes a secret, or reads PII from a restricted
component is now blocked locally. CI runs the same check on the PR diff against its base
branch (`compliance-spine scan-diff --base origin/<base>`).

## Make it smarter (optional LLM layer)
The deterministic gates are the fail-closed **floor**. An LLM adds a **ceiling** — a layered
reviewer that reads the code and the docs and catches the long tail the fixed rules miss. The
union is fail-closed: the assessor can *raise* the verdict (add a block/escalate) but never
*clear* a gate's block, and a human owns the judgment calls. See
[docs/LLM-LAYER.md](./docs/LLM-LAYER.md): `llm-review` runs floor ∪ ceiling, `scorecard` proves
the recall lift, `assess-eval` measures the assessor itself, `propose` drafts change metadata for
a human to confirm, and `adjudicate` / `learn` turn confirmed findings into new gates. It runs on
your own Copilot model, with an optional headless **GitHub Models / Azure AI Foundry** detector
for unattended CI or an independent reviewer.

## What's implemented
- **17 fail-closed gates** — *data governance:* no-PII-in-logs, lawful basis, special category,
  retention, cross-border transfer, encryption/secrets, automated decision (Art 22), AI-Act risk
  tier, PII access-boundary, model-governance, consent-default; *security & hygiene (code-scanning):*
  weak-password-hash, insecure-transport, permissive-cors, pii-in-url, error-leakage,
  secret-file-committed.
- **Evidence** — schema-validated, hash-chained ledger + ghost-decision detector.
- **4 agents** — coding-advisor, test-author, quality-reviewer, ai-act-baseline.
- **ZAVA** — 161-case suite (native + DeepEval), recall 1.00 / FPR 0.00, per-gate.
- **LLM layer** — a layered reviewer (deterministic gates as the fail-closed floor ∪ a pluggable
  assessor as the ceiling), a recall scorecard, an assessor eval (`assess-eval`), metadata
  propose/confirm, and a learning loop (`adjudicate` / `learn`) that turns confirmed findings
  into new rules.
- **Callable Copilot agents** — the four agents + a Compliance Spine orchestrator as `/agent`
  entries (`.github/agents/`).
- **Installable skill** — `.github/skills/gdpr-ai-act-compliance/` packages the GDPR + EU AI Act
  guidance as a Copilot skill that also tells the agent to run the spine when present.
- **Copilot app canvas** — `.github/extensions/compliance-dashboard/` renders the evidence feed,
  adjudication queue, compliance matrix, and ghosts in the app side panel (open it with
  *"Open the Compliance Dashboard canvas"*); adjudications write through the CLI.
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
