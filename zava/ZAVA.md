# ZAVA — the compliance eval suite

ZAVA proves the controls actually work. It defines compliance-specific **datasets, metrics,
and thresholds**; a runner (DeepEval, promptfoo, Azure AI Evaluation, MLflow) executes them.
See README §"ZAVA" for the rationale.

## Eval anatomy
```
zava/datasets/<eval-id>/
  golden/            # labelled compliant + non-compliant cases (ground truth)
  adversarial/       # red-team cases designed to slip past the spine
  eval.yaml          # metric, threshold, which agent/gate it targets, runner mapping
  README.md          # what this eval proves + the failure that matters most
```

`eval.yaml` shape:
```yaml
id: no-pii-in-logs-efficacy
targets: spine/policies/no-pii-in-logs      # gate or agent under test
metric: recall_on_violations                # see below
threshold: 1.0                              # must catch ALL seeded violations
runner: deepeval                            # or promptfoo | azure-ai-eval | mlflow
on_regression: close_gate                   # a drop below threshold blocks the change
```

## The eight starter evals (README table)
| id | targets | proves |
|---|---|---|
| `pii-leak-redteam` | Privacy-Guidance + gates | adversarial input can't make an agent log/over-collect PII |
| `dsar-fulfilment` | Compliance-Testing | access/erasure/rectification truly complete |
| `automated-decision-safeguards` | AI-Act + gates | Art 22 human-intervention + explanation present |
| `special-category-handling` | Privacy-Guidance + gates | Art 9 gets explicit basis + stricter controls + DPIA |
| `retention-transfer` | gates | data expires; stays in-region |
| `gate-efficacy` | each gate | a known violation makes the gate **close** |
| `ghost-decision-recall` | detector | seeded unowned decisions get flagged |
| `ai-act-classification` | AI-Act agent | tier assigned correctly vs golden set |

## Metrics — what to optimise
- **`recall_on_violations` is the primary metric.** A *missed* violation (false-negative) is
  far worse than a false alarm. Threshold is high (often 1.0 for critical gates).
- Track: per-category pass rate, **false-negative rate** (the dangerous one), precision
  (secondary — to keep noise sane), and **drift** over time.
- For classification evals, weight **recall on the high-risk class** — a high-risk system
  mislabelled low is the failure that costs.

## Where it runs
- **CI:** on every change to a spine rule or an agent. A regression → `on_regression:
  close_gate` → the change is blocked.
- **Scheduled:** against production behaviour, to catch drift.
- **Output:** scorecards written to the Evidence surface (evals are evidence the spine works).

## Building the first eval (MVP)
1. `zava/datasets/no-pii-in-logs-efficacy/` with a few golden violating + compliant fixtures.
2. `eval.yaml` targeting the `no-pii-in-logs` gate, metric `recall_on_violations`, threshold 1.0.
3. Run on your chosen runner in CI; assert the gate **closes** on every seeded violation.
4. When it's green, you've proven the gate — not just written it.

## Authoring a new eval
- Start from a real (anonymised) failure mode; encode it as an adversarial case.
- Label ground truth carefully — the eval is only as honest as its labels.
- Always add the eval when you add a gate or an agent. **A control with no eval is unproven.**
