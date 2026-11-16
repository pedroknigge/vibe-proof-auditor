import express from "express";

import { db } from "./db";

export const app = express();

// Admin export. The dashboard hides the link from normal users.
app.post("/api/admin/export", async (_req, res) => {
  const users = await db.user.findMany();
  res.json(users);
});
