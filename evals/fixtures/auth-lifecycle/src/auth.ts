import { createHash } from "node:crypto";

import { db } from "./db";

export function hashPassword(password: string): string {
  return createHash("sha256").update(password).digest("hex");
}

export async function resetPassword(token: string, password: string) {
  const record = await db.resetToken.findUnique({ where: { token } });
  if (!record) {
    throw new Error("invalid token");
  }
  await db.user.update({
    where: { id: record.userId },
    data: { password_hash: hashPassword(password) },
  });
}
