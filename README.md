# Compliance Spine

**An ISEE-based agent that keeps agentic software development GDPR- and EU AI Act-accountable — by construction.**

> Status: **running implementation** — installable Python package (`compliance_spine`)
> with a CLI, an MCP server, 9 fail-closed gates, 4 agents, a hash-chained Evidence
> ledger, and an 89-case ZAVA suite (recall 1.00 / FPR 0.00). See
> [GETTING-STARTED](./GETTING-STARTED.md) to install and run `./scripts/demo.sh`.
> **Not legal advice.** This agent *assists and evidences* compliance; it does not
> certify it. A human owner (DPO / privacy engineer / legal) signs off. See
> [Boundaries](#boundaries--honest-limits).

---

## 1. The problem

Coding agents now write, test, and ship software faster than any human can review.
Two things break at that speed:

1. **GDPR decisions get made by nobody.** An agent adds a field that stores personal
   data, logs a token, skips a retention TTL, or moves data across a border — and no
   one decided it. A *ghost decision* with a regulator-sized bill attached.
2. **The EU AI Act now writes part of your spine.** If the system you're building is
   high-risk (Annex III) or uses a GPAI model, obligations apply — risk management,
   data governance, logging, human oversight, technical documentation — and "we didn't
   know the classification" is not a defence.

The fix is not "more review" (that reimposes the human-speed bottleneck agents removed)
and not "trust the agent" (that is the ghost-decision factory). The fix is **structure
that carries intent** — a *spine* the coding, testing, and quality agents operate inside,
that enforces the non-negotiables automatically and forces a human owner at the moments
that matter.

---

## 2. The idea — a compliance spine, on ISEE

This is **ISEE** (Intent → Structure → Execution → Evidence) applied to regulation.
The spine is the connective tissue between what the org *decided* (its privacy and
AI-Act posture) and what the agents *actually ship*.

| ISEE layer | In this agent | Owner | Cadence |
|---|---|---|---|
| **Intent** | The *never-delegate list*: privacy + AI-Act non-negotiables (e.g. "no personal data in logs", "no processing without a lawful basis", "no prohibited AI practice", "human oversight on high-risk decisions"). GDPR principles (Art 5) + AI Act prohibitions (Art 5) as the constitution. | DPO / Legal / Privacy lead | quarters |
| **Structure (the spine)** | Intent rendered as **policy-as-code**: gates, checks, linters, test policies, data-flow rules the agents inherit. Slow to change, instant to enforce. | Privacy/Platform engineers (spine authors) | slow to change, instant to enforce |
| **Execution** | The working agents — coding-guidance, compliance-testing, quality, and AI-Act-baseline — operating *inside* the spine on real code. | Cells (human + agents) | continuous |
| **Evidence** | The audit trail + compliance artifacts (RoPA, DPIA, AI Act technical docs, logs, test results) + a **ghost-decision detector** for compliance decisions made with no owner. Evidence challenges Intent (new data flow → does the DPIA / never-delegate list need updating?). | The system itself; read by the DPO/steward | continuous |

**The load-bearing rule:** *"the spine signed off" is only an answer if the spine has an
author.* Every enforced compliance rule traces to a human signature (a policy commit by a
named spine author) — so accountability lands somewhere, not nowhere.

---

## 3. The four agents (Execution layer)

All four are **skills/agents that operate inside the spine** (§4) and emit into Evidence (§5).

### 3.1 Privacy-Guidance Agent — *guides the coding agents*
Sits alongside code generation. Before/while a coding agent writes code, it:
- Detects **personal data** entering the design (fields, params, logs, telemetry, prompts).
- Injects the applicable constraints as context the coding agent must respect
  (data minimisation, purpose tagging, pseudonymisation, encryption, retention TTL,
  lawful-basis presence, no-PII-in-logs).
- Flags **special-category data** (GDPR Art 9 — e.g. health, biometric) and cross-border
  flows (Chap V) early, and *raises the bar*: explicit lawful basis/consent, stricter
  minimisation, access restriction, and a mandatory DPIA trigger.
- Output: constraints + inline guidance the coding agent consumes, **not** a post-hoc scold.

### 3.2 Compliance-Testing Agent — *tests for GDPR compliance*
Generates and runs tests that assert the privacy behaviour, not just the feature:
- **DSAR tests** — data subject rights work: access/export (Art 15/20), erasure (Art 17),
  rectification (Art 16), restriction/objection (Art 18/21).
- **Data-handling tests** — no PII in logs, encryption at rest/in transit (Art 32),
  retention/TTL enforced (Art 5(1)(e)), consent respected (Art 7), purpose limitation.
- **Automated-decision tests** — safeguards where Art 22 applies.
- **Data-flow tests** — no unapproved cross-border transfer; data stays in declared region.
- Output: an executable, re-runnable compliance test suite (part of CI, §7).

### 3.3 Quality Gate — *quality with GDPR built in*
Extends normal review/quality to treat compliance as a first-class quality attribute:
- Reviews diffs for privacy regressions (new PII sink, weakened control, removed gate).
- Blocks or escalates at the **review gates** (§6) — e.g. change introduces new personal-data
  processing, or touches a high-risk AI function.
- Confirms every finding has an owner and a trace before "green".

### 3.4 EU AI Act Baseline Agent — *classifies risk + enforces the baseline*
- **Classifies** the AI system/feature: prohibited (Art 5) / high-risk (Annex III) /
  limited-risk transparency (Art 50) / minimal; and **provider vs deployer** role.
- Applies the **baseline obligations** for the tier (see §9): risk management (Art 9),
  data governance (Art 10), technical documentation (Art 11 / Annex IV), logging (Art 12),
  human oversight (Art 14), accuracy/robustness/security (Art 15), transparency (Art 50),
  and GPAI duties (Art 53+) where a general-purpose model is used.
- **Generates** the starting artifacts: an Annex IV technical-documentation skeleton,
  a logging plan, a human-oversight design, and transparency notices.
- Output: a risk classification + an obligations checklist + doc skeletons in Evidence.

---

## 4. The Spine (Structure) — policy-as-code

The spine is where Intent becomes enforceable. Keep it **declarative, versioned, and
authored** (every rule has a signature).

```
spine/
  intent/
    never-delegate.md         # the 3–7 privacy + AI-Act non-negotiables (human-owned)
    lawful-basis.yaml         # declared purposes + lawful basis per data category
    data-catalogue.yaml       # personal-data inventory, categories, regions, retention
  policies/                   # policy-as-code (the gates)
    no-pii-in-logs.rego       # e.g. OPA/Rego, or your gate DSL
    encryption-required.rego
    retention-ttl.rego
    cross-border-transfer.rego
    ai-act-risk-tier.rego
    human-oversight-required.rego
  gates/
    gate-config.yaml          # which gates block vs warn vs escalate, and to whom
```

Three levels of enforcement (borrowed from the git-ape model):
1. **Prose constraints** — context files the agents read (carry the *why*).
2. **Gate agents** — evaluate a change and block/allow/escalate.
3. **Pipeline gates** — deterministic checks in CI (policy-as-code, tests) that cannot be
   skipped informally. *A spine that can be overridden informally is not a spine.*

### Fail-closed enforcement (gates that close on violation)

Gates default to **fail-closed**: if a gate cannot *prove* compliance, or detects a GDPR
violation, it **blocks**. Absence of evidence is treated as a violation, never waved
through. *A control that can't be verified must fail loud, never pass silently.*

| Severity | Example | Build-time (CI) | Run-time (deployed) |
|---|---|---|---|
| **Critical** | personal data in logs · special-category with no lawful basis · unapproved cross-border transfer · missing DSAR path | **block merge/deploy** · page the DPO · open remediation | **trip the circuit-breaker** — halt the path / flag-off the feature / quarantine affected data · auto-start the breach path (Art 33/34, 72-hour clock) if data crossed a boundary |
| **High** | control weakened · retention TTL removed | block · require named human sign-off | alert · degrade rather than expose |
| **Medium** | interpretation / style | warn · escalate · log | log · escalate |

- **No informal override.** A closed gate reopens only via authorised **silencing** —
  time-boxed, justified in writing, signed by a spine author / DPO, recorded in Evidence.
- **Containment over exposure.** At runtime, prefer halt / roll back / flag-off over
  shipping a violation — AI Act Art 14 "human-in-command" made real.
- Every closure and every override is an Evidence event.

---

## 5. Evidence — a mechanism you can audit

Evidence is generated as a by-product of execution (audit *by construction*) and built to
survive scrutiny: append-only, traceable, and read by a human reader-of-record.

**Evidence contract (per agent + gate).** Each declares *what* it must emit, *when*, and in
*what shape* — so a missing signal is itself detectable (a *ghost signal*).

**Record schema** — one entry per consequential decision:

```yaml
id:           evt_a1b2                      # unique
ts:           2026-01-01T03:14:00Z          # timestamp
actor:        { type: agent|human, id }     # who/what acted
action:       allow | block | escalate | override | emit
subject:      { change: "PR#123", data_category, ai_feature }
rule_id:      spine/policies/no-pii-in-logs # the spine rule applied
intent_ref:   intent/never-delegate#no-pii-in-logs   # traces up to Intent
severity:     critical | high | medium
owner:        { human_id, signature }       # who owns it (required when gated)
inputs_hash:  sha256:…                       # what was evaluated
outputs_hash: sha256:…
artifacts:    [ dpia/…, ropa/…, annexIV/… ] # linked evidence
prev_hash:    sha256:…                        # hash-chain → tamper-evident
```

Four properties make it real:
1. **Traceability chain** — every enforced decision links *gate → spine rule → Intent
   principle → human author*. A decision that can't be traced has no standing.
2. **Tamper-evident** — records are append-only and **hash-chained** (`prev_hash`), so the
   log can't be quietly rewritten; artifacts carry provenance (who/what generated them,
   from which inputs, when — signed). Chain of custody end to end.
3. **Queryable surface** — hierarchical (per-change → per-cell → org), readable at each
   altitude without the ones below. The **DPO is the reader-of-record**.
4. **Ghost-decision detector** — compares what the evidence contract *promises* against what
   the surface *contains*, and flags any compliance-relevant decision that shipped with
   **no owner** (new PII sink, silenced gate, skipped DSAR). The unowned decision becomes
   visible.

**Evidence hygiene:** the evidence is itself sensitive — minimise it, secure it, retain it
per policy, and **version it alongside the spine** so you can reconstruct *which rule was in
force when this shipped*. It assembles continuously: RoPA (Art 30), DPIA (Art 35,
auto-triggered), AI Act technical docs (Art 11 / Annex IV), logs (Art 12), and the decision log.

---

## ZAVA — the compliance eval suite

Gates and agents can *look* compliant and still be wrong. **ZAVA** is the eval suite on top
of the spine that continuously answers one question: **do the controls actually work?** It is
how Evidence earns trust — evals are the proof the spine does what Intent says. ZAVA defines
the compliance-specific datasets, metrics, and thresholds; run them on any eval runner
(DeepEval, promptfoo, Azure AI Evaluation, MLflow) — don't reinvent the runner.

Each eval = a labelled/golden dataset + an adversarial set + a pass threshold.

| Eval | What it proves | The failure that matters most |
|---|---|---|
| **PII-leak red-team** | adversarial inputs can't make a coding agent log personal data / skip encryption / over-collect | a leak the spine *didn't* block |
| **DSAR fulfilment** | generated code truly completes access / erasure / rectification | partial or silent erasure |
| **Automated-decision safeguards** | human-intervention path + explanation exist where Art 22 applies; consistent outcomes | a legal-effect decision with no recourse |
| **Special-category handling** | Art 9 data gets explicit basis + stricter controls + DPIA | special-category slipping through as ordinary data |
| **Retention & transfer** | data expires; stays in the declared region | silent over-retention / out-of-region flow |
| **Gate efficacy (fail-closed)** | given a *known* violation, the gate **closes** | a violation that passed |
| **Ghost-decision recall** | seeded unowned decisions get flagged | a ghost the detector missed |
| **AI Act classification** | risk tier assigned correctly vs a golden set | a high-risk system mis-labelled low |

**Metric priority:** weight **recall on violations** above precision — a *missed* violation
is far worse than a false alarm. Track per-category pass rate, false-negative rate (the
dangerous one), and drift over time.

**Where it runs:** on every change to a spine rule or an agent (CI), and on a schedule
against production behaviour. A **ZAVA regression closes the gate** on the change that caused
it — the eval suite is itself an enforcement input, and its scorecards land in Evidence.

---

## 6. Human-in-the-loop & accountability

Delegate more, but retain oversight at the moments that matter. Human **review gates** fire on:
- new **personal-data processing** or a new data category;
- a change classified **high-risk** under the AI Act, or any move toward a **prohibited** practice;
- a **cross-border transfer** (Chapter V);
- an **automated decision** with legal or significant effect on a person (Art 22) — the
  gate requires a human-intervention path and a contestable explanation;
- **silencing** a spine rule (allowed, but time-boxed, justified, and logged).

The human who approves is the **author** — their signature is what turns a ghost decision
into an owned one. The DPO/steward is the *reader-of-record* for the Evidence surface.

---

## 7. Architecture & integration

```
        ┌──────────────── INTENT (DPO/Legal own) ─────────────────┐
        │  never-delegate list · lawful basis · data catalogue     │
        └───────────────────────────┬─────────────────────────────┘
                                     │ authored into
        ┌──────────────── STRUCTURE / SPINE ──────────────────────┐
        │  policy-as-code gates · CI checks · gate config          │
        └───────┬───────────────┬───────────────┬─────────────────┘
   inherits     │               │               │
        ┌────────▼───┐   ┌───────▼──────┐  ┌─────▼──────────┐   EXECUTION
        │ Privacy-   │   │ Compliance-  │  │ Quality Gate + │   (inside the
        │ Guidance   │   │ Testing      │  │ AI Act Baseline│    spine)
        │ agent      │   │ agent        │  │ agent          │
        └────────┬───┘   └───────┬──────┘  └─────┬──────────┘
                 └───────────────┴───────────────┘ emit
        ┌──────────────── EVIDENCE ───────────────────────────────┐
        │ RoPA · DPIA · Annex IV docs · logs · decision log ·      │
        │ ghost-decision detector  →  challenges Intent            │
        └──────────────────────────────────────────────────────────┘
```

**Reuse what you already built:**
- **`git-ape`** → the gate / approval / drift-detection / evidence engine. Retarget its
  policy gates + human-approval + audit at compliance instead of infra.
- **`ape-context`** → extract the org's compliance **Intent** (never-delegate list, data
  catalogue) from existing policies/DPAs into the spine.
- **`isee-advisor`** → a **compliance maturity diagnostic** ("how governed is your
  delegation?") as a companion.

**Runtimes:**
- **CI/CD** — the spine's pipeline gates + the compliance test suite run on every PR.
- **ZAVA** — the eval suite runs in CI and on a schedule; a regression closes the gate.
- **GitHub Copilot App** — ship the four agents as skills; use **Canvas** as the review-gate
  surface and **Work IQ / MCP** connected tools for org context (policies, DPAs).
- **MCP server** — expose the spine (`check_change`, `classify_ai_risk`, `emit_evidence`)
  so any coding agent can call it.

---

## 8. GDPR control catalogue (what the agents enforce)

Starter set — extend per your data catalogue. Each maps to an article and a machine check.

| Control | GDPR | Machine check (examples) |
|---|---|---|
| Data minimisation | Art 5(1)(c) | flag new personal-data fields with no declared purpose |
| Purpose limitation | Art 5(1)(b) | every PII field tagged to a declared purpose |
| Storage limitation | Art 5(1)(e) | retention TTL present + enforced; no "forever" |
| Lawful basis | Art 6 | processing has a declared lawful basis |
| Special-category data | Art 9 | explicit lawful basis/consent; stricter minimisation; access-restricted; DPIA required |
| Consent | Art 7 | consent captured/withdrawable where basis = consent |
| Subject rights (DSAR) | Art 15–22 | access/export/erasure/rectification endpoints exist + tested |
| Automated decisions | Art 22 | human-intervention path + explanation/contestability where a decision has legal or significant effect |
| Privacy by design/default | Art 25 | defaults are least-data; opt-in not opt-out |
| Records of processing | Art 30 | RoPA generated + current |
| Security | Art 32 | encryption in transit/at rest; pseudonymisation; secrets not hardcoded |
| Breach readiness | Art 33–34 | breach-detection + notification path exists |
| DPIA | Art 35 | auto-triggered on high-risk processing |
| Transfers | Chap V (44–50) | no data leaves declared region without a transfer mechanism |
| No PII in logs | Art 5 / 32 | log scanner blocks personal data / tokens in logs |

## 9. EU AI Act baseline (what the AI Act agent enforces)

> Timeline (verify against current text): in force **1 Aug 2024**; **prohibited** practices
> from **2 Feb 2025**; **GPAI** obligations from **2 Aug 2025**; **high-risk (Annex III)**
> from **2 Aug 2026**; remaining high-risk **2 Aug 2027**. Fines up to **€35M / 7%** of global
> turnover (prohibited), **€15M / 3%** (most obligations), **€7.5M / 1%** (misinformation).

1. **Classify** the system → tier + role (provider vs deployer).
   - **Prohibited (Art 5):** block — e.g. social scoring, manipulative or exploitative AI,
     untargeted facial scraping, certain biometric categorisation.
   - **High-risk (Annex III):** e.g. employment/HR, credit scoring, essential services,
     biometrics, critical infrastructure, education.
   - **Limited-risk (Art 50):** transparency duties (tell users it's AI; label deepfakes/AI content).
   - **Minimal:** no specific obligations (still good practice).
   - **Default to caution:** where a system makes consequential decisions about
     individuals, treat it as **high-risk until a documented assessment shows otherwise** —
     the baseline obligations cost far less than the fine.
2. **High-risk baseline obligations** (checklist + artifacts):
   - Risk-management system — **Art 9**
   - Data & data governance — **Art 10**
   - Technical documentation — **Art 11 + Annex IV** (agent generates the skeleton)
   - Record-keeping / logging — **Art 12**
   - Transparency to deployers — **Art 13**
   - Human oversight — **Art 14** (design the override/halt path)
   - Accuracy, robustness, cybersecurity — **Art 15**
   - Quality management system — **Art 17**; conformity assessment — **Art 43**
3. **GPAI** (if a general-purpose model is used) — **Art 53+**: technical documentation,
   copyright policy, training-data summary; systemic-risk GPAI has extra duties.

---

## 10. Repo structure (proposed)

```
compliance-spine/
  README.md                     # this file
  spine/                        # Structure — policy-as-code (see §4)
  agents/
    privacy-guidance/           # 3.1
    compliance-testing/         # 3.2
    quality-gate/               # 3.3
    ai-act-baseline/            # 3.4
  evidence/                     # append-only hash-chained decision log + schema + artifacts
                                #   (RoPA, DPIA, Annex IV, logs) — see §5
  zava/                         # ZAVA compliance eval suite — golden + adversarial datasets,
                                #   metrics, thresholds (runs on DeepEval/promptfoo/etc.)
  mcp/                          # MCP server exposing the spine to coding agents
  ci/                           # pipeline gates + compliance test runner
  diagnostics/                  # isee-advisor-style compliance maturity check
  docs/                         # control catalogue, article mapping, ADRs
```

## 11. MVP → roadmap

**MVP (prove the loop on one repo, one data category):**
1. `intent/never-delegate.md` + a minimal `data-catalogue.yaml` (one personal-data category).
2. Two spine gates: **no-PII-in-logs** + **retention-TTL-required** (policy-as-code in CI).
3. Privacy-Guidance agent injects those constraints into a coding agent's context.
4. Compliance-Testing agent generates a DSAR-erasure test + a no-PII-in-logs test.
5. Evidence: a **hash-chained** decision log + the ghost-decision detector flagging one
   unowned change.
6. One human review gate ("new personal-data processing"), plus one **fail-closed** gate
   that *blocks* on a seeded no-PII-in-logs violation.
7. One **ZAVA** eval — seed the violation, prove the gate closes (a gate-efficacy eval).

**Phase 2:** full GDPR control catalogue; DPIA auto-trigger; RoPA generation; cross-border gate.

**Phase 3:** AI Act Baseline agent — classifier + high-risk obligations checklist + Annex IV skeleton.

**Phase 4:** GHCP App skills + Canvas review gates + Work IQ context; isee-advisor compliance diagnostic; multi-repo (the comb).

## 12. Success measures

- % of personal-data changes that ship **with a named owner** (target: 100%).
- Ghost compliance decisions detected per week — and time-to-owner.
- DSAR test coverage; retention-TTL coverage; PII-in-logs incidents (target: 0).
- AI Act: % of AI features with a current classification + obligations checklist.
- Audit-readiness: time to produce RoPA / DPIA / Annex IV docs (target: on demand, not weeks).

## 13. Boundaries — honest limits

- **This is not legal advice and does not certify compliance.** It assists engineering teams
  and *evidences* decisions; a qualified human (DPO/legal) owns the sign-off.
- The agent governs **runtime behaviour and the SDLC** — not your full legal DPIA process,
  contracts, or upstream model training. It complements, not replaces, legal review.
- Classifications and article mappings here are a **starting point** — verify against the
  current GDPR / EU AI Act text and your DPO. Regulation moves; the spine must be re-authored,
  not frozen.
- A control the agent can't verify must **fail loud or escalate**, never pass silently.

## 14. References (verify current versions)

- GDPR — Regulation (EU) 2016/679 (esp. Art 5, 6, 9, 15–22, 25, 30, 32–35, Chap V).
- EU AI Act — Regulation (EU) 2024/1689 (esp. Art 5, 9–15, 50, 53; Annex III, Annex IV).
- Your own: `Azure/git-ape`, `suuus/ape-context`, `suuus/isee-advisor`; the ISEE framework
  (agentile.org) and *Ghost Decisions* (Ch 13 — regulation as architecture).

---

*Built on ISEE: Intent → Structure → Execution → Evidence. The point isn't to slow the agents
down. It's to make sure that when they act on personal data or a regulated function, a human
still owns the decision — and the evidence proves it.*
