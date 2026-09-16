# Pilot runbook

A short, opinionated path for a **design-partner pilot** of the compliance spine on one real
repository. Plan for ~1 day to stand up, then a 2–4 week pilot. It assists and *evidences*
compliance — **it is not legal advice and does not certify compliance** (see [README §13](../README.md)).

## Who's in the room
- **Engineering owner** — installs, wires CI, triages findings.
- **DPO / privacy owner** — signs `spine/intent/never-delegate.md`, owns adjudications.
- (Optional) **the coding agent** you're governing (GitHub Copilot / any MCP client).

## Set expectations first (read these aloud)
1. **The ceiling defaults to a *heuristic* assessor**, not an LLM. Real non-deterministic review
   needs you to wire your own Copilot / Azure AI Foundry model (see [LLM-LAYER](./LLM-LAYER.md)).
2. **Tuning is the work.** Out of the box the gates use generic field/component names; expect
   false positives/negatives until `data-catalogue.yaml` and `access-boundaries.yaml` are yours.
3. **It fail-closes.** A control it can't verify **blocks or escalates** — never passes silently.
   You get a bounded human override + an adjudication path; wire them before you turn CI on.
4. **Coverage is uneven by language.** Deterministic gates are pattern-based (strong on common
   Python/JS shapes); the assessor covers the judgment-heavy long tail as *advisory* findings.
5. **Scope is GDPR + EU AI Act.** Sector rules (e.g. financial-supervision) are **your** private
   framework pack — see [FRAMEWORKS](./FRAMEWORKS.md). Nothing sector-specific ships in the core.
6. **Install in isolation.** The `[mcp]` extra's web deps can clash with an app's own; use a
   **dedicated venv or `pipx`**, not the app's runtime environment.

## Stand it up (≈1 day)

**1. Install (isolated).**
```bash
python -m venv .spine-venv && source .spine-venv/bin/activate
pip install "compliance-spine[zava,mcp] @ git+https://github.com/suuus/compliance-spine"
```
> A `git clone ... SSL_ERROR_SYSCALL` here is your **network/proxy**, not the package — retry off
> VPN or configure the proxy. Prefer `pipx install` for a self-contained CLI.

**2. Scaffold + tune (the real work).**
```bash
compliance-spine init            # writes a working spine/ + evidence/schema (doctor passes)
```
Then edit the four files `init` created:
- `spine/intent/never-delegate.md` — assign **real owners + signatures** (DPO).
- `spine/data-catalogue.yaml` — **your** personal / special-category field names.
- `spine/access-boundaries.yaml` — **your** components that must never touch raw PII.
- `spine/gates/gate-config.yaml` — severities / silence policy / circuit-breaker.

**3. Verify.**
```bash
compliance-spine doctor          # every gate traces to a principle
compliance-spine matrix          # regulation → article → gate → coverage (regulator-facing)
compliance-spine frameworks      # which packs are active
```
> Non-Python repo? Set `COMPLIANCE_SPINE_ROOT=/path/to/repo` (authoritative).

**4. Turn on enforcement — start advisory, then required.**
- **Local:** `pre-commit install` (runs `scan-diff --staged`) — fast feedback for developers.
- **CI (advisory first):** run the gate on the PR diff **without** blocking merges for week 1:
  ```bash
  compliance-spine scan-diff --base origin/<base>     # deterministic floor
  compliance-spine llm-review --base origin/<base>    # floor ∪ ceiling (assessor)
  ```
  Then promote it to a **required** check once the noise is tuned out.
- **Copilot-native (optional):** copy `.github/agents/`, `.github/skills/`, `.github/instructions/`,
  `.github/copilot-instructions.md`, and register `.mcp.json → compliance-spine-mcp`.

## Run the loop (the pilot)
1. Open PRs as usual; the gate annotates them (floor block + ceiling advisory flags).
2. **Triage each finding:**
   - True positive → fix, or `compliance-spine override <change> <gate> --reason … --signer …`
     for a bounded, co-signed exception.
   - Advisory ceiling flag → `compliance-spine adjudicate <FINDING_ID> --outcome confirmed|dismissed
     --human <you> --signature <sig>`. `compliance-spine learn` shows the confirmed/dismissed/pending set.
   - False positive → tune the catalogue/boundaries or `spine/scan-ignore`; note it for feedback.
3. **Evidence:** `compliance-spine verify` (hash-chain intact) and
   `compliance-spine export <CHANGE_ID> --out bundle.json` (audit / DSAR bundle) prove the trail.

## Call it a success if…
- Every gate traces to a signed principle (`doctor` green) and the catalogue/boundaries reflect
  the repo's real data and components.
- The gate is a **required** CI check and has **caught ≥1 real issue** the team agrees was worth it.
- The **false-positive rate is livable** (tuned), and every override/adjudication has a named human.
- The DPO can read the `matrix` and an exported evidence bundle and trust them.

## Feedback loop
Capture, each week: false positives (with the file/pattern), gaps the assessor should have caught,
and any friction in `init` / tuning. These become new gates (via `adjudicate` → `learn`), catalogue
entries, or a private framework pack. File them as issues on the spine repo.

> **Not legal advice.** A qualified human (DPO/legal) owns the sign-off. The spine makes that
> judgment cheaper, enforced, and evidenced — it does not replace it.
