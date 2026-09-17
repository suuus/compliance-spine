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
- **Action buttons** — a toolbar to run common commands from the panel (Refresh, Scan staged,
  Verify ledger, Run ZAVA, Scan ghosts, Diagnose); output shows inline.
- **Resolution diagnostic** — the header shows whether the CLI + ledger were found and which repo
  root resolved, so a "no findings" problem is diagnosable at a glance.

Live-updates over SSE; read-mostly (all writes go through the CLI).

## Finding the `compliance-spine` CLI (important)
The Copilot app launches the extension **without your venv on `PATH`**, so a bare `compliance-spine`
fails. The extension resolves the binary automatically, in order:
1. `$COMPLIANCE_SPINE_BIN` (explicit override),
2. `<repo>/.venv/bin/compliance-spine` then `<repo>/.spine-venv/bin/compliance-spine` (the adopter
   convention),
3. `~/.local/bin/compliance-spine` (pipx),
4. bare `compliance-spine` on `PATH`.

If the header shows **⚠ cli on PATH?**, set `COMPLIANCE_SPINE_BIN` to the absolute binary path (or
`pipx install "compliance-spine[mcp]"` for a global one). The evidence feed reads the ledger file
directly, so findings show even before the CLI resolves; matrix/ghosts/verify/adjudicate need it.

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
