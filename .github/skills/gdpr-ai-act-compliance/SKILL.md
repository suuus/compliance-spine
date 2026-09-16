---
name: gdpr-ai-act-compliance
description: "Keep code GDPR- and EU AI Act-compliant by default, and — when the compliance-spine engine is present — enforce it rather than trust judgment. Use when writing, reviewing, or refactoring anything that touches personal data (logging, storage, APIs, auth, transfers, analytics, error handling) or adds an AI/ML feature. Triggers: 'GDPR', 'personal data', 'PII', 'privacy', 'retention', 'consent', 'lawful basis', 'DSAR', 'EU AI Act', 'high-risk AI', 'data protection', 'is this compliant'. Pairs with the compliance-spine gates, evidence ledger, and ZAVA evals."
---

# GDPR & EU AI Act compliance

Actionable engineering reference for GDPR **and** the EU AI Act. Two layers:

1. **Advice (this skill)** — the rules to follow while writing and reviewing code.
2. **Enforcement (the [compliance-spine](https://github.com/suuus/compliance-spine))** — fail-closed
   gates, a tamper-evident evidence ledger, and ZAVA proof. **If the spine is present in the repo,
   run it and act on its verdict — do not rely on your own judgment.** Instructions set intent; the
   spine disposes and records the decision.

> **Golden rule:** Collect less. Store less. Expose less. Retain less. And never self-approve a
> *never-delegate* item — those need a named human (DPO / privacy owner).

## Run the spine first (when present)

```bash
compliance-spine check change.json     # the fail-closed gates + evidence
compliance-spine scan-diff --staged    # code gates on the staged diff (pre-commit / CI)
compliance-spine llm-review change.json # gates (floor) ∪ your model (ceiling), fail-closed
compliance-spine advise | review        # GDPR-aware coding guidance / diff review
```
Or, in the Copilot app, call the agents: `/agent Compliance Reviewer` (or *Advisor / Test Author /
AI Act Baseline*), or the `compliance-spine` MCP tools (`check_change`, `review`,
`classify_ai_act_risk`). The LLM proposes and assesses; the gates dispose; a human owns the calls.

## Hard stops — never do these

- Personal data in logs, traces, error messages, telemetry, analytics, or model prompts.
- Hardcoded secrets/keys/tokens, or committing secret files (`.env`, `*.pem`, `*.key`, `*.pfx`,
  `*.p12`, `id_rsa`, `secrets/`). Use a KMS / secrets manager.
- Real or production personal data in prompts, examples, tests, or fixtures — use synthetic data.
- Processing personal data with no declared lawful basis (Art 6; an Art 9(2) condition for
  special-category).
- Storing personal data without a retention limit and a real erasure path.
- Moving personal data outside its region without a valid transfer mechanism (Chapter V).
- A solely-automated decision with legal/significant effect without a human path + explanation (Art 22).
- Weakening, disabling, or silencing a compliance gate, test, or redaction to make a build pass.

## Establish the data context before coding

State it; if you can't answer, ask — don't assume:
- Does this touch personal data? Category: none / personal / special (Art 9)?
- Lawful basis and purpose? Stored → retention + erasure path? Crosses a region → transfer mechanism?
- Is there an AI feature? Its EU AI Act risk tier? (If unassessed, treat as **high-risk**.)

## Rules by area

**Data minimisation (Art 5(1)(c)).** Collect and store the minimum; no `SELECT *` on personal-data
tables. Don't log request/response bodies or user objects — log a non-personal correlation id.

**Purpose limitation (Art 5(1)(b)).** Data collected for purpose A must not be reused for purpose B
without a new basis. Keep analytics/reporting/logging/marketing components away from raw personal data.

**Storage limitation (Art 5(1)(e), Art 17).** Set the TTL at schema-design time, compute
`retention_expires_at` at insert, enforce it with an automated job. Real deletion/anonymisation, not
just soft-delete. Sensible defaults:

| Data | Max retention |
|---|---|
| Auth / audit logs | 12–24 months |
| Session / refresh tokens | 30–90 days |
| Email / notification logs | 6 months |
| Inactive accounts | 12 months after last login → notify → delete |
| Payment records | as tax law requires (7–10 years), minimised |
| Analytics events | 13 months |

**Consent & privacy by default (Art 6/7/25).** Optional data collection (analytics, telemetry,
tracking) is **off by default and opt-in**. Consent must be specific, freely given, and withdrawable.

**Security (Art 32).** Encrypt at rest and in transit. **Passwords:** Argon2id or bcrypt (cost ≥ 12)
with a unique salt — never MD5, SHA-1, or bare SHA-256. **Transport:** TLS 1.2+, no disabled cert
verification (`verify=False`, `rejectUnauthorized: false`), no TLS 1.0/1.1.

**API design & error handling (Art 5(1)(f), 25, 32).** No personal data in URL paths or query
parameters. Opaque UUIDs, not sequential ids. Ownership checks on every resource. No
`Access-Control-Allow-Origin: *` on authenticated APIs. Return RFC 7807 problem details — never stack
traces, internal paths, DB errors, or PII; log detail server-side against a correlation id.

**Anonymisation vs pseudonymisation.** Anonymisation is irreversible → out of scope; use it for
records retained after erasure. Pseudonymisation is reversible → still personal data; keep the key in
a KMS, separate from the data.

**Data subject rights (Art 15–22).** Design for access, rectification, erasure, portability, and
objection from the start — findable and deletable by subject id.

## EU AI Act — when a change adds or uses an AI feature

- Classify the risk tier; if unassessed, treat as **high-risk until proven otherwise**.
- **Prohibited (Art 5):** stop and escalate.
- **High-risk (Art 9–15):** risk management, data governance, technical documentation,
  logging/traceability, transparency to deployers, human oversight, accuracy/robustness/security.
- **Limited-risk (Art 50):** disclose that a person is interacting with AI or AI-generated content.
- Never present model output as a decision without the human oversight the tier requires.

## What the spine mechanically enforces (the floor)

Ten data-governance + seven security/hygiene fail-closed gates, each mapped to a never-delegate
principle and covered by ZAVA:

| Gate | Rule |
|---|---|
| no-pii-in-logs · lawful-basis-required · special-category | Art 5, 6, 9 |
| retention-ttl · cross-border-transfer · encryption-required | Art 5(1)(e), Ch V, 32 |
| automated-decision · pii-access-boundary | Art 22, 5(1)(b) |
| ai-act-risk-tier · model-governance | EU AI Act Art 5–15, 11–12 |
| consent-default | Art 25(2) — opt-in only |
| weak-password-hash · insecure-transport · permissive-cors | Art 32 |
| pii-in-url · error-leakage · secret-file-committed | Art 5(1)(f), 25, 32 |

A change that adds or modifies a gate must add ZAVA cases (including adversarial ones) and keep
recall high with a low false-positive rate.

---
*Sources:* GDPR and the EU AI Act, plus engineering practice distilled from CNIL developer guidance,
ENISA, OWASP, and NIST. Move from *instructions* to *enforced* with the compliance-spine.
