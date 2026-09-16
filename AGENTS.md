# Working in this repo with Copilot

This repository is the **compliance spine** — an ISEE-based system that keeps agentic
software development GDPR- and EU AI Act-accountable *by construction*. When you (Copilot)
propose, review, or ship changes here, operate **inside** the spine.

> **Full GDPR + EU AI Act behavioural ruleset** (hard stops, per-area rules for coding,
> testing, and review): see [`.github/copilot-instructions.md`](.github/copilot-instructions.md).
> It applies to all Copilot work here. This file is the spine-workflow quick reference.

## The golden rule
Any change that touches **personal data, logging/telemetry, storage, cross-border data flow,
secrets, or an AI feature** must pass the spine's fail-closed check before it is considered
mergeable. Do not bypass a gate. If a gate **blocks** or **escalates**, surface it and the
required fix — never self-approve a never-delegate item; those need a named human (DPO).

## How to run it
The tools live in a venv. Either `source .venv/bin/activate` first, or call `.venv/bin/…`.
```bash
compliance-spine check CHANGE.json     # run the 10 fail-closed gates, emit Evidence
compliance-spine propose CHANGE.json   # advisory LLM metadata proposal + non-binding preview
compliance-spine advise CHANGE.json    # remediation guidance for a change
compliance-spine review CHANGE.json    # quality-reviewer verdict (+ Evidence)
compliance-spine ai-act CHANGE.json    # AI-Act risk tier + Art 9-15 checklist
compliance-spine eval                  # ZAVA: recall / false-positive-rate per gate
compliance-spine verify                # verify the tamper-evident Evidence hash-chain
compliance-spine scan-diff --staged    # code gates on the staged diff (used by the pre-commit hook)
compliance-spine llm-review CHANGE.json # gates (floor) + assessor (ceiling), union fail-closed
compliance-spine scorecard             # recall lift: gates only vs. gates + assessor
compliance-spine assess-eval           # ZAVA on the assessor: its own recall / precision
compliance-spine diagnose              # ISEE coverage (Intent/Structure/Execution/Evidence)
```
A **change** is a small JSON file (see `examples/`): `files` + a `metadata` block that
declares the compliance context. Gates fire on what a change declares and fail closed when
a required attestation is missing.

## Prefer the MCP tools
This repo ships an MCP server (`compliance-spine-mcp`, registered as `compliance-spine`).
Prefer its tools over shelling out: `check_change`, `advise`, `recommend_tests`, `review`,
`classify_ai_act_risk`, `verify_ledger`, `scan_ghosts`, `run_evals`, `list_intent`.

## Callable agents (Copilot App / `/agent`)
This repo defines five selectable agents in `.github/agents/` — pick them with `/agent`:
**Compliance Spine** (the front door; routes to the rest), **Compliance Reviewer**,
**Compliance Advisor**, **AI Act Baseline**, and **Compliance Test Author**. Each runs the
spine and never self-approves a never-delegate item.

## Confidentiality (hard rule)
This spine was built for a specific customer in a regulated domain. **Nothing about that
customer or domain may appear in any file** — code, docs, tests, examples, or commit
messages. Keep everything generic (article references + generic categories only). The
leak-guard (`ci/leak_scan.py`) enforces this in pre-commit and CI; keep it green.

## Definition of done for any change
- `ruff check .` clean · `pytest` green · `python ci/leak_scan.py .` clean.
- New or changed gate ⇒ add ZAVA cases under `zava/datasets/` (including adversarial ones);
  `compliance-spine eval` must stay at recall 1.00 / FPR 0.00.
- New gate ⇒ it must trace to a never-delegate principle (`compliance-spine doctor` green).

## Boundaries
Not legal advice. The spine assists and evidences compliance; a qualified human owns the
sign-off. See `README.md` §13.
