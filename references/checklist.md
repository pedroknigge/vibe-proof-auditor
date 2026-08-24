# Checklist

Single home for **scored items**. Do not copy this list into `assets/checklist-template.md` (that file is a cover: metadata, score table, gates). Marks: Pass / Partial / Fail / N/A. Numeric mapping, floors, and N/A matrix: `references/scoring.md`. Verdicts and gate thresholds: `references/gates.md`. Security expansion (grep playbook): `references/security-deep.md`.

**Critical** items are marked `[C]`. Floors: `references/scoring.md` (do not restate them here).

**Evidence:** paths, snippets, or absence. Absence of a required, applicable control is Fail. Tool failure is `insufficient evidence`, not a critical Fail. Human-interview items are listed separately: `not assessed` if unasked — never Fail, never a gate.

**Partial:** control exists on some paths only, or is weak. **Pass:** present and applied on the relevant paths.

---

## 1. Security

Do **not** add a mega-item “complies with OWASP Top 10”. Use `references/security-deep.md` in Deep mode.

### Secrets

- [ ] **[C]** No hardcoded secrets in source (API keys, tokens, passwords, JWT secrets, connection strings).
- [ ] **[C]** No secrets in the client bundle: no public env prefix (`NEXT_PUBLIC_`, `VITE_`, `EXPO_PUBLIC_`, or equivalent) wrapping a server secret; no `service_role` / `sk_live` / equivalent in client components or shipped JS; production source maps do not expose secrets. N/A if there is no client/browser bundle. **Fail** if a server secret is readable from shipped client JS or prod source maps.
- [ ] Secrets only in env or a secret manager; `.env` gitignored; `.env.example` present without real values.
- [ ] Secret scan in CI or documented equivalent (gitleaks, TruffleHog, GitHub secret scanning) — `insufficient evidence` if tools cannot run, not Fail.
- [ ] If a secret ever landed in git, rotation is documented in-tree. If unknown, `insufficient evidence`, not Fail.

### Authentication (N/A if the product has no auth)

- [ ] **[C]** Authentication is server-side (not client-only middleware or localStorage checks).
- [ ] Mature provider when the product **has users** (Clerk, Auth0, Supabase Auth, Better Auth, NextAuth). N/A if no users. Do not invent auth for CLIs, libraries, or static sites.
- [ ] Rate limiting on login, register, and auth endpoints, **and** on expensive / LLM / paid-API endpoints when those exist. N/A the LLM/paid sub-path if the product has none. A frontend-only limiter is not Pass (Partial at best if the server/edge limiter is missing).
- [ ] Brute-force / credential-stuffing protections (lockout, backoff, or provider equivalent).
- [ ] **[C]** Session or JWT cookies: HttpOnly, Secure, SameSite, short expiry (or provider equivalent). N/A if no cookie/session auth. **Fail** if the session is JS-readable (`localStorage` JWT, or cookies with HttpOnly off). **Partial** if HttpOnly is on but Secure/SameSite is missing or max-age is months/years.
- [ ] Session invalidation: logout and server-side revoke (or provider equivalent) when cookie/session/JWT auth exists. N/A if no such auth. **Fail** if sessions cannot be ended. **Partial** if logout exists but stolen tokens cannot be revoked.

### Authorization (N/A if no users and resources)

- [ ] **[C]** Object-level authorization (IDOR / BOLA) on every sensitive resource.
- [ ] Frontend is not the authorization boundary.
- [ ] Roles and permissions evaluated on the server.
- [ ] Datastore rules (Postgres RLS, Firebase Security Rules, or equivalent) when the product has users **and** a client-reachable datastore (anon/authenticated client key, mobile SDK, etc.). Applies to `saas-single-user` when a client key can read rows — not only `saas-multi-tenant`. N/A if there is no client-reachable datastore. **Fail** if rules are off, missing, or open (`USING (true)`, allow-all Firebase rules, or equivalent).

### Input / output

- [ ] **[C]** Server-side input validation on entry points. **Fail** if a hardcoded `true` (or equivalent) skips validation on a live path.
- [ ] Parameterized queries / safe ORM (no string-concat SQL/NoSQL).
- [ ] Output encoding / XSS prevention. N/A if no HTML UI.
- [ ] Security headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options) when an HTTP app serves browsers.
- [ ] Production CORS is not `Access-Control-Allow-Origin: *` with credentials, and not a prod wildcard that lets any origin call credentialed APIs. N/A if there is no browser-cross-origin API. **Fail** if `*` plus credentials, or prod `*` on a credentialed API. **Partial** if `*` without credentials on a public API.

### Data stores

- [ ] Least-privilege database credentials.
- [ ] No public tables or storage buckets holding sensitive data.

### Other

- [ ] CSRF protection where cookie sessions apply.
- [ ] HTTPS only in deployed environments (N/A for local libraries).
- [ ] No public admin, debug, or sensitive health endpoints.
- [ ] Security events logged without PII or tokens.
- [ ] If the app uses LLMs: prompt-injection controls. N/A if no LLM.
- [ ] Webhook signatures verified (Stripe / GitHub / Svix or equivalent) when those handlers exist. N/A if there are no webhook receivers.

---

## 2. Comprehension (repo-evidence only)

Score only what the tree shows. Do not Fail this category because a human was not interviewed.

- [ ] Architecture README (or equivalent) describes the main flow.
- [ ] ADRs or recorded “why” for important decisions.
- [ ] Naming and module layout make data flow traceable from the tree.
- [ ] No unexplained god files hiding the critical path.
- [ ] Critical features have a documented or easily traced in-tree walkthrough.
- [ ] Connections between pieces are visible without a human narrator.

### Human interview (not scored / not a gate)

Mark `not assessed` unless the user was actually asked. Never Fail a gate on these.

- [ ] Author can explain the architecture and main flow in under 3 minutes without the AI.
- [ ] AI-generated diffs were read and understood before accept.
- [ ] A human can debug a critical flow without 100% AI dependence.

---

## 3. Testing

- [ ] **[C]** Tests exist for critical flows.
- [ ] **[C]** Principal edge cases and error paths covered (null/empty, malformed, timeouts, dependency failure).
- [ ] **[C]** Authorization/isolation tests when the product has users (user A cannot access user B). N/A otherwise.
- [ ] Test suite runs in CI.
- [ ] Happy path covered for critical features.
- [ ] Coverage measured on critical modules, or documented why not.
- [ ] Regression suite exists (new changes do not silently break old paths).
- [ ] “Works on my machine / demo” is not the only check. `ignoreBuildErrors` / `eslint.ignoreDuringBuilds` (or equivalent) is evidence against Pass.

---

## 4. Architecture

- [ ] Minimal spec or design in-tree before large features.
- [ ] Clear separation of concerns (domain vs infrastructure, modules, layers).
- [ ] Features are not stacked at random (no accretion-only design).
- [ ] Data model is consistent (no improvised field drift).
- [ ] Data flows are documented or easily traced.
- [ ] Naming, folder structure, and patterns are followed.
- [ ] No serious circular dependencies.
- [ ] Extensible without a rewrite of the core.
- [ ] Important decisions recorded (short ADRs or equivalent).

---

## 5. Maintainability

- [ ] Readable, consistent style and patterns.
- [ ] Clear naming.
- [ ] Reasonable function/module size (no god classes / god files).
- [ ] No critical “TODO: fix later” without a ticket or context.
- [ ] Refactor is possible without fear of silent breakage.
- [ ] New-developer onboarding is viable from the tree (README + layout).
- [ ] Technical debt is tracked (issues, ADRs, or an in-tree list).
- [ ] No unreadable generated slop as the main implementation.

---

## 6. Error handling

- [ ] **[C]** Errors are not swallowed (`catch` empty, ignored promises, discarded results).
- [ ] **[C]** Stack traces not exposed to end users.
- [ ] Timeouts, retries, and circuit breakers where external calls exist.
- [ ] Graceful degradation when external services fail.
- [ ] Structured error logs with useful context.
- [ ] Distinct user-facing vs developer error messages.
- [ ] Security decisions fail closed.
- [ ] No silent broken states (failed writes reported, jobs marked failed).

---

## 7. Performance

- [ ] No obvious N+1 queries.
- [ ] Appropriate database indexes. N/A if no database.
- [ ] Caching where it is justified.
- [ ] Pagination or limits on lists.
- [ ] Realistic load considered (not only a 10-user demo).
- [ ] Basic performance metrics or a documented plan to measure.
- [ ] Frontend Core Web Vitals acceptable if there is a UI. N/A otherwise.

---

## 8. Dependencies

- [ ] Each dependency is justified (prefer stdlib or small audited packages).
- [ ] No hallucinated, abandoned, unnecessary, or **slopsquatted** packages (names the model invented that are unpublished, or newly registered squatters of those names).
- [ ] Pinned versions and lockfiles present.
- [ ] SBOM or a generated dependency inventory, or `npm/pip/cargo audit` equivalent in CI.
- [ ] API / token costs estimated and alerted when paid APIs exist. N/A otherwise.
- [ ] No dependency bloat that enlarges attack surface without benefit.
- [ ] Known critical CVEs addressed.

---

## 9. Process / environments

Repo-evidence only for scored items.

- [ ] Git used with atomic commits and intelligible messages (sample the log).
- [ ] `.gitignore` covers secrets, dependencies, and build output.
- [ ] Distinct local / staging / production (or documented equivalent) in CI/config/docs.
- [ ] Rollback path for data-critical systems (docs, scripts, or platform config).
- [ ] Code review required before merge to the default branch.
- [ ] Branch protection + CI (tests, lint, security scans) on the default branch.
- [ ] Changes land as small reviewed diffs (no unreviewed mass rewrites as the norm).

### Human interview (not scored / not a gate)

- [ ] AI agent never has write access to production or prod secrets.

---

## 10. Product / scope

Score from the tree (README, spec, issues, changelog). Missing product evidence is Partial, not a security Fail.

- [ ] Validated with real users or strong in-tree evidence before overbuilding.
- [ ] MVP defined and respected.
- [ ] New features justified (issue, spec, or README).
- [ ] Scope creep controlled (no infinite “one more feature” log without cuts).
- [ ] Success metrics defined.

---

## Extras (not in overall)

Same marks. Category scores optional. Excluded from overall: `references/scoring.md`.

### Data model / migrations

- [ ] Schema is versioned (migrations or equivalent).
- [ ] Destructive changes are explicit and reversible when data is critical.
- [ ] Restorable backup for data-critical systems, distinct from platform deploy rollback (Vercel/Heroku/image rollback is not a database backup). N/A if no durable user data.

### Docs

- [ ] README: what it is, how to run, env vars.
- [ ] Architecture notes sufficient to find the critical path.

### Mobile / responsive

- [ ] UI works on small viewports (real device or emulator). N/A if no UI.

### Accessibility

- [ ] Basic a11y if frontend (labels, keyboard, contrast). N/A if no UI.

### Observability

- [ ] Structured logs.
- [ ] Metrics and alerts for critical paths when the system is deployed. N/A for `skill/docs`.
