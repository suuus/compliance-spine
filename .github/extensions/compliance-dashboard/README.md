# Compliance Dashboard (Copilot app canvas)

A [GitHub Copilot **canvas extension**](https://docs.github.com/en/copilot/how-tos/github-copilot-app/working-with-canvas-extensions)
that gives the compliance spine a UI in the app's side panel:

- **Evidence feed** — ledger records grouped by gate, each with its findings (`file:line: message`).
- **Adjudication queue** — pending assessor/reasoned findings (`llm/*`) with **Confirm / Dismiss**
  buttons that write through `compliance-spine adjudicate` (the hash-chained ledger stays the
  source of truth).
- **Compliance matrix** — regulation → article → gate → coverage, from `compliance-spine matrix --json`.
- **Ghosts + integrity** — unowned decisions (`compliance-spine ghosts`) and a ledger-intact badge
  (`compliance-spine verify`).

Live-updates over SSE; read-mostly (all writes go through the CLI).

## Use it
This ships in the repo under `.github/extensions/` (project scope), so the GitHub Copilot app
discovers it automatically. Open a session in a repo that has adopted the spine and ask:

```
Open the Compliance Dashboard canvas
```

The agent can also drive it via the tools `compliance_dashboard_state` and `compliance_adjudicate`,
or the canvas actions `get_dashboard` / `adjudicate_finding` / `refresh`.

**Prereqs:** the `compliance-spine` CLI must be on `PATH` for the matrix/ghosts/verify/adjudicate
features (the evidence feed reads the ledger file directly and works without it). The panel
resolves the repo from the session's working directory and pins `COMPLIANCE_SPINE_ROOT`.

## Files
- `extension.mjs` — canvas + local HTTP server + `joinSession` wiring (uses `@github/copilot-sdk`).
- `data.mjs` — SDK-free data layer (reads the ledger, shells out to the CLI, builds dashboard state).
- `public/index.html` — the panel UI (vanilla HTML/JS + SSE, no build step).
- `test.mjs` — `node test.mjs` unit-tests the data layer (no app required).

## Status
Starter / reference. The data layer is unit-tested; the canvas/SDK wiring follows the documented
API but should be exercised in the GitHub Copilot desktop app. Iterate with `/create-canvas` or by
editing these files. Not legal advice — it visualizes the spine; a human owns the sign-off.
