// Extension: compliance-dashboard
// A Copilot app canvas for the compliance spine. Reads the repo's evidence ledger and
// `compliance-spine matrix --json` and renders an evidence feed, an adjudication queue, the
// compliance matrix, and ghost decisions — and writes adjudications back *through the CLI* so
// the hash-chained ledger stays the single source of truth.
//
// Faithful to the verified canvas pattern: a local 127.0.0.1 HTTP server serves the UI + a REST
// API; createCanvas() declares agent/UI actions; joinSession() wires agent tools. The data layer
// lives in ./data.mjs (SDK-free, unit-tested).

import { CanvasError, createCanvas, joinSession } from "@github/copilot-sdk/extension";
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { adjudicate, buildDashboard, setCwd } from "./data.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// The session reports the active repo checkout as `workingDirectory` (not workspacePath, which
// is the session-state folder) — everything resolves relative to it.
function captureCwd(ctx) {
  setCwd(ctx?.session?.workingDirectory);
}

function adjudicateOrThrow(input) {
  try {
    return adjudicate(input);
  } catch (err) {
    throw new CanvasError("adjudicate_failed", err.message || String(err));
  }
}

// ─── SSE for live refresh ───

const sseClients = new Set();
function broadcast() {
  const msg = `event: state\ndata: ${JSON.stringify(buildDashboard())}\n\n`;
  for (const res of sseClients) {
    try {
      res.write(msg);
    } catch {
      sseClients.delete(res);
    }
  }
}

// ─── HTTP server (localhost only) ───

function readJson(req) {
  return new Promise((resolve, reject) => {
    let body = "";
    req.on("data", (c) => (body += c));
    req.on("end", () => resolve(body ? JSON.parse(body) : {}));
    req.on("error", reject);
  });
}
function json(res, code, data) {
  res.writeHead(code, { "Content-Type": "application/json" });
  res.end(JSON.stringify(data));
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);

  if (url.pathname === "/events") {
    res.writeHead(200, { "Content-Type": "text/event-stream", "Cache-Control": "no-cache", Connection: "keep-alive" });
    sseClients.add(res);
    req.on("close", () => sseClients.delete(res));
    res.write(`event: state\ndata: ${JSON.stringify(buildDashboard())}\n\n`);
    return;
  }
  if (req.method === "GET" && url.pathname === "/api/dashboard") {
    json(res, 200, buildDashboard());
    return;
  }
  if (req.method === "POST" && url.pathname === "/api/adjudicate") {
    try {
      const result = adjudicate(await readJson(req));
      broadcast();
      json(res, 200, { ...result, state: buildDashboard() });
    } catch (err) {
      json(res, 400, { error: err.message || String(err) });
    }
    return;
  }
  if (url.pathname === "/") {
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    res.end(fs.readFileSync(path.join(__dirname, "public", "index.html"), "utf8"));
    return;
  }
  res.writeHead(404);
  res.end("Not found");
});

await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const port = () => server.address().port;

// ─── Canvas + session ───

const canvas = createCanvas({
  id: "compliance-dashboard",
  displayName: "Compliance Dashboard",
  description:
    "Evidence feed, adjudication queue, compliance matrix, and ghost decisions for the compliance spine (GDPR + EU AI Act).",
  actions: [
    {
      name: "get_dashboard",
      description: "Return the current compliance dashboard: evidence, pending findings, matrix, ghosts, integrity.",
      inputSchema: { type: "object", properties: {}, additionalProperties: false },
      handler(ctx) {
        captureCwd(ctx);
        return buildDashboard();
      },
    },
    {
      name: "adjudicate_finding",
      description: "Confirm or dismiss a reasoned/assessor finding (evt_* id) — recorded to the ledger via the CLI.",
      inputSchema: {
        type: "object",
        properties: {
          finding_id: { type: "string", description: "the evt_* id of the finding" },
          outcome: { type: "string", enum: ["confirmed", "dismissed"] },
          human: { type: "string", description: "the deciding human's id" },
          signature: { type: "string" },
          reason: { type: "string" },
        },
        required: ["finding_id", "outcome"],
        additionalProperties: false,
      },
      handler(ctx) {
        captureCwd(ctx);
        const result = adjudicateOrThrow(ctx.input);
        broadcast();
        return result;
      },
    },
    {
      name: "refresh",
      description: "Re-read the ledger and matrix and push the latest state to the panel.",
      inputSchema: { type: "object", properties: {}, additionalProperties: false },
      handler(ctx) {
        captureCwd(ctx);
        broadcast();
        return buildDashboard();
      },
    },
  ],
  open(ctx) {
    captureCwd(ctx);
    const d = buildDashboard();
    return {
      url: `http://127.0.0.1:${port()}`,
      title: "Compliance Dashboard",
      status: `${d.ledgerSize} evidence records · ${d.pending.length} pending`,
    };
  },
});

const session = await joinSession({
  canvases: [canvas],
  tools: [
    {
      name: "compliance_dashboard_state",
      description: "Get the compliance spine dashboard state (evidence, pending findings, matrix, ghosts).",
      parameters: { type: "object", properties: {}, additionalProperties: false },
      handler: async () => JSON.stringify(buildDashboard()),
    },
    {
      name: "compliance_adjudicate",
      description: "Confirm or dismiss a compliance finding (evt_* id); writes a hash-chained ledger record.",
      parameters: {
        type: "object",
        properties: {
          finding_id: { type: "string" },
          outcome: { type: "string", enum: ["confirmed", "dismissed"] },
          human: { type: "string" },
          signature: { type: "string" },
          reason: { type: "string" },
        },
        required: ["finding_id", "outcome"],
      },
      handler: async (args) => {
        const result = adjudicateOrThrow(args);
        broadcast();
        return JSON.stringify(result);
      },
    },
  ],
});

void session;
