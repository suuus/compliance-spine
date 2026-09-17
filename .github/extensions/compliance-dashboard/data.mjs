// Pure data layer for the compliance-dashboard canvas — node builtins only, no SDK import,
// so it is unit-testable outside the Copilot app. extension.mjs wires this to the canvas/HTTP.

import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

let workspaceCwd = null;

export function setCwd(dir) {
  if (typeof dir === "string" && dir.trim()) workspaceCwd = dir;
}
export function repoRoot() {
  return workspaceCwd || process.env.COMPLIANCE_SPINE_ROOT || process.cwd();
}

// Run the compliance-spine CLI at the repo root, pinning COMPLIANCE_SPINE_ROOT (needed when the
// repo has no pyproject.toml). Returns a structured result; never throws.
export function spine(args, run = spawnSync) {
  const root = repoRoot();
  const res = run("compliance-spine", args, {
    cwd: root,
    encoding: "utf8",
    env: { ...process.env, COMPLIANCE_SPINE_ROOT: root },
  });
  return {
    ok: res.status === 0 && !res.error,
    code: res.status,
    stdout: (res.stdout || "").trim(),
    stderr: (res.stderr || "").trim(),
    missing: Boolean(res.error && res.error.code === "ENOENT"),
  };
}

export function ledgerPath() {
  return path.join(repoRoot(), "evidence", "ledger", "decisions.ledger.jsonl");
}

export function readLedger() {
  try {
    return fs
      .readFileSync(ledgerPath(), "utf8")
      .split("\n")
      .filter((l) => l.trim())
      .map((l) => {
        try {
          return JSON.parse(l);
        } catch {
          return null;
        }
      })
      .filter(Boolean);
  } catch {
    return [];
  }
}

// An assessor/reasoning finding (rule_id "llm/*") is pending until a "human/adjudication"
// record references its id via subject.adjudicates.
export function pendingFindings(records) {
  const adjudicated = new Set(
    records
      .filter((r) => r.rule_id === "human/adjudication")
      .map((r) => r.subject && r.subject.adjudicates)
      .filter(Boolean),
  );
  return records.filter(
    (r) => String(r.rule_id || "").startsWith("llm/") && !adjudicated.has(r.id),
  );
}

export function summarize(records) {
  const by = { block: 0, allow: 0, emit: 0, override: 0, escalate: 0 };
  for (const r of records) if (r.action in by) by[r.action] += 1;
  return by;
}

export function matrixRows(runSpine = spine) {
  const out = runSpine(["matrix", "--json"]);
  if (!out.ok) {
    return { available: false, rows: [], hint: out.missing ? "compliance-spine not on PATH" : out.stderr };
  }
  try {
    const parsed = JSON.parse(out.stdout);
    return { available: true, rows: Array.isArray(parsed) ? parsed : parsed.rows || [] };
  } catch {
    return { available: false, rows: [], hint: "could not parse matrix --json" };
  }
}

export function ghostLines(runSpine = spine) {
  const out = runSpine(["ghosts"]);
  if (out.missing) return { available: false, lines: [] };
  return { available: true, lines: out.stdout.split("\n").filter((l) => l.trim() && !/no ghost/i.test(l)) };
}

export function integrity(runSpine = spine) {
  const out = runSpine(["verify"]);
  if (out.missing) return { available: false, ok: null, detail: "compliance-spine not on PATH" };
  return { available: true, ok: out.ok, detail: (out.stdout || out.stderr).split("\n")[0] || "" };
}

export function buildDashboard(deps = {}) {
  const runSpine = deps.spine || spine;
  const records = (deps.readLedger || readLedger)();
  const recent = records.slice(-200).reverse();
  return {
    updatedAt: new Date().toISOString(),
    repoRoot: repoRoot(),
    counts: summarize(records),
    ledgerSize: records.length,
    integrity: integrity(runSpine),
    evidence: recent.map((r) => ({
      id: r.id,
      ts: r.ts,
      action: r.action,
      severity: r.severity,
      actor: r.actor || {},
      rule_id: r.rule_id,
      change: (r.subject && r.subject.change) || "",
      confidence: r.confidence,
      findings: r.findings || [],
    })),
    pending: pendingFindings(records).map((r) => ({
      id: r.id,
      kind: (r.subject && r.subject.kind) || String(r.rule_id || "").replace(/^llm\//, ""),
      confidence: r.confidence,
      note: (r.subject && r.subject.note) || "",
      findings: r.findings || [],
    })),
    matrix: matrixRows(runSpine),
    ghosts: ghostLines(runSpine),
  };
}

// Write-through adjudication — the CLI appends the hash-chained record; the ledger stays the
// source of truth. Throws Error on bad input or CLI failure (the caller maps to CanvasError).
export function adjudicate(input, runSpine = spine) {
  const { finding_id, outcome, human, signature, reason } = input || {};
  if (!finding_id || !/^(confirmed|dismissed)$/.test(outcome || "")) {
    throw new Error("finding_id and outcome (confirmed|dismissed) are required");
  }
  const args = [
    "adjudicate", finding_id,
    "--outcome", outcome,
    "--human", human || "canvas-reviewer",
    "--signature", signature || "canvas",
  ];
  if (reason) args.push("--reason", reason);
  const out = runSpine(args);
  if (!out.ok) {
    throw new Error(out.missing ? "compliance-spine not on PATH" : out.stderr || out.stdout || "adjudicate failed");
  }
  return { ok: true, detail: out.stdout };
}
