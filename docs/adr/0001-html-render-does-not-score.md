# ADR 0001: HTML render is style, not scores

The renderer (`scripts/render-report.py`) turns `vibe-proof-audit-report.md` into HTML.

It must not compute, round, or invent category scores, gates, or verdict words. Those live in `references/scoring.md` and `references/gates.md` and are already in the markdown.

Artifacts land at the audited project root, next to the markdown.
