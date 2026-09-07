# Roadmap: AI structural anti-patterns

Status: plan. Nothing here is implemented yet.

Source: `.orderfield/fields/ord_76e583cb/SPEC.md` (chat transcript, 2026-09-07) and its three
amendments, indexed as AUDIT-001 / AUDIT-002 / AUDIT-003 in
`.orderfield/REQUIREMENTS.json`. Gap map behind this plan:
`.orderfield/fields/ord_76e583cb/work/scratch/explorer_6fd2d7/notes.md`.

Baseline surveyed at `06bd86f`: `references/checklist.md` = 299 lines, 10 scored categories.

## Hard constraint on any row added here

`vibe_proof_auditor/parser.py:53` drops any census row whose category name is not a key of
`scorelib.WEIGHTS` (`vibe_proof_auditor/scorelib.py:14`). Every row proposed below therefore
lands **inside one of the existing 10 categories**. No 11th category. If one is ever wanted,
`references/scoring.md:9-20` (weights, sum 12.1) and `vibe_proof_auditor/scorelib.py:14` must
change together, plus the floors block at `scorelib.py:28`.

Adding rows changes a category's item denominator only. It does not change weights, floors
(`references/scoring.md`), or gates (`references/gates.md`). No code change is required for
milestones 1–3.

## Coverage today

| Req | Covered by | Verdict |
|-----|-----------|---------|
| AUDIT-001 shallow implementations | `checklist.md:118` `fragile-api-glue` (`[C]`), `:141` `aesthetic-deception` (`[C]`), `:140` `ai-debug-dependency` (`[C]`), `:137` `over-generation`, plus `blind-acceptance` / `open-ended-trap` / `skipped-planning` / `ai-code-drift` | Partial |
| AUDIT-002 structural vulnerabilities | — | Essentially uncovered |
| AUDIT-003 cohesion / integration cost | `checklist.md:113` (premature complexity), `:118`, `:136` (duplicate write paths), `:150` `vibe-coded-obsolescence`, `:106-107` | Partial |

AUDIT-002 evidence of absence: grep over `references/`, `assets/`, `SKILL.md`, `README.md` for
`memory|leak|buffer|dispose|unsubscribe|lifecycle|close\(\)|connection pool|file handle` returns
**only secret-leak hits** (`references/security-deep.md:133,208`; `checklist.md:24`;
`scoring.md:124`; `example-report.md:21,101,114,203`). Zero hits for ring/circular buffer,
memory leak, resource disposal, unsubscribe, connection-pool exhaustion, or file-handle leak.
`checklist.md:112` "No serious circular dependencies" is module-level **import** cycles, not the
SPEC's runtime "implementación circular encubierta". Category 7 Performance
(`checklist.md:166-177`) has no memory/resource dimension; category 6 Error handling
(`checklist.md:153-165`) has no cleanup-on-failure row.

## Milestone 1 — AUDIT-002: resource lifecycle and structural vulnerabilities

Largest gap; do this first. Four rows, three categories, all existing.

**Category 7 Performance** (`checklist.md:166-177`):

- Bounded buffers, queues, and caches: every in-memory accumulator has an explicit bound and a
  defined behaviour at the bound (drop, block, evict). Ring/circular buffers have their wrap and
  full-vs-empty arithmetic covered by a test. **Fail** if an unbounded structure grows with
  traffic, or if a hand-rolled circular buffer has no test that crosses the wrap point.
  Finding id: `unbounded-buffer`. N/A if the product holds no in-memory state across requests.
- Resource release: connections, file handles, subscriptions, timers, watchers, and workers are
  released by whoever acquires them. **Partial** if some paths clean up; **Fail** if a long-lived
  service acquires without a matching release on the critical path.
  Finding id: `resource-leak`.

**Category 6 Error handling** (`checklist.md:153-165`):

- Cleanup happens on the failure path too (`finally` / `defer` / context manager / `try`-scoped
  teardown), not only on the happy path. **Fail** if an early `return`/`throw` between acquire
  and release leaks the resource. Finding id: `cleanup-on-failure-missing`.

**Category 4 Architecture** (`checklist.md:103-122`):

- No covert circular implementation: no runtime mutual-call or re-entrant loop hidden behind
  layers (A calls B, B calls back into A via an event, hook, or middleware). Distinct from
  `checklist.md:112`, which is about import cycles. **Fail** if a request can re-enter its own
  handler with no depth bound or idempotence guard. Finding id: `covert-recursion`.

Acceptance: the four rows exist with those exact finding ids, each id also has a row in the
Common finding IDs table (`checklist.md:272-299`), and `references/security-deep.md` gains grep
patterns for at least `resource-leak` and `unbounded-buffer` so the ids are auditable, not
aspirational.

## Milestone 2 — AUDIT-001: step-skipping inside plausible code

The SPEC's specific shape is "te propaga un patrón … solamente de A---B, no tiene idea de la
importancia de ---": a procedure that looks right and compiles but omits a required intermediate
step. `checklist.md:118` is about framework understanding, not procedure completeness. No
current row asserts the implemented sequence matches the required protocol.

**Category 4 Architecture**, marked `[C]` (peer of `fragile-api-glue`):

- **[C]** Procedure completeness: where the code implements a known protocol, algorithm, or
  state machine (handshake, retry/backoff, transaction, pagination cursor, auth flow, upload
  lifecycle), the required intermediate steps are present and ordered — not compressed to the
  two endpoints that make a demo pass. **Fail** if a step whose omission is invisible in the
  happy path (ack, commit, revoke, close, verify, checkpoint) is missing.
  Finding id: `step-skipped`. N/A if the tree implements no such protocol.

Acceptance: row present, `[C]` marked, id in the Common finding IDs table, and at least one
eval fixture under `evals/fixtures/` exhibits it so the id is exercised end to end.

## Milestone 3 — AUDIT-003: cohesion as a measured property

`checklist.md:113` guards the *opposite* direction (premature distribution). Nothing scores
cohesion/coupling as an observed property, nor the SPEC's economic claim that integration,
maintenance and evolution get progressively more expensive.

**Category 4 Architecture**:

- Cohesive system, not a patchwork of micro-systems: features share their transport, auth,
  config, and error conventions instead of each shipping its own. **Partial** if two features
  solve the same cross-cutting concern differently; **Fail** if the integration surface grows
  at least as fast as the feature count. Finding id: `micro-system-patchwork`.

Deliberately **not** added: a second maintenance-cost row. `checklist.md:150`
`vibe-coded-obsolescence` already carries the cost/longevity claim; extending its wording to
name integration and evolution cost is cheaper than a duplicate row and avoids double-counting
in the Maintainability denominator.

Acceptance: row present, id in the table, `:150` wording extended, no new Maintainability row.

## Milestone 4 — consistency debt found while surveying

Independent of the SPEC, but it makes milestones 1–3 land on a clean surface.

1. **Two scored rows sit in a non-scored subsection.** `checklist.md:150-151`
   (`vibe-coded-obsolescence`, `raw-code-delusion`) were inserted immediately before
   `## 6. Error handling`, which places them **after** `### Human interview (not scored / not a
   gate)` at `checklist.md:143`. By the file's own convention (`checklist.md:9`,
   `references/scoring.md:44`) everything under that heading is `not assessed`. Move both rows
   above `:143`. The product rows at `:229-230` do not have this problem.
2. **Four finding ids are defined on rows but absent from the Common finding IDs table**
   (`checklist.md:272-299`): `vibe-coded-obsolescence` (:150), `raw-code-delusion` (:151),
   `clone-vulnerable` (:229), `missing-sla` (:230). One table row each.
3. **Version drift.** `VERSION` and `SKILL.md:3,7,11` say `0.9.5`;
   `vibe_proof_auditor/scorelib.py:11` says `0.9.4`.
4. **`patch_checklist.py` is untracked at the repo root** and is a one-shot string-replace
   mutator of `references/checklist.md` with no idempotence guard — re-running it duplicates all
   four rows it inserts. Either delete it (its edits are already committed) or make it
   idempotent and track it.

## Sequencing

Milestone 4 → 1 → 2 → 3. Milestone 4 first so the anchors the other milestones edit against are
stable; milestone 1 next because it is the only requirement with no coverage at all.

## Out of scope

- Weight, floor, gate, and verdict changes (`references/scoring.md`, `references/gates.md`).
- An 11th category.
- Static analysis or runtime instrumentation. Every row above must be markable from repo
  evidence — paths, snippets, or documented absence — per `checklist.md:9`.

## Validation for each milestone

- `python -m pytest tests/` green. No test currently reads `references/checklist.md`, so row
  additions should be inert; if that changes, the coupling is itself the finding.
- Re-run the evals (`evals/fixtures/` vs `evals/expected/*.json`) and confirm census counts still
  reconcile — expected files record per-category pass/partial/fail, so adding items to a category
  shifts the denominator for any fixture re-audited against the new list.
- `CHANGELOG.md` entry plus a `VERSION` bump, with `scorelib.VERSION` kept in lockstep (see
  milestone 4 item 3).
