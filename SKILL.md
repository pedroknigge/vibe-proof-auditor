---
name: vibe-proof-auditor
description: Use when the user asks for a vibe-proof audit, production gates, a production checklist, an anti-vibe or anti-slop review, or whether a repo is listo para prod. Trigger phrases include auditar proyecto, control de calidad, and similar production-readiness requests on local, mixed, or AI-generated code.
license: MIT
metadata:
  version: "2.0"
  author: pedroknigge
---

# Vibe-Proof Auditor

Evidence-based production audit. Numbers, gates, and verdict words live only in `references/` — never invent them.

## When to Use

A production-readiness or anti-vibe audit of a project path.

## When NOT to Use

- Architecture-principle ranking → `arquitectura-software-analyzer`
- Over-engineering deletion pass → `ponytail-audit`
- This package or docs-only trees: allowed as product type `skill/docs`

## Workflow

1. **Path.** Missing project root → ask once. Else infer stack, prototype/MVP/production, and product type from the tree. Do not block on questions.

2. **Snapshot (real only).** Inspect tree, languages, test ratio, secret patterns, dependencies, largest files, CI, Docker, `.env.example`, README, docs. Never simulate or invent it. Tool failure → say so, mark affected scored items `insufficient evidence`. Unasked human-interview → `not assessed`.

3. **Audit.** Deep: load `references/checklist.md` first. Load `references/scoring.md` before any number. Per category: repo evidence, score, 1–3 evidences, 1 fix. Load `references/security-deep.md` with Security (Deep). Unassessed human-interview items → `not assessed`, never Fail, never a gate.

4. **Gates.** `references/gates.md` only.

5. **Report.** Format below. Verdict strings only from `references/gates.md`.

6. **Optional artifacts** (if asked): cover `assets/checklist-template.md` + marked `references/checklist.md`, AGENTS.md rules, remediation prompt, tools (gitleaks, trivy, codeql).

## Modes

- **Deep** (default): key files, full checklist, concrete evidence.
- **Quick**: "quick"/"rápido" or ≤40 source files (`git ls-files`; skip vendor/build/lock). Snapshot + scores + top 5 gaps + gates. ≤15 key-file reads. Skip `security-deep.md`. Report Audit mode Quick and that skip.
- **Remediation**: after an audit, only if asked. Default: copyable prompt. Edit the target repo only when asked to apply fixes.

## Principles

- Evidence > opinion. Demo-works is not Pass. Do not hallucinate snapshots.
- Think like an attacker and a future maintainer.
- Mature auth only when the product has users — never invent auth for CLIs, libraries, or static sites.
- Prefer stdlib and small audited deps.
- Human-only claims are not gates and not automatic Fail.

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
(for each scored category: score, evidence paths, gaps, priority actions)

## Extras (not in overall)
...

## Prioritized Remediation
1. P0 ...
2. P1 ...
3. P2 ...

## Remediation Prompt (copy-paste)
...
```

## Resources

- `references/checklist.md` — Deep: load first
- `references/scoring.md` — before numbers
- `references/gates.md` — before verdict
- `references/security-deep.md` — Security, Deep
- `references/prompt-maestro.md` — export
- `references/example-report.md` — worked report
- `assets/checklist-template.md` — cover only
