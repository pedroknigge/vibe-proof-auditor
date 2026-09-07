// Feature 1: billing.
// Transport: express. Auth: bearer JWT. Logging: pino JSON. Config: process.env.
// Errors: { error: { code, message } } with a 4xx/5xx status.
import express from "express";
import jwt from "jsonwebtoken";
import pino from "pino";

const log = pino({ name: "billing", level: process.env.LOG_LEVEL ?? "info" });

const config = {
  port: Number(process.env.BILLING_PORT ?? 3001),
  jwtSecret: process.env.JWT_SECRET ?? "",
  stripeKey: process.env.STRIPE_KEY ?? "",
};

function requireJwt(req: any, res: any, next: any) {
  const header = String(req.headers.authorization ?? "");
  const token = header.startsWith("Bearer ") ? header.slice(7) : "";
  try {
    req.actor = jwt.verify(token, config.jwtSecret);
    next();
  } catch {
    res.status(401).json({ error: { code: "unauthenticated", message: "bad token" } });
  }
}

export function startBilling() {
  const app = express();
  app.use(express.json());
  app.get("/invoices/:id", requireJwt, (req, res) => {
    log.info({ invoice: req.params.id, actor: (req as any).actor?.sub }, "invoice read");
    res.json({ id: req.params.id, amount_cents: 1200 });
  });
  app.listen(config.port, () => log.info({ port: config.port }, "billing up"));
}
