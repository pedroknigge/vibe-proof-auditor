# ADR 0002: Validator checks math; renderer still does not

`scripts/validate-report.py` recomputes category scores, overall, Evidence coverage, the verdict rule, and the exact stage note from the Mark census plus gates table.

The agent still classifies evidence (Pass / Partial / Fail / N/A / insufficient evidence) and writes the markdown. The script rejects arithmetic that does not match `references/scoring.md` and `references/gates.md`.

`scripts/render-report.py` stays style-only (ADR 0001). It must not grow scoring logic.

Constants in `scripts/scorelib.py` must match those markdown files. CI greps the tables so drift fails.

`--json` / `--sarif` export the **computed** payload after that check. They are not a second scoring home.
