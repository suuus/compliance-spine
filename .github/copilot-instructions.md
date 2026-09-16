# GDPR & EU AI Act instructions for GitHub Copilot

**Purpose:** keep everything you help produce here GDPR- and EU AI Act-compliant *by default*, in
every mode (coding, refactoring, reviewing, testing, answering). When a rule and a convenience
collide, the rule wins.

This file is the always-on **constitution** — the hard stops only. The full engineering playbook
(retention defaults, password hashing, API design, anonymisation, EU AI Act tiers, testing) lives
in the **`gdpr-ai-act-compliance` skill**, which loads on demand when you touch personal data or an
AI feature. Path-specific rules live in `.github/instructions/`.

**If a compliance-spine is present, do not rely on your own judgment** — run it
(`compliance-spine check | advise | review | scan-diff`, or the MCP tools `check_change` / `review`
/ `classify_ai_act_risk`) and act on the verdict. Instructions and skills set intent; the gates
enforce it and record the decision in tamper-evident Evidence. The LLM proposes and assesses; the
gates dispose; a named human owns the never-delegate calls.

## Hard stops — never do these
- **Never** put personal data in logs, traces, error messages, telemetry, analytics, or model prompts.
- **Never** hardcode secrets/keys/tokens, or commit secret files (`.env`, `*.pem`, `*.key`, `id_rsa`, `secrets/`).
- **Never** send real or production personal data to the model — use synthetic data.
- **Never** exfiltrate personal data to external tools, web searches, or third-party services.
- **Never** process personal data without a declared lawful basis (Art 6; an Art 9(2) condition for special-category).
- **Never** store personal data without a retention limit and a real erasure path.
- **Never** move personal data outside its declared region without a valid transfer mechanism (Chapter V).
- **Never** enable analytics/telemetry by default — optional data collection is opt-in (Art 25(2)).
- **Never** ship a solely-automated decision with legal/significant effect without a human-intervention path and a contestable explanation (Art 22).
- **Never** hash a password with MD5/SHA (use Argon2id/bcrypt), disable TLS verification, put personal data in a URL, open CORS to `*`, or return a stack trace to a client.
- **Never** weaken, disable, silence, or delete a compliance gate, test, or redaction to make a build pass. Fix the cause or escalate.
- **Never** self-approve a *never-delegate* item — those require a named human (DPO / privacy owner).

## Before you write code — establish the data context
State it; if you can't answer, ask — don't assume:
- Does this touch personal data? Category: none / personal / special (Art 9)?
- Lawful basis and purpose? Stored → retention + erasure path? Crosses a region → transfer mechanism?
- Is there an AI feature? Its EU AI Act risk tier? (If unassessed, treat as **high-risk**.)

You may *infer* this context and **propose** it (`compliance-spine propose`), but an inferred
declaration is a proposal, not a fact — a human confirms it before it binds.

## When blocked or unsure
- A gate block → fix the root cause. Only a named human (DPO) may override, time-boxed and co-signed. Never you.
- Unsure whether something is personal data, or which basis applies → treat it as personal, fail closed, ask the DPO.

## Confidentiality (this repo)
- Keep any customer **identity** (names, codenames, customer-specific details) out of code, docs, tests, and commit messages — the regulated sector itself is fine. The leak-guard enforces this — keep it green.

---
*Depth on demand:* the `gdpr-ai-act-compliance` skill (`.github/skills/`) carries the full playbook;
`.github/instructions/` holds path-scoped rules; the compliance-spine gates enforce and prove.
Drop this file (and the skill) into any repository to make Copilot GDPR/AI-Act-aware, then pair it
with the spine to move from *instructions* to *enforced*.
