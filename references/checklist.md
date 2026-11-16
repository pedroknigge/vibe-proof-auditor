# Checklist

Single home for **scored items**. Do not copy this list into `assets/checklist-template.md` (that file is a cover: metadata, score table, gates). Marks: Pass / Partial / Fail / N/A. Numeric mapping, floors, and N/A matrix: `references/scoring.md`. Verdicts and gate thresholds: `references/gates.md`. Security expansion (grep playbook): `references/security-deep.md`.

**Growth rule:** improve an existing row for a repeated failure. Add a row for a distinct, applicable, testable failure. Remove or merge a row that only restates an opinion or another mark.

**Critical** items are marked `[C]`. Floors: `references/scoring.md` (do not restate them here).

**Evidence:** for each applicable row identify the affected path, the input or failure sequence, the observable result, and a test or trace that distinguishes Pass from Fail. A grep hit is a lead, not proof; a missing grep hit is not proof of safety. Absence of a required, applicable control is Fail only after the relevant paths are inspected. Tool failure is `insufficient evidence`, not a critical Fail. Human-interview items are listed separately: `not assessed` if unasked — never Fail, never a gate. Score outcomes, not a preferred framework, provider, document format, or history of AI use.

**Partial:** control exists on some paths only, or is weak. **Pass:** present and applied on the relevant paths.

---

## 1. Security

Do **not** add a mega-item “complies with OWASP Top 10”. Use `references/security-deep.md` in Deep mode.

### Secrets

- [ ] **[C]** No hardcoded secrets in source (API keys, tokens, passwords, JWT secrets, connection strings). Gate: critical security.
- [ ] **[C]** No secrets in the client bundle: no public env prefix (`NEXT_PUBLIC_`, `VITE_`, `EXPO_PUBLIC_`, or equivalent) wrapping a server secret; no `service_role` / `sk_live` / equivalent in client components or shipped JS; production source maps do not expose secrets. N/A if there is no client/browser bundle. **Fail** if a server secret is readable from shipped client JS or prod source maps.
- [ ] Secrets only in env or a secret manager; `.env` gitignored; `.env.example` present without real values.
- [ ] Secret scan in CI or documented equivalent (gitleaks, TruffleHog, GitHub secret scanning) — `insufficient evidence` if tools cannot run, not Fail.
- [ ] If a secret ever landed in git, rotation is documented in-tree. If unknown, `insufficient evidence`, not Fail.

### Authentication (N/A if the product has no auth)

- [ ] **[C]** Authentication is server-side (not client-only middleware or localStorage checks). Gate: critical security.
- [ ] Authentication verifies credentials or tokens at the server boundary, checks expiry and issuer/audience where relevant, and does not trust a client-supplied user id. A provider is one implementation; verify its configuration and use. N/A if the product has no authenticated users.
- [ ] Rate limiting on login, register, password-reset, and auth endpoints, **and** on expensive / LLM / paid-API endpoints when those exist. Enforcement runs in a trusted server, provider, or edge layer before the expensive operation. For password login, check independent per-account and per-source limits (or an equivalent control against both distributed attempts at one account and one-source account sweeps); one combined `IP:account` bucket alone does not cover either pattern. Verify the source address comes from a trusted proxy path, not a caller-controlled header. N/A the paid sub-path if absent. **Fail** if a live auth or paid endpoint has no trusted limiter at all. **Partial** if the limiter misses a relevant path or either abuse pattern. A frontend counter is never Pass. Finding id: `missing-rate-limit`.
- [ ] Brute-force / credential-stuffing and bot protection (lockout, exponential backoff, CAPTCHA / Turnstile / device check, or provider equivalent) on login, signup, and public write forms. **Partial** if only one of lockout/backoff/bot-check is present on a public signup or login. Maps to `missing-rate-limit` when the endpoint has no throttle of any kind.
- [ ] **[C]** Session exposure and expiry match the threat model. For cookie sessions, inspect HttpOnly, Secure, SameSite, expiry, and CSRF protection; for bearer tokens, inspect where they are stored, XSS exposure, expiry, and refresh handling. **Fail** when a token can be stolen or reused through a demonstrated path, or an unverified token grants access. JS-readable storage is a risk to investigate, not proof of broken authorization on its own. N/A if there is no session or token auth.
- [ ] Session invalidation: logout and server-side revoke (or provider equivalent) when cookie/session/JWT auth exists. N/A if no such auth. **Fail** if sessions cannot be ended. **Partial** if logout exists but stolen tokens cannot be revoked.

### Authorization (N/A if no users and resources)

- [ ] **[C]** Object-level authorization — lock record access (IDOR / BOLA) on every sensitive resource. Every read, update, and delete that takes an id from the request re-derives the owner/tenant server-side; a stranger who guesses or increments the id gets 403/404, not the record. **Pass** requires the server ownership/tenant predicate on the resource path **and** an isolation test or equivalent request-level proof (the *stranger permission test*: authenticate as user B, request user A's id, expect denied). Grep / “the UI hides the button” only is **Partial**, never Pass. Finding id: `idor` (alias `idor-open`). Distinct from datastore rules below: this row is the **application** ownership check on the server path; `rls-open` is the **datastore** policy that protects the same rows when a client key reaches the database directly. Both can Fail independently — score them separately, and do not Pass this row because RLS exists. Gate: critical security.
- [ ] Frontend is not the authorization boundary.
- [ ] Roles and permissions evaluated on the server.
- [ ] Datastore rules (Postgres RLS, Firebase Security Rules, or equivalent) when the product has users **and** a client-reachable datastore (anon/authenticated client key, mobile SDK, etc.). Applies to `saas-single-user` when a client key can read rows — not only `saas-multi-tenant`. N/A if there is no client-reachable datastore. **Fail** if rules are off, missing, or open (`USING (true)`, allow-all Firebase rules, or equivalent).

### Input / output

- [ ] **[C]** Server-side input validation on entry points. **Fail** if a hardcoded `true` (or equivalent) skips validation on a live path. Gate: critical security.
- [ ] Parameterized queries / safe ORM (no string-concat SQL/NoSQL).
- [ ] Block field tampering on writes, and trim what reads return. Writes bind an explicit allowlist of client-settable fields (schema `.pick()`, DTO, `strict()` / `attr_accessible` equivalent) so a caller cannot smuggle `role`, `is_admin`, `price`, `owner_id`, `credits`, or `status` into an update; reads return only the fields the caller needs. **Fail** if a handler spreads the raw request body into a create/update (`{...req.body}`, `Model(**payload)`, `Object.assign(entity, body)`, `update(body)`) on a table holding privilege, money, or ownership columns, or if an endpoint serializes a whole user/account row (password hash, tokens, internal ids, other tenants' fields) to the client. **Partial** if some routes bind explicitly and others do not, or if writes are guarded but responses over-fetch. N/A if the product has no client-supplied writes and no API responses. Finding id: `mass-assignment-open`.
- [ ] Restrict file uploads. N/A if there are no uploads. Trace an oversized, unexpected, and path-shaped file through the server: enforce a size bound before unbounded buffering; validate content for its intended use rather than trusting only the declared MIME type or extension; prevent caller-controlled storage paths; and serve files with access and execution policy appropriate to their sensitivity. Public storage is acceptable only for intentionally public, non-executable content. **Fail** when a concrete upload path permits traversal, unbounded memory/disk use, executable content, or unauthorized retrieval. Finding id: `unrestricted-file-upload`.
- [ ] Output encoding / XSS prevention. N/A if no HTML UI.
- [ ] Security headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options) when an HTTP app serves browsers.
- [ ] Production CORS is not `Access-Control-Allow-Origin: *` with credentials, and not a prod wildcard that lets any origin call credentialed APIs. N/A if there is no browser-cross-origin API. **Fail** if `*` plus credentials, or prod `*` on a credentialed API. **Partial** if `*` without credentials on a public API.

### Data stores

- [ ] Least-privilege database credentials.
- [ ] No public tables or storage buckets holding sensitive data.

### Other

- [ ] CSRF protection where cookie sessions apply.
- [ ] HTTPS only in deployed environments (N/A for local libraries).
- [ ] Generic authentication responses on login and password reset. The server returns "Invalid email or password" or "If an account exists, we sent instructions" without exposing whether the account exists. **Fail** if the app leaks account existence to unauthenticated callers.
- [ ] Agent hooks and repository automation that execute code are reviewed before use. Verify security boundaries with an isolated request-level test or local probe when runnable; do not fabricate tokens or treat static pattern matches as proof.
- [ ] Spend controls and budget alerts configured for paid APIs and downstream providers.
- [ ] No public admin, debug, or sensitive health endpoints.
- [ ] Security events logged without PII or tokens.
- [ ] If the app uses LLMs: prompt-injection controls. N/A if no LLM.
- [ ] Webhook signatures verified (Stripe / GitHub / Svix or equivalent) when those handlers exist. N/A if there are no webhook receivers.
- [ ] Automated security scanning (e.g., Codex Security, Claude security-guidance, `npm audit`, `pip-audit`) is run, and the stack is patched against known vulnerabilities before release. **Partial** if only a lightweight scan is used without addressing critical advisories.
- [ ] Privacy notice exists that accurately maps what the app exposes, collects, why, who receives it, and user rights. N/A for internal-only tools without personal data.

---

## 2. Comprehension (repo-evidence only)

Score only what the tree shows. Do not Fail this category because a human was not interviewed.

- [ ] A reviewer can trace a critical request or job from entry point through validation, state change, external effect, and response using paths in the tree. Note the first missing or ambiguous link.
- [ ] Large or complex modules have a reason to exist and a safe change seam; demonstrate a specific change that otherwise requires editing unrelated behavior. Line count and complexity metrics select candidates for review, not automatic Fail.
- [ ] Failure modes of the critical path are findable from the tree (logs, errors, or a short debug note) without the author on call.

### Human interview (not scored / not a gate)

Mark `not assessed` unless the user was actually asked. Never Fail a gate on these.

- [ ] Author can explain the architecture and main flow in under 3 minutes without the AI.
- [ ] AI-generated diffs were read and understood before accept (not “it looks done”).
- [ ] A human can debug a critical flow without 100% AI dependence.
- [ ] “It works” was not treated as “it’s ready” — tests or equivalent were run before calling it shippable.

---

## 3. Testing

- [ ] **[C]** Critical behavior is exercised through the relevant boundaries (for example request → authorization → durable state or UI → API → effect), with a realistic success and failure scenario. Unit tests can supply additional signal for isolated rules; a mock-only test of one function is not proof that a multi-component feature works. Gate: testing.
- [ ] **[C]** Principal edge cases and error paths covered (null/empty, malformed, timeouts, dependency failure). Gate: testing.
- [ ] **[C]** Authorization/isolation tests when the product has users (user A cannot access user B). N/A otherwise. Gate: testing.
- [ ] Test suite runs in CI.
- [ ] Happy path covered for critical features.
- [ ] Tests detect a meaningful wrong result on a critical path: for example, remove an ownership predicate, duplicate a delivery, or force an external failure and observe a failing test. Assertions check externally observable behavior or domain invariants, not just the code's current branches, mock call counts, snapshots of implementation text, or file changes. Coverage and mutation tools are optional ways to select or check cases, not universal gates. Finding id: `low-signal-tests`.
- [ ] Complex cross-component tests leave a repeatable artifact (seed/fixture, command, environment, result, and relevant trace or state) so a second developer can reproduce a failure. N/A if the product has no cross-component flow. **Partial** if only a screenshot or green badge remains. Finding id: `unreproducible-e2e`.
- [ ] Concurrent requests preserve critical invariants (stock, balance, uniqueness, quotas, or versioned updates). N/A without shared mutable state. **Fail** when two valid simultaneous operations can both succeed and leave an invalid state; verify with a concurrent test or a demonstrated missing atomic/locking boundary. Finding id: `concurrent-invariant-break`.
- [ ] Duplicate or retried requests with an externally visible effect do not double charge, send, grant, or create. N/A if there are no such effects. **Fail** when replaying the same operation changes the outcome twice without an intended business rule. Finding id: `duplicate-effect`.
- [ ] Regression suite exists (new changes do not silently break old paths).
- [ ] “Works on my machine / demo” is not the only check. `ignoreBuildErrors` / `eslint.ignoreDuringBuilds` (or equivalent) is evidence against Pass.

---

## 4. Architecture

- [ ] A critical change has an observable contract: expected inputs, outputs, state changes, and failure behavior can be found in code, tests, or a short design note.
- [ ] A change to one business rule has an identifiable owner and does not require editing unrelated transports or feature copies; demonstrate a duplicated rule or conflicting path when marking Fail.
- [ ] Where state lives is explicit: client / server / durable store — not inferred from a finished-looking UI. **Fail** if critical state has no owner and no single home in the tree. Finding id: `state-orphan`.
- [ ] A field's type, nullability, ownership, and meaning agree across schema, API, and clients; **Fail** when a concrete write or read silently drops or misinterprets the field.
- [ ] An import cycle has no observable initialization, lifecycle, or change-order defect; a detected cycle alone is a lead, not Fail.
- [ ] Known near-term changes (a new field, role, integration, or larger dataset) have an incremental path; **Fail** only when a named, required change is blocked by a concrete data or API constraint that forces replacement. Finding id: `architectural-dead-end`.
- [ ] Related durable writes preserve an identified business invariant atomically, whether via a transaction, database constraint, single write boundary, or equivalent. **Fail** when a route can persist half an operation or bypass a rule enforced elsewhere. Finding id: `aggregate-bypass`. N/A without related durable writes.
- [ ] Multiple write paths for one entity enforce the same invariants; **Fail** when one handler or worker bypasses a constraint applied by another.
- [ ] Custom infrastructure or abstractions have an observed need; **Fail** when they duplicate an existing capability and introduce a concrete failure or maintenance cost. Finding id: `mythical-architecture-trap`.
- [ ] **[C]** Cross-component behavior matches the claimed contract, including ordering, identity, state ownership, and error propagation. **Fail** on a demonstrated broken path, not because the code looks like API glue. Finding id: `fragile-api-glue`.
- [ ] No covert circular implementation: no runtime mutual-call or re-entrant loop hidden behind layers (A calls B, B calls back into A through an event, hook, middleware, or ORM callback). Distinct from the import-cycle row above, which is static. **Fail** if a request can re-enter its own handler with no depth bound and no idempotence guard. Finding id: `covert-recursion`.
- [ ] **[C]** Procedure completeness: where the code implements a known protocol, algorithm, or state machine (handshake, retry/backoff, transaction, pagination cursor, auth flow, upload lifecycle), the required intermediate steps are present and ordered — not compressed to the two endpoints that make a demo pass. **Fail** if a step whose omission is invisible on the happy path (ack, commit, revoke, close, verify, checkpoint) is missing. Finding id: `step-skipped`. N/A if the tree implements no such protocol.
- [ ] Cohesive system, not a patchwork of micro-systems: features share their transport, auth, config, and error conventions instead of each shipping its own. **Partial** if two features solve the same cross-cutting concern differently; **Fail** if the integration surface grows at least as fast as the feature count. Finding id: `micro-system-patchwork`.
- [ ] A state change and its external message/event cannot silently diverge. N/A without both durable writes and externally delivered effects. **Fail** when a crash after either step leaves an unrecoverable partial result; an outbox, transactional broker, reconciliation, or equivalent can satisfy the outcome. Finding id: `split-write-loss`.

---

## 5. Maintainability

Shipping is the easy part. Score whether someone who **did not write this** can still change it six months later.

- [ ] Formatting and lint checks run on changed code where the stack supports them; failures are reviewed rather than disabled to ship.
- [ ] Public names and boundaries are consistent enough to find all callers of a business rule; demonstrate an ambiguous or misleading name before marking Fail.
- [ ] A critical TODO names the blocked behavior, risk, and next action; **Fail** when a known broken path is left active with only “fix later.”
- [ ] Stranger handoff: a developer who did not author the code can find and change a critical path from the tree alone (README + layout + traced flow). **Fail** if the only workable path is the original chat thread or “ask the model that wrote it.” Finding id: `stranger-handoff`.
- [ ] Maintenance policy in-tree: how to change, how to release, and what “done” means after the first ship (CONTRIBUTING, runbook, or equivalent). Finding id: `maintenance-policy-missing`.
- [ ] Custom code duplicating a maintained dependency or platform capability has a documented requirement and test; **Fail** when the duplicate introduces a concrete bug or ongoing maintenance burden. Finding id: `over-generation`.
- [ ] A newcomer can implement a named change to a critical flow with a bounded diff and an executable safety check; **Fail** when the only viable path is replacing the module because behavior and dependencies cannot be isolated. Finding id: `rebuild-trap`.
- [ ] A failing critical request or job has enough correlation, error context, and local reproduction steps to identify the failing stage without the original chat. **Fail** on a demonstrated opaque failure path. Finding id: `ai-debug-dependency`.
- [ ] Repeated changes to a critical path do not require increasingly broad edits; compare two representative feature changes or duplicated integration points. Documented opinions about maintenance cost are not evidence. Finding id: `vibe-coded-obsolescence`.

### Human interview (not scored / not a gate)

- [ ] Author believes a stranger could maintain this six months later without a full rewrite.
- [ ] Author can name who owns each critical module (even if “me, solo”).

---

## 6. Error handling

- [ ] **[C]** Errors are not swallowed (`catch` empty, ignored promises, discarded results). Gate: error handling.
- [ ] **[C]** Stack traces not exposed to end users. Gate: error handling.
- [ ] External calls have a bounded timeout or deadline and an explicit retry decision. **Fail** when an indefinite wait blocks a critical path, or a retry can repeat a non-idempotent effect. Circuit breakers are optional. Finding id: `unsafe-retry`.
- [ ] An external service failure produces an explicit failed, queued, or degraded state; **Fail** when the caller sees success while the required effect was lost.
- [ ] A failed critical request or job logs a correlation id, operation, and safe cause without logging secrets; **Fail** when an incident cannot identify which stage failed.
- [ ] User-facing errors identify a recoverable action without exposing stack traces, credentials, or internal paths; developer logs retain the diagnostic detail.
- [ ] A failed identity, permission, or policy lookup denies the action; **Fail** when an exception falls through to allow.
- [ ] Cleanup happens on the failure path too (`finally` / `defer` / context manager / `try`-scoped teardown), not only on the happy path. **Fail** if an early `return` or `throw` between acquire and release leaks the resource. Finding id: `cleanup-on-failure-missing`.
- [ ] A retry or worker redelivery has a defined attempt limit, backoff, and terminal state when applicable. **Fail** when a persistent failure loops without bound, hides work indefinitely, or multiplies downstream load. N/A without retries or redelivery. Finding id: `retry-storm`.

---

## 7. Performance

- [ ] A list path does not issue a query per returned item at expected list size; compare query counts for one item and a larger page. N/A without relational or remote per-item fetches.
- [ ] Critical queries use an index or bounded scan appropriate to expected data volume; inspect a query plan on representative data. N/A without a database.
- [ ] When cached data affects permissions, money, inventory, or other mutable decisions, invalidation or expiry keeps it consistent with the authoritative state. N/A without such caching. **Fail** when a revoked permission or changed price remains usable through a stale cache. Finding id: `stale-critical-cache`.
- [ ] Public or frequently called list endpoints enforce a server-side size limit and stable continuation or ordering; **Fail** when one request can load the full growing dataset.
- [ ] A critical path has a measured or reproducible bound at the expected data volume; cite the query plan, load test, or bounded algorithm rather than a claim that scale was considered.
- [ ] Deployed critical paths expose latency, error, and saturation signals that let an operator distinguish slow demand from a failed dependency. N/A for offline packages.
- [ ] A critical UI flow has a measured load and interaction budget on a representative device; **Fail** on a reproduced regression that makes the flow unusable. N/A without a UI.
- [ ] Bounded buffers, queues, and caches: every in-memory accumulator has an explicit bound and a defined behaviour at the bound (drop, block, evict). Ring/circular buffers have their wrap and full-vs-empty arithmetic covered by a test. **Fail** if an unbounded structure grows with traffic, or if a hand-rolled circular buffer has no test that crosses the wrap point. Finding id: `unbounded-buffer`. N/A if the product holds no in-memory state across requests.
- [ ] Resource release: connections, file handles, subscriptions, timers, watchers, and workers are released by whoever acquires them. **Partial** if some paths clean up; **Fail** if a long-lived service acquires without a matching release on the critical path. Finding id: `resource-leak`.
- [ ] For an agent harness that assembles model requests, price-weighted token cost is measured per completed task, with output, uncached input, cached input, and all agent turns included. Compare a representative task mix with task success; **Fail** when a claimed saving counts only one request or drops quality without measuring it. N/A outside agent harnesses. Finding id: `harness-cost-unmeasured`.
- [ ] For an agent harness that controls request assembly or tool output, inspect rendered requests for repeated static context, volatile prefix bytes, or large/truncated tool results; verify the chosen cache and retrieval behavior against actual provider behavior and task outcomes. **Fail** only for a demonstrated cache miss, lost evidence, or repeated context cost on representative tasks. N/A when the product cannot control these surfaces. Finding id: `harness-context-waste`.

---

## 8. Dependencies

- [ ] A dependency's role is identifiable, supported, and compatible with the target runtime; flag a package only when its maintenance, permissions, or transitive footprint creates a concrete risk.
- [ ] Package names and publishers resolve to the intended projects; investigate an unpublished, newly registered, or abandoned package before install. Finding id: `slopsquat`.
- [ ] Deployed artifacts resolve reproducible dependency versions from a lockfile or equivalent; libraries may publish supported version ranges.
- [ ] Known applicable critical advisories from the resolved dependency tree are patched or have a documented, tested mitigation.

---

## 9. Process / environments

Repo-evidence only for scored items.

- [ ] A reviewer can identify the change and its verification from a diff, PR, or release record; commit count and message style alone do not establish quality.
- [ ] `.gitignore` covers secrets, dependencies, and build output.
- [ ] Distinct local / staging / production (or documented equivalent) in CI/config/docs. Gate: environment isolation.
- [ ] A failed release has a versioned rollback path for application code and configuration. For durable data, show how the old and new versions coexist during rollback or how data is restored/reconciled. **Fail** if reverting code leaves the old version unable to read changed data. Finding id: `rollback-trap`. Gate: environment isolation.
- [ ] In a shared production repository, changes to critical paths have an independent review before release. N/A for a solo or non-deployed project.
- [ ] In a shared production repository, release checks cannot be silently bypassed on the default branch; verify branch rules and CI. N/A for a solo or non-deployed project.
- [ ] A broad rewrite preserves unrelated behavior as shown by a focused diff or regression check. A single initial commit is not a Fail. Finding id: `one-shot-dump`.
- [ ] Claimed install / run / test commands from README (or equivalent) were executed in this audit snapshot and exited 0 — or failure is recorded as evidence. **Fail** if the docs promise a command that was never run and cannot be shown to work. Tool missing → `insufficient evidence`.
- [ ] A large change has stated acceptance boundaries in a test, issue, spec, or PR; **Fail** only when an omitted boundary caused a demonstrated wrong outcome. Finding id: `skipped-planning`.
- [ ] **[C]** Open-ended features have executable or inspectable contracts for the business rules that matter. **Fail** on a specific contradiction between implemented behavior and a required boundary, not on the wording of a prompt. Finding id: `open-ended-trap`.
- [ ] **[C]** Critical library calls and generated logic use real APIs and satisfy their documented contract; reproduce a wrong return value, error handling path, or nonexistent API before marking Fail. Finding id: `blind-acceptance`.
- [ ] **[C]** A change does not silently remove unrelated behavior; compare a concrete diff or regression test. AI authorship alone does not affect the mark. Finding id: `ai-code-drift`.
- [ ] Before production release, rehearse rollback against a disposable environment or equivalent deployment test, including a migrated dataset if applicable. Record the command, result, and recovery time; a document that only says “rollback” is Partial. N/A for packages with no deployment. Finding id: `rollback-unproven`. Gate: environment isolation.
- [ ] A data-critical system can restore or reconcile durable state from a backup or event history tested on a disposable copy. **Fail** when a backup exists but cannot reproduce a critical read or required invariant. N/A without durable user data. Finding id: `restore-unproven`. Gate: environment isolation.

### Human interview (not scored / not a gate)

- [ ] AI agent never has write access to production or prod secrets.

---

## 10. Product / scope

Score product claims that the project actually makes. N/A for product claims that are not made; a deployed user-facing product with no stated user or task Fails the target-user row. Do not infer strategy from a code tree alone.

- [ ] Target user and problem stated in-tree (who it is for, what pain). **Fail** if the tree never says who it solves for.
- [ ] A claimed validated need has traceable user evidence or usage data; N/A when the project makes no validation claim. **Fail** when a claim is contradicted by available evidence.
- [ ] The core workflow performs the stated user task on representative input; **Fail** when only the landing/demo works. Finding id: `landing-over-product`.
- [ ] Business rules in code or tests match the stated workflow rather than a generic CRUD shell; name a missing rule and its incorrect outcome. Finding id: `raw-code-delusion`.
- [ ] The project has an observable success condition for its stated task (completed action, correct result, or operational target); a formal KPI document is optional. Finding id: `missing-product-judgment`.

---

- [ ] If the product claims defensibility, its evidence names a user need, distribution advantage, workflow, or service quality that code alone does not provide. N/A when no such claim is made. A cloneable implementation is not a technical Fail. Finding id: `clone-vulnerable`.
- [ ] If the product promises availability or support, its monitoring, recovery path, and cost capacity match that promise. N/A without such a promise. Do not require an SLA from a prototype. Finding id: `missing-sla`.

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
- [ ] A migration on populated data has a compatibility plan across old and new application versions, a backfill or dual-read/write strategy where needed, and a tested failure path. **Fail** when rollback to the previous application version cannot read the migrated data. Finding id: `migration-rollback-break`.
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
| `aggregate-bypass` | Fail / Partial | A write path bypasses a business invariant or leaves related state half-written |
| `rebuild-trap` | Fail | Rational next step for a stranger is rewrite, not refactor |
| `maintenance-policy-missing` | Fail / Partial | No in-tree how-to-change / how-to-release after first ship |
| `one-shot-dump` | Fail / Partial | Broad rewrite removes behavior without reviewable proof or regression detection |
| `landing-over-product` | Fail / Partial | Marketing surface dominates; problem unproven |
| `architectural-dead-end` | Fail | A named required change cannot be made incrementally because of a concrete constraint |
| `over-generation` | Fail / Partial | Generated a massive custom solution for a solved problem (should write less code) |
| `skipped-planning` | Fail / Partial | An unstated acceptance boundary caused a demonstrated wrong outcome |
| `missing-product-judgment` | Fail / Partial | Missing reasoning for what to build and why |
| `fragile-api-glue` | Fail | Cross-component behavior breaks a stated contract despite compiling |
| `ai-debug-dependency` | Fail | Critical failure cannot be localized from correlation, errors, or reproduction steps |
| `open-ended-trap` | Fail | Implemented behavior contradicts a required business boundary |
| `blind-acceptance` | Fail | Critical API or generated logic demonstrably violates its contract |
| `ai-code-drift` | Fail | A change silently removes unrelated behavior, shown by diff or regression |
| `vibe-coded-obsolescence` | Fail / Partial | Successive changes to a critical path require increasingly broad edits |
| `raw-code-delusion` | Fail / Partial | Missing business rule yields an incorrect workflow outcome |
| `unbounded-buffer` | Fail / Partial | In-memory accumulator with no bound, or an untested ring-buffer wrap |
| `resource-leak` | Fail / Partial | Connections, handles, subscriptions, timers or workers acquired without release |
| `cleanup-on-failure-missing` | Fail / Partial | Teardown only on the happy path; an early return/throw leaks the resource |
| `covert-recursion` | Fail | Runtime re-entrant or mutual-call loop hidden behind an event, hook or middleware |
| `step-skipped` | Fail | Protocol compressed to its endpoints; a required intermediate step is missing |
| `micro-system-patchwork` | Fail / Partial | Features each ship their own transport/auth/config instead of shared conventions |
| `clone-vulnerable` | Fail / Partial | A defensibility claim has no supporting user, workflow, distribution, or service evidence |
| `missing-sla` | Fail / Partial | Promised availability/support lacks monitoring, recovery, or cost capacity |
| `idor` | Fail | Object-level AuthZ missing: a request id is trusted without a server-side owner/tenant check |
| `idor-open` | Fail | Alias of `idor`. Accepted in reports; `idor` stays the canonical id used by eval manifests |
| `isolation-tests` | Fail | No user A vs user B proof (the stranger permission test was never run) |
| `rls-open` | Fail | Datastore rules missing or open. Datastore layer — not a substitute for `idor` on the app path |
| `mass-assignment-open` | Fail / Partial | Raw request body bound into a create/update (field tampering), or responses over-fetch privileged fields |
| `missing-rate-limit` | Fail / Partial | No server/edge rate limit or bot protection on login, signup, or expensive/paid endpoints |
| `low-signal-tests` | Fail / Partial | Tests mirror implementation or detect edits but miss a plausible behavior defect |
| `unreproducible-e2e` | Fail / Partial | Cross-component result lacks the setup, command, and output needed to repeat it |
| `harness-cost-unmeasured` | Fail / Partial | Harness cost claim omits billing categories, turns, or task success |
| `harness-context-waste` | Fail / Partial | Rendered requests or tool outputs cause demonstrated cache misses, context cost, or lost evidence |
| `unrestricted-file-upload` | Fail / Partial | Uploads without a server-side type/size allowlist, with caller-controlled names, or stored publicly/executably |
| `client-bundle-secret` | Fail | Server secret in shipped client |
| `localstorage-jwt` | Fail / Partial | Browser-readable token has demonstrated exposure or is trusted without server verification |
| `ignore-build-errors` | Fail | Build/lint errors ignored to ship the demo |
| `auth-enumeration` | Fail | App leaks account existence to unauthenticated callers (no generic responses) |
| `hostile-repo-config` | Fail | Unreviewed agent hooks/config execute untrusted code in an isolated environment |
| `missing-spend-limits` | Fail / Partial | No budget alerts or provider spend controls configured |
| `missing-security-scan` | Fail / Partial | Automated security scan is missing or vulnerabilities are unpatched before release |
| `missing-privacy-notice` | Fail / Partial | Privacy notice missing or inaccurate |
| `concurrent-invariant-break` | Fail | Concurrent valid requests violate a shared-state invariant |
| `duplicate-effect` | Fail | Retry or replay repeats an externally visible effect |
| `split-write-loss` | Fail | Database state and external message/effect diverge after a crash |
| `unsafe-retry` | Fail / Partial | External call waits indefinitely or repeats a non-idempotent effect |
| `retry-storm` | Fail / Partial | Failed work retries without a bound, backoff, or terminal state |
| `stale-critical-cache` | Fail / Partial | Stale cache controls permissions, money, or inventory |
| `rollback-trap` | Fail | Reverted application cannot read or reconcile changed data |
| `rollback-unproven` | Fail / Partial | Rollback is documented but never rehearsed |
| `migration-rollback-break` | Fail | Populated migration breaks old/new version compatibility |
| `restore-unproven` | Fail / Partial | Backup or recovery path cannot be shown to restore data |
