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

**Rate limit (server/edge, not the React counter):**

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

## Other high-yield vibe-coding greps

Map hits onto existing checklist rows.

| Pattern | OWASP | Command / note |
|---------|-------|----------------|
| IDOR | A01 | `rg -n "params\.id|\.eq\('id'|findUnique|findById" --glob '*.{ts,js,py,go}'` then confirm an owner/tenant predicate. Grep alone is Partial; Pass needs isolation/request proof (`references/checklist.md`). |
| SQL/NoSQL concat | A03 | `rg -n "\$\{.*\}.*(SELECT\|INSERT\|UPDATE)|execute\(|raw\(" --glob '*.{ts,js,py,go}'` |
| XSS | A03 | `rg -n "dangerouslySetInnerHTML|innerHTML|v-html" --glob '*.{ts,tsx,js,jsx,vue}'` |
| CSRF | A01 | Cookie sessions without SameSite/CSRF token on mutating routes. |
| SSRF | A10 | `rg -n "fetch\(.*req\.|axios.*url" --glob '*.{ts,js,py}'` user-controlled URLs. |
| Build errors ignored | A04 | Testing **“works on my machine / demo”**. See §12. |
| CORS `*` | A05 | Checklist **production CORS**. See §10. |
| Unsigned webhooks | A08 | Checklist **webhook signatures**. See §11. |
| `eval` / `new Function` | A03 | `rg -n "\beval\(|new Function\(" --glob '*.{ts,js,py}'` |
| Debug endpoints | A05 | `rg -n "debug=true|/debug|/admin" --glob '*.{ts,js,py}'` plus auth check. |

---

## How to write Security evidence

For each finding: path + line, what is missing, which checklist row it marks. Example: `` `app/api/tasks/[id]/route.ts` loads by `id` with no `org_id` → AuthZ `[C]` Fail ``.

Do not score “attacker imagination” without a path. Do not Pass because the demo login works.
