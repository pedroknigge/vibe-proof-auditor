# Scoring

Single home for **weights**, **formula**, **critical floors**, **scale**, **product-type N/A matrix**, and **mark values**. Gates and verdict strings live in `references/gates.md`. Checklist items live in `references/checklist.md`.

## Ten scored categories (weights)

| # | Category | Weight |
|---|----------|--------|
| 1 | Security | 2.0 |
| 2 | Comprehension | 1.0 |
| 3 | Testing | 1.5 |
| 4 | Architecture | 1.3 |
| 5 | Maintainability | 1.0 |
| 6 | Error handling | 1.0 |
| 7 | Performance | 1.0 |
| 8 | Dependencies | 1.0 |
| 9 | Process / environments | 1.0 |
| 10 | Product / scope | 1.0 |

Sum of weights = **12.8**.

## Extras (report only)

Score for the report, **exclude from overall**:

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
| insufficient evidence | 0.5 (tool failed or file unreadable). Not a critical Fail. Do not apply a critical floor. |
| not assessed | excluded — human-interview only, never a Fail |

`category_ratio = sum(marks of applicable items) / count(applicable items)`

If count is 0, the category is N/A: omit it from the overall numerator and subtract its weight from the denominator. Never substitute 0.

`category_score = round(category_ratio * 10)` to nearest integer, **half up**.

Then apply **critical floors** (critical items are marked in `references/checklist.md`):

- Any **critical** applicable Security item is Fail → cap Security at 4.
- Any **critical** applicable Testing item is Fail → cap Testing at 6.
- Any **critical** applicable Error handling item is Fail → cap Error handling at 6.

Floors cap; they never raise a score.

## Overall

`overall = Σ(weight_i × category_score_i) / D` to **one decimal** (half up).

`D = 12.8` when all ten categories are applicable. If a category is fully N/A, `D` is 12.8 minus that category’s weight.

Do not include extras in `D` or the numerator.

Feed `overall` and category scores into `references/gates.md` for the verdict. Do not apply verdict logic here.

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
| `saas-multi-tenant` | Almost nothing. Tenant isolation / RLS applies. |
| `saas-single-user` | Cross-user AuthZ, IDOR tests, and tenant RLS N/A if there is no sharing and no user-owned foreign resources. AuthN still applies if accounts exist. |
| `cli` | Browser XSS/CSP/headers, mobile/responsive, accessibility. AuthN/AuthZ N/A unless the CLI calls user-scoped APIs. |
| `library` | AuthN/AuthZ, SaaS env isolation, XSS unless it renders HTML, mobile, a11y, service observability. Tests, deps, errors, maintainability still apply. Publish/rollback docs may apply. |
| `static-site` | Server AuthZ/IDOR, RLS, data rollback, N+1 unless a backend/BFF exists. AuthN N/A unless there is login. |
| `skill/docs` | Runtime AuthN/AuthZ, HTTP security headers, DB performance, mobile, a11y, deploy envs, error-handling runtime. Still score: secrets in examples, architecture of the package, maintainability, product/scope. Testing N/A unless a runnable contract exists. |
| `mobile` | Web CSP/headers N/A. Platform storage and platform AuthZ apply. |
| `infra` | Product UX, mobile, a11y N/A. IAM, secrets, state isolation, rollback apply. |

Auth-provider preference (Clerk / Auth0 / Supabase Auth) applies **only** when the product has users. Do not invent auth for `cli`, `library`, `static-site`, or `skill/docs`.

Prefer mature AuthZ (RLS, server ownership checks) **only** when the product has users and resources.

## Worked example (ForgeBoard)

Fictional `saas-multi-tenant` Next.js + Supabase app. Details: `references/example-report.md`.

**Security (23 applicable, 1 N/A):** 12 Pass + 4 Partial + 6 Fail + 1 `insufficient evidence`, including critical AuthZ Fail.

N/A: LLM prompt-injection (no LLM). `insufficient evidence`: secret rotation (leak history unknown). Fail: secret scan in CI, **[C]** object-level AuthZ, frontend as AuthZ boundary, roles on server, RLS, public storage bucket. Partial: auth rate-limit, brute-force, XSS, security headers. Pass: **[C]** no hardcoded secrets, env/gitignore/example, **[C]** AuthN server-side, mature provider, session cookies, **[C]** input validation, parameterized queries, least-privilege DB, CSRF, HTTPS, no public admin/debug, security logs without tokens.

`category_ratio = (12×1 + 4×0.5 + 6×0 + 1×0.5) / 23 = 14.5 / 23 = 0.6304` → `round(6.304) = 6` → critical floor caps at **4**.

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
| Maintainability | 6 | 1.0 | 6.0 |
| Error handling | 7 | 1.0 | 7.0 |
| Performance | 6 | 1.0 | 6.0 |
| Dependencies | 8 | 1.0 | 8.0 |
| Process / environments | 6 | 1.0 | 6.0 |
| Product / scope | 5 | 1.0 | 5.0 |
| **Sum** | | **12.8** | **69.6** |

`overall = 69.6 / 12.8 = 5.4375` → **5.4**

Extras (excluded): Data model 7, Docs 6, Mobile 5, Accessibility 4, Observability 5.

Verdict: apply `references/gates.md` (absolute Security and Testing fail) → `BLOCKED FOR PRODUCTION`.
