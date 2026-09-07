# Checklist

Single home for **scored items**. Do not copy this list into `assets/checklist-template.md` (that file is a cover: metadata, score table, gates). Marks: Pass / Partial / Fail / N/A. Numeric mapping, floors, and N/A matrix: `references/scoring.md`. Verdicts and gate thresholds: `references/gates.md`. Security expansion (grep playbook): `references/security-deep.md`.

**Growth rule:** this list is allowed to grow. A repeated dunk **improves** an existing row. A new dunk **adds** a row. Do not refuse a real production dunk because the list feels long enough.

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
- [ ] Rate limiting on login, register, password-reset, and auth endpoints, **and** on expensive / LLM / paid-API endpoints when those exist. The limiter runs server-side or at the edge and keys on something the caller cannot freely rotate (account + IP, or the provider's own limiter) — not on a client counter. N/A the LLM/paid sub-path if the product has none. **Fail** if a live auth or paid endpoint has no server/edge limiter at all. **Partial** if a limiter exists but misses the auth path, or keys only on a header the caller controls. A frontend-only limiter is never Pass. Finding id: `missing-rate-limit`.
- [ ] Brute-force / credential-stuffing and bot protection (lockout, exponential backoff, CAPTCHA / Turnstile / device check, or provider equivalent) on login, signup, and public write forms. **Partial** if only one of lockout/backoff/bot-check is present on a public signup or login. Maps to `missing-rate-limit` when the endpoint has no throttle of any kind.
- [ ] **[C]** Session or JWT cookies: HttpOnly, Secure, SameSite, short expiry (or provider equivalent). N/A if no cookie/session auth. **Fail** if the session is JS-readable (`localStorage` JWT, or cookies with HttpOnly off). **Partial** if HttpOnly is on but Secure/SameSite is missing or max-age is months/years.
- [ ] Session invalidation: logout and server-side revoke (or provider equivalent) when cookie/session/JWT auth exists. N/A if no such auth. **Fail** if sessions cannot be ended. **Partial** if logout exists but stolen tokens cannot be revoked.

### Authorization (N/A if no users and resources)

- [ ] **[C]** Object-level authorization — lock record access (IDOR / BOLA) on every sensitive resource. Every read, update, and delete that takes an id from the request re-derives the owner/tenant server-side; a stranger who guesses or increments the id gets 403/404, not the record. **Pass** requires the server ownership/tenant predicate on the resource path **and** an isolation test or equivalent request-level proof (the *stranger permission test*: authenticate as user B, request user A's id, expect denied). Grep / “the UI hides the button” only is **Partial**, never Pass. Finding id: `idor` (alias `idor-open`). Distinct from datastore rules below: this row is the **application** ownership check on the server path; `rls-open` is the **datastore** policy that protects the same rows when a client key reaches the database directly. Both can Fail independently — score them separately, and do not Pass this row because RLS exists.
- [ ] Frontend is not the authorization boundary.
- [ ] Roles and permissions evaluated on the server.
- [ ] Datastore rules (Postgres RLS, Firebase Security Rules, or equivalent) when the product has users **and** a client-reachable datastore (anon/authenticated client key, mobile SDK, etc.). Applies to `saas-single-user` when a client key can read rows — not only `saas-multi-tenant`. N/A if there is no client-reachable datastore. **Fail** if rules are off, missing, or open (`USING (true)`, allow-all Firebase rules, or equivalent).

### Input / output

- [ ] **[C]** Server-side input validation on entry points. **Fail** if a hardcoded `true` (or equivalent) skips validation on a live path.
- [ ] Parameterized queries / safe ORM (no string-concat SQL/NoSQL).
- [ ] Block field tampering on writes, and trim what reads return. Writes bind an explicit allowlist of client-settable fields (schema `.pick()`, DTO, `strict()` / `attr_accessible` equivalent) so a caller cannot smuggle `role`, `is_admin`, `price`, `owner_id`, `credits`, or `status` into an update; reads return only the fields the caller needs. **Fail** if a handler spreads the raw request body into a create/update (`{...req.body}`, `Model(**payload)`, `Object.assign(entity, body)`, `update(body)`) on a table holding privilege, money, or ownership columns, or if an endpoint serializes a whole user/account row (password hash, tokens, internal ids, other tenants' fields) to the client. **Partial** if some routes bind explicitly and others do not, or if writes are guarded but responses over-fetch. N/A if the product has no client-supplied writes and no API responses. Finding id: `mass-assignment-open`.
- [ ] Restrict file uploads. N/A if the product accepts no uploads. Otherwise **Pass** needs, on the server: an extension **and** content-type allowlist (not a denylist, and not the client-declared MIME type alone), a maximum size enforced before the file is buffered to memory or disk, a stored name the server generates (no caller-controlled path — no `../`, no raw filename), and storage that does not execute or serve what was uploaded from an app-executable path (private bucket / non-web-root, signed URLs with short expiry, no `Content-Type` reflected back from the upload). **Fail** if any of those is missing on a live upload path, if uploads land in a public bucket or a web-served directory, or if the only check is client-side. **Partial** if the size and type checks exist but storage is public or the filename is caller-controlled. Finding id: `unrestricted-file-upload`.
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
- [ ] Failure modes of the critical path are findable from the tree (logs, errors, or a short debug note) without the author on call.

### Human interview (not scored / not a gate)

Mark `not assessed` unless the user was actually asked. Never Fail a gate on these.

- [ ] Author can explain the architecture and main flow in under 3 minutes without the AI.
- [ ] AI-generated diffs were read and understood before accept (not “it looks done”).
- [ ] A human can debug a critical flow without 100% AI dependence.
- [ ] “It works” was not treated as “it’s ready” — tests or equivalent were run before calling it shippable.

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

- [ ] Minimal spec or design in-tree before large features (not one-shot “build the whole product”).
- [ ] Clear separation of concerns (domain vs infrastructure, modules, layers).
- [ ] Features are not stacked at random (no accretion-only design).
- [ ] Where state lives is explicit: client / server / durable store — not inferred from a finished-looking UI. **Fail** if critical state has no owner and no single home in the tree. Finding id: `state-orphan`.
- [ ] Data model is consistent (no improvised field drift).
- [ ] Data flows are documented or easily traced.
- [ ] Naming, folder structure, and patterns are followed.
- [ ] No serious circular dependencies.
- [ ] Complexity matches the problem (no premature microservices / event-bus / distributed theater for a simple MVP). **Partial** if the stack is heavier than the stated problem; **Fail** if the complexity is the product.
- [ ] **[C]** Architectural foresight (no "road ends in a lake"): the design anticipates known limits, scale boundaries, or data model dead ends before writing the code. **Fail** if a foreseeable roadblock will require a total rewrite. Finding id: `architectural-dead-end`.
- [ ] Durable writes go through an **aggregate root** (or one clear transactional write boundary per business entity). Dependent entities are persisted only through that root; invariants are enforced there — not in the route, the UI, or a random util. **Fail** if handlers/adapters write child tables directly and bypass the root. Finding id: `aggregate-bypass`. N/A if the product has no durable business writes (typical `cli` / `library` / static / docs-only).
- [ ] One aggregate (or write boundary) per business entity; adapters may wrap external deps, but DB writes are not scattered across features. **Partial** if only some entities obey it; **Fail** if every feature opens the DB and writes whatever it wants.
- [ ] Extensible without a rewrite of the core. **Fail** if the realistic next step for a stranger is “rebuild,” not change.
- [ ] **[C]** Structural understanding (Civil Engineer vs Bricklayer): the architecture shows intentional design (proper decoupling, data flow, error boundaries) rather than just API glue that happens to compile. **Fail** if the system is a fragile house of cards stitched together without understanding of the underlying frameworks. Finding id: `fragile-api-glue`.
- [ ] No covert circular implementation: no runtime mutual-call or re-entrant loop hidden behind layers (A calls B, B calls back into A through an event, hook, middleware, or ORM callback). Distinct from the import-cycle row above, which is static. **Fail** if a request can re-enter its own handler with no depth bound and no idempotence guard. Finding id: `covert-recursion`.
- [ ] **[C]** Procedure completeness: where the code implements a known protocol, algorithm, or state machine (handshake, retry/backoff, transaction, pagination cursor, auth flow, upload lifecycle), the required intermediate steps are present and ordered — not compressed to the two endpoints that make a demo pass. **Fail** if a step whose omission is invisible on the happy path (ack, commit, revoke, close, verify, checkpoint) is missing. Finding id: `step-skipped`. N/A if the tree implements no such protocol.
- [ ] Cohesive system, not a patchwork of micro-systems: features share their transport, auth, config, and error conventions instead of each shipping its own. **Partial** if two features solve the same cross-cutting concern differently; **Fail** if the integration surface grows at least as fast as the feature count. Finding id: `micro-system-patchwork`.
- [ ] Important decisions recorded (short ADRs or equivalent).

---

## 5. Maintainability

Shipping is the easy part. Score whether someone who **did not write this** can still change it six months later.

- [ ] Readable, consistent style and patterns.
- [ ] Clear naming.
- [ ] Reasonable function/module size (no god classes / god files).
- [ ] No critical “TODO: fix later” without a ticket or context.
- [ ] Refactor is possible without fear of silent breakage. **Pass** needs a safety net on the critical path (tests or equivalent). Demo-only confidence is **Fail**.
- [ ] New-developer onboarding is viable from the tree (README + layout + how to run).
- [ ] Stranger handoff: a developer who did not author the code can find and change a critical path from the tree alone (README + layout + traced flow). **Fail** if the only workable path is the original chat thread or “ask the model that wrote it.” Finding id: `stranger-handoff`.
- [ ] Maintenance policy in-tree: how to change, how to release, and what “done” means after the first ship (CONTRIBUTING, runbook, or equivalent). Finding id: `maintenance-policy-missing`.
- [ ] Ownership of critical modules is visible (CODEOWNERS, OWNERS, or a short ownership map). N/A for solo prototypes with no shared repo claim.
- [ ] Accidental complexity controlled: no duplicate write paths, dead feature sketches, or unjustified abstraction layers as the main surface. AI-sped delivery is not an excuse for two systems that do one job.
- [ ] Code volume control (less is more): prefers standard libraries, managed services, or established patterns over custom AI-generated code. **Fail** if the AI generated a massive custom solution for a solved problem. Finding id: `over-generation`.
- [ ] Technical debt is tracked (issues, ADRs, or an in-tree list).
- [ ] No unreadable generated slop as the main implementation (model dump that cannot be maintained without the original prompt history). Finding id: `rebuild-trap` when a stranger’s rational move is rewrite.
- [ ] **[C]** Autonomous debuggability ("Until the first bug"): the code is structured, logged, and explicit enough that a human could isolate a bug without pasting the entire file back into an AI. **Fail** if a critical path bug forces full context-window reliance to even understand what failed. Finding id: `ai-debug-dependency`.
- [ ] **[C]** Aesthetic deception vs Engineering: the code is structurally sound, not just visually formatted (nice comments/indents hiding weak logic). **Fail** if the codebase looks neat but lacks fundamental software engineering design (state management, boundaries) when scrutinized. Finding id: `aesthetic-deception`.
- [ ] Maintenance cost and longevity: explicit recognition (in docs, runbooks, or policy) that maintenance, integration, and evolution are harder and more costly than the initial build, and that the cost grows with every feature. The app is architected for continuous updates, not just to live for a week (vibe-coded obsolescence). Finding id: `vibe-coded-obsolescence`.
- [ ] Intrinsic business understanding vs raw code: the code reflects a deep understanding of the business domain, not just generated boilerplate. **Fail** if the team treats 1:1 cloning without business context as a fatal competitor threat, ignoring that raw code is commoditized. Finding id: `raw-code-delusion`.

### Human interview (not scored / not a gate)

- [ ] Author believes a stranger could maintain this six months later without a full rewrite.
- [ ] Author can name who owns each critical module (even if “me, solo”).

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
- [ ] Cleanup happens on the failure path too (`finally` / `defer` / context manager / `try`-scoped teardown), not only on the happy path. **Fail** if an early `return` or `throw` between acquire and release leaks the resource. Finding id: `cleanup-on-failure-missing`.

---

## 7. Performance

- [ ] No obvious N+1 queries.
- [ ] Appropriate database indexes. N/A if no database.
- [ ] Caching where it is justified.
- [ ] Pagination or limits on lists.
- [ ] Realistic load considered (not only a 10-user demo).
- [ ] Basic performance metrics or a documented plan to measure.
- [ ] Frontend Core Web Vitals acceptable if there is a UI. N/A otherwise.
- [ ] Bounded buffers, queues, and caches: every in-memory accumulator has an explicit bound and a defined behaviour at the bound (drop, block, evict). Ring/circular buffers have their wrap and full-vs-empty arithmetic covered by a test. **Fail** if an unbounded structure grows with traffic, or if a hand-rolled circular buffer has no test that crosses the wrap point. Finding id: `unbounded-buffer`. N/A if the product holds no in-memory state across requests.
- [ ] Resource release: connections, file handles, subscriptions, timers, watchers, and workers are released by whoever acquires them. **Partial** if some paths clean up; **Fail** if a long-lived service acquires without a matching release on the critical path. Finding id: `resource-leak`.

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
- [ ] Changes land as small reviewed diffs (no unreviewed mass rewrites as the norm). Finding id: `one-shot-dump` when history is one mega-commit that drops the app.
- [ ] Claimed install / run / test commands from README (or equivalent) were executed in this audit snapshot and exited 0 — or failure is recorded as evidence. **Fail** if the docs promise a command that was never run and cannot be shown to work. Tool missing → `insufficient evidence`.
- [ ] Iterative delivery evidence: features land in steps with verification between them (commits, PRs, or changelog), not one prompt → whole product.
- [ ] Upfront planning evidence ("what to do and what not"): issues, spec, or ADRs show the author planned the boundary of the work before shipping it. Speed of execution did not skip the planning phase. Finding id: `skipped-planning`.
- [ ] **[C]** Convergent problem framing ("condiciones de contorno"): open-ended problems are broken down into testable, convergent boundaries or explicit contracts before code is written. **Fail** if the author prompted an open-ended feature without defining strict boundaries, leading to hallucinated or inconsistent logic. Finding id: `open-ended-trap`.
- [ ] **[C]** Technocritical validation: evidence that AI-generated logic and library choices were validated against ground truth (e.g., explicit tests, accurate API usage, no hallucinated imports). **Fail** if the code relies on hallucinated patterns or "context rot" that the author blindly accepted. Finding id: `blind-acceptance`.
- [ ] **[C]** Silent AI drift (Change Management Hell): updates and new features do not silently drop, hallucinate, or rewrite unrelated code. **Fail** if history shows agentic changes routinely breaking or rewriting unrelated code without explicit instructions (vibe coding drift). Finding id: `ai-code-drift`.

### Human interview (not scored / not a gate)

- [ ] AI agent never has write access to production or prod secrets.

---

## 10. Product / scope

Score from the tree (README, spec, issues, changelog). Missing product evidence is Partial, not a security Fail.

- [ ] Target user and problem stated in-tree (who it is for, what pain). **Fail** if the tree never says who it solves for.
- [ ] Validated with real users or strong in-tree evidence before overbuilding.
- [ ] MVP defined and respected (one small problem first — not “build everything at once”).
- [ ] New features justified (issue, spec, or README).
- [ ] Product judgment explicit ("what to build and why"): clear reasoning exists for why a feature was built, not just that it could be built quickly. Finding id: `missing-product-judgment`.
- [ ] Scope creep controlled (no infinite “one more feature” log without cuts).
- [ ] Marketing / landing polish does not dominate the tree while the core problem is still unproven. **Partial** if the landing is the product; **Fail** if there is no in-tree evidence of the actual problem being solved. Finding id: `landing-over-product`.
- [ ] Success metrics defined.

---

- [ ] User moat and platform friction: the product strategy (README, docs) acknowledges that owning users and creating friction to switch is the real moat, not "uncloneable" software. Finding id: `clone-vulnerable`.
- [ ] SLA, infra costs, and support: expectations for Service Level Agreements (SLAs), uptime, and infrastructure costs are explicitly handled or documented. It proves it is a maintained service (SaaS), not just a raw app (AaaS). Finding id: `missing-sla`.

## Extras (not in overall)

Same marks. Category scores optional. Excluded from overall: `references/scoring.md`.

### Handoff readiness

Six-month test. Score for the report; does not change overall or absolute gates.

- [ ] Critical-path walkthrough a stranger can follow without the author.
- [ ] Top failure modes have a runbook or equivalent (what breaks, how to see it, how to recover).
- [ ] Debt list with owners or dates (not only “TODO later”).
- [ ] “Rebuild vs refactor” is an explicit decision when a module is past recovery — not the silent default.

### Data model / migrations

- [ ] Schema is versioned (migrations or equivalent).
- [ ] Destructive changes are explicit and reversible when data is critical.
- [ ] Restorable backup for data-critical systems, distinct from platform deploy rollback (Vercel/Heroku/image rollback is not a database backup). N/A if no durable user data.
- [ ] Critical entity invariants live on the write path (aggregate / domain), not only as UI validation. N/A if no durable business writes. Aligns with Architecture `aggregate-bypass`.

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

---

## Common finding IDs

Use these ids in the Findings table when the dunk matches. Security ids also live in `references/security-deep.md`.

| ID | Typical mark | Means |
|----|--------------|-------|
| `stranger-handoff` | Fail / Partial | Only the original author or chat thread can change the critical path |
| `state-orphan` | Fail / Partial | UI looks done; no owner for client / server / durable state |
| `aggregate-bypass` | Fail / Partial | DB writes skip the aggregate root / write boundary; children written from routes/adapters |
| `rebuild-trap` | Fail | Rational next step for a stranger is rewrite, not refactor |
| `maintenance-policy-missing` | Fail / Partial | No in-tree how-to-change / how-to-release after first ship |
| `one-shot-dump` | Fail / Partial | One mega-commit or one prompt dropped the whole app |
| `landing-over-product` | Fail / Partial | Marketing surface dominates; problem unproven |
| `architectural-dead-end` | Fail | Design hits a foreseeable limit that requires a total rewrite |
| `over-generation` | Fail / Partial | Generated a massive custom solution for a solved problem (should write less code) |
| `skipped-planning` | Fail / Partial | Shipped code blindly without planning what to do and what not to do |
| `missing-product-judgment` | Fail / Partial | Missing reasoning for what to build and why |
| `fragile-api-glue` | Fail | System is stitched together without understanding of underlying frameworks |
| `ai-debug-dependency` | Fail | Code cannot be debugged by a human without pasting back into AI |
| `open-ended-trap` | Fail | Prompted an open-ended problem without defining strict boundary conditions |
| `blind-acceptance` | Fail | Accepted hallucinated logic or context rot without technocritical validation |
| `aesthetic-deception` | Fail | Code looks neat visually but lacks structural software engineering design |
| `ai-code-drift` | Fail | AI agent routinely dropped or modified unrelated code during updates |
| `vibe-coded-obsolescence` | Fail / Partial | No recognition that maintenance, integration and evolution cost more than the build |
| `raw-code-delusion` | Fail / Partial | Treats cloneable code as the moat; no business-domain understanding in the tree |
| `unbounded-buffer` | Fail / Partial | In-memory accumulator with no bound, or an untested ring-buffer wrap |
| `resource-leak` | Fail / Partial | Connections, handles, subscriptions, timers or workers acquired without release |
| `cleanup-on-failure-missing` | Fail / Partial | Teardown only on the happy path; an early return/throw leaks the resource |
| `covert-recursion` | Fail | Runtime re-entrant or mutual-call loop hidden behind an event, hook or middleware |
| `step-skipped` | Fail | Protocol compressed to its endpoints; a required intermediate step is missing |
| `micro-system-patchwork` | Fail / Partial | Features each ship their own transport/auth/config instead of shared conventions |
| `clone-vulnerable` | Fail / Partial | Strategy relies on code being uncloneable rather than on users and switching friction |
| `missing-sla` | Fail / Partial | No documented SLA, uptime expectation, infra cost or support posture |
| `idor` | Fail | Object-level AuthZ missing: a request id is trusted without a server-side owner/tenant check |
| `idor-open` | Fail | Alias of `idor`. Accepted in reports; `idor` stays the canonical id used by eval manifests |
| `isolation-tests` | Fail | No user A vs user B proof (the stranger permission test was never run) |
| `rls-open` | Fail | Datastore rules missing or open. Datastore layer — not a substitute for `idor` on the app path |
| `mass-assignment-open` | Fail / Partial | Raw request body bound into a create/update (field tampering), or responses over-fetch privileged fields |
| `missing-rate-limit` | Fail / Partial | No server/edge rate limit or bot protection on login, signup, or expensive/paid endpoints |
| `unrestricted-file-upload` | Fail / Partial | Uploads without a server-side type/size allowlist, with caller-controlled names, or stored publicly/executably |
| `client-bundle-secret` | Fail | Server secret in shipped client |
| `localstorage-jwt` | Fail | Session readable from JS |
| `ignore-build-errors` | Fail | Build/lint errors ignored to ship the demo |