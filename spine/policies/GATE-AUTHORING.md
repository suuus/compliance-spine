# Gate authoring — how to write a fail-closed gate

A gate turns one Intent principle into an automatic, enforceable check. Gates are
**fail-closed**: if the gate cannot *prove* compliance, it **blocks**. Absence of proof is a
violation, never a pass.

## Anatomy of a gate
Every gate declares:
- **`id`** — stable, e.g. `no-pii-in-logs`.
- **`intent_ref`** — which never-delegate item it enforces (traceability).
- **`author`** — the human signature (a spine author).
- **`severity`** — `critical | high | medium` → maps to the response (README §4).
- **`decision`** — `allow | block | escalate` (+ runtime: `halt | quarantine`).
- **`evidence`** — what it emits on every evaluation (see `evidence/`).
- **`silence`** — whether it may be silenced, and by whom (default: DPO + spine author).

## Severity → response (fail-closed)
| Severity | Build-time | Run-time |
|---|---|---|
| critical | block merge/deploy · page DPO | trip circuit-breaker · quarantine · breach path if data crossed a boundary |
| high | block · require named sign-off | alert · degrade rather than expose |
| medium | warn · escalate · log | log · escalate |

## Authoring steps
1. Pick one never-delegate item. One gate = one principle. Keep it deterministic.
2. Decide what "provable" means. If you can't verify it statically, **escalate to a human
   gate** rather than pass — never assume compliant.
3. Write the check in your policy engine (OPA/Rego, Conftest, or the gate DSL).
4. Emit an Evidence event (allow **and** block) with `rule_id` + `intent_ref` + `severity`.
5. Add the matching **ZAVA gate-efficacy eval**: seed a known violation → assert the gate
   **closes**. A gate with no eval is unproven.
6. Wire into CI so it can fail the build. Register runtime enforcement where relevant.

## Example — `no-pii-in-logs` (illustrative Rego shape)
```rego
package spine.no_pii_in_logs

# metadata
id         := "no-pii-in-logs"
intent_ref := "intent/never-delegate#no-pii-in-logs"
severity   := "critical"

# personal-data patterns (extend from your data-catalogue.yaml)
pii_patterns := ["email", "bsn", "iban", "phone", "dob", "address", "ip_address"]

# a log/trace call that includes a personal-data field → violation
deny[msg] {
  some call
  input.log_calls[call]
  some field
  input.log_calls[call].fields[field]
  contains_pii(field)
  msg := sprintf("personal data '%s' in log call at %s", [field, input.log_calls[call].loc])
}

contains_pii(field) {
  some p
  p := pii_patterns[_]
  contains(lower(field), p)
}

# fail-closed: if we could not analyse the change, block
deny[msg] {
  input.analysis_complete == false
  msg := "log analysis incomplete — blocking (fail-closed)"
}
```
The second `deny` is the important half: **unverifiable = blocked.**

## Testing a gate
- Unit-test the policy against a golden set (compliant + violating fixtures).
- The ZAVA `gate-efficacy` eval is the acceptance test — it must show the gate closes on a
  real seeded violation, in CI, before the gate is trusted.

## Files
- Policy: `spine/policies/<id>.rego`
- Config (block/warn/escalate, silence rights): `spine/gates/gate-config.yaml`
- Eval: `zava/datasets/<id>-efficacy/`
