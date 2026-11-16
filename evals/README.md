# Evals

Thirteen planted fixtures plus expected-finding manifests. The fixtures plant concrete failure paths (secrets, weak auth, demo-only tests, recovery traps, and neighbors). The agent still classifies evidence. Compare a report with a manifest after an agent audit to measure detection; CI alone checks fixture behavior and manifest structure, not agent recall.

## Fixtures

| Dir | Product type | Planted |
|-----|--------------|---------|
| `fixtures/saas-multi-tenant` | `saas-multi-tenant` | IDOR, open RLS, `NEXT_PUBLIC_` service role, client-only button guard, `ignoreBuildErrors`; browser-readable token alone is not an extra Fail |
| `fixtures/saas-single-user` | `saas-single-user` | Firebase `allow read, write: if true` (datastore rules apply; isolation tests N/A) |
| `fixtures/cli` | `cli` | Empty `catch`; no HTTP/auth |
| `fixtures/library` | `library` | Hallucinated package `react-sate-managment`, no lockfile |
| `fixtures/skill-docs` | `skill/docs` | Native AGY discovery docs, runnable script, zero tests |
| `fixtures/worker-protocol` | `cli` | Broker lease protocol compressed to `receive` + write; `renew`/`ack`/`nack` never called |
| `fixtures/resource-leak` | `library` | SQLite connection left open on the early-return error path (`resource-leak`, `cleanup-on-failure-missing`) |
| `fixtures/unbounded-buffer` | `cli` | Per-label series map with no bound or eviction, plus a hand-rolled ring buffer whose wrap is never exercised |
| `fixtures/covert-recursion` | `cli` | Handler -> save -> ORM hook -> event -> same handler, no depth bound and no idempotence guard |
| `fixtures/micro-system-patchwork` | `saas-single-user` | `billing` and `reports` each ship their own transport, auth, logging, config and error shape |
| `fixtures/rollback-trap` | `saas-single-user` | Migration renames a column; code-only rollback redeploys an old reader that crashes on the new schema |
| `fixtures/low-signal-tests` | `library` | Passing checkout test derives its expected value from the same helper and misses the shipping charge |
| `fixtures/auth-lifecycle` | `saas-single-user` | SHA-256 password hash, reusable reset token stored raw, anonymous admin export, no unique email, unused phone field |

`expected/forgeboard.json` is the golden for `references/example-report.md` (CI).

## Run (after an agent audit)

```bash
python3 -m vibe_proof_auditor.validate_report vibe-proof-audit-report.md --json report.json --sarif report.sarif
python3 -m vibe_proof_auditor.compare_eval evals/expected/saas-multi-tenant.json report.json
```

Baseline (fail only on new Fail gates/findings):

```bash
python3 -m vibe_proof_auditor.compare_eval --baseline previous.json report.json
```

CI does not spawn coding agents. It checks math on the worked example and the compare-eval contract. Inter-model recall is a 1.0 gate, not a 0.6 one.
