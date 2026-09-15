# Never-delegate list (Intent)

The 3–7 privacy + AI-Act non-negotiables this organisation will **not** trade for speed or
convenience. This is the constitution the agents inherit. Keep it short, ranked, and signed.

> **How to use:** replace the examples below with your real commitments. Each must survive
> the test: *"we will lose time / revenue rather than compromise this."* Rank them — when two
> collide, the higher number wins. Every item needs an owner and at least one enforcing gate.
> Owned by the DPO. Changes are slow and deliberate (quarters), and signed.

---

## The list

1. **No personal data in logs, traces, or prompts.**
   - Enforced by: `spine/policies/no-pii-in-logs.rego`
   - Owner: <name> · Ranked: 1

2. **No processing without a declared lawful basis** (GDPR Art 6; Art 9 for special-category).
   - Enforced by: `spine/policies/lawful-basis-required.rego`
   - Owner: <name> · Ranked: 2

3. **No special-category data without explicit basis, stricter minimisation, and a DPIA.**
   - Enforced by: `spine/policies/special-category.rego` + auto-DPIA trigger
   - Owner: <name> · Ranked: 3

4. **No automated decision with legal/significant effect without a human-intervention path
   and a contestable explanation** (Art 22).
   - Enforced by: `spine/policies/automated-decision.rego`
   - Owner: <name> · Ranked: 4

5. **No personal data leaves its declared region without a valid transfer mechanism**
   (Chapter V).
   - Enforced by: `spine/policies/cross-border-transfer.rego`
   - Owner: <name> · Ranked: 5

6. **No personal data processed without appropriate security** — encryption in transit and
   at rest, access controls, and secrets kept out of source (GDPR Art 32).
   - Enforced by: `spine/policies/encryption-required.rego`
   - Owner: <name> · Ranked: 6

7. **No personal data kept beyond its declared retention window** (storage limitation,
   GDPR Art 5(1)(e)).
   - Enforced by: `spine/policies/storage-limitation.rego`
   - Owner: <name> · Ranked: 7

8. **No prohibited AI practice; no high-risk AI system ships without its baseline obligations**
   (EU AI Act Art 5; Art 9–15).
   - Enforced by: `spine/policies/ai-act-risk-tier.rego` + the AI Act Baseline agent
   - Owner: <name> · Ranked: 8

9. **No component accesses personal data outside its declared purpose or access boundary**
   (purpose limitation, GDPR Art 5(1)(b); data minimisation, Art 5(1)(c)).
   - Enforced by: `spine/policies/pii-access-boundary.rego`
   - Owner: <name> · Ranked: 9

10. **No model or AI change ships without validation, documentation, and a recorded change**
   (accountability; EU AI Act Art 11–12; model change control).
   - Enforced by: `spine/policies/model-governance.rego`
   - Owner: <name> · Ranked: 10

11. **Every consequential decision has a named human owner in Evidence.**
   - Enforced by: the ghost-decision detector (`evidence/`)
   - Owner: <name> · Ranked: 11

---

## Ranking rule
When two principles conflict, the **lower-numbered** one is satisfied first (strict priority,
not a weighting). Do not leave the ordering implicit — implicit ordering is decided by whoever
hits the conflict first, at the worst possible moment.

## Companion files
- `spine/lawful-basis.yaml` — declared purposes + lawful basis per data category.
- `spine/data-catalogue.yaml` — the personal-data inventory (categories, regions, retention).

_Signed:_ <DPO name>, <date>. _Version:_ v0.1 — seed.
