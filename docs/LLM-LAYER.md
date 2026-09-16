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

> Not built yet: this repo ships the **propose/confirm** flow on your Copilot model. A headless
> GitHub Models / Azure AI Foundry detector is an optional add-on for CI or independent review —
> the hooks (advisory Evidence, DeepEval eval, MCP) are already here.
