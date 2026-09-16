---
applyTo: "**/*.{py,js,ts,jsx,tsx,java,go,rb,cs,php,kt,scala,sql}"
---
# Personal-data handling (fires when you edit source)

These are the GDPR / Art 32 rules most likely to bite in code. The compliance-spine gates enforce
them — run `compliance-spine scan-diff --staged` before committing to see if you've tripped one.
For the full rationale, tables, and EU AI Act detail, the `gdpr-ai-act-compliance` skill loads on
demand.

- **Logs:** no personal data in logs, traces, or error messages — log a non-personal correlation id.
- **Minimise:** select named columns, not `SELECT *`; don't log request/response bodies or user objects.
- **Secrets & transport:** no hardcoded secrets and no secret files in the repo; TLS 1.2+ with
  certificate verification (never `verify=False` / `rejectUnauthorized: false`).
- **Passwords:** Argon2id or bcrypt with a unique salt — never MD5, SHA-1, or bare SHA-256.
- **APIs:** no personal data in URL paths or query params; opaque UUIDs, not sequential ids;
  ownership checks on every resource; no `Access-Control-Allow-Origin: *`; RFC 7807 errors — never
  return a stack trace, internal path, or PII to the client.
- **Storage:** every personal-data store declares a retention TTL and a real erasure path.

If a change adds or uses an AI feature, classify its EU AI Act risk tier (treat unassessed as
high-risk) and run `compliance-spine check` / `classify_ai_act_risk`.
