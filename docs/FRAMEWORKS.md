# Framework packs

A **framework pack** groups the gates that enforce one regulation. The gate carries its
never-delegate principle, its ZAVA cases, and its article references, so a pack is simply the set
of gate names for a regulation. Packs make "which regulation" a first-class, queryable unit.

The spine ships two packs — **GDPR** and **EU AI Act** — declared in
[`spine/frameworks.yaml`](../spine/frameworks.yaml).

## Inspect

```bash
compliance-spine frameworks                 # list packs + gate coverage (+ any unassigned gates)
compliance-spine matrix --framework gdpr    # the compliance matrix for one pack
```

## Add a pack

A new regulation (including a sector regulation an adopter needs) is added the same way the core
packs are built — nothing in the engine is hard-coded to GDPR/AI-Act:

1. **Write the gate(s).** Add a gate class under `gates/builtins/` (code-scanning) or a declaration
   gate, and register it in `gates/builtins/__init__.py`.
2. **Configure them.** Add each gate to `spine/gates/gate-config.yaml` (severity, build/run
   behaviour) with an `intent_ref`.
3. **State the intent.** Add a never-delegate principle for each gate in
   `spine/intent/never-delegate.md`, referencing the regulation's article(s) — the article text is
   what the compliance matrix reads.
4. **Prove it.** Add ZAVA cases under `zava/datasets/<gate>.jsonl` (block + allow).
5. **Declare the pack.** Add a `frameworks.yaml` entry:

   ```yaml
   frameworks:
     my-regulation:
       name: "My Regulation"
       description: "..."
       gates: [my-gate-a, my-gate-b]
   ```

`compliance-spine frameworks` then reports it, `matrix --framework my-regulation` scopes to it, and
`doctor` still checks every gate traces to a principle.

## Confidentiality

Keep customer identity out of pack names/descriptions; the regulated **sector** itself is fine.
A customer's own sector regulations are best added in their **private** repository, not here.
