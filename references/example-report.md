# Vibe-Proof Audit Report

**Project:** `/Users/demo/forgeboard`  
**Date:** 2026-08-24  
**Mode:** Production  
**Audit mode:** Deep  
**Product type:** `saas-multi-tenant`  
**Overall Score:** 5.4 / 10  
**Status:** BLOCKED FOR PRODUCTION  
**Stage note:** Not expected. Do not ship.

Worked example for the formula in `references/scoring.md` (ForgeBoard). Verdict and stage note from `references/gates.md` only.

## Snapshot (real)

- Next.js 14 App Router + TypeScript + Supabase (Postgres + Auth + Storage)
- `app/`, `src/lib/`, `supabase/migrations/`, `__tests__/`
- Test ratio: 4 test files / 62 TS source files
- No `gitleaks` job; `.env` not tracked; `.env.example` present
- Largest file: `src/lib/sync.ts` (912 lines)
- CI: `.github/workflows/ci.yml` (lint + unit tests)
- Vercel project linked; Docker absent
- README architecture section present; no `docs/adr/`

## Executive Summary

- Strengths: no secrets in the tree; lockfile and few dependencies; CI runs the unit suite; generic API errors hide stack traces.
- Weaknesses: task APIs load by id with no tenant check; RLS never enabled; no isolation tests; N+1 comments on the list endpoint.
- Verdict: applicable Security and Testing absolute gates fail. Do not ship.

## Category Scores

| Category | Score | Status | Notes |
|----------|-------|--------|-------|
| 1. Security | 4 | Fail | Critical AuthZ Fail; floor applied (`references/scoring.md`) |
| 2. Comprehension | 7 | Partial | README flow; 912-line `sync.ts` |
| 3. Testing | 5 | Fail | Critical isolation-test and edge/error-path Fail |
| 4. Architecture | 7 | Partial | Clear folders; tenant column unused |
| 5. Maintainability | 6 | Partial | God file; untracked TODOs |
| 6. Error handling | 7 | Partial | No user-facing stacks; reconnect logs, no retry |
| 7. Performance | 6 | Partial | N+1 on task comments |
| 8. Dependencies | 8 | Pass | Lockfile, no hallucinated packages |
| 9. Process / environments | 6 | Partial | Preview + prod; rollback via Vercel |
| 10. Product / scope | 5 | Partial | MVP named; no user evidence in-tree |

## Production Gates

| Gate | Status | Evidence |
|------|--------|----------|
| Critical security | Fail | `app/api/tasks/[id]/route.ts` GET/PATCH/DELETE by `id` only; `supabase/migrations/0001_init.sql` has no `ENABLE ROW LEVEL SECURITY`; Security score 4 |
| Testing | Fail | No test that user A is denied user B’s task; Testing score 5 |
| Error handling | Pass | API `error.ts` returns `{ error: "internal" }`; no stacks in responses; score 7 |
| Environment isolation | Pass | `.env.example` local; Vercel Preview vs Production; `vercel rollback` documented in README |
| Basic performance | Fail | `listTasks` queries comments per row in `src/lib/tasks.ts` |
| Dependency audit | Pass | `package-lock.json`; `npm audit` in CI; 11 runtime deps |
| Minimal docs | Pass | README runbook exists; env vars listed |
| Basic observability | Fail | `console.log` only; no request ids, metrics, or alerts |

## Category Detail

### 1. Security — 4/10 (Fail)

Marks: 28 checklist rows → 3 N/A + 25 applicable: 14 Pass, 4 Partial, 6 Fail, 1 `insufficient evidence` (includes **[C]** object-level AuthZ Fail). Ratio 16.5/25 → 7, then critical floor → **4**. See `references/scoring.md` worked example.

N/A: LLM prompt-injection (no LLM in the tree); production CORS (same-origin App Router, no cross-origin API); webhook signatures (billing is an unused Stripe sketch — no receiver).

`insufficient evidence`: secret rotation (no in-tree leak history; git log not proof of a past leak).

Fail: no secret-scan job in CI; **[C]** object-level AuthZ; frontend is the AuthZ boundary; roles not evaluated per resource; datastore rules (RLS off; would also apply if this were `saas-single-user` with an anon key); `task-attachments` public.

Partial: auth rate-limit (Supabase defaults only; no LLM/paid endpoint in tree); brute-force (same); XSS (`dangerouslySetInnerHTML` in `CommentBody.tsx`); security headers (no CSP).

Pass: **[C]** no hardcoded secrets; **[C]** no client-bundle secrets (`service_role` / `sk_live` absent from client; no `NEXT_PUBLIC_` server secret; `productionBrowserSourceMaps` not set); env/gitignore/`.env.example`; **[C]** AuthN server-side (`supabase.auth.getUser()`); mature provider; **[C]** session cookies (HttpOnly); session invalidation (Supabase Auth `signOut`); **[C]** Zod on task routes (no hardcoded `true` skip); parameterized Supabase client; least-privilege anon key; CSRF/SameSite; HTTPS on Vercel; no public admin/debug routes; security logs without tokens.

Evidence:

- `app/api/tasks/[id]/route.ts` — `supabase.from('tasks').select('*').eq('id', id).single()` with no `org_id` / `user_id` predicate.
- `middleware.ts` — redirects when `sb-access-token` cookie is missing; does not bind a tenant (AuthZ boundary is still the client).
- `supabase/migrations/0001_init.sql` — `tasks`, `comments`, `orgs` created; no RLS; `task-attachments` bucket `public: true`.
- `.github/workflows/ci.yml` — lint + `npm test`; no gitleaks/TruffleHog/secret-scanning job.

Gaps: IDOR on every task/comment route; RLS off; public attachments; no secret scan.

Fix: enable RLS (`org_id = auth.jwt()->>'org_id'`), enforce the same predicate in every route/action, make the bucket private + signed URLs, add CSP, add a secret-scan CI job.

### 2. Comprehension — 7/10 (Partial)

Evidence: `README.md` “Architecture” traces App Router → route handlers → Supabase. No `docs/adr/`. `src/lib/sync.ts` (912 lines) mixes realtime, cache, and billing.

Fix: split `sync.ts`; add a one-page ADR for tenant isolation.

Human interview: **not assessed** (author not asked). Not a gate.

### 3. Testing — 5/10 (Fail)

Marks: 8 applicable, 0 N/A → 3 Pass, 2 Partial, 3 Fail (includes **[C]** isolation tests and **[C]** edge/error paths). Ratio 0.5 → **5**.

Pass: **[C]** tests for critical flows (create/list); suite in CI; happy path. Partial: coverage undocumented; AuthZ still demo-shaped. Fail: **[C]** isolation tests; **[C]** principal edge cases and error paths (no 401/403/timeout); regression suite.

Evidence:

- `__tests__/tasks.test.ts` — create/list happy path only.
- No file matches `authz|idor|isolation|tenant`.
- `.github/workflows/ci.yml` runs `npm test`.

Gaps: no 401/403/timeout tests; no user-A/user-B case.

Fix: two seeded orgs; assert 404/403 on cross-org GET/PATCH/DELETE; add webhook timeout test.

### 4. Architecture — 7/10 (Partial)

Evidence: `app/api/` vs `src/lib/` separation. `tasks.org_id` exists but is not consulted in handlers. Server Actions and REST handlers duplicate writes.

Fix: one repository module that always filters by `org_id`; delete the duplicate Server Action path.

### 5. Maintainability — 6/10 (Partial)

Evidence: consistent Prettier/TS. `src/lib/sync.ts` god file. `TODO: fix later` in `src/lib/billing.ts` with no ticket.

Fix: split sync; file the billing TODO or delete the dead path.

### 6. Error handling — 7/10 (Partial)

**[C]** not swallowed: Pass (reconnect errors are logged). **[C]** no user-facing stacks: Pass.

Evidence: `app/api/error.ts` maps unknown errors to `{ error: "internal" }`. `src/lib/sync.ts` logs reconnect failures but has no retry budget or user-visible dead-sync state (Partial on retries/degradation).

Fix: retry with backoff; surface a dead-sync banner.

### 7. Performance — 6/10 (Partial)

Evidence: `src/lib/tasks.ts` `listTasks` loops `comments` per task (N+1). `tasks_org_id_idx` exists. No pagination on `/api/tasks`.

Fix: join/select comments in one query; `limit`/`cursor`.

### 8. Dependencies — 8/10 (Pass)

Evidence: `package-lock.json`; 11 runtime deps; no unpublished or slopsquatted names; `npm audit` in CI with `high` fail.

Fix: pin `supabase-js` to the minor already in the lockfile in `package.json`.

### 9. Process / environments — 6/10 (Partial)

Evidence: conventional commits; `.gitignore` includes `.env`; Preview vs Production on Vercel; no required CODEOWNERS.

Human interview (“agent never touches prod”): **not assessed**. Not a gate.

Fix: protect `main`; require CI + one review.

### 10. Product / scope — 5/10 (Partial)

Evidence: README claims “MVP: shared task board”. No interviews, metrics, or cut-list in-tree. `src/lib/billing.ts` is an unused Stripe sketch.

Fix: delete or hide billing until a written MVP check passes.

## Extras (not in overall)

| Extra | Score | Notes |
|-------|-------|-------|
| Data model / migrations | 5 | Schema versioned (Pass); no down migrations (Partial); restorable backup Fail (`vercel rollback` is not a DB backup) |
| Docs | 6 | README run/env; no ownership diagram |
| Mobile / responsive | 5 | Tailwind; no tested breakpoint below `md` |
| Accessibility | 4 | Icon buttons without names in `TaskRow.tsx` |
| Observability | 5 | `console.log` only |

## Why this dunks (plain language)

**P0 — anyone can open someone else's task.** The API loads a task by `id` and never checks org. A logged-in user who guesses (or lists) another org's id can read and edit it. That screenshot is the classic IDOR dunk. Ignore it and you leak customer data the day you have two tenants. Tell the model: *filter every task/comment query by `org_id` from the verified session, enable RLS with the same rule, private bucket + signed URLs.*

**P0 — you never proved user A can't see user B.** Happy-path tests exist. There is no test with two orgs. Seniors will say you only tested the demo. Without that test, the IDOR fix can regress next week. Tell the model: *two seeded orgs; A gets 403/404 on B's GET/PATCH/DELETE; fail CI if that fails.*

**P1 — the list endpoint queries comments once per row.** Works with 10 tasks. Falls over with 500. Tell the model: *one query for comments; paginate `/api/tasks`.*

## Prioritized Remediation

1. **P0** — Object-level AuthZ + RLS + private storage on tasks, comments, attachments.
2. **P0** — Isolation tests (two orgs) on GET/PATCH/DELETE; fail CI if they fail.
3. **P1** — Kill N+1 list query; add sync retry/backoff; add CSP.
4. **P1** — Split `sync.ts`; require review on `main`.
5. **P2** — ADR for tenancy; a11y names; request-id logs; delete unused billing.

## Remediation Prompt (copy-paste)

```
You are remediating ForgeBoard after a vibe-proof-auditor pass (BLOCKED FOR PRODUCTION).

Do not argue with the findings. Implement P0 first, then P1. Keep diffs small.

P0:
1. Enable RLS on `tasks`, `comments`, `orgs`, `task-attachments`. Policies: a row is visible only when `org_id` equals the JWT org claim. Revoke public bucket access; use signed URLs.
2. In every route and Server Action that loads a task or comment by id (`app/api/tasks/[id]/route.ts` and duplicates), filter by both `id` and `org_id` from the verified session. Do not trust middleware alone.
3. Add tests with two orgs: user A must receive 403/404 on user B’s task GET/PATCH/DELETE. Wire them into `.github/workflows/ci.yml`.

P1:
4. Replace per-row comment queries in `src/lib/tasks.ts` with one query; paginate `/api/tasks`.
5. Add retry/backoff in `src/lib/sync.ts` and user-visible resync state.
6. Add a strict CSP; split `src/lib/sync.ts` into realtime / cache / billing modules; billing stays unshipped.

Do not add features. Do not weaken tests to make them pass.
```
