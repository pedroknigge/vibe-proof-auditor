# ADR 0002: Validator checks item coverage and math; renderer does not

`python3 -m vibe_proof_auditor.validate_report` recomputes category scores, overall, Evidence coverage, the verdict rule, and the exact stage note from the Mark census plus gates table. For current-version reports it also checks every scored checklist item against the evidence ledger and rejects a Pass gate with a non-Pass constituent. It does not verify that the path-level claim is true; the auditor must inspect or test it.

The agent still classifies evidence (Pass / Partial / Fail / N/A / insufficient evidence) and writes the markdown. The script rejects arithmetic that does not match `references/scoring.md` and `references/gates.md`.

`vibe_proof_auditor.render_report` stays style-only (ADR 0001). It must not grow scoring logic.

Constants in `vibe_proof_auditor.scorelib` must match those markdown files. Tests check the numeric tables for drift.

`--json` / `--sarif` export the **computed** payload after that check. They are not a second scoring home.
