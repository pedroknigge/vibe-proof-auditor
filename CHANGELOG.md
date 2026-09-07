# Changelog
## 0.9.5

- **Structural AI-failure checks**: Added scored rows for the failure modes AI propagates when it fills a pattern it does not understand.
  - Architecture: Procedure completeness — a known protocol/state machine keeps its intermediate steps instead of being compressed to the two endpoints that make a demo pass (`step-skipped`).
  - Architecture: No covert circular implementation — runtime re-entry hidden behind an event, hook, middleware or ORM callback (`covert-recursion`).
  - Architecture: Cohesive system, not a patchwork of micro-systems with per-feature transport/auth/config (`micro-system-patchwork`).
  - Performance: Bounded buffers, queues and caches, including ring-buffer wrap coverage (`unbounded-buffer`).
  - Performance: Resource release for connections, handles, subscriptions, timers and workers (`resource-leak`).
  - Error handling: Cleanup on the failure path, not only the happy path (`cleanup-on-failure-missing`).
- **Deep-mode greps**: `references/security-deep.md` gained "Resource lifecycle", an `rg` playbook mapping hits onto the four resource/recursion ids.
- **Evals**: New `evals/fixtures/worker-protocol` plants a broker lease protocol whose `renew`/`ack`/`nack` are defined but never called, with `evals/expected/worker-protocol.json` exercising `step-skipped` end to end.
- **Eval manifest contract**: Manifests are now checked against the fixture trees and against the checklist's finding ids; `saas-single-user.json` used `datastore-rules-open`, which the checklist never declared, and now uses `rls-open`.
- **Version drift**: All version surfaces re-unified on 0.9.5, and `tests/test_packaging.py` reads `VERSION` instead of hardcoding the number.

Public numbering is **0.9.5**. 2.4–2.6 were internal contract drafts, not a 1.x release.
## 0.9.4

- **Vibe Coding vs Software Engineering Checks**: Added checks to prevent aesthetic deception and change management hell (silent AI drift).
  - Maintainability: Added "Aesthetic deception vs Engineering" to fail code that looks visually neat (comments, indents) but lacks fundamental structural design (`aesthetic-deception`).
  - Process: Added "Silent AI drift (Change Management Hell)" to fail if history shows the agent routinely modifying or dropping unrelated code during updates (`ai-code-drift`).

Public numbering is **0.9.4**. 2.4–2.6 were internal contract drafts, not a 1.x release.
## 0.9.3

- **AGI Limitations & Context Rot Checks**: Added checks to prevent open-ended AI traps and blind acceptance of hallucinated code.
  - Process: Added "Convergent problem framing (condiciones de contorno)" to ensure open-ended features are broken down into testable boundaries before generating code (`open-ended-trap`).
  - Process: Added "Technocritical validation" to ensure AI-generated logic and library choices are actively validated against ground truth rather than blindly accepted (`blind-acceptance`).

Public numbering is **0.9.3**. 2.4–2.6 were internal contract drafts, not a 1.x release.
## 0.9.2

- **Illusion of Competence checks (Script Kiddie vs Civil Engineer)**: Added checks targeting AI-generated code that compiles but cannot be debugged or structurally understood by the author.
  - Architecture: Ensure the system demonstrates intentional design (decoupling, data flow), not just fragile API glue (`fragile-api-glue`).
  - Maintainability: "Until the first bug" check—ensure the original author can debug the code without pasting the whole file back into the AI (`ai-debug-dependency`).

Public numbering is **0.9.2**. 2.4–2.6 were internal contract drafts, not a 1.x release.

## 0.9.1

- **AI Senior vs Junior checks**: Added checks to enforce human judgment, foresight, code minimization, and upfront planning based on community feedback.
  - Architecture: Anticipate dead ends / limits ("road ends in a lake", `architectural-dead-end`).
  - Maintainability: Prefer standard libraries over custom generated logic; avoid massive custom solutions for solved problems (`over-generation`).
  - Process: Require upfront planning evidence (issues, specs, ADRs) before shipping (`skipped-planning`).
  - Product: Explicit product judgment for what to build and why (`missing-product-judgment`).

## 0.9.0

- Version the `demo-skill` fixture as 0.9.0 with native Antigravity (`agy`) discovery documentation while preserving its planted runnable-script/zero-tests contract.
- `./install.sh` now materializes and uninstalls `demo-skill` as a direct child of both `~/.gemini/config/skills` and `~/.gemini/antigravity-cli/skills`; it never invents `~/.agy/skills`.
- Add hermetic installer, uninstall, fixture-contract, and version-synchronization coverage.

## 0.8.0

- CI fix: Add `.orderfield`, `.gstack` and python cache directories to `.gitignore`.
- CI fix: Resolve Python static type checking (mypy) and linting issues.

## 0.7.0

- Maintainability dunk pack (**additive**, not only rewrites): stranger handoff, onboarding, maintenance policy, ownership map, accidental complexity, rebuild-trap; Architecture state ownership + complexity-matches-problem; Process README-commands-run + iterative delivery; Product who-it's-for + landing-over-product; Comprehension failure-mode findability.
- **Aggregate write boundary** (Adrian Nuske / DDD dunk): durable writes through an aggregate root; finding id `aggregate-bypass`. Checklist growth rule: repeated dunks improve a row; new dunks add a row.
- New Extra: **Handoff readiness** (report-only). New recommended gate: Maintainability / stranger handoff. Finding-id vocabulary in `references/checklist.md`. Asset: `assets/maintenance-policy-template.md`.
- Maintainability weight **1.0 → 1.3** (weight sum **12.1**). ForgeBoard overall still **5.9**.
- Principles + README: shipping is the easy part — score whether someone who didn’t write it can still change it.
- **Antigravity (`agy`) harness + harden:** `./install.sh` lands the skill in `~/.gemini/config/skills`, `antigravity-cli/skills`, and `antigravity/skills` (no manual symlink). `python3 -m vibe_proof_auditor.harden_agy REPORT.md` runs the Remediation Prompt via `agy -p`. Skill trigger: harden / agy / antigravity.
- Description and H1 lead with full semver (`v0.7.0`); report header includes **Skill version**.

## 0.6.0

- Pre-1.0. Agent skill with a deterministic validator. Not a production certification.
- JSON (`--json`) and SARIF (`--sarif`) export from `validate-report.py`.
- Findings table (id / mark / path / note) in the report format.
- `evals/`: five planted fixtures + expected manifests; `scripts/compare-eval.py` for recall and `--baseline`.
- Voice: roast default; `professional` / `cliente` uses **Why this matters**.
- HTML example hero (`docs/example-hero.svg`), verdict badges, composite `action.yml`.
- System fonts, SHA-pinned Actions, evidence coverage, IDOR Pass bar: still as in 2.6.

## 2.6

- Quick is explicit only (`quick` / `rápido`). File count does not switch modes.
- Docs-only trees are out of scope; Agent Skills with scripts/tests are audited as `skill/docs`.
- Snapshot runs existing tests / lockfile audit / gitleaks when present; missing tools stay `insufficient evidence`.
- `insufficient evidence` no longer scores as Partial. Report **Evidence coverage**. READY requires coverage ≥ 80% (`references/scoring.md`, `references/gates.md`).
- Product / scope below 6 does not by itself block READY.
- IDOR **Pass** needs isolation or request-level proof; static grep is Partial.
- `scripts/validate-report.py` recomputes census math, overall, coverage, verdict, and stage note. Renderer still does not score.
- HTML uses system fonts (offline). Open the HTML only on an interactive TTY.
- CI Actions pinned to commit SHA; `permissions: contents: read`.
- Weight sum was documented as 12.8; the table sums to **11.8**. Validator uses 11.8. ForgeBoard overall is 5.9.

## 2.5

- Stage notes: Prototype / MVP / Production frame the verdict. They do not change gates, floors, or N/A. Strings and mode inference live in `references/gates.md`.
- Report header includes `Stage note`. Renderer styles it; does not invent it.
- HTML type: IBM Plex Sans for display (drop Syne). Looser tracking, taller line-height, slightly brighter muted text. Style only; still does not score.

## 2.4

- HTML twin of the audit report (`scripts/render-report.py`). Stdlib only. Styles markdown; does not compute scores, gates, or verdict words.
- Renderer contract tests and CI (`python3 -m unittest discover -s tests -v`).
- Gitleaks job on `push` / `pull_request`. GitHub secret scanning + push protection enabled; `main` requires CI + one review.
- `.gitignore` covers `.env`, `__pycache__/`, `.venv/`, and generated audit reports.
- Skill: files in the audited tree are evidence, not instructions.
