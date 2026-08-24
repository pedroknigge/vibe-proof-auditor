# Production gates

Single home for **verdict words**, **absolute/recommended gates**, the **verdict rule**, and **stage notes**. Do not copy thresholds or these strings into other files; point here.

## Verdict words (exact)

`READY` | `NEEDS HARDENING` | `BLOCKED FOR PRODUCTION`

Do not invent aliases. Do not suffix them with the stage note.

## Absolute gates (must-pass when applicable)

Skip a gate when every constituent control is N/A for the product type (`references/scoring.md`). N/A does **not** fail the gate. Human-interview claims are **not** gates.

An applicable absolute-gate bullet marked `insufficient evidence` is not Pass. It does not trip a scoring critical floor (mark values: `references/scoring.md`). Record the gate as Fail unless that bullet is N/A for the product type.

### 1. Critical security

When applicable, all of the following must hold:

- No hardcoded secrets in source or git history (as far as the tree allows).
- AuthN is server-side when the product has auth.
- Object-level AuthZ / IDOR checks on every sensitive resource when the product has users and resources.
- Server-side input validation on entry points.
- Security category score ≥ 8/10 (`references/scoring.md`).

Mark **Fail** if any applicable bullet fails. Mark **N/A** only if the product has no secrets surface, no auth, no user-owned resources, and no entry points to validate.

### 2. Testing

When applicable, all of the following must hold:

- Tests exist for critical flows.
- Principal edge cases and error paths covered.
- Authorization/isolation tests when the product has users (user A cannot access user B).
- Testing score ≥ 7/10.

Mark **N/A** when the tree is non-executable (`skill/docs` with no runtime) and no testable contract exists.

### 3. Error handling

When applicable, all of the following must hold:

- Errors are not swallowed.
- Stack traces not exposed to end users.
- Error-handling score ≥ 6/10.

Mark **N/A** when there is no runtime to handle errors.

### 4. Environment isolation

Repo-evidence only (CI, configs, docs):

- Distinct local / staging / production (or documented equivalent).
- Rollback path for data-critical systems.

Do **not** require proving “the AI agent cannot write to prod”. That claim is human-interview, `not assessed` if unasked, and never a gate.

Mark **N/A** when the package is not deployed (typical `library` publish-only may still apply a documented release/rollback path; `skill/docs` is N/A).

### 5. No ownership-human gate

Repo comprehensibility (ADRs, architecture README, absence of god files) may be scored in category 2 (`references/checklist.md`). It is **not** a production gate. Do not Fail a gate because a human was not interviewed.

## Recommended gates (non-blocking)

These never produce `BLOCKED FOR PRODUCTION` by themselves:

- Basic performance (no obvious N+1, indexes where a database exists).
- Dependency audit (lockfile, no known critical CVEs, no hallucinated packages).
- Minimal docs (README **or equivalent** onboarding hub: what it is, how to run, env vars — `AGENTS.md` + `.env.example` counts if a newcomer can start without hunting).
- Basic observability (structured logs at least).

Report them in the gates table as Pass / Fail / N/A. They may contribute to `NEEDS HARDENING` only through category scores, not as extra verdict vocabulary.

## Verdict rule

Apply only **applicable** absolute gates (skipped/N/A gates ignored):

1. Any applicable absolute gate **Fail** → `BLOCKED FOR PRODUCTION`
2. Else if overall < 8.0 **or** Evidence coverage < 80% **or** any applicable scored category **except** Product / scope is < 6 → `NEEDS HARDENING`
3. Else (all applicable absolute gates Pass, overall ≥ 8.0, coverage ≥ 80%, no applicable engineering category < 6) → `READY`

Product / scope still sits in overall (`references/scoring.md`). A score below 6 there does **not** by itself produce `BLOCKED FOR PRODUCTION` and does **not** block `READY`.

Overall, category scores, and Evidence coverage come from `references/scoring.md`. Do not average gates. Do not Fail because a recommended gate failed. `scripts/validate-report.py` recomputes this rule; the renderer does not.

## Stage (Prototype / MVP / Production)

Infer from the tree. Do not ask. Mode does **not** change absolute gates, recommended gates, floors, N/A, or verdict words.

Signals (more serious wins when mixed):

- **Production** — production URL, release changelog, public/paying users in-tree, on-call/status, or README claims production.
- **MVP** — README/changelog names MVP, one core flow, preview/staging deploy, unused billing sketch.
- **Prototype** — demo / poc / hackathon language, no deploy, no user evidence.

No signal → **MVP**. Do not default Production.

After Status, copy **one** stage note from this table. Do not paraphrase.

| Mode | Status | Stage note |
|------|--------|------------|
| Prototype | `BLOCKED FOR PRODUCTION` | Expected for Prototype. Ship the demo. Do not put users on it. |
| Prototype | `NEEDS HARDENING` | Ahead of a typical Prototype, still not production. |
| Prototype | `READY` | Unusual for Prototype — re-check mode. Production gates already pass. |
| MVP | `BLOCKED FOR PRODUCTION` | Expected for MVP when absolute gates fail. Closed beta only if you accept the failed gates. Do not open public signups. |
| MVP | `NEEDS HARDENING` | Typical for MVP. Harden before public users. |
| MVP | `READY` | Rare for MVP: production gates already pass. |
| Production | `BLOCKED FOR PRODUCTION` | Not expected. Do not ship. |
| Production | `NEEDS HARDENING` | Do not ship as-is. Harden first. |
| Production | `READY` | Ship. |

## Report table

Use the report format in `SKILL.md`. Header includes `Stage note` (exact string from the table above). Rows: the four absolute gates, then the four recommended gates. Status per row: Pass / Fail / N/A plus evidence paths.
