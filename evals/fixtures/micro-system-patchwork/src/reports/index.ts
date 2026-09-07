// Feature 2: reports.
// MICRO-SYSTEM-PATCHWORK: same cross-cutting concerns as billing, solved
// differently on every axis.
//   Transport: raw node:http instead of express.
//   Auth: a shared X-API-Key compared against a file, instead of bearer JWT.
//   Logging: console.log with a pipe-delimited line, instead of pino JSON.
//   Config: reports.config.json read off disk, instead of process.env.
//   Errors: a plain-text body with status 200 and { ok: false }, instead of 4xx.
import http from "node:http";
import fs from "node:fs";

type ReportsConfig = { port: number; apiKeyFile: string };

const config: ReportsConfig = JSON.parse(
  fs.readFileSync(new URL("./reports.config.json", import.meta.url), "utf8"),
);

function logLine(level: string, message: string) {
  console.log(`reports|${level}|${new Date().toISOString()}|${message}`);
}

function checkApiKey(req: http.IncomingMessage): boolean {
  const presented = String(req.headers["x-api-key"] ?? "");
  const expected = fs.readFileSync(config.apiKeyFile, "utf8").trim();
  return presented.length > 0 && presented === expected;
}

export function startReports() {
  const server = http.createServer((req, res) => {
    if (!checkApiKey(req)) {
      logLine("warn", `rejected ${req.url}`);
      // Different error convention: 200 with ok:false, no code, no message shape.
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify({ ok: false }));
      return;
    }
    logLine("info", `served ${req.url}`);
    res.writeHead(200, { "content-type": "application/json" });
    res.end(JSON.stringify({ ok: true, rows: [] }));
  });
  server.listen(config.port, () => logLine("info", `reports up on ${config.port}`));
}
