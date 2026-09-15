# Governance — roles, gates, and overrides

Who owns what, when a human must decide, and how an override works. This is the
human-in-the-loop layer that makes "the spine signed off" a real answer.

## Roles
| Role | Owns | Notes |
|---|---|---|
| **DPO / Privacy lead** | **Intent** — the never-delegate list; the constitutional read | Signs the spine. Reader-of-record for Evidence. |
| **Spine author** (privacy/platform engineer) | **Structure** — writes + maintains the policy-as-code gates | Every rule carries their signature. |
| **Steward** | Delivery + outcomes for a domain; first reader of Evidence against Intent | Does not manage people. |
| **Cell** (product + engineering + business minds + agents) | **Execution** — ships inside the spine | Inherits Intent + Structure; owes Evidence upward. |

Accountability lives at the **authorship layer** — wherever the spine last had a human
signature. If a rule has no author, accountability has nowhere to land.

## Human review gates (the moments that matter)
A human must approve when a change:
1. introduces **new personal-data processing** or a new data category;
2. is classified **high-risk** under the AI Act, or moves toward a **prohibited** practice;
3. performs a **cross-border transfer** (GDPR Chapter V);
4. makes an **automated decision** with legal or significant effect (Art 22) — approval must
   confirm a human-intervention path and a contestable explanation exist;
5. **silences** a spine rule (see below).

The approver's signature is what turns a ghost decision into an owned one, and it lands in
Evidence with a trace to the rule and the Intent principle.

## Silencing (the only way to open a closed gate)
Gates are fail-closed. A closed gate does **not** get bypassed informally. It can only be
**silenced**, and silencing is itself governed:
- **Time-boxed** — a named expiry date, not "we'll revisit".
- **Justified in writing** — why, and the compensating control.
- **Signed** — by a spine author *and* the DPO for anything critical.
- **Logged in Evidence** — as an `override` event, with owner + reason + expiry.
- **Local** — silenced for one domain/context, not removed globally.
- **Auto-expires** — the rule re-arms unless explicitly renewed.

*A spine that can be overridden informally is not a spine.*

## Human-in-command (runtime)
For deployed systems, a human (or the DPO on escalation) can **halt** a processing path —
the AI Act Art 14 stop. The circuit-breaker (README §4) is the automated version; the halt
is the manual one. Both produce Evidence.

## The constitutional read
Someone must periodically ask the questions no dashboard answers: *is Intent still right? are
ghost decisions accumulating? does the evidence challenge a belief we held last quarter?*
That reader-of-record is the DPO/steward. No reader-of-record is a choice; **no one reading is
not**.
