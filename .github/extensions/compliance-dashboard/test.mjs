// SDK-free tests for the dashboard data layer. Run: `node test.mjs` (no Copilot app needed).
import assert from "node:assert/strict";
import * as d from "./data.mjs";

const LEDGER = [
  { id: "evt_a", action: "block", severity: "critical", rule_id: "spine/policies/no-pii-in-logs",
    actor: { type: "gate", id: "no-pii-in-logs" }, subject: { change: "pr-1" },
    findings: [{ file: "svc/auth.py", line: 2, message: "logs personal-data attribute 'user'" }] },
  { id: "evt_b", action: "emit", severity: "high", rule_id: "llm/automated-decision", confidence: 0.8,
    actor: { type: "llm", id: "reasoning" }, subject: { change: "pr-1", kind: "automated-decision", note: "no human path" },
    findings: [{ file: "risk/service.js", line: 116, message: "auto-declines (Art 22)" }] },
  { id: "evt_c", action: "emit", severity: "info", rule_id: "llm/pii-in-response", confidence: 0.55,
    subject: { change: "pr-1", kind: "pii-in-response" }, findings: [{ file: "api.js", line: 9, message: "returns PII" }] },
  { id: "evt_d", action: "block", rule_id: "human/adjudication", subject: { adjudicates: "evt_c", outcome: "confirmed" } },
];

const fakeSpine = (a) => {
  if (a[0] === "matrix") return { ok: true, stdout: JSON.stringify({ rows: [{ rank: 1, gate: "no-pii-in-logs", status: "enforced" }] }) };
  if (a[0] === "verify") return { ok: true, stdout: "[OK] chain intact" };
  if (a[0] === "ghosts") return { ok: true, stdout: "no ghost decisions" };
  return { ok: false, stdout: "", stderr: "", missing: false };
};

// pending = llm/* not yet adjudicated (evt_c was adjudicated by evt_d)
const pending = d.pendingFindings(LEDGER);
assert.deepEqual(pending.map((r) => r.id), ["evt_b"], "only un-adjudicated llm/* findings are pending");

assert.deepEqual(d.summarize(LEDGER), { block: 2, allow: 0, emit: 2, override: 0, escalate: 0 });

const dash = d.buildDashboard({ spine: fakeSpine, readLedger: () => LEDGER });
assert.equal(dash.ledgerSize, 4);
assert.equal(dash.evidence.length, 4);
assert.equal(dash.pending.length, 1);
assert.equal(dash.evidence[0].id, "evt_d", "evidence is most-recent-first");
assert.deepEqual(
  dash.evidence.find((e) => e.id === "evt_a").findings[0],
  { file: "svc/auth.py", line: 2, message: "logs personal-data attribute 'user'" },
  "findings carry file:line:message",
);
assert.equal(dash.matrix.available, true);
assert.equal(dash.matrix.rows.length, 1);
assert.equal(dash.integrity.ok, true);

// adjudicate builds the right CLI argv and reports failure cleanly
const calls = [];
const okAdj = (a) => (calls.push(a), { ok: true, stdout: "adjudication recorded" });
const res = d.adjudicate({ finding_id: "evt_b", outcome: "confirmed", human: "DPO" }, okAdj);
assert.equal(res.ok, true);
assert.deepEqual(calls[0].slice(0, 5), ["adjudicate", "evt_b", "--outcome", "confirmed", "--human"]);

assert.throws(() => d.adjudicate({ finding_id: "evt_b", outcome: "nope" }, okAdj), /confirmed\|dismissed/);
assert.throws(() => d.adjudicate({ finding_id: "evt_b", outcome: "confirmed" }, () => ({ ok: false, missing: true })), /not on PATH/);

console.log("compliance-dashboard data layer: all assertions passed");
