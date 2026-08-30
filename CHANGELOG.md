# Changelog

Public numbering is **0.9.0**. 2.4–2.6 were internal contract drafts, not a 1.x release.

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
