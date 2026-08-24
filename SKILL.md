---
name: vibe-proof-auditor
description: "v2.3. Use when the user asks for a vibe-proof audit, production gates, a production checklist, an anti-vibe or anti-slop review, or whether a repo is listo para prod. Trigger phrases include auditar proyecto, control de calidad, and similar production-readiness requests on local, mixed, or AI-generated code."
license: MIT
metadata:
  version: "2.3"
  author: pedroknigge
---

# Vibe-Proof Auditor

Numbers, gates, and verdict words live only in `references/` — never invent them.

## When to Use

A production-readiness or anti-vibe audit of a project path.

## When NOT to Use

- Architecture-principle ranking → `arquitectura-software-analyzer`
- Over-engineering deletion pass → `ponytail-audit`
- Docs-only trees: product type `skill/docs`

## Workflow

1. **Path.** Missing project root → ask once. Else infer stack, mode, and product type. Do not block on questions.

2. **Snapshot (real only).** Tree, stack, tests, secrets, deps, CI, env example, docs. Never simulate. Tool failure → `insufficient evidence`. Unasked interview → `not assessed`.

3. **Audit.** Deep: load `references/checklist.md` first, `references/scoring.md` before numbers. Per category: evidence, score, 1–3 proofs, 1 fix. Census must sum. Load `references/security-deep.md` with Security. Fan-out if the host can spawn agents.

4. **Gates.** `references/gates.md` only.

5. **Report.** Format below. Verdicts from `references/gates.md` only. Report only — no planner chatter.

6. **Optional artifacts** (if asked): cover + marked checklist, AGENTS.md rules, remediation prompt.

## Modes

- **Deep** (default): key files, full checklist, concrete evidence.
- **Quick**: "quick"/"rápido" or ≤40 source files (`git ls-files`; skip vendor/build/lock). Snapshot + scores + top 5 gaps + gates. ≤15 reads. Skip `security-deep.md`. Declare that skip.
- **Remediation**: after an audit, only if asked. Prompt default; edit repo only when asked.

## Parallelism

Deep **and** host can spawn agents → fan-out. Coordinator: 1–2, N/A, merge, 4–6. Children: independent categories; `checklist.md` + `scoring.md`; marks, evidence, one fix; no verdicts. Security child loads `security-deep.md`. Apply `gates.md` once. Else serial. Never fan-out the verdict.

## Principles

- Evidence > opinion. Demo-works is not Pass. Do not hallucinate snapshots.
- Mature auth only when the product has users — never invent it for CLIs, libraries, or static sites.
- Human-only claims are not gates and not automatic Fail.
- P0 is impact (high-impact Partials allowed). Do not retcon a Fail for P0.

## Report format

```markdown
# Vibe-Proof Audit Report

**Project:** [path]
**Date:** [today]
**Mode:** [Prototype / MVP / Production]
**Audit mode:** [Deep / Quick]
**Product type:** [from scoring.md]
**Overall Score:** X.X / 10
**Status:** [from gates.md]

## Executive Summary
- 3 strengths
- 3 critical weaknesses
- 1–2 sentence verdict

## Category Scores
| Category | Score | Status | Notes |
|----------|-------|--------|-------|
| 1. Security | X | Pass/Partial/Fail/N/A | ... |
| ... | ... | ... | ... |

## Production Gates
| Gate | Status | Evidence |
|------|--------|----------|
| (from gates.md) | Pass/Fail/N/A | ... |

## Category Detail
(score, evidence, gaps, actions)

## Extras (not in overall)
...

## Why this dunks (plain language)
Each P0: what shipped, the screenshot, the risk, smallest model ask. Translate jargon once. Senior evidence stays in Category Detail.

## Prioritized Remediation
1. P0 ...
2. P1 ...
3. P2 ...

## Remediation Prompt (copy-paste)
...
```

## Resources

- `references/checklist.md` — Deep first
- `references/scoring.md` / `gates.md` — numbers / verdict
- `references/security-deep.md` — Security, Deep
- `references/prompt-maestro.md` / `example-report.md` — export / example
- `assets/checklist-template.md` — cover
