# Vibe-Proof Auditor

**AI writes the happy path. Vibe-Proof audits the consequences.**

```bash
npx skills add pedroknigge/vibe-proof-auditor -g -y
```

![ForgeBoard worked example: 5.9 BLOCKED FOR PRODUCTION](docs/example-hero.svg)

[![skills.sh](https://skills.sh/b/pedroknigge/vibe-proof-auditor)](https://skills.sh/pedroknigge/vibe-proof-auditor)
![vibe-proof BLOCKED](assets/badge-blocked.svg)

Pre-1.0 (`0.6.0`). A good adversarial agent skill with a deterministic validator. Not a production certification.

```
 __     _____ ____  _____
 \ \   / /_ _| __ )| ____|
  \ \ / / | ||  _ \|  _|
   \ V /  | || |_) | |___
    \_/  |___|____/|_____|
            p r o o f
         ── auditor ──
    run the roast on yourself
```

The internet is very brave about other people's pull requests.

Every week the timeline invents a new reason vibe coding is going to sink production. Auth that only lives in `localStorage`. Tests that cover the demo and nothing else. A 900-line `utils.ts` that "the model wrote." A senior quote-tweets a screenshot, the dunks pile up, and someone who actually shipped gets told they aren't a real engineer.

Here's the bit they skip: **every one of those dunks is a checklist item.** Secrets in git. IDOR because the UI "hides" the button. No user-A / user-B tests. "It worked on my machine." That's not a personality. That's an audit.

This skill is the roast, bottled. We scooped up what people actually mock when someone codes with AI, and we pointed an agent at it. The model already trained on those threads. It already knows the lecture. It just needed a north star instead of vibes.

If you're shipping with AI anyway — good. Run the roast on yourself before someone does it for clout.

The report talks to two people at once. A senior gets paths, marks, gates, and a copy-paste fix prompt. A vibe coder gets **Why this dunks**: what you shipped, what would get screenshot-quoted, what happens if you ignore it, and the smallest thing to tell the model. Same audit. No dumbed-down scores.

Install once. It lands in every coding agent the [Skills CLI](https://github.com/vercel-labs/skills) finds (Grok, Claude Code, Cursor, Codex, Windsurf, Copilot, Gemini CLI, and 70+ more).

## Install (all your agents, all projects)

```bash
npx skills add pedroknigge/vibe-proof-auditor -g -y
```

`-g` = global (home directory, every project). Omit it to install only in the current repo. `-y` skips prompts. The CLI auto-detects installed agents and **symlinks** them to one copy, so updates are a single pull.

This repo is a valid Agent Skill (`SKILL.md` at the root) per [agentskills.io](https://agentskills.io/specification).

## Update

```bash
npx skills update vibe-proof-auditor -g -y
```

Or update every installed skill:

```bash
npx skills update -g -y
```

## Use

In any supported agent:

- `/vibe-proof-auditor`
- “vibe-proof this repo”
- “auditar proyecto”
- “listo para prod”
- “production checklist”

Point it at a project path. Deep mode is the default. Say “quick” / “rápido” for a short pass (file count does not switch modes). If the host can spawn parallel agents, Deep fans out independent categories and merges once — same gates, one verdict. Prototype and MVP still run the production gates; the **stage note** says whether `BLOCKED` was expected. The write-up always includes a senior evidence block **and** a plain-language **Why this dunks** section so a vibe coder can learn the finding without losing the path-level proof.

Every pass writes markdown + JSON at the project root (HTML opens only on an interactive TTY):

- `vibe-proof-audit-report.md` — evidence report
- `vibe-proof-audit-report.json` — computed scores / gates / findings
- `vibe-proof-audit-report.html` — styled twin

`scripts/validate-report.py` recomputes the math. `--sarif` is optional. `scripts/compare-eval.py --baseline` diffs new Fail rows. Say `professional` for a sober **Why this matters** section.

Planted fixtures: `evals/`. Worked HTML: `docs/example-report.html`.

## One-off without installing

```bash
npx skills use pedroknigge/vibe-proof-auditor
```

## Manual copy (no Node)

```bash
git clone https://github.com/pedroknigge/vibe-proof-auditor.git ~/.grok/skills/vibe-proof-auditor
```

Symlink or copy that folder into the skills directory of each agent you use (`~/.claude/skills/`, `~/.cursor/skills/`, `~/.codex/skills/`, …). Prefer `npx skills add` so updates stay one command.

## Layout

```
vibe-proof-auditor/
├── SKILL.md                      # Agent prompt
├── README.md
├── CHANGELOG.md
├── LICENSE
├── scripts/
│   ├── scorelib.py               # Weights, floors, verdict math
│   ├── validate-report.py        # Census / scores / verdict; --json --sarif
│   ├── compare-eval.py           # expected.json vs report JSON; --baseline
│   └── render-report.py          # Markdown → HTML (no scores)
├── evals/                        # Planted fixtures + expected manifests
├── tests/
│   ├── test_render_report.py
│   ├── test_scorelib.py
│   ├── test_validate_report.py
│   └── test_export_and_eval.py
├── references/
│   ├── checklist.md              # Scored items (only home)
│   ├── gates.md                  # Verdicts and production gates
│   ├── scoring.md                # Formula, weights, N/A matrix
│   ├── security-deep.md          # Security grep playbook
│   ├── prompt-maestro.md         # Short export for other agents
│   └── example-report.md         # Worked report
├── docs/adr/
│   └── 0001-html-render-does-not-score.md
└── assets/
    └── checklist-template.md     # Cover sheet (not a second item list)
```

Python **3.9+**. The renderer is stdlib only.

```bash
python3 -m py_compile scripts/scorelib.py scripts/validate-report.py scripts/compare-eval.py scripts/render-report.py
python3 -m unittest discover -s tests -v
```

`main` is protected: CI jobs `renderer` + `gitleaks`, one review on PRs (repo admins can still push so the first workflow can land). Secret scanning and push protection are on.

## Contract (do not restate numbers here)

| Fact | Home |
|------|------|
| Verdict words, absolute/recommended gates, verdict rule, stage notes | `references/gates.md` |
| Weights, formula, floors, scale, product-type N/A matrix | `references/scoring.md` |
| Scored items and human-interview (unscored) items | `references/checklist.md` (only home; the template is a cover) |
| Security grep playbook | `references/security-deep.md` |
| Report format | `SKILL.md` |
| HTML render | `scripts/render-report.py` |
| HTML render does not score | `docs/adr/0001-html-render-does-not-score.md` |
| Validator recomputes scores / verdict | `scripts/validate-report.py` (`docs/adr/0002-validator-checks-math.md`) |
| Evidence coverage, insufficient-evidence mark | `references/scoring.md` |
| One worked report | `references/example-report.md` (`docs/example-report.html`) |
| Planted evals | `evals/` |
| JSON / SARIF / baseline | `scripts/validate-report.py`, `scripts/compare-eval.py` |

## Related skills

- Architecture-principle ranking → `arquitectura-software-analyzer`
- Over-engineering deletion pass → `ponytail-audit`

## License

MIT
