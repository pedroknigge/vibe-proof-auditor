# Vibe-Proof Checklist — [project name]

Cover sheet only. **Items live solely in `references/checklist.md`.** Do not paste or rewrite that list here.

**Date:**  
**Auditor:**  
**Project path:**  
**Mode:** Prototype / MVP / Production  
**Product type:** _(from `references/scoring.md`)_  
**Audit mode:** Deep / Quick  
**Evidence coverage:** _% (from `references/scoring.md`)_

Marks: Pass | Partial | Fail | N/A | insufficient evidence (coverage only, not Partial)  
Human-interview rows: not assessed | Pass | Fail — **not scored, not a gate**

Scoring: `references/scoring.md`  
Gates / verdict words / stage notes: `references/gates.md`

## How to fill

1. Copy `references/checklist.md` next to this cover (or mark a working copy).
2. Mark every row there. Do not add, remove, or rename items.
3. Copy category scores onto this cover. Fill gates from `references/gates.md` only.

## Category scores

| Category | Score | Status | Notes |
|----------|-------|--------|-------|
| 1. Security | | Pass / Partial / Fail / N/A | |
| 2. Comprehension | | | |
| 3. Testing | | | |
| 4. Architecture | | | |
| 5. Maintainability | | | |
| 6. Error handling | | | |
| 7. Performance | | | |
| 8. Dependencies | | | |
| 9. Process / environments | | | |
| 10. Product / scope | | | |

## Extras (not in overall)

| Extra | Score | Notes |
|-------|-------|-------|
| Handoff readiness | | |
| Data model / migrations | | |
| Docs | | |
| Mobile / responsive | | |
| Accessibility | | |
| Observability | | |

## Production gates

Fill from `references/gates.md` only. Do not invent rows or verdict words.

| Gate | Status (Pass / Fail / N/A) | Evidence |
|------|----------------------------|----------|
| Critical security | | |
| Testing | | |
| Error handling | | |
| Environment isolation | | |
| Basic performance (recommended) | | |
| Dependency audit (recommended) | | |
| Minimal docs (recommended) | | |
| Basic observability (recommended) | | |
| Maintainability / stranger handoff (recommended) | | |

**Overall score:** __._ / 10  _(formula: `references/scoring.md`)_  
**Status:** _(exact strings: `references/gates.md`)_  
**Stage note:** _(exact strings: `references/gates.md`)_

**Notes / actions:**
