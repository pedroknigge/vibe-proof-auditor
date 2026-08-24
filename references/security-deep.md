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

Red flags: `localStorage.setItem('token')` plus client-only route guards; JWTs decoded (not verified) in the browser to assign roles.

---

## 3. Supabase (or similar) with RLS off

**OWASP:** A01, A05 Security Misconfiguration.

Anon/authenticated clients plus missing RLS = IDOR by URL.

```bash
rg -n "ENABLE ROW LEVEL SECURITY|enable row level security" --glob '*.sql'
rg -n "CREATE POLICY|create policy" --glob '*.sql'
rg -n "service_role|SERVICE_ROLE|supabaseServiceRole" --glob '*.{ts,tsx,js,jsx,env*}'
rg -n "createClient" --glob '*.{ts,tsx,js,jsx}'
```

Red flags: `service_role` imported into `app/` client components or `NEXT_PUBLIC_*`; migrations that `CREATE TABLE` without `ENABLE ROW LEVEL SECURITY`; policies that use `USING (true)`.

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

## 7. Hallucinated or typosquat packages

**OWASP:** A06 Vulnerable and Outdated Components, A08 Software and Data Integrity Failures.

```bash
# Node
rg -n '"dependencies"|"devDependencies"' package.json
# Compare names against the registry; unpublished names are blockers.
# Python
rg -n "^[a-zA-Z0-9_.-]+==" requirements.txt pyproject.toml 2>/dev/null
# Look for packages the model commonly invents next to real ones.
```

Red flags: names that do not exist on npm/PyPI; `latest` tags in production; postinstall scripts from unknown publishers; missing lockfile.

---

## 8. Leaked `.env` in git

**OWASP:** A02.

```bash
git ls-files | rg '(^|/)\.env($|\.)' || true
git log --all --full-history -- '.env' '.env.*' 2>/dev/null | head
rg -n "sk-|ghp_|xoxb-|AKIA[0-9A-Z]{16}|-----BEGIN" --glob '!*.lock' --glob '!**/node_modules/**'
```

Red flags: `.env` tracked; `NEXT_PUBLIC_` wrapping a server secret; keys in README “examples” that look live.

If `git` is unavailable, say so and scan the working tree only (`insufficient evidence` for history).

---

## Other high-yield vibe-coding greps

Map hits onto existing checklist rows.

| Pattern | OWASP | Command / note |
|---------|-------|----------------|
| IDOR | A01 | `rg -n "params\.id|\.eq\('id'|findUnique|findById" --glob '*.{ts,js,py,go}'` then confirm an owner/tenant predicate. |
| SQL/NoSQL concat | A03 | `rg -n "\$\{.*\}.*(SELECT\|INSERT\|UPDATE)|execute\(|raw\(" --glob '*.{ts,js,py,go}'` |
| XSS | A03 | `rg -n "dangerouslySetInnerHTML|innerHTML|v-html" --glob '*.{ts,tsx,js,jsx,vue}'` |
| CSRF | A01 | Cookie sessions without SameSite/CSRF token on mutating routes. |
| SSRF | A10 | `rg -n "fetch\(.*req\.|axios.*url" --glob '*.{ts,js,py}'` user-controlled URLs. |
| Build errors ignored | A04 | `rg -n "ignoreBuildErrors|eslint\.ignoreDuringBuilds" --glob 'next.config.*'` |
| CORS `*` | A05 | `rg -n "Access-Control-Allow-Origin.*\*|origin:\s*['\"]\\*"` |
| Unsigned webhooks | A08 | Stripe/GitHub handlers without signature verify. |
| `eval` / `new Function` | A03 | `rg -n "\beval\(|new Function\(" --glob '*.{ts,js,py}'` |
| Debug endpoints | A05 | `rg -n "debug=true|/debug|/admin" --glob '*.{ts,js,py}'` plus auth check. |

---

## How to write Security evidence

For each finding: path + line, what is missing, which checklist row it marks. Example: `` `app/api/tasks/[id]/route.ts` loads by `id` with no `org_id` → AuthZ `[C]` Fail ``.

Do not score “attacker imagination” without a path. Do not Pass because the demo login works.
