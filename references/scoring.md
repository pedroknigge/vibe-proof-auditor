# Scoring

Single home for **weights**, **formula**, **critical floors**, **scale**, **product-type N/A matrix**, and **mark values**. Gates, verdict strings, and stage notes live in `references/gates.md`. Checklist items live in `references/checklist.md`. Mode (Prototype / MVP / Production) does not change weights, floors, or N/A.

## Ten scored categories (weights)

| # | Category | Weight |
|---|----------|--------|
| 1 | Security | 2.0 |
| 2 | Comprehension | 1.0 |
| 3 | Testing | 1.5 |
| 4 | Architecture | 1.3 |
| 5 | Maintainability | 1.3 |
| 6 | Error handling | 1.0 |
| 7 | Performance | 1.0 |
| 8 | Dependencies | 1.0 |
| 9 | Process / environments | 1.0 |
| 10 | Product / scope | 1.0 |

Sum of weights = **12.1**.

## Extras (report only)

Score for the report, **exclude from overall**:

- Handoff readiness
- Data model / migrations
- Docs
- Mobile / responsive
- Accessibility
- Observability

## Marks

Per applicable checklist item:

| Mark | Value |
|------|-------|
| Pass | 1 |
| Partial | 0.5 |
| Fail | 0 |
| N/A | excluded (not in numerator or denominator) |
| insufficient evidence | excluded from the ratio (tool failed or file unreadable). Not a Partial. Not a critical Fail. Do not apply a critical floor. Counts only in **Evidence coverage**. |
| not assessed | excluded — human-interview only, never a Fail |

Publish a **Mark census** table per `SKILL.md` before the ratio. N/A listed separately. `Pass + Partial + Fail + insufficient evidence` **must equal** the applicable count (items that are not N/A). If they do not sum, recount. Do not divide by a number you did not list.

`known = Pass + Partial + Fail`

`category_ratio = sum(marks of known items) / known`

`insufficient evidence` is not in `known`. If `known` is 0, the category is N/A for the overall (omit it; subtract its weight). Never substitute 0. A category that is all `insufficient evidence` is not Pass.

**Evidence coverage** (report header; not a category score):

`coverage = known / (known + insufficient evidence)` across the ten scored categories. N/A is not in this fraction. Publish as an integer percent, half up. `scripts/validate-report.py` recomputes it.

`category_score = round(category_ratio * 10)` to nearest integer, **half up**.

Then apply **critical floors** (critical items are marked in `references/checklist.md`):

- Any **critical** applicable Security item is Fail → cap Security at 4.
- Any **critical** applicable Testing item is Fail → cap Testing at 6.
- Any **critical** applicable Error handling item is Fail → cap Error handling at 6.

Floors cap; they never raise a score.

## Overall

`overall = Σ(weight_i × category_score_i) / D` to **one decimal** (half up).

`D = 12.1` when all ten categories are applicable. If a category is fully N/A, `D` is 12.1 minus that category’s weight.

Do not include extras in `D` or the numerator.

Feed `overall`, category scores, and Evidence coverage into `references/gates.md` for the verdict and stage note. Do not apply verdict or stage-note logic here.

## Category status (report table)

| Status | When |
|--------|------|
| N/A | every item in the category is N/A |
| Fail | score 0–4, **or** a critical applicable item is Fail |
| Partial | score 5–7 and no critical applicable Fail |
| Pass | score 8–10 and no critical applicable Fail |

## Scale (category 0–10)

| Score | Meaning |
|-------|---------|
| 9–10 | Exemplary / production-grade |
| 7–8 | Strong |
| 5–6 | Adequate with important gaps |
| 3–4 | Significant issues |
| 0–2 | Critical failure / absent |

## Product-type N/A matrix

Infer type from the tree. Item-level N/A is the mechanism; a category is N/A only if every item is N/A.

| Product type | Typically N/A or reduced |
|--------------|--------------------------|
| `saas-multi-tenant` | Almost nothing. Datastore rules (RLS / Firebase rules) apply. |
| `saas-single-user` | Cross-user AuthZ and IDOR tests N/A if there is no sharing and no user-owned foreign resources. AuthN still applies if accounts exist. Datastore rules (RLS / Firebase rules) **apply** when a client key can read rows — not N/A merely because the product is single-user. |
| `cli` | Browser XSS/CSP/headers/CORS, mobile/responsive, accessibility. AuthN/AuthZ N/A unless the CLI calls user-scoped APIs. Client-bundle secrets N/A unless it ships a browser bundle. Webhooks N/A unless it receives them. |
| `library` | AuthN/AuthZ, SaaS env isolation, XSS unless it renders HTML, mobile, a11y, service observability, CORS unless it serves HTTP. Tests, deps, errors, maintainability still apply. Publish/rollback docs may apply. Client-bundle secrets N/A unless it ships client JS. Webhooks N/A unless it receives them. |
| `static-site` | Server AuthZ/IDOR, data rollback, N+1 unless a backend/BFF exists. AuthN N/A unless there is login. Datastore rules apply if a client-reachable datastore exists (e.g. Firebase/Supabase from the static app); N/A if none. |
| `skill/docs` | Runtime AuthN/AuthZ, HTTP security headers, CORS, DB performance, mobile, a11y, deploy envs, error-handling runtime, webhooks. Still score: secrets in examples, architecture of the package, maintainability, product/scope. Testing N/A unless a runnable contract exists. Client-bundle secrets N/A unless the package ships client JS. |
| `mobile` | Web CSP/headers N/A. Platform storage and platform AuthZ apply. Datastore rules apply when a client SDK key can read rows. CORS N/A unless the app exposes a browser-cross-origin HTTP API. |
| `infra` | Product UX, mobile, a11y N/A. IAM, secrets, state isolation, rollback apply. Datastore rules / CORS / client-bundle N/A unless those surfaces exist. |

Auth-provider preference (Clerk / Auth0 / Supabase Auth) applies **only** when the product has users. Do not invent auth for `cli`, `library`, `static-site`, or `skill/docs`.

Prefer mature AuthZ (RLS / Firebase rules, server ownership checks) when the product has users **and** a client-reachable datastore or user-owned resources — including `saas-single-user` when a client key can read rows. IDOR tests stay N/A only when there is no sharing and no user-owned foreign resources.

Webhook-signature scoring is N/A unless the tree has webhook receivers (Stripe / GitHub / Svix or equivalent). Production CORS is N/A unless there is a browser-cross-origin API. Session invalidation is N/A if there is no cookie/session/JWT auth. Client-bundle secrets are N/A if there is no client/browser bundle. Restorable backup (extra) is N/A if there is no durable user data.

## Worked example (ForgeBoard)

Fictional `saas-multi-tenant` Next.js + Supabase app. Details: `references/example-report.md`.

**Security (25 applicable, 3 N/A):** 14 Pass + 4 Partial + 6 Fail + 1 `insufficient evidence`, including critical AuthZ Fail.

N/A: LLM prompt-injection (no LLM); production CORS (same-origin App Router, no cross-origin API); webhook signatures (no Stripe/GitHub/Svix receivers). `insufficient evidence`: secret rotation (leak history unknown). Fail: secret scan in CI, **[C]** object-level AuthZ, frontend as AuthZ boundary, roles on server, datastore rules (RLS off), public storage bucket. Partial: auth rate-limit (Supabase defaults only; no LLM/paid endpoint in tree), brute-force, XSS, security headers. Pass: **[C]** no hardcoded secrets, **[C]** no client-bundle secrets (no `service_role` / `sk_live` / `NEXT_PUBLIC_` server secret in client; `productionBrowserSourceMaps` not enabled), env/gitignore/example, **[C]** AuthN server-side, mature provider, **[C]** session cookies, session invalidation (Supabase Auth `signOut` / provider revoke), **[C]** input validation, parameterized queries, least-privilege DB, CSRF, HTTPS, no public admin/debug, security logs without tokens.

`known = 24`. `category_ratio = (14×1 + 4×0.5 + 6×0) / 24 = 16 / 24 = 0.666…` → `round_half_up(6.666…) = 7` → critical floor caps at **4**. The insufficient row is not in the 24.

**Testing (8 applicable, 0 N/A):** 3 Pass + 2 Partial + 3 Fail, including critical isolation-test Fail and critical edge/error-path Fail.

Pass: **[C]** tests for critical flows, suite in CI, happy path. Partial: coverage undocumented, still demo-shaped for AuthZ. Fail: **[C]** isolation tests, **[C]** principal edge cases and error paths, regression suite.

`category_ratio = (3×1 + 2×0.5 + 3×0) / 8 = 4 / 8 = 0.5` → **5**. Floor cap 6 does not raise it.

Other category scores: Comprehension 7, Architecture 7, Maintainability 6, Error handling 7, Performance 6, Dependencies 8, Process / environments 6, Product / scope 5.

| Category | Score | Weight | Product |
|----------|-------|--------|---------|
| Security | 4 | 2.0 | 8.0 |
| Comprehension | 7 | 1.0 | 7.0 |
| Testing | 5 | 1.5 | 7.5 |
| Architecture | 7 | 1.3 | 9.1 |
| Maintainability | 6 | 1.3 | 7.8 |
| Error handling | 7 | 1.0 | 7.0 |
| Performance | 6 | 1.0 | 6.0 |
| Dependencies | 8 | 1.0 | 8.0 |
| Process / environments | 6 | 1.0 | 6.0 |
| Product / scope | 5 | 1.0 | 5.0 |
| **Sum** | | **12.1** | **71.4** |

`overall = 71.4 / 12.1 = 5.900…` → **5.9**

Extras (excluded): Handoff readiness 4, Data model 4 (schema Pass, destructive Partial, restorable backup Fail — Vercel rollback is not a DB backup; invariants not on write path), Docs 6, Mobile 5, Accessibility 4, Observability 5.

Verdict and stage note: apply `references/gates.md` (absolute Security and Testing fail).
