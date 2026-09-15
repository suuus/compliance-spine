# Agents — build guide & I/O contracts

The four Execution-layer agents. All **inherit the spine** (Intent + policies), operate
inside it, and **emit Evidence**. None of them is the enforcer — the *gates* enforce; the
agents guide, test, review, and classify. Build them as GitHub Copilot App skills / MCP
tools so any coding-agent surface can call them.

Shared contract:
- **Input:** the change under consideration (diff / PR / plan), plus spine context
  (never-delegate list, data-catalogue, active policies) via the MCP server.
- **Output:** findings + guidance, and one or more **Evidence events**
  (`evidence/schema/decision-record.schema.json`).
- **Rule:** if the agent cannot determine compliance, it **escalates** (never assumes pass).

---

## 3.1 Privacy-Guidance agent — guides the coding agents
- **Reads:** the design/diff + data-catalogue + never-delegate list.
- **Does:** detects personal data entering the design (fields, params, logs, prompts,
  telemetry); flags special-category (Art 9) + cross-border early; injects the applicable
  constraints (minimisation, purpose tag, pseudonymisation, encryption, retention TTL,
  lawful-basis presence, no-PII-in-logs) as **context the coding agent consumes**.
- **Emits:** `emit` events for each constraint injected; `escalate` if a new data category
  appears.
- **Build tip:** run it *before/while* code is written, not after — guidance, not a scold.

## 3.2 Compliance-Testing agent — tests for GDPR
- **Reads:** the shipped/changed code + the data-catalogue.
- **Does:** generates + runs an executable suite — DSAR (access/export/erasure/rectification),
  data-handling (no-PII-in-logs, encryption, retention/TTL, consent, purpose limitation),
  automated-decision safeguards (Art 22), data-flow (no unapproved transfer).
- **Emits:** test results as Evidence; a failing compliance test is a **gate input**
  (fail-closed).
- **Build tip:** tests live in `ci/`; they assert *privacy behaviour*, not just the feature.

## 3.3 Quality Gate — quality with GDPR built in
- **Reads:** the diff + the other agents' findings.
- **Does:** treats compliance as a first-class quality attribute — blocks/escalates on a
  privacy regression (new PII sink, weakened control, removed gate); confirms every finding
  has an owner + trace before "green".
- **Emits:** an `allow`/`block`/`escalate` decision, signed when a human approves.

## 3.4 EU AI Act Baseline agent — classify + enforce the baseline
- **Reads:** the system/feature description + model usage.
- **Does:** classifies tier (prohibited / high-risk / limited / minimal) + role
  (provider vs deployer); **defaults to caution** (high-risk until a documented assessment
  shows otherwise) for consequential decisions about people; applies the tier's obligations
  (README §9); generates the Annex IV technical-doc skeleton, logging plan, human-oversight
  design, transparency notices.
- **Emits:** the classification + an obligations checklist + doc skeletons into Evidence.
- **Build tip:** wrong direction matters — a false *low-risk* is the dangerous error; the
  ZAVA `AI Act classification` eval weights recall on high-risk.

---

## Prompt / skill structure (per agent)
```
agents/<name>/
  skill.md            # role, inputs, tools, output contract, escalation rule
  prompt.md           # the system prompt / instructions (inherits spine context)
  evals -> ../../zava/datasets/<name>/   # its ZAVA evals
```
Keep each agent's authority explicit: what it may decide vs what it must escalate. An agent
that silently decides a compliance question is producing ghost decisions.
