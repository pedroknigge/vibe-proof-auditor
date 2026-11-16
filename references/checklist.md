# Checklist

Single home for **scored items**. Do not copy this list into `assets/checklist-template.md` (that file is a cover: metadata, score table, gates). Marks: Pass / Partial / Fail / N/A / insufficient evidence. Numeric mapping, floors, and N/A matrix: `references/scoring.md`. Verdicts and gate thresholds: `references/gates.md`. Security expansion (grep playbook): `references/security-deep.md`.

**Growth rule:** improve an existing row for a repeated failure. Add a row for a distinct, applicable, testable failure. Remove or merge a row that only restates an opinion or another mark.

**Critical** items are marked `[C]`. Floors: `references/scoring.md` (do not restate them here).

**Evidence:** for each applicable row identify the affected path, the input or failure sequence, the observable result, and a test or trace that distinguishes Pass from Fail. A grep hit is a lead, not proof; a missing grep hit is not proof of safety. Absence of a required, applicable control is Fail only after the relevant paths are inspected. Tool failure is `insufficient evidence`, not a critical Fail. Human-interview items are listed separately: `not assessed` if unasked — never Fail, never a gate. Score outcomes, not a preferred framework, provider, document format, or history of AI use.

**Partial:** control exists on some paths only, or is weak. **Pass:** present and applied on the relevant paths.

---

## 1. Security

Do **not** add a mega-item “complies with OWASP Top 10”. Use `references/security-deep.md` in Deep mode.

### Secrets

- [ ] **[C]** No hardcoded secrets in source (API keys, tokens, passwords, JWT secrets, connection strings). Gate: critical security.
- [ ] **[C]** No secrets in the client bundle: no public env prefix (`NEXT_PUBLIC_`, `VITE_`, `EXPO_PUBLIC_`, or equivalent) wrapping a server secret; no `service_role` / `sk_live` / equivalent in client components or shipped JS; production source maps do not expose secrets. N/A if there is no client/browser bundle. **Fail** if a server secret is readable from shipped client JS or prod source maps. Finding id: `client-bundle-secret`. Gate: critical security.
- [ ] Secrets only in env or a secret manager; `.env` gitignored; `.env.example` present without real values. **Fail** when a real secret is committed, `.env` is tracked, or no example lists the required variables.
- [ ] Secret scan in CI or documented equivalent (gitleaks, TruffleHog, GitHub secret scanning) — `insufficient evidence` if tools cannot run, not Fail.
- [ ] If a secret ever landed in git, rotation is documented in-tree. If unknown, `insufficient evidence`, not Fail.

### Authentication (N/A if the product has no auth)

- [ ] **[C]** Authentication is server-side (not client-only middleware or localStorage checks). Gate: critical security.
- [ ] Authentication verifies credentials or tokens at the server boundary, checks expiry and issuer/audience where relevant, and does not trust a client-supplied user id. A provider is one implementation; verify its configuration and use. **Fail** when a token is accepted without signature, expiry, or issuer verification on a path that trusts it. N/A if the product has no authenticated users.
- [ ] Rate limiting on login, register, password-reset, and auth endpoints, **and** on expensive / LLM / paid-API endpoints when those exist. Enforcement runs in a trusted server, provider, or edge layer before the expensive operation. For password login, check independent per-account and per-source limits (or an equivalent control against both distributed attempts at one account and one-source account sweeps); one combined `IP:account` bucket alone does not cover either pattern. Verify the source address comes from a trusted proxy path, not a caller-controlled header. N/A the paid sub-path if absent. **Fail** if a live auth or paid endpoint has no trusted limiter at all. **Partial** if the limiter misses a relevant path or either abuse pattern. A frontend counter is never Pass. Finding id: `missing-rate-limit`.
- [ ] Brute-force / credential-stuffing and bot protection (lockout, exponential backoff, CAPTCHA / Turnstile / device check, or provider equivalent) on login, signup, and public write forms. **Partial** if only one of lockout/backoff/bot-check is present on a public signup or login. **Fail** when a public login, signup, or write form has no throttle, backoff, or bot check at all. N/A without public authentication or write forms. Maps to `missing-rate-limit` when the endpoint has no throttle of any kind.
- [ ] **[C]** Session exposure and expiry match the threat model. For cookie sessions, inspect HttpOnly, Secure, SameSite, expiry, and CSRF protection; for bearer tokens, inspect where they are stored, XSS exposure, expiry, and refresh handling. **Fail** when a token can be stolen or reused through a demonstrated path, or an unverified token grants access. JS-readable storage is a risk to investigate, not proof of broken authorization on its own. N/A if there is no session or token auth. Finding id: `localstorage-jwt`.
- [ ] Session invalidation: logout and server-side revoke (or provider equivalent) when cookie/session/JWT auth exists. N/A if no such auth. **Fail** if sessions cannot be ended. **Partial** if logout exists but stolen tokens cannot be revoked.
- [ ] **[C]** Passwords are stored with a modern, salted password hash (bcrypt, scrypt, argon2, or PBKDF2 with a current work factor), never plaintext, reversible encryption, or an unsalted fast hash (MD5, SHA-1, SHA-256 alone). **Fail** when a schema, seed, or migration shows a stored password or a fast-hash column. N/A without password auth. Gate: critical security. Finding id: `weak-password-hash`.
- [ ] Password reset and email verification tokens are single-use, expiring, bound to the account, and checked server-side before the credential or address changes. Execute one reset and one verification on a disposable account or provider test mode; **Fail** when a token is reusable, predictable, long-lived, or the flow was never run. N/A without password auth. Finding id: `unproven-reset-flow`.

### Authorization (N/A if no users and resources)

- [ ] **[C]** Every server entry point declares and enforces its auth requirement: route handler, server action, RPC, admin or debug route, and scheduled job. Login is not permission. **Fail** when a sensitive or mutating endpoint is reachable anonymously without an intended signature or token check, or by any authenticated user regardless of role, or when a handler trusts a client-supplied role or user id. Gate: critical security. Finding id: `endpoint-authz-missing`.
- [ ] **[C]** Object-level authorization — lock record access (IDOR / BOLA) on every sensitive resource. Every read, update, and delete that takes an id from the request re-derives the owner/tenant server-side; a stranger who guesses or increments the id gets 403/404, not the record. **Pass** requires the server ownership/tenant predicate on the resource path **and** an isolation test or equivalent request-level proof (the *stranger permission test*: authenticate as user B, request user A's id, expect denied). Grep / “the UI hides the button” only is **Partial**, never Pass. Finding id: `idor` (alias `idor-open`). Distinct from datastore rules below: this row is the **application** ownership check on the server path; `rls-open` is the **datastore** policy that protects the same rows when a client key reaches the database directly. Both can Fail independently — score them separately, and do not Pass this row because RLS exists. Gate: critical security.
- [ ] Frontend is not the authorization boundary: hiding a route, button, or field does not protect the resource. **Fail** when a direct request from an unauthorized account succeeds because the only check lived in the client. N/A when the product has no privileged client action or protected resource.
- [ ] Roles and permissions evaluated on the server. **Fail** when a role check exists only in the client, or every authenticated user receives the same privilege.
- [ ] **[C]** Datastore rules (Postgres RLS, Firebase Security Rules, or equivalent) when the product has users **and** a client-reachable datastore (anon/authenticated client key, mobile SDK, etc.). Applies to `saas-single-user` when a client key can read rows — not only `saas-multi-tenant`. N/A if there is no client-reachable datastore. **Fail** if rules are off, missing, or open (`USING (true)`, allow-all Firebase rules, a policy that grants every authenticated user access to every row, or equivalent). Verify the policy predicate matches the actual owner or tenant column, not only “authenticated”. Finding id: `rls-open`. Gate: critical security.

### Input / output

- [ ] **[C]** Server-side input validation on entry points. **Fail** if a hardcoded `true` (or equivalent) skips validation on a live path. Gate: critical security.
- [ ] Parameterized queries / safe ORM (no string-concat SQL/NoSQL). **Fail** when user input reaches a query string, shell, or template through concatenation or interpolation with no parameter binding.
- [ ] Block field tampering on writes, and trim what reads return. Writes bind an explicit allowlist of client-settable fields (schema `.pick()`, DTO, `strict()` / `attr_accessible` equivalent) so a caller cannot smuggle `role`, `is_admin`, `price`, `owner_id`, `credits`, or `status` into an update; reads return only the fields the caller needs. **Fail** if a handler spreads the raw request body into a create/update (`{...req.body}`, `Model(**payload)`, `Object.assign(entity, body)`, `update(body)`) on a table holding privilege, money, or ownership columns, or if an endpoint serializes a whole user/account row (password hash, tokens, internal ids, other tenants' fields) to the client. **Partial** if some routes bind explicitly and others do not, or if writes are guarded but responses over-fetch. N/A if the product has no client-supplied writes and no API responses. Finding id: `mass-assignment-open`.
- [ ] Restrict file uploads. N/A if there are no uploads. Trace an oversized, unexpected, and path-shaped file through the server: enforce a size bound before unbounded buffering; validate content for its intended use rather than trusting only the declared MIME type or extension; prevent caller-controlled storage paths; and serve files with access and execution policy appropriate to their sensitivity. Public storage is acceptable only for intentionally public, non-executable content. **Fail** when a concrete upload path permits traversal, unbounded memory/disk use, executable content, or unauthorized retrieval. Finding id: `unrestricted-file-upload`.
- [ ] Output encoding / XSS prevention. **Fail** when untrusted input reaches HTML, an attribute, or a script context without context-specific encoding, or a raw-HTML sink trusts stored content. **Partial** when encoding exists but one sink or rich-text path bypasses it. N/A if no HTML UI.
- [ ] Security headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options) when an HTTP app serves browsers. N/A when no browser client exists. **Fail** when a production HTML response lacks CSP or HSTS without a documented compensating control. Finding id: `missing-security-headers`.
- [ ] Production CORS is not `Access-Control-Allow-Origin: *` with credentials, and not a prod wildcard that lets any origin call credentialed APIs. N/A if there is no browser-cross-origin API. **Fail** if `*` plus credentials, or prod `*` on a credentialed API. **Partial** if `*` without credentials on a public API. Finding id: `cors-wildcard`.

### Data stores

- [ ] Least-privilege database credentials: the runtime user can read and write its tables but cannot alter the schema, grant roles, or read unrelated databases. N/A without a database. **Fail** when the application connects as an owner, superuser, or `service_role` on a path that only needs row access. Finding id: `db-superuser`.
- [ ] No public tables or storage buckets holding sensitive data: list/read access is limited to intended readers, and object URLs are not guessable and permanent for private content. N/A without storage or a public database surface. **Fail** when a private bucket or table is world-readable. Finding id: `public-storage-bucket`.
- [ ] Sensitive data at rest is protected: the database and object storage use provider-managed encryption, and secrets, tokens, recovery codes, and credentials are not stored in plaintext. **Fail** when a schema, seed, or storage dump shows a plaintext password, API key, session or reset token, or recovery code. N/A without durable sensitive data. Finding id: `plaintext-sensitive-data`.

### Other

- [ ] CSRF protection where cookie sessions apply (token, SameSite, or equivalent). N/A without cookie-authenticated state changes. **Fail** when a cross-site form or fetch can perform an authenticated state change. Finding id: `missing-csrf`.
- [ ] HTTPS only in deployed environments, on the intended domain, with a valid certificate that renews automatically. N/A for local libraries. **Fail** when the public URL serves HTTP, uses a self-signed or expired certificate, or the configured domain does not resolve to the deployed app.
- [ ] Generic authentication responses on login and password reset. The server returns "Invalid email or password" or "If an account exists, we sent instructions" without exposing whether the account exists. **Fail** if the app leaks account existence to unauthenticated callers. N/A without authentication. Finding id: `auth-enumeration`.
- [ ] Agent hooks and repository automation that execute code are reviewed before use, and they cannot exfiltrate secrets or write to production. **Fail** when an unreviewed hook, MCP server, or CI step runs network code with repository credentials. Verify with an isolated probe when runnable; do not fabricate tokens or treat static pattern matches as proof. Finding id: `hostile-repo-config`.
- [ ] Spend controls and budget alerts configured for paid APIs, downstream providers, and cloud infrastructure usage. **Fail** when a provider bill or quota can grow without a configured alert or hard cap. Finding id: `missing-spend-limits`.
- [ ] No public admin, debug, or sensitive health endpoints. **Fail** when an unauthenticated caller reaches an admin panel, debug inspector, metrics detail, or health payload that exposes configuration or dependencies. N/A when no such endpoint exists.
- [ ] Security events and privileged or irreversible actions (role change, permission grant, data export, deletion, payment adjustment, credential reset) leave an audit record with actor, action, target, timestamp, outcome, and request correlation. **Fail** when such an action leaves no attributable record. N/A when the product has no privileged or irreversible actions. Finding id: `missing-audit-trail`.
- [ ] Security events logged without PII or tokens: no password, session token, full request body, or personal record in application or error-tracker logs. **Fail** when a log line or error payload contains a credential or sensitive personal field. Finding id: `pii-in-logs`.
- [ ] Stored personal data is limited to fields with a use: every personal-data column has a read path or documented purpose, and no sensitive identifier is collected “in case.” **Fail** when an unused field holds a phone number, birth date, address, government id, or free-text PII with no use and no retention or deletion path. N/A without personal data. Finding id: `pii-overcollection`.
- [ ] If the app uses LLMs: prompt-injection controls. Untrusted content is separated from instructions, tool calls are bounded, and model output is not executed or trusted as authorization. **Fail** when retrieved or user content can change system behavior or reach a privileged tool without a boundary. N/A if no LLM.
- [ ] Webhook signatures verified (Stripe / GitHub / Svix or equivalent) when those handlers exist. **Fail** when a receiver trusts the payload without verifying the signature and rejecting replays. N/A if there are no webhook receivers.
- [ ] Automated security scanning (e.g., Codex Security, Claude security-guidance, `npm audit`, `pip-audit`) is run, and the stack is patched against known vulnerabilities before release. **Fail** when a known applicable critical advisory is unpatched at release. **Partial** if only a lightweight scan is used without addressing critical advisories. Finding id: `missing-security-scan`.
- [ ] Privacy notice exists that accurately maps what the app exposes, collects, why, who receives it, and user rights. **Fail** when the product collects personal data with no notice, or the notice names a different data flow than the tree shows. **Partial** when the notice exists but omits a recipient or user right. N/A for internal-only tools without personal data. Finding id: `missing-privacy-notice`.

---

## 2. Comprehension (repo-evidence only)

Score only what the tree shows. Do not Fail this category because a human was not interviewed.

- [ ] A reviewer can trace a critical request or job from entry point through validation, state change, external effect, and response using paths in the tree. Note the first missing or ambiguous link. **Fail** when no critical path can be traced end to end from the tree.
- [ ] Large or complex modules have a reason to exist and a safe change seam; demonstrate a specific change that otherwise requires editing unrelated behavior. Line count and complexity metrics select candidates for review, not automatic Fail. **Fail** only when a demonstrated change requires editing unrelated behavior.
- [ ] Failure modes of the critical path are findable from the tree (logs, errors, or a short debug note) without the author on call. **Fail** when the failure mode exists only in the author's memory or chat history.

### Human interview (not scored / not a gate)

Mark `not assessed` unless the user was actually asked. Never Fail a gate on these.

- [ ] Author can explain the architecture and main flow in under 3 minutes without the AI.
- [ ] AI-generated diffs were read and understood before accept (not “it looks done”).
- [ ] A human can debug a critical flow without 100% AI dependence.
- [ ] “It works” was not treated as “it’s ready” — tests or equivalent were run before calling it shippable.

---

## 3. Testing

- [ ] **[C]** Critical behavior is exercised through the relevant boundaries (for example request → authorization → durable state or UI → API → effect), with a realistic success and failure scenario. The happy path of a critical feature is included. Unit tests can supply additional signal for isolated rules; a mock-only test of one function is not proof that a multi-component feature works. Gate: testing.
- [ ] **[C]** Principal edge cases and error paths covered (null/empty, malformed, timeouts, dependency failure). Gate: testing.
- [ ] **[C]** Authorization/isolation tests when the product has users (user A cannot access user B). N/A otherwise. Gate: testing. Finding id: `isolation-tests`.
- [ ] Test suite runs in CI and a pull request cannot merge with failing tests. N/A never: a tree with no automated suite is Fail. Finding id: `no-tests`.
- [ ] Tests detect a meaningful wrong result on a critical path: for example, remove an ownership predicate, duplicate a delivery, or force an external failure and observe a failing test. Assertions check externally observable behavior or domain invariants, not just the code's current branches, mock call counts, snapshots of implementation text, or file changes. Coverage and mutation tools are optional ways to select or check cases, not universal gates. Finding id: `low-signal-tests`.
- [ ] Complex cross-component tests leave a repeatable artifact (seed/fixture, command, environment, result, and relevant trace or state) so a second developer can reproduce a failure. N/A if the product has no cross-component flow. **Partial** if only a screenshot or green badge remains. Finding id: `unreproducible-e2e`.
- [ ] A release candidate was exercised on the deployed non-production environment with its real configuration: the critical flow, one authorization or isolation check, and one failure path. **Fail** when a deployed product has only local or mocked runs and no staging execution record. N/A without a deployment. Finding id: `staging-unproven`.
- [ ] Concurrent requests preserve critical invariants (stock, balance, uniqueness, quotas, or versioned updates). N/A without shared mutable state. **Fail** when two valid simultaneous operations can both succeed and leave an invalid state; verify with a concurrent test or a demonstrated missing atomic/locking boundary. Finding id: `concurrent-invariant-break`.
- [ ] Duplicate or retried requests with an externally visible effect do not double charge, send, grant, or create. N/A if there are no such effects. **Fail** when replaying the same operation changes the outcome twice without an intended business rule. Finding id: `duplicate-effect`.
- [ ] Regression suite exists (new changes do not silently break old paths). **Partial** when only a handful of critical paths are protected; **Fail** when no regression check exists.
- [ ] “Works on my machine / demo” is not the only check. `ignoreBuildErrors` / `eslint.ignoreDuringBuilds` (or equivalent) is evidence against Pass. **Partial** when a known broken path ships with a disabled check and no tracked fix; **Fail** when the only check is a manual demo. Finding id: `ignore-build-errors`.

---

## 4. Architecture

- [ ] A critical change has an observable contract: expected inputs, outputs, state changes, and failure behavior can be found in code, tests, or a short design note. **Fail** when a critical behavior can only be inferred from a finished UI or a chat thread.
- [ ] A change to one business rule has an identifiable owner and does not require editing unrelated transports or feature copies; demonstrate a duplicated rule or conflicting path when marking Fail.
- [ ] Where state lives is explicit: client / server / durable store — not inferred from a finished-looking UI. **Fail** if critical state has no owner and no single home in the tree. Finding id: `state-orphan`.
- [ ] A field's type, nullability, ownership, and meaning agree across schema, API, and clients; **Fail** when a concrete write or read silently drops or misinterprets the field.
- [ ] An import cycle has no observable initialization, lifecycle, or change-order defect; a detected cycle alone is a lead, not Fail.
- [ ] Known near-term changes (a new field, role, integration, or larger dataset) have an incremental path; **Fail** only when a named, required change is blocked by a concrete data or API constraint that forces replacement. Finding id: `architectural-dead-end`.
- [ ] Related durable writes preserve an identified business invariant atomically, whether via a transaction, database constraint, single write boundary, or equivalent. **Fail** when a route can persist half an operation or bypass a rule enforced elsewhere. Finding id: `aggregate-bypass`. N/A without related durable writes.
- [ ] Multiple write paths for one entity enforce the same invariants; **Fail** when one handler or worker bypasses a constraint applied by another.
- [ ] Invariants the datastore can enforce are enforced there: `NOT NULL`, `UNIQUE`, foreign keys, and `CHECK` constraints protect required fields, uniqueness, and relations instead of relying only on application code. **Fail** when a duplicate, orphan, or null-owned row can be created through a valid path because the schema permits it. N/A without a relational or schema-declared datastore. Finding id: `missing-db-constraint`.
- [ ] Custom infrastructure or abstractions have an observed need; **Fail** when they duplicate an existing capability and introduce a concrete failure or maintenance cost. Finding id: `mythical-architecture-trap`.
- [ ] **[C]** Cross-component behavior matches the claimed contract, including ordering, identity, state ownership, and error propagation. **Fail** on a demonstrated broken path, not because the code looks like API glue. Finding id: `fragile-api-glue`.
- [ ] No covert circular implementation: no runtime mutual-call or re-entrant loop hidden behind layers (A calls B, B calls back into A through an event, hook, middleware, or ORM callback). Distinct from the import-cycle row above, which is static. **Fail** if a request can re-enter its own handler with no depth bound and no idempotence guard. Finding id: `covert-recursion`.
- [ ] **[C]** Procedure completeness: where the code implements a known protocol, algorithm, or state machine (handshake, retry/backoff, transaction, pagination cursor, auth flow, upload lifecycle), the required intermediate steps are present and ordered — not compressed to the two endpoints that make a demo pass. **Fail** if a step whose omission is invisible on the happy path (ack, commit, revoke, close, verify, checkpoint) is missing. Finding id: `step-skipped`. N/A if the tree implements no such protocol.
- [ ] Cohesive system, not a patchwork of micro-systems: features share their transport, auth, config, and error conventions instead of each shipping its own. **Partial** if two features solve the same cross-cutting concern differently; **Fail** if the integration surface grows at least as fast as the feature count. Finding id: `micro-system-patchwork`.
- [ ] A state change and its external message/event cannot silently diverge. N/A without both durable writes and externally delivered effects. **Fail** when a crash after either step leaves an unrecoverable partial result; an outbox, transactional broker, reconciliation, or equivalent can satisfy the outcome. Finding id: `split-write-loss`.

---

## 5. Maintainability

Shipping is the easy part. Score whether someone who **did not write this** can still change it six months later.

- [ ] Formatting and lint checks run on changed code where the stack supports them; failures are reviewed rather than disabled to ship. **Fail** when checks are disabled or bypassed to ship a known failure.
- [ ] Public names and boundaries are consistent enough to find all callers of a business rule; demonstrate an ambiguous or misleading name before marking Fail.
- [ ] A critical TODO names the blocked behavior, risk, and next action; **Fail** when a known broken path is left active with only “fix later.”
- [ ] Stranger handoff: a developer who did not author the code can find and change a critical path from the tree alone (README + layout + traced flow). **Fail** if the only workable path is the original chat thread or “ask the model that wrote it.” Finding id: `stranger-handoff`.
- [ ] Maintenance policy in-tree: how to change, how to release, and what “done” means after the first ship (CONTRIBUTING, runbook, or equivalent). **Partial** when only one of change/release/done is documented. Finding id: `maintenance-policy-missing`.
- [ ] Custom code duplicating a maintained dependency or platform capability has a documented requirement and test; **Fail** when the duplicate introduces a concrete bug or ongoing maintenance burden. Finding id: `over-generation`.
- [ ] A newcomer can implement a named change to a critical flow with a bounded diff and an executable safety check; **Fail** when the only viable path is replacing the module because behavior and dependencies cannot be isolated. Finding id: `rebuild-trap`.
- [ ] A failing critical request or job has enough correlation, error context, and local reproduction steps to identify the failing stage without the original chat. **Fail** on a demonstrated opaque failure path. Finding id: `ai-debug-dependency`.
- [ ] Repeated changes to a critical path do not require increasingly broad edits; compare two representative feature changes or duplicated integration points. Documented opinions about maintenance cost are not evidence. **Partial** when one critical path needs repeated broad edits; **Fail** when every representative change does. Finding id: `vibe-coded-obsolescence`.

### Human interview (not scored / not a gate)

- [ ] Author believes a stranger could maintain this six months later without a full rewrite.
- [ ] Author can name who owns each critical module (even if “me, solo”).

---

## 6. Error handling

- [ ] **[C]** Errors are not swallowed (`catch` empty, ignored promises, discarded results). Gate: error handling. Finding id: `empty-catch`.
- [ ] **[C]** Stack traces not exposed to end users. Gate: error handling.
- [ ] External calls have a bounded timeout or deadline and an explicit retry decision. **Fail** when an indefinite wait blocks a critical path, or a retry can repeat a non-idempotent effect. Circuit breakers are optional. Finding id: `unsafe-retry`.
- [ ] An external service failure produces an explicit failed, queued, or degraded state; **Fail** when the caller sees success while the required effect was lost.
- [ ] A failed critical request or job logs a correlation id, operation, and safe cause without logging secrets; **Fail** when an incident cannot identify which stage failed.
- [ ] A user-facing error identifies a recoverable action or next step, and developer logs retain the diagnostic detail. **Partial** when the message is generic but a safe retry path exists; **Fail** when the user sees a dead end with no action. Stack-trace exposure is scored in the gate row above.
- [ ] A critical UI flow shows distinct loading, empty, and error states. **Fail** when a failed request leaves a blank screen, an endless spinner, stale success data, or a disabled action with no explanation. N/A without a UI. Finding id: `missing-ui-states`.
- [ ] A failed identity, permission, or policy lookup denies the action; **Fail** when an exception falls through to allow.
- [ ] Cleanup happens on the failure path too (`finally` / `defer` / context manager / `try`-scoped teardown), not only on the happy path. **Fail** if an early `return` or `throw` between acquire and release leaks the resource. Finding id: `cleanup-on-failure-missing`.
- [ ] A retry or worker redelivery has a defined attempt limit, backoff, and terminal state when applicable. **Fail** when a persistent failure loops without bound, hides work indefinitely, or multiplies downstream load. N/A without retries or redelivery. Finding id: `retry-storm`.

---

## 7. Performance

- [ ] A list path does not issue a query per returned item at expected list size; compare query counts for one item and a larger page. **Partial** when the count grows with page size but the default page stays small; **Fail** when a normal page issues one query per item. N/A without relational or remote per-item fetches.
- [ ] Critical queries use an index or bounded scan appropriate to expected data volume; inspect a query plan on representative data. **Fail** when a plan on representative volume shows a full scan that grows with the table on a critical path. N/A without a database.
- [ ] Database connections are bounded: a pool or provider limit caps concurrent connections, and per-request or serverless clients do not open an unbounded number. **Fail** when each request opens a connection without release, or expected concurrency can exhaust the provider limit. N/A without a database. Finding id: `connection-pool-unbounded`.
- [ ] When cached data affects permissions, money, inventory, or other mutable decisions, invalidation or expiry keeps it consistent with the authoritative state. N/A without such caching. **Fail** when a revoked permission or changed price remains usable through a stale cache. Finding id: `stale-critical-cache`.
- [ ] Public or frequently called list endpoints enforce a server-side size limit and stable continuation or ordering; **Fail** when one request can load the full growing dataset.
- [ ] A critical path has a measured or reproducible bound at the expected data volume; cite the query plan, load test, or bounded algorithm rather than a claim that scale was considered. **Fail** when no measurement or bound exists and the expected volume is material.
- [ ] Provider plan limits (database connections, storage, function concurrency and timeout, request and job quotas) are known, and expected launch load fits them with an upgrade or degradation path. **Fail** when launch traffic can exceed a documented hard limit and no path exists. N/A without a hosted provider limit. Finding id: `plan-limit-unknown`.
- [ ] Deployed critical paths expose latency, error, and saturation signals that let an operator distinguish slow demand from a failed dependency. **Fail** when an operator cannot distinguish slow demand from a failed dependency. N/A for offline packages.
- [ ] A critical UI flow has a measured load and interaction budget on a representative device; **Fail** on a reproduced regression that makes the flow unusable. N/A without a UI.
- [ ] Bounded buffers, queues, and caches: every in-memory accumulator has an explicit bound and a defined behaviour at the bound (drop, block, evict). Ring/circular buffers have their wrap and full-vs-empty arithmetic covered by a test. **Fail** if an unbounded structure grows with traffic, or if a hand-rolled circular buffer has no test that crosses the wrap point. Finding id: `unbounded-buffer`. N/A if the product holds no in-memory state across requests.
- [ ] Resource release: connections, file handles, subscriptions, timers, watchers, and workers are released by whoever acquires them. **Partial** if some paths clean up; **Fail** if a long-lived service acquires without a matching release on the critical path. Finding id: `resource-leak`.
- [ ] For an agent harness that assembles model requests, price-weighted token cost is measured per completed task, with output, uncached input, cached input, and all agent turns included. Compare a representative task mix with task success; **Fail** when a claimed saving counts only one request or drops quality without measuring it. N/A outside agent harnesses. Finding id: `harness-cost-unmeasured`.
- [ ] For an agent harness that controls request assembly or tool output, inspect rendered requests for repeated static context, volatile prefix bytes, or large/truncated tool results; verify the chosen cache and retrieval behavior against actual provider behavior and task outcomes. **Fail** only for a demonstrated cache miss, lost evidence, or repeated context cost on representative tasks. N/A when the product cannot control these surfaces. Finding id: `harness-context-waste`.

---

## 8. Dependencies

- [ ] A dependency's role is identifiable, supported, and compatible with the target runtime; flag a package only when its maintenance, permissions, or transitive footprint creates a concrete risk. **Fail** when a critical path depends on an abandoned package with a known exploitable issue, or a dependency requests permissions it does not need.
- [ ] Package names and publishers resolve to the intended projects; investigate an unpublished, newly registered, or abandoned package before install. **Fail** when an install resolves to a package whose name or publisher does not match the intended project. Finding id: `slopsquat`.
- [ ] Deployed artifacts resolve reproducible dependency versions from a lockfile or equivalent; libraries may publish supported version ranges. **Partial** when a lockfile exists but a deploy path ignores it; **Fail** when no lockfile or equivalent pins a deployed build.
- [ ] The runtime and build inputs are pinned: language version, package manager, and base image tag resolve to fixed versions instead of `latest` or an unconstrained system default. **Fail** when a deployed build changes runtime between releases because the version was never pinned. Finding id: `unpinned-runtime`.
- [ ] Known applicable critical advisories from the resolved dependency tree are patched or have a documented, tested mitigation. **Fail** when a known applicable critical advisory is reachable on a deployed path and unpatched.

---

## 9. Process / environments

Repo-evidence only for scored items.

- [ ] A reviewer can identify the change and its verification from a diff, PR, or release record; commit count and message style alone do not establish quality. **Partial** when the record exists but verification is unstated; **Fail** when no record lets a reviewer separate intentional change from accident.
- [ ] `.gitignore` covers secrets, dependencies, and build output. **Fail** when a local secret, dependency tree, or build artifact is tracked or committed.
- [ ] Distinct local / staging / production (or documented equivalent) in CI/config/docs. Gate: environment isolation.
- [ ] A deployed environment resolves every required variable from its own configuration, without falling back to a development default or a hardcoded localhost/dev URL. **Fail** when production silently uses a dev database, bucket, mail catcher, or API base URL. Finding id: `dev-default-in-prod`. Gate: environment isolation.
- [ ] A failed release has a versioned rollback path for application code and configuration. For durable data, show how the old and new versions coexist during rollback or how data is restored/reconciled. **Fail** if reverting code leaves the old version unable to read changed data. Finding id: `rollback-trap`. Gate: environment isolation.
- [ ] A deployed long-running service restarts automatically after a crash or exit (platform restart policy, process manager, or orchestrator) with a bounded restart loop. **Fail** when the only supervision is an open shell session or a manual restart. N/A for serverless functions, static sites, and non-deployed packages. Finding id: `no-restart-policy`.
- [ ] A deployed service exposes a health or readiness signal that gates traffic and reflects the dependencies needed before serving. **Fail** when the platform routes traffic to an instance that cannot serve its critical dependency, or when a probe reports ready during a dependency outage. A shallow liveness probe is acceptable only when the platform drains the instance on failure. N/A without a deployed service. Finding id: `missing-health-check`.
- [ ] In a shared production repository, changes to critical paths have an independent review before release. **Fail** when the default branch accepts unreviewed critical changes. N/A for a solo or non-deployed project.
- [ ] In a shared production repository, release checks cannot be silently bypassed on the default branch; verify branch rules and CI. **Fail** when an admin bypass is routine or required CI can be skipped. N/A for a solo or non-deployed project.
- [ ] An initial broad rewrite preserves unrelated behavior as shown by a focused diff or regression check. A single initial commit is not a Fail. **Partial** when the rewrite is unreviewable but a regression check exists; **Fail** when behavior was replaced with no proof. Finding id: `one-shot-dump`.
- [ ] Claimed install / run / test commands from README (or equivalent) were executed in this audit snapshot and exited 0 — or failure is recorded as evidence. **Fail** if the docs promise a command that was never run and cannot be shown to work. Tool missing → `insufficient evidence`.
- [ ] A large change has stated acceptance boundaries in a test, issue, spec, or PR; **Fail** only when an omitted boundary caused a demonstrated wrong outcome. Finding id: `skipped-planning`.
- [ ] **[C]** Open-ended features have executable or inspectable contracts for the business rules that matter. **Fail** on a specific contradiction between implemented behavior and a required boundary, not on the wording of a prompt. Finding id: `open-ended-trap`.
- [ ] **[C]** Critical library calls and generated logic use real APIs and satisfy their documented contract; reproduce a wrong return value, error handling path, or nonexistent API before marking Fail. Finding id: `blind-acceptance`.
- [ ] **[C]** A subsequent change does not silently remove unrelated behavior; compare a concrete diff or regression test. AI authorship alone does not affect the mark. Finding id: `ai-code-drift`.
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
- [ ] Business rules in code or tests match the stated workflow rather than a generic CRUD shell; name a missing rule and its incorrect outcome. **Partial** when a secondary rule is missing; **Fail** when the stated core workflow gives a wrong result. Finding id: `raw-code-delusion`.
- [ ] The project has an observable success condition for its stated task (completed action, correct result, or operational target); a formal KPI document is optional. **Partial** when the success condition is stated but not observable; **Fail** when no condition distinguishes success from a demo. Finding id: `missing-product-judgment`.

---

- [ ] If the product claims defensibility, its evidence names a user need, distribution advantage, workflow, or service quality that code alone does not provide. N/A when no such claim is made. A cloneable implementation is not a technical Fail. **Partial** when the claim names only code features; **Fail** when available evidence contradicts the claim. Finding id: `clone-vulnerable`.
- [ ] If the product promises availability or support, its monitoring, recovery path, incident communication, and cost capacity match that promise. N/A without such a promise. Do not require an SLA from a prototype. **Partial** when one of monitoring, recovery, communication, or cost capacity is missing; **Fail** when the promise exceeds all four. Finding id: `missing-sla`.

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
- [ ] Backups are automated, monitored, and retained long enough to match the recovery expectation; a failed backup alerts a human. **Fail** when the only backup is a manual export or the last successful backup is unknown. N/A without durable data.
- [ ] Deletion and retention semantics are defined: hard delete, soft delete, cascade, and retention window match what the product promises. **Fail** when deleting an account or record leaves orphaned personal data or silently removes data the product says it keeps. N/A without stored user records.
- [ ] A user can export or retrieve the personal data the product holds, when the product or its privacy notice promises that right. **Fail** when the promised export is absent or omits a data class the notice names. N/A when no export right is promised.

### Deployment

- [ ] A deployed app has an isolated review environment per change (preview deployment or equivalent) with production-like configuration. N/A for solo or non-deployed projects.
- [ ] A release avoids dropping in-flight traffic: zero-downtime rollout or a documented maintenance window with a health gate. N/A for non-deployed packages.

### Docs

- [ ] README: what it is, how to run, env vars.
- [ ] Architecture notes sufficient to find the critical path.

### Mobile / responsive

- [ ] UI works on small viewports (real device or emulator). N/A if no UI.
- [ ] A critical flow was exercised on a slow or offline network; loading and retry behavior remain usable. N/A if no UI.

### Accessibility

- [ ] Basic a11y if frontend (labels, keyboard, contrast). N/A if no UI.

### Observability

- [ ] Structured logs with a request or job id. **Fail** when a deployed service leaves only ad-hoc console output. N/A for non-deployed packages.
- [ ] Metrics cover latency, error rate, and saturation for critical paths, with thresholds that route to a monitored channel. N/A without a deployed service.
- [ ] Unhandled errors reach an error tracker with release, environment, and request context. N/A for `skill/docs`.
- [ ] An external uptime check alerts a human channel when the public endpoint is unavailable. N/A without a deployed endpoint.
- [ ] Users have a feedback or support channel, and a critical outage has a status page or equivalent communication path. N/A for internal-only tools.

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
| `weak-password-hash` | Fail | Passwords stored in plaintext or with a fast, unsalted hash |
| `unproven-reset-flow` | Fail / Partial | Reset or verification token is reusable, predictable, or the flow was never executed |
| `endpoint-authz-missing` | Fail | A server entry point trusts the client for authentication or role, or has no auth requirement |
| `plaintext-sensitive-data` | Fail | Secrets, tokens, or credentials stored unencrypted at rest |
| `missing-audit-trail` | Fail / Partial | Privileged or irreversible actions leave no attributable record |
| `pii-overcollection` | Fail / Partial | Personal data is stored without a use, retention, or deletion path |
| `missing-db-constraint` | Fail / Partial | Duplicate, orphan, or null-owned rows are possible because the schema does not enforce the invariant |
| `staging-unproven` | Fail / Partial | A deployed product has no execution record on its non-production environment |
| `missing-ui-states` | Fail / Partial | Failed or empty requests leave a blank screen, spinner, or stale success state |
| `unpinned-runtime` | Fail / Partial | Deployed build changes runtime or base image between releases |
| `dev-default-in-prod` | Fail | Production silently uses a development database, bucket, mailer, or API base URL |
| `no-restart-policy` | Fail | A long-running service depends on a shell session or manual restart |
| `missing-health-check` | Fail / Partial | Traffic reaches an instance that cannot serve its critical dependency |
| `connection-pool-unbounded` | Fail / Partial | Per-request connections or fan-out can exhaust the database provider limit |
| `plan-limit-unknown` | Fail / Partial | Launch load exceeds a documented provider quota with no upgrade or degradation path |
| `mythical-architecture-trap` | Fail / Partial | Custom abstraction duplicates an existing capability and adds a concrete failure or maintenance cost |
| `slopsquat` | Fail | A dependency resolves to an unpublished, newly registered, or unintended package |
| `pii-in-logs` | Fail | Credentials or sensitive personal data appear in logs or error-tracker payloads |
| `missing-security-headers` | Fail / Partial | A production browser response lacks CSP, HSTS, or equivalent baseline headers |
| `cors-wildcard` | Fail / Partial | Production CORS allows every origin, or a wildcard with credentials |
| `db-superuser` | Fail | The runtime connects as owner, superuser, or service role with more privilege than its path needs |
| `public-storage-bucket` | Fail | A private table or bucket is world-readable |
| `missing-csrf` | Fail | A cross-site request can perform an authenticated state change |
| `empty-catch` | Fail | An error is swallowed and the caller or user sees success |
| `no-tests` | Fail | The tree or CI has no automated suite for a runnable contract |
