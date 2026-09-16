# The LLM layer — reasoning that proposes, gates that dispose

The spine's enforcement is **deterministic** on purpose: fail-closed gates, a hash-chained
Evidence ledger, and a repeatable eval (ZAVA). An LLM can make it *smarter* — but only in a
role that never weakens those guarantees.

## The one rule

> **LLMs propose. Deterministic gates dispose. A human owns the never-delegate calls.**

An LLM is non-deterministic, prompt-injectable, and hard to audit, so it must never be the
thing that **blocks** or **approves**. It is a **detector / drafter / explainer** whose output
is *advisory* until a human confirms it or it's converted into a deterministic check. The
binding decision always stays with the gates and the human.

## Where the LLM adds value

- **Metadata inference** — read a diff and *draft* the compliance context (data_category,
  lawful_basis, retention, ai_feature, …) that the declaration gates need. This is the biggest
  win: it unlocks the gates that otherwise wait on manual declaration.
- **Semantic detection** — flag long-tail issues the heuristics miss (re-identification,
  purpose creep, consent dark patterns).
- **Context-aware remediation** — write the actual redaction / retention config / DPIA note.
- **Gate & test synthesis** — draft new gates and ZAVA cases from a policy or a regulation clause.

## Default: use your GitHub Copilot model

For anything a human drives — authoring, review, PRs — **the model Copilot already runs is the
LLM layer.** The `.github/agents/*.agent.md` agents reason on it and call the deterministic
spine (`compliance-spine …` / the MCP tools). No API keys, no extra cost line, no new
data-processor, and it keeps the GitHub-native story intact. Do not stand up a parallel LLM
stack for this.

### The draft-and-confirm flow (built in)

```
Copilot model reads the diff
      │  drafts compliance context
      ▼
change.json  →  proposed_metadata: { data_category: personal, lawful_basis: contract, … }
      │
      ▼
compliance-spine propose change.json      # records an ADVISORY llm proposal (non-binding)
      │                                     # + previews what the gates would say
      ▼
human reviews the preview  →  confirms  →  promotes proposed_metadata → metadata
      │
      ▼
compliance-spine check change.json         # the binding, deterministic, human-owned decision
```

The proposal is written to the Evidence ledger as `action: emit`, `actor.type: llm` — clearly
advisory, and distinct from a gate decision. It never allows, blocks, or escalates.

## The layered reviewer — floor + ceiling (built)

Detection is where a model earns its keep, so the reviewer is a **union, fail-closed**:

- **Floor** — the deterministic gates: a regression net of what we've already learned must
  never slip.
- **Ceiling** — a pluggable *assessor* that catches what the fixed rules miss.

The assessor may **add** findings and **raise** the verdict; it can **never clear** a gate's
block. You get the assessor's recall without a floor that regresses or that a prompt-injected
input can erode — a garbage/injected model response parses to *no findings*, so the floor still
blocks.

```bash
compliance-spine llm-review CHANGE.json   # gates (floor) union assessor (ceiling), fail-closed
compliance-spine scorecard                # measure the recall lift vs. gates-only
```

Assessors are pluggable (`compliance_spine.llm`):
- `HeuristicAssessor` — a deterministic **stand-in** (not a model), shipped so the architecture,
  evidence, and scorecard run offline and in CI. It catches a few real patterns the core gates
  miss (personal data sent to a model/prompt, personal data in an outbound call, PII in a TODO).
- `CallableAssessor(fn)` — wrap **any** model callable `(prompt) -> json`: your Copilot model,
  GitHub Models, or an Azure AI Foundry endpoint. This is where real probabilistic recall comes
  from; the stand-in only proves the plumbing.

### The scorecard — let the numbers decide

`compliance-spine scorecard` runs an *extended* dataset (violations the fixed rules don't cover)
through gates-only vs. gates-∪-assessor and prints the recall lift. With the shipped stand-in it
already shows a lift with no new false positives; swap in a real model and it measures the real
thing. **That is how you earn trust in a probabilistic decider: measure it, watch for drift, and
gate its authority on the score.** Every assessor finding is recorded as an advisory Evidence
entry (`actor.type: llm`) with its rationale — reproducible accountability comes from the record,
not from determinism.

## Recording and learning from probabilistic findings

A probabilistic finding is only useful if it's recorded and adjudicated. So:

- **Every assessor finding is recorded** with its **confidence** (`actor.type: llm`,
  `confidence: 0-1`) and rationale — even the ones no deterministic gate caught.
- **A human's decision on a finding is recorded too** — `compliance-spine adjudicate
  <finding-id> --outcome confirmed|dismissed --human <id> --signature <sig>` writes a
  human-owned record linked to the finding. This captures *the decision the agent or human
  made*, which the gates alone would have left invisible.
- **The flywheel** — `compliance-spine learn` sorts findings by adjudication:
  - **confirmed** → a real violation the fixed rules missed → a candidate to **encode as a new
    gate + ZAVA case** (recall you then keep deterministically, forever).
  - **dismissed** → an assessor false positive → signal to tune the assessor / prompt.
  - **pending** → awaiting human review.

That is how the probabilistic layer *improves the deterministic one*: the LLM finds the long
tail, a human labels it, and the confirmed labels become permanent rules. The gates never get
cleverer — the rulebook gets bigger, from evidence.

## Optional: a headless model (GitHub Models or Azure AI Foundry)

Use a dedicated, **pinned** model only for the narrow cases where the Copilot-model default
doesn't fit:

1. **Unattended CI** — LLM-level screening on every PR with no human in a Copilot session.
2. **Reproducibility for the eval/audit** — a fixed model + prompt version makes an advisory
   finding reproducible and lets ZAVA/DeepEval measure the detector against a stable baseline.
3. **Reviewer independence** — the model that *wrote* the code sharing the compliance review
   shares its blind spots; a different, pinned reviewer model catches correlated mistakes.

Two in-ecosystem options, both **advisory-only** (they never gate):

- **GitHub Models** — simplest; stays inside GitHub, no separate infra.
- **Azure AI Foundry** — when you need **data residency, network isolation, private endpoints,
  or content-safety controls**. Deploy a model to a Foundry endpoint (e.g. an EU region for
  GDPR data-locality), pin the deployment + prompt version, and call it from a headless
  detector. Record the model + prompt reference in the Evidence proposal (`actor.id`) so the
  advisory finding is reproducible. Foundry also gives you Azure content safety and private
  networking, which matter when the reviewer runs unattended.

Whichever you choose, the wiring is the same: the detector **proposes** (advisory Evidence),
the deterministic gates **dispose**, and the human owns the never-delegate calls. Keep real
personal data out of the model's inputs — run it on diffs/code, which the `no-pii-in-logs`
gate keeps clean (the deterministic layer protects the LLM layer's inputs).

> Built: the propose/confirm flow **and** the layered reviewer + scorecard (with a deterministic
> stand-in assessor, so they run offline and in CI). To get real probabilistic recall, wire a
> model via `CallableAssessor` — your Copilot model, GitHub Models, or an Azure AI Foundry
> endpoint. The hooks (advisory Evidence, the scorecard, DeepEval, MCP) are already here.
