# Vibe-Proof Auditor

[![skills.sh](https://skills.sh/b/pedroknigge/vibe-proof-auditor)](https://skills.sh/pedroknigge/vibe-proof-auditor)

Evidence-based production audit skill for coding agents. Install once; it lands in every agent the [Skills CLI](https://github.com/vercel-labs/skills) detects (Grok, Claude Code, Cursor, Codex, Windsurf, Copilot, Gemini CLI, and 70+ more).

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

Point it at a project path. Deep mode is the default. Say “quick” / “rápido” for a short pass.

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
├── LICENSE
├── references/
│   ├── checklist.md              # Scored items (only home)
│   ├── gates.md                  # Verdicts and production gates
│   ├── scoring.md                # Formula, weights, N/A matrix
│   ├── security-deep.md          # Security grep playbook
│   ├── prompt-maestro.md         # Short export for other agents
│   └── example-report.md         # Worked report
└── assets/
    └── checklist-template.md     # Cover sheet (not a second item list)
```

## Contract (do not restate numbers here)

| Fact | Home |
|------|------|
| Verdict words, absolute/recommended gates, verdict rule | `references/gates.md` |
| Weights, formula, floors, scale, product-type N/A matrix | `references/scoring.md` |
| Scored items and human-interview (unscored) items | `references/checklist.md` (only home; the template is a cover) |
| Security grep playbook | `references/security-deep.md` |
| Report format | `SKILL.md` |
| One worked report | `references/example-report.md` |

## Related skills

- Architecture-principle ranking → `arquitectura-software-analyzer`
- Over-engineering deletion pass → `ponytail-audit`

## License

MIT
