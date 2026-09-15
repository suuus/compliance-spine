# Getting started

How to go from the [README](./README.md) design to a running MVP. Read the README first —
this is the build path.

## Prerequisites
- An eval runner for ZAVA (pick one): DeepEval, promptfoo, Azure AI Evaluation, or MLflow.
- A policy engine for the gates (pick one): OPA/Rego, Conftest, or a small gate DSL.
- CI that can fail a build (GitHub Actions, etc.) and block a merge.
- Access to the coding-agent surface you're governing (e.g. GitHub Copilot App skills / MCP).
- A named human owner: **DPO / privacy engineer** who signs the spine. Nothing ships without one.

## How the pieces connect
```
Intent (never-delegate)  →  Structure (spine: policies + fail-closed gates)
        │                                   │
        │ agents inherit                    │ enforce
        ▼                                   ▼
Execution (4 agents on real code)  →  Evidence (hash-chained log + detector)
                                            ▲
                                    ZAVA proves the gates actually close
```
- **Fail-closed gates** enforce → **Evidence** records it (tamper-evident, traceable) →
  **ZAVA** proves the controls work. Build them in that dependency order.

## MVP build path (prove the loop on one repo, one data category)
1. **Intent** — fill in [`spine/intent/never-delegate.md`](./spine/intent/never-delegate.md)
   with 3–7 real non-negotiables. Start with one: *no personal data in logs*.
2. **Structure** — author one fail-closed gate: `spine/policies/no-pii-in-logs.rego`
   (see [GATE-AUTHORING](./spine/policies/GATE-AUTHORING.md)). Wire it into CI so it **blocks**.
3. **Evidence** — implement the writer against
   [`evidence/schema/decision-record.schema.json`](./evidence/schema/decision-record.schema.json):
   append-only, `prev_hash` chained. Emit an event on every gate decision.
4. **Detector** — flag one seeded change that touches personal data with no owner.
5. **ZAVA** — add one `zava/datasets/` gate-efficacy eval: seed the violation, assert the
   gate **closes** (see [ZAVA](./zava/ZAVA.md)).
6. **Human gate** — one review checkpoint on "new personal-data processing"
   (see [GOVERNANCE](./GOVERNANCE.md)).

When step 5 is green and step 4 flags the seeded ghost, the loop works. Everything else is
breadth (more controls, more evals, the AI Act baseline, more agents).

## Reuse what already exists
- **git-ape** → the gate / approval / drift-detection / evidence engine. Fastest path for
  steps 2–4.
- **ape-context** → generate `never-delegate.md` + `data-catalogue.yaml` from existing
  policies/DPAs.
- **isee-advisor** → the `diagnostics/` compliance-maturity check.

## Then, phase by phase
See README §11. Phase 2 = full GDPR control catalogue; Phase 3 = AI Act baseline agent;
Phase 4 = GitHub Copilot App skills + Canvas review gates + Work IQ context.

> **Not legal advice.** This assists + evidences compliance; a qualified human owns the
> sign-off. See README §13.
