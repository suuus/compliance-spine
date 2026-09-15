# GDPR & EU AI Act instructions for GitHub Copilot

**Purpose:** keep everything you (Copilot) help produce here — code, tests, reviews, prompts —
GDPR- and EU AI Act-compliant *by default*, in every mode: coding, refactoring, reviewing,
testing, and answering questions. When a rule and a convenience collide, the rule wins.

If a **compliance-spine** is present in this repo, do not rely on your own judgment for
compliance — run it (`compliance-spine check | advise | review`, or the MCP tools
`check_change` / `review` / `classify_ai_act_risk`) and act on the verdict. Instructions set
intent; the spine enforces it and records the decision in tamper-evident Evidence.

## Hard stops — never do these
- **Never** put personal data in logs, traces, error messages, telemetry, analytics, or model prompts.
- **Never** hardcode secrets, keys, tokens, connection strings, or credentials. Use a secrets manager / environment.
- **Never** send real or production personal data to the model — not in prompts, examples, tests, or fixtures. Use synthetic data.
- **Never** introduce processing of personal data without a declared lawful basis (Art 6; an Art 9(2) condition for special-category).
- **Never** store personal data without a retention limit and a real erasure path.
- **Never** move personal data outside its declared region without a valid transfer mechanism (Chapter V).
- **Never** ship a solely-automated decision with legal or significant effect without a human-intervention path and a contestable explanation (Art 22).
- **Never** weaken, disable, silence, or delete a compliance gate, test, or redaction to make a build pass. If it blocks, fix the cause or escalate.
- **Never** self-approve a *never-delegate* item. Those require a named human (DPO / privacy owner).

## Before you write code — establish the data context
State it explicitly; if you can't answer, ask — don't assume:
- Does this touch personal data? Category: none / personal / special (Art 9)?
- Lawful basis and purpose? (purpose limitation)
- Is it stored? Retention period + erasure path?
- Does it cross a region boundary? Transfer mechanism?
- Is there an AI feature? Its EU AI Act risk tier?

When proposing a change through the spine, emit the `metadata` block (data_category,
lawful_basis, retention_days, transfers, encryption, ai_feature, ai_risk_tier, component) so
the gates can evaluate it, then run `compliance-spine check`.

## Writing code — rules by area
**Data minimisation (Art 5(1)(c))**
- Store and collect the minimum. No `SELECT *` on tables holding personal data — select named, needed columns.
- Don't log request/response bodies, user objects, or PII fields. Log a non-personal correlation id. If a value must appear, redact / mask / hash it.
- Prefer pseudonymised or aggregated data; de-identify as early as possible.

**Purpose limitation (Art 5(1)(b))**
- Don't read personal data from a component that shouldn't hold it (analytics, reporting, public/edge, logging, marketing). Consume de-identified / aggregated data there, or go through an authorised service.

**Storage limitation (Art 5(1)(e), Art 17)**
- Every personal-data store declares a retention/TTL and an erasure path. Build real deletion or anonymisation, not just soft-delete.

**Lawful basis & consent (Art 6 / 7 / 9)**
- New processing → declare the basis. Consent must be specific, freely given, and withdrawable — build the withdrawal path. Special-category data (health, biometric, ethnicity, religion, and the other Art 9 categories) needs an Art 9(2) condition, a DPIA, and stricter minimisation.

**Data subject rights (Art 15–22)**
- Design for access, rectification, erasure, portability, and objection from the start. Personal data must be findable and deletable by subject id.

**Security (Art 32)**
- Encrypt personal data at rest and in transit. Least privilege. No secrets in source. Validate and sanitise inputs; use parameterised queries.

**Automated decisions (Art 22)**
- Solely-automated + significant effect → add human intervention and a contestable explanation. Record decision inputs for contestability (without logging raw PII).

**Cross-border transfers (Chapter V)**
- Any transfer outside the declared region needs adequacy / SCCs / BCRs / a documented derogation. Third-party SDKs and endpoints that receive personal data are transfers.

**Privacy & security by design and by default (Art 25)**
- Default to the most private setting. Opt-in, not opt-out. Don't switch on data collection you don't need.

## EU AI Act — when a change adds or uses an AI feature
- Classify the risk tier. If unassessed, treat it as **high-risk until proven otherwise**.
- Prohibited practices (Art 5): stop and escalate.
- High-risk (Art 9–15): reference the baseline — risk management, data governance, technical documentation, logging/traceability, transparency to deployers, human oversight, and accuracy/robustness/cybersecurity.
- Limited-risk: disclose that a person is interacting with AI or with AI-generated content (Art 50).
- Never present model output as a decision without the human oversight the tier requires.

## Writing tests
- Use synthetic / clearly-fake data only. Never real users, emails, ids, or tokens; never copy production data into fixtures.
- Test the privacy controls themselves: PII never reaches logs, retention/erasure works, access boundaries hold, redaction is applied, and DSAR paths return or delete the right data.
- If the spine is present, a change that adds or modifies a gate must add ZAVA cases (including adversarial ones) and keep recall high with a low false-positive rate.

## Reviewing changes
- Run the spine on the diff (`compliance-spine review`, or the `review` MCP tool) before approving.
- Block on: PII in logs, secrets, missing lawful basis or retention, unbounded transfers, unassessed AI features, access-boundary violations.
- Escalate never-delegate items to the DPO and record the decision in Evidence. Do not rubber-stamp.

## Your own data hygiene (prompts & context)
- Strip personal data before adding files, logs, or data to the prompt. If a file contains PII, summarise or redact rather than paste it.
- Don't exfiltrate personal data to external tools, web searches, or third-party services.

## When blocked or unsure
- Gate blocks → fix the root cause. Only a named human (DPO) may override — time-boxed and co-signed. Never you.
- Unsure whether something is personal data, or which basis applies → treat it as personal, fail closed, and ask the DPO. Caution is the default.

## Confidentiality (this repo)
- Keep any customer or domain identity out of code, docs, tests, and commit messages. The leak-guard enforces this — keep it green.

---
*Reusable:* drop this file into any repository's `.github/` to make Copilot GDPR/AI-Act-aware
there too. Pair it with the compliance-spine to move from *instructions* to *enforced*.
