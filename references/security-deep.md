# Security deep (patterns, not a second gate list)

Load in **Deep** mode when scoring Security. Item marks stay in `references/checklist.md`. Thresholds stay in `references/gates.md`. This file is a **search playbook**: vibe-coding failure modes mapped to OWASP, with commands.

Do not treat a finding here as a new scored mega-item. Map each hit onto the matching checklist row (AuthZ, secrets, injection, …). Absence of a pattern is evidence for Pass on that row, not a separate bonus.

Run from the project root. If a command fails, record `insufficient evidence` on affected checklist items.

Assume `rg` (ripgrep). Substitute `grep -R` if needed.

---

## 1. Client-only Next.js middleware “auth”

**OWASP:** A01 Broken Access Control, A07 Identification and Authentication Failures.

Middleware that only checks a cookie exists, or `getSession` only in Client Components, is not AuthZ. Server routes, Server Actions, and RSC data loaders must re-check identity and ownership.

```bash
rg -n "middleware" --glob 'middleware.{ts,js}' --glob 'src/middleware.{ts,js}'
rg -n "getSession|getServerSession|createServerClient|auth\(\)" --glob '*.{ts,tsx,js,jsx}'
rg -n "matcher:" --glob 'middleware.{ts,js}'
```

Red flags: `if (!cookie) redirect` with no user id; API handlers that trust `x-user-id` headers; `export const runtime` handlers that never call the auth SDK.

---

## 2. localStorage JWT as AuthZ

**OWASP:** A01, A07, A02 Cryptographic Failures.

A token in `localStorage` is readable by XSS. Using it only in the browser to hide UI is not authorization.

```bash
rg -n "localStorage\.(get|set)Item" --glob '*.{ts,tsx,js,jsx}'
rg -n "jwt|access_token|id_token|refresh_token" --glob '*.{ts,tsx,js,jsx}'
rg -n "Authorization.*localStorage|Bearer.*localStorage"
```

Red flags: `localStorage.setItem('token')` plus client-only route guards; JWTs decoded (not verified) in the browser to assign roles; `httpOnly: false` / missing HttpOnly on session cookies (map to checklist **[C]** session cookies — Fail, not Partial). Missing `signOut` / session revoke / token denylist maps to checklist **session invalidation** (not this row).

```bash
rg -n "httpOnly:\\s*false|httpOnly:\\s*!1" --glob '*.{ts,js}'
rg -n "maxAge:\\s*[0-9]{6,}" --glob '*.{ts,js}'
rg -n "signOut|sign.out|revokeSession|invalidate.*token|\\.logout\\(" --glob '*.{ts,tsx,js,jsx}'
```

---

## 3. Supabase / Firebase datastore rules off or open

**OWASP:** A01, A05 Security Misconfiguration.

Anon/authenticated clients plus missing RLS / Firebase rules = IDOR by URL. Map hits to checklist **datastore rules** (not only `saas-multi-tenant`). `service_role` / live keys in client JS map to **[C] client-bundle secrets**, not this row.

```bash
rg -n "ENABLE ROW LEVEL SECURITY|enable row level security" --glob '*.sql'
rg -n "CREATE POLICY|create policy" --glob '*.sql'
rg -n "USING \\(true\\)|using \\(true\\)" --glob '*.sql'
rg -n "allow read, write: if true|allow read: if true" --glob '*.{rules,json}'
rg -n "firebase\\.json|firestore\\.rules|storage\\.rules" --glob '*.{json,rules}'
rg -n "createClient" --glob '*.{ts,tsx,js,jsx}'
```

Red flags: migrations that `CREATE TABLE` without `ENABLE ROW LEVEL SECURITY`; policies `USING (true)`; Firebase `allow read, write: if true`; no `firestore.rules` / `storage.rules` while the client uses Firebase.

---

## 4. Public storage buckets

**OWASP:** A01, A05.

```bash
rg -n "public:\s*true|bucket.*public" --glob '*.{ts,js,sql,json}'
rg -n "storage\.from\(|createBucket|makePublic" --glob '*.{ts,tsx,js,jsx}'
rg -n "S3_BUCKET|ACL.*public-read|BlockPublicAcls" --glob '*.{ts,js,tf,yml,yaml,json}'
```

Red flags: user uploads in a public bucket; signed URLs with year-long expiry; no content-type allowlist.

---

## 5. Prompt injection (LLM apps)

**OWASP:** A03 Injection, plus LLM01 Prompt Injection (OWASP LLM Top 10). N/A if no LLM.

```bash
rg -n "system:|system_prompt|You are" --glob '*.{ts,tsx,js,py,md}'
rg -n "openai|anthropic|chat\.completions|ChatCompletion" --glob '*.{ts,js,py}'
rg -n "user.*content|messages\.push" --glob '*.{ts,js,py}'
```

Red flags: untrusted user text concatenated into the system prompt; tools that execute SQL/shell from model output without a allowlist; retrieved docs pasted verbatim as instructions.

---

## 6. Agent / CI production credentials

**OWASP:** A05, A07, A02.

Do **not** Fail a gate because you cannot prove an agent “never touches prod”. Score the **repo**: prod secrets in the client, in committed env files, or in CI jobs that deploy with overly broad tokens.

```bash
rg -n "AWS_SECRET|OPENAI_API_KEY|DATABASE_URL|PRIVATE_KEY|SERVICE_ROLE" --glob '*.{yml,yaml,tf,env*,md,json}'
rg -n "environment: production|vercel --prod|kubectl apply" --glob '*.{yml,yaml}'
ls -la .github/workflows 2>/dev/null
```

Red flags: prod `DATABASE_URL` in `docker-compose.yml`; the same secret used in preview and production; deploy keys with write-all.

---

## 7. Hallucinated or slopsquatted packages

**OWASP:** A06 Vulnerable and Outdated Components, A08 Software and Data Integrity Failures.

Map to checklist **no hallucinated / slopsquatted packages**.

```bash
# Node
rg -n '"dependencies"|"devDependencies"' package.json
# Compare names against the registry; unpublished names are blockers.
# Python
rg -n "^[a-zA-Z0-9_.-]+==" requirements.txt pyproject.toml 2>/dev/null
# Look for packages the model commonly invents next to real ones.
```

Red flags: names that do not exist on npm/PyPI; names published days ago with near-zero downloads matching a common hallucination (**slopsquatting**); `latest` tags in production; postinstall scripts from unknown publishers; missing lockfile.

---

## 8. Leaked `.env` in git

**OWASP:** A02.

```bash
git ls-files | rg '(^|/)\.env($|\.)' || true
git log --all --full-history -- '.env' '.env.*' 2>/dev/null | head
rg -n "sk-|ghp_|xoxb-|AKIA[0-9A-Z]{16}|-----BEGIN" --glob '!*.lock' --glob '!**/node_modules/**'
```

Red flags: `.env` tracked; keys in README “examples” that look live. `NEXT_PUBLIC_` wrapping a server secret belongs on **[C] client-bundle secrets**, not this row.

If `git` is unavailable, say so and scan the working tree only (`insufficient evidence` for history).

---

## 9. Secrets in the client bundle / prod source maps

**OWASP:** A02. Map to checklist **[C] no secrets in the client bundle**.

```bash
rg -n "NEXT_PUBLIC_|VITE_|EXPO_PUBLIC_|PUBLIC_" --glob '*.{ts,tsx,js,jsx,env*}'
rg -n "service_role|SERVICE_ROLE|sk_live|sk_test|supabaseServiceRole" --glob '*.{ts,tsx,js,jsx,env*}'
rg -n "productionBrowserSourceMaps|devtool:\\s*['\"]source-map|hidden-source-map" --glob '*.{js,ts,mjs,cjs}'
```

Red flags: `NEXT_PUBLIC_SUPABASE_SERVICE_ROLE`; `sk_live` imported from `app/` client components; `service_role` in any file that ships to the browser; `productionBrowserSourceMaps: true` (or webpack `devtool: 'source-map'` in a prod build) next to secrets in frontend source. A publishable/anon key on a public prefix (`NEXT_PUBLIC_SUPABASE_ANON_KEY`, Stripe `pk_`) is expected — not this Fail.

---

## 10. Production CORS wildcard

**OWASP:** A05. Map to checklist **production CORS**.

```bash
rg -n "Access-Control-Allow-Origin.*\\*|origin:\\s*['\"]\\*|origin:\\s*\\*" --glob '*.{ts,js,py,go,json}'
rg -n "cors\\(|Access-Control-Allow-Credentials" --glob '*.{ts,js,py,go}'
```

Red flags: `origin: '*'` with `credentials: true`; a prod env that sets `Access-Control-Allow-Origin: *` on cookie/session APIs. Same-origin App Router with no CORS config is N/A, not Fail.

---

## 11. Unsigned webhooks

**OWASP:** A08. Map to checklist **webhook signatures**. N/A if no receivers.

```bash
rg -n "stripe|constructEvent|webhook" --glob '*.{ts,js,py,go}'
rg -n "x-github-event|X-Hub-Signature|svix" --glob '*.{ts,js,py}'
```

Red flags: Stripe/GitHub/Svix handlers that parse the body without `constructEvent` / signature header verify.

---

## 12. Frontend-only rate limit / skipped validation / ignored build errors

Map each hit onto an existing checklist row — not new mega-items.

**Rate limit (server/edge, not the React counter):** map to **`missing-rate-limit`**. Full playbook, including bot protection, in §14.

```bash
rg -n "rateLimit|rate-limit|ratelimit|upstash.*ratelimit" --glob '*.{ts,js,py,go}'
rg -n "rateLimit|cooldown|attempts" --glob '**/app/**/*.{ts,tsx,js,jsx}'
```

Red flags: limiter only in a Client Component; login/LLM routes with no server/edge limiter. Map to **rate limiting**.

**Hardcoded `true` skipping validation** — map to **[C] server-side input validation**:

```bash
rg -n "if\\s*\\(\\s*true\\s*\\)|skipValidation|validate:\\s*false|safeParse[\\s\\S]{0,80}true" --glob '*.{ts,js,py}'
```

**`ignoreBuildErrors` / source maps as demo-shaped shipping** — map `ignoreBuildErrors` / `eslint.ignoreDuringBuilds` to Testing **“works on my machine / demo”**; prod source maps that leak secrets to **[C] client-bundle secrets**:

```bash
rg -n "ignoreBuildErrors|eslint\\.ignoreDuringBuilds" --glob 'next.config.*'
rg -n "productionBrowserSourceMaps:\\s*true" --glob 'next.config.*'
```

---

## 13. Resource lifecycle: unbounded buffers, leaks, covert recursion

Not an OWASP category on its own, but the same greps serve the availability side (A04/A05: a
process that grows until the OOM killer takes it is an outage). Hits map onto Performance
`unbounded-buffer` / `resource-leak`, Error handling `cleanup-on-failure-missing`, and
Architecture `covert-recursion` in `references/checklist.md` — not onto new mega-items.

**Unbounded in-memory accumulators** — map to **`unbounded-buffer`**:

```bash
# module-level mutable state that only ever grows
rg -n "^(const|let|var)\s+\w+\s*[:=]\s*(new (Map|Set|WeakMap)\(|\[\]|\{\})" --glob '*.{ts,js}'
rg -n "^\w+\s*[:=]\s*(\[\]|\{\}|set\(\)|dict\(\)|defaultdict)" --glob '*.py'
# growth with no eviction: push/append/set with no delete/evict/shift/maxsize nearby
rg -n "\.(push|append|add|set)\(" --glob '*.{ts,js,py,go}' -A2 | rg -v "delete|evict|shift|splice|pop|clear|maxsize|maxLen|capacity"
# caches and queues declared without a bound
rg -n "lru|LRUCache|node-cache|cacheable|Queue\(|deque\(" --glob '*.{ts,js,py}' | rg -v "max|ttl|capacity|bound"
```

Red flags: a `Map` of sessions/sockets/jobs at module scope with no `delete`; `deque()` with no
`maxlen`; an in-process job list that is the queue. Pass needs the bound **and** the documented
behaviour at the bound (drop / block / evict).

**Hand-rolled circular / ring buffers** — the SPEC's "buffer circular malformado". Map to
**`unbounded-buffer`**:

```bash
rg -n "ring|circular.?buffer|RingBuffer|head\s*=\s*\(|tail\s*=\s*\(|%\s*(size|capacity|len)" --glob '*.{ts,js,py,go,c,cc,cpp,rs}'
```

Then read the wrap arithmetic and look for a test that crosses it. **Fail** if `head == tail`
is the only full-vs-empty discriminator with no count/sentinel, or if no test drives the buffer
past `capacity`. This is the canonical "compiles, looks right, corrupts under load" shape:
absence of a wrap-crossing test is the evidence, not a hunch.

**Acquire without release** — map to **`resource-leak`**:

```bash
rg -n "createConnection|createPool|new Pool\(|connect\(|createClient\(" --glob '*.{ts,js,py,go}'
rg -n "open\(|fs\.(open|createReadStream|createWriteStream)|tempfile" --glob '*.{ts,js,py}'
rg -n "setInterval|setTimeout|\.watch\(|new Worker\(|spawn\(|Thread\(" --glob '*.{ts,js,py}'
rg -n "addEventListener|\.on\(|subscribe\(" --glob '*.{ts,tsx,js,jsx}'
# now count the matching releases
rg -c "close\(\)|end\(\)|release\(\)|destroy\(\)|dispose\(\)|clearInterval|clearTimeout|removeEventListener|unsubscribe\(|\.terminate\(\)" --glob '*.{ts,tsx,js,jsx,py,go}'
```

Red flags: `createPool` per request instead of per process; `setInterval` in a component or
request handler with no `clearInterval`; `subscribe` with no `unsubscribe` in teardown; a
transport or long-lived service that opens per call and never closes. In Python, prefer the
absence of `with` / `contextlib.closing` as the evidence:

```bash
rg -n "=\s*open\(" --glob '*.py' | rg -v "with\s"
```

**Cleanup missing on the failure path** — map to **`cleanup-on-failure-missing`**:

```bash
# try blocks with no finally / defer / context manager
rg -n --multiline "try\s*\{[\s\S]{0,600}?\}\s*catch[\s\S]{0,400}?\}(?!\s*finally)" --glob '*.{ts,js}'
rg -c "finally" --glob '*.{ts,js,py}'
rg -c "defer " --glob '*.go'
```

Red flag: an early `return` or `throw` between the acquire and the release, so the happy path
cleans up and the error path does not.

**Covert circular implementation** — the SPEC's "implementación circular encubierta". Map to
**`covert-recursion`**:

```bash
# runtime re-entry through events, hooks, middleware or ORM callbacks
rg -n "emit\(|dispatch\(|publish\(|trigger\(" --glob '*.{ts,js,py}'
rg -n "afterSave|afterUpdate|post_save|@receiver|beforeCreate|hooks:" --glob '*.{ts,js,py}'
# recursion with no depth bound
rg -n "depth|maxDepth|_seen|visited|recursion" --glob '*.{ts,js,py}'
```

Red flags: a `post_save` / `afterUpdate` hook that writes the same table it fires on; a
middleware that re-issues the request it is handling; a retry wrapper that calls a function
which retries. Static import-cycle tools (`madge`, `import-linter`) do **not** catch these —
that is why the checklist keeps this row separate from the import-cycle row.

---

## 14. Rate limit and bot protection on auth and paid endpoints

**OWASP:** A07 Identification and Authentication Failures, A04 Insecure Design. Map to checklist **rate limiting** and **brute-force / bot protection** — finding id **`missing-rate-limit`**.

Vibe-coded auth ships the login route and stops. The limiter, when it exists, is a `useState` counter in the form component, or an in-process `Map` that resets on every serverless cold start and does not exist on the second instance.

```bash
# is there a server/edge limiter at all?
rg -n "rateLimit|rate.?limit|Ratelimit|slidingWindow|fixedWindow|tokenBucket" --glob '*.{ts,tsx,js,jsx,py,go}'
rg -n "@upstash/ratelimit|express-rate-limit|rate-limiter-flexible|slowapi|limiter=|flask_limiter|throttle_classes" --glob '*.{ts,js,py,go,json}'
# the auth routes themselves — do any of them import a limiter?
rg -n --files-with-matches "signin|sign-in|login|register|signup|forgot.?password|reset.?password|verify.?otp" --glob '**/{app,pages,routes,api,src}/**/*.{ts,tsx,js,jsx,py,go}'
# limiter living only in the browser (never Pass)
rg -n "attempts|cooldown|retryAfter|disabled=" --glob '**/{components,app}/**/*.{tsx,jsx}'
# a limiter that a serverless deploy resets or shards
rg -n "new Map\(\)|const attempts|_attempts\s*=\s*\{\}|defaultdict\(int\)" --glob '*.{ts,js,py}'
# bot protection
rg -n "captcha|hcaptcha|recaptcha|turnstile|altcha|friendly.?captcha|arcjet|botid|BotD" --glob '*.{ts,tsx,js,jsx,py,go,html}'
# and its server-side verification, not just the widget
rg -n "siteverify|verify.*turnstile|challenges\.cloudflare\.com|assessments" --glob '*.{ts,js,py,go}'
```

Red flags: a login/register/reset route with no limiter import on any server path; the limiter keyed only on `x-forwarded-for` taken straight from a caller-settable header with no trusted-proxy config; an in-memory counter as the only store on a serverless or multi-instance deploy; a CAPTCHA widget rendered in the form whose token is never sent to `siteverify` (the widget is decoration until the server verifies it); LLM or paid-API routes throttled nowhere. Absence of any server/edge limiter on a live auth path is **Fail** — do not Pass because the login form disables its button.

---

## 15. Mass assignment and over-fetching (block field tampering, trim API responses)

**OWASP:** A01 Broken Access Control (API3:2023 Broken Object Property Level Authorization), A04 Insecure Design. Map to checklist **block field tampering / trim API responses** — finding id **`mass-assignment-open`**.

Two halves of the same defect. **Write:** the handler spreads the request body into the model, so the caller sets `role`, `is_admin`, `credits`, `price`, `status`, or `owner_id` by adding a key the UI never renders. **Read:** the handler returns the whole row, so the client receives the password hash, the reset token, the internal id, or another tenant's fields — invisible in the UI, visible in the network tab.

```bash
# writes: raw body straight into a create/update
rg -n "\.\.\.(req|request)\.body|\.\.\.body\b|\.\.\.(await )?req\.json\(\)|\.\.\.input\b|\.\.\.data\b" --glob '*.{ts,tsx,js,jsx}'
rg -n "Object\.assign\((entity|user|record|row|model|doc)" --glob '*.{ts,js}'
rg -n "\.(create|update|updateOne|updateMany|findOneAndUpdate|insert|save)\(\s*(req\.body|body|data|payload)" --glob '*.{ts,js}'
rg -n "\*\*(request\.(json|data|POST)|payload|body|data)\)" --glob '*.py'
rg -n "fields\s*=\s*'__all__'|exclude\s*=\s*\(\)|permit!|params\.permit\b" --glob '*.{py,rb}'
# is there an allowlist anywhere?
rg -n "\.pick\(|\.omit\(|\.strict\(\)|z\.object\([\s\S]{0,200}strict|class Config|model_config|only=|dump_only|read_only" --glob '*.{ts,js,py}'
# reads: whole-row serialization
rg -n "select\(\s*\*|SELECT \*|\.select\('\*'\)|findMany\(\)|findFirst\(\)|\.find\(\{\}\)" --glob '*.{ts,js,py,sql}'
rg -n "return\s+(NextResponse\.)?json\((user|account|profile|row|record)\b" --glob '*.{ts,js}'
# privileged columns that must never be client-settable
rg -n "\b(is_?[Aa]dmin|role|roles|permissions|credits|balance|price|amount|status|owner_?id|tenant_?id|org_?id|email_?verified|plan|stripe_customer)\b" --glob '*.{ts,js,py,sql,prisma}'
# secrets that must never be serialized out
rg -n "password_?hash|passwordHash|reset_?token|refresh_?token|api_?key|two_?factor_?secret" --glob '*.{ts,js,py}'
```

Read the write handler and answer one question: **which fields can the caller set?** If the answer is "whatever it sends", that is **Fail** when the table holds privilege, money, or ownership columns. A Zod/Pydantic schema that validates the shape but is not `.strict()` (or is spread into the model after parsing extra keys) is not an allowlist. For reads, `SELECT *` behind a `/api/users` route that returns `password_hash` is **Fail** even though nothing renders it. **Partial** when some routes bind explicitly and others do not.

---

## 16. Unrestricted file uploads

**OWASP:** A01, A03 Injection, A04, A05 Security Misconfiguration. Map to checklist **restrict file uploads** — finding id **`unrestricted-file-upload`**. N/A if the product accepts no uploads.

```bash
# is there an upload path at all?
rg -n "multipart/form-data|FormData|multer|busboy|formidable|UploadFile|request\.files|createPresignedPost|getSignedUrl|storage\.from\([^)]*\)\.upload" --glob '*.{ts,tsx,js,jsx,py,go}'
# server-side type allowlist (client MIME alone is not one)
rg -n "mimetype|mimeType|content-?type|accept=|allowedMimeTypes|fileFilter|file_?type|magic|filetype|python-magic|file-type" --glob '*.{ts,tsx,js,jsx,py,go}'
# size cap enforced before buffering
rg -n "limits:\s*\{|fileSize|maxFileSize|MAX_CONTENT_LENGTH|client_max_body_size|maxSize|bodyParser.*limit" --glob '*.{ts,js,py,conf,yml,yaml}'
# caller-controlled filename / path traversal
rg -n "originalname|file\.filename|filename\)|path\.join\([^)]*(filename|originalname|req\.)" --glob '*.{ts,js,py}'
rg -n "secure_filename|randomUUID|nanoid|uuid4" --glob '*.{ts,js,py}'
# where it lands: public, or web-served, or executable
rg -n "public:\s*true|public/uploads|static/uploads|ACL.*public-read|makePublic|/var/www" --glob '*.{ts,js,py,sql,json,tf,yml,yaml}'
rg -n "createSignedUrl|getSignedUrl|expiresIn|Expires" --glob '*.{ts,js,py}'
```

Red flags: `multer({ dest })` or a raw `request.files[...]` write with no `fileFilter` and no `limits.fileSize`; an allowlist built from the client-declared `file.type` / `Content-Type` (the caller sets both — check the magic bytes or re-encode); a **denylist** of extensions (`.php`, `.exe`) instead of an allowlist; `path.join(uploadDir, file.originalname)` with no sanitiser, so `../../` escapes the directory and the caller picks the extension; uploads written into `public/` or `static/` where the app server will serve — and possibly execute — them; a public bucket, or signed URLs with year-long expiry; SVG or HTML accepted into a same-origin served path (stored XSS); no cap, so one request fills the disk or the memory of the instance.

Pass needs the whole set: server-side type **and** size limits, a server-generated stored name, and non-executable, non-public storage. Missing any one of those on a live upload path is **Fail**; type and size present but public or caller-named storage is **Partial**.

---

## 17. Object-level access: the stranger permission test

**OWASP:** A01 (API1:2023 Broken Object Level Authorization). Map to checklist **[C] object-level authorization / lock record access** — finding id **`idor`** (alias `idor-open`). Distinct from §3: that row is the datastore policy (`rls-open`); this one is the application check on the server path. A product can have RLS on and still be IDOR-open through a service-role server route, and vice versa.

```bash
# every handler that takes an id from the request
rg -n "params\.id|params\.\w+Id|req\.params|request\.args\.get|path_params|\[id\]|<int:.*_id>" --glob '*.{ts,tsx,js,jsx,py,go}'
# the lookup itself
rg -n "findUnique|findFirst|findById|getById|\.eq\('id'|\.eq\(\"id\"|filter_by\(id=|objects\.get\(|WHERE id\s*=" --glob '*.{ts,js,py,go,sql}'
# now: is the owner/tenant in the same predicate?
rg -n "owner_?id|user_?id|tenant_?id|org_?id|account_?id|workspace_?id" --glob '*.{ts,js,py,go,sql}'
# a check that runs after the row is already loaded and returned is not one
rg -n --multiline "findUnique\([\s\S]{0,300}?\}\)[\s\S]{0,200}?(return|res\.json)" --glob '*.{ts,js}'
# and the proof: does an isolation test exist?
rg -n "userB|user_b|other_?user|stranger|forbidden|403|404" --glob '**/{test,tests,spec,__tests__,e2e}/**/*'
```

**The stranger permission test.** Grep is not the evidence — a request is. Authenticate as user B, request an id that belongs to user A, on every sensitive resource and every verb (`GET`, `PATCH`, `DELETE`, and the list endpoint), and record the status. Expect `403` or `404`. `200` with A's data is **Fail**. `200` with an empty body but a real row behind it is still **Fail** if a sibling verb leaks it.

Red flags: the ownership check lives in the client, in a `useEffect`, or in a middleware that only proves *a* session exists; the id is a sequential integer and the route filters on it alone; `findUnique({ where: { id } })` followed by a `if (row.userId !== session.user.id)` that runs after the row was already spread into the response; nested routes (`/orgs/:org/items/:id`) that trust `:org` from the URL instead of from the session; a service-role / admin datastore client used inside a user-facing route, which bypasses RLS entirely; a `list` endpoint that is scoped correctly while the `detail` endpoint is not.

Absent a request-level proof, the row is **Partial** at best — never Pass. If the isolation test itself is missing, also record `isolation-tests` (Testing).

---

## Other high-yield vibe-coding greps

Map hits onto existing checklist rows.

| Pattern | OWASP | Command / note |
|---------|-------|----------------|
| IDOR / lock record access | A01 | Full playbook in §17. `rg -n "params\.id|\.eq\('id'|findUnique|findById" --glob '*.{ts,js,py,go}'` then confirm an owner/tenant predicate. Grep alone is Partial; Pass needs the stranger permission test (`idor`). |
| Mass assignment / over-fetching | A01 | Checklist **block field tampering** (`mass-assignment-open`). See §15. |
| Unrestricted upload | A01/A03 | Checklist **restrict file uploads** (`unrestricted-file-upload`). See §16. |
| No rate limit / bot protection | A07 | Checklist **rate limiting** (`missing-rate-limit`). See §14. |
| SQL/NoSQL concat | A03 | `rg -n "\$\{.*\}.*(SELECT\|INSERT\|UPDATE)|execute\(|raw\(" --glob '*.{ts,js,py,go}'` |
| XSS | A03 | `rg -n "dangerouslySetInnerHTML|innerHTML|v-html" --glob '*.{ts,tsx,js,jsx,vue}'` |
| CSRF | A01 | Cookie sessions without SameSite/CSRF token on mutating routes. |
| SSRF | A10 | `rg -n "fetch\(.*req\.|axios.*url" --glob '*.{ts,js,py}'` user-controlled URLs. |
| Build errors ignored | A04 | Testing **“works on my machine / demo”**. See §12. |
| CORS `*` | A05 | Checklist **production CORS**. See §10. |
| Unsigned webhooks | A08 | Checklist **webhook signatures**. See §11. |
| `eval` / `new Function` | A03 | `rg -n "\beval\(|new Function\(" --glob '*.{ts,js,py}'` |
| Debug endpoints | A05 | `rg -n "debug=true|/debug|/admin" --glob '*.{ts,js,py}'` plus auth check. |
| Auth enumeration | A02 | `rg -n "email not found|user does not exist|already registered" --glob '*.{ts,js,py}'` (`auth-enumeration`) |
| Hostile repo config | A05 | `rg -n "build:|preinstall:|prebuild:" --glob 'package.json'`; check `.serena/project.yml` (`hostile-repo-config`) |
| Missing privacy notice | A01 | `rg -n "privacy|gdpr" --glob '*.md'` or UI files (`missing-privacy-notice`) |

---

## How to write Security evidence

For each finding: path + line, what is missing, which checklist row it marks. Example: `` `app/api/tasks/[id]/route.ts` loads by `id` with no `org_id` → AuthZ `[C]` Fail ``.

Do not score “attacker imagination” without a path. Do not Pass because the demo login works.

## 18. Hostile Agent Configuration (Vibe Coder Trap)

**OWASP:** A05 Security Misconfiguration. Map to checklist **agent hooks** — finding id **`hostile-repo-config`**. 
Agents operating in unfamiliar or third-party repositories can be hijacked by hidden execution hooks.

```bash
# Check for agent-specific configurations that might execute code
rg -n "build:|preinstall:|prebuild:" --glob 'package.json'
rg -n "\.serena/|mcp_config|codex-security|claude-plugins" --glob '**/*'
```

**The Threat:** In August 2024, GitLab disclosed that agent configurations like `.serena/project.yml` could execute attacker-controlled code when a repository is merely opened by an agent.
**Evidence:** If an unfamiliar repository contains undocumented agent instructions, hooks, editor tasks, or MCP configurations, it must be opened in an isolated environment with low-privilege credentials. **Fail** if these are present and unreviewed.

---

## 19. Attack the Authentication Flow (Smoke Tests)

**OWASP:** A02 Cryptographic Failures / A07 Identification and Authentication Failures. Map to checklist **Generic authentication responses** — finding id **`auth-enumeration`**.

Testing the "happy path" is not enough for vibe-coded apps. You must attack the flow.

```bash
# Check for account enumeration leaks in error responses
rg -n "User not found|Email not found|Account does not exist|Invalid password|Incorrect password" --glob '*.{ts,js,py,go}'
# Check for token expiration and single-use constraints
rg -n "expiresIn|maxAge|exp" --glob '*.{ts,js,py}'
```

**The Smoke Tests:**
1. Submit wrong passwords: verify backoff/lockout.
2. Password reset for unknown email: must return same generic response as a known email ("If an account exists...").
3. Reuse reset link: must expire or be single-use.
4. Signup existing email: must not expose account state before user proves control.

**Fail** if the app leaks whether an account exists or uses explicit errors ("Invalid password"). Pass requires generic responses ("Invalid email or password").

---

## 20. Abuse, Spending, and Cost Amplification

**OWASP:** A04 Insecure Design. Map to checklist **Spend controls** — finding id **`missing-spend-limits`**.
A polished UI with a paid API (like OpenAI) behind it is a vulnerability if not bounded.

```bash
# Look for paid API usage
rg -n "openai|anthropic|stripe|replicate|aws|billing" --glob '*.{ts,js,py}'
# Look for local rate limiters or budget checks
rg -n "rateLimit|upstash|bottleneck|Turnstile|budget|spend_limit" --glob '*.{ts,js,py}'
```

**The Threat:** An unprotected endpoint lets a script call a paid API thousands of times.
**Evidence:** Do not rely on one universal requests-per-minute number. Choose limits based on expected behavior and endpoint cost. **Fail** if paid endpoints lack concurrency limits, cost budgets, or enforced provider spend limits.

---

## 21. Automated Deep Security Review

**OWASP:** A06 Vulnerable and Outdated Components. Map to checklist **Automated security scanning** — finding id **`missing-security-scan`**.

```bash
# Check if a deep scanner is configured in CI
rg -n "codex-security scan|claude-security|npm audit|pip-audit|trufflehog" --glob '.github/workflows/*.yml' --glob 'package.json'
```

**The Threat:** A security scanner cannot compensate for choosing to run a version with a known critical vulnerability (e.g., Next.js August 25 AVIF RCE). 
**Evidence:** **Fail** if the stack is not patched against known advisories before scanning.
