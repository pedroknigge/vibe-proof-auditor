# Vibe-Proof Auditor

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

[![skills.sh](https://skills.sh/b/pedroknigge/vibe-proof-auditor)](https://skills.sh/pedroknigge/vibe-proof-auditor)

The internet is very brave about other people's pull requests.

Every week the timeline invents a new reason vibe coding is going to sink production. Auth that only lives in `localStorage`. Tests that cover the demo and nothing else. A 900-line `utils.ts` that "the model wrote." A senior quote-tweets a screenshot, the dunks pile up, and someone who actually shipped gets told they aren't a real engineer.

Here's the bit they skip: **every one of those dunks is a checklist item.** Secrets in git. IDOR because the UI "hides" the button. No user-A / user-B tests. "It worked on my machine." That's not a personality. That's an audit.

This skill is the roast, bottled. We scooped up what people actually mock when someone codes with AI, and we pointed an agent at it. The model already trained on those threads. It already knows the lecture. It just needed a north star instead of vibes.

If you're shipping with AI anyway — good. Run the roast on yourself before someone does it for clout.

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

Point it at a project path. Deep mode is the default. Say “quick” / “rápido” for a short pass. If the host can spawn parallel agents, Deep fans out independent categories and merges once — same gates, one verdict.

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
