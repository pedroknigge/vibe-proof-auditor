# Production gates

Single home for **verdict words**, **absolute/recommended gates**, and the **verdict rule**. Do not copy thresholds or these strings into other files; point here.

## Verdict words (exact)

`READY` | `NEEDS HARDENING` | `BLOCKED FOR PRODUCTION`

Do not invent aliases.

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
- Minimal docs (README, how to run, env vars).
- Basic observability (structured logs at least).

Report them in the gates table as Pass / Fail / N/A. They may contribute to `NEEDS HARDENING` only through category scores, not as extra verdict vocabulary.

## Verdict rule

Apply only **applicable** absolute gates (skipped/N/A gates ignored):

1. Any applicable absolute gate **Fail** → `BLOCKED FOR PRODUCTION`
2. Else if overall < 8.0 **or** any applicable scored category < 6 → `NEEDS HARDENING`
3. Else (all applicable absolute gates Pass, overall ≥ 8.0, no applicable category < 6) → `READY`

Overall and category scores come from `references/scoring.md`. Do not average gates. Do not Fail because a recommended gate failed.

## Report table

Use the report format in `SKILL.md`. Rows: the four absolute gates, then the four recommended gates. Status per row: Pass / Fail / N/A plus evidence paths.
