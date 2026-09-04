# Evals

Five planted fixtures plus expected-finding manifests. The fixtures plant the same class of public dunks the auditor is built from (secrets, weak auth, demo-only tests, and neighbors). The agent still classifies evidence. These files measure whether it found the planted dunks.

## Fixtures

| Dir | Product type | Planted |
|-----|--------------|---------|
| `fixtures/saas-multi-tenant` | `saas-multi-tenant` | IDOR, open RLS, `NEXT_PUBLIC_` service role, localStorage JWT, `ignoreBuildErrors` |
| `fixtures/saas-single-user` | `saas-single-user` | Firebase `allow read, write: if true` (datastore rules apply; isolation tests N/A) |
| `fixtures/cli` | `cli` | Empty `catch`; no HTTP/auth |
| `fixtures/library` | `library` | Hallucinated package `react-sate-managment`, no lockfile |
| `fixtures/skill-docs` | `skill/docs` | Native AGY discovery docs, runnable script, zero tests |

`expected/forgeboard.json` is the golden for `references/example-report.md` (CI).

## Run (after an agent audit)

```bash
python3 scripts/validate-report.py vibe-proof-audit-report.md --json report.json --sarif report.sarif
python3 scripts/compare-eval.py evals/expected/saas-multi-tenant.json report.json
```

Baseline (fail only on new Fail gates/findings):

```bash
python3 scripts/compare-eval.py --baseline previous.json report.json
```

CI does not spawn coding agents. It checks math on the worked example and the compare-eval contract. Inter-model recall is a 1.0 gate, not a 0.6 one.
