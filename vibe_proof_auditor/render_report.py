#!/usr/bin/env python3
"""Render a vibe-proof audit markdown report into a self-contained HTML file.

Stdlib only. Offline (system fonts). Does not invent scores, gates, verdict
words, or stage notes — it styles whatever the markdown already contains.
Math lives in ``scripts/validate-report.py`` (ADR 0001 / 0002).
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

META_LABELS = (
    "Project",
    "Date",
    "Mode",
    "Audit mode",
    "Product type",
    "Overall Score",
    "Evidence coverage",
    "Status",
    "Stage note",
)

SKIP_BODY_HEADINGS = {
    "category scores",
    "production gates",
}

STATUS_CLASS = {
    "READY": "ready",
    "NEEDS HARDENING": "harden",
    "BLOCKED FOR PRODUCTION": "blocked",
    "Pass": "pass",
    "Partial": "partial",
    "Fail": "fail",
    "N/A": "na",
}


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def inline(text: str) -> str:
    text = esc(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    return text


def strip_inline_md(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^`+|`+$", "", text)
    text = re.sub(r"\*\*", "", text)
    return text.strip()


def parse_meta(md: str) -> dict[str, str]:
    meta: dict[str, str] = {}
    for label in META_LABELS:
        m = re.search(
            rf"^\*\*{re.escape(label)}:\*\*\s*(.+?)\s*$",
            md,
            re.MULTILINE,
        )
        if m:
            meta[label] = strip_inline_md(m.group(1))
    return meta


def parse_tables(md: str) -> dict[str, list[list[str]]]:
    """Map lowercase heading → table rows (header first)."""
    tables: dict[str, list[list[str]]] = {}
    heading = ""
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        h = re.match(r"^#{2,6}\s+(.+)$", lines[i])
        if h:
            heading = re.sub(r"\s+", " ", h.group(1)).strip().lower()
            heading = re.sub(r"\s*\(.*\)$", "", heading)
            i += 1
            continue
        if lines[i].lstrip().startswith("|") and heading:
            rows: list[list[str]] = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                raw = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", c.replace(" ", "")) for c in raw):
                    rows.append(raw)
                i += 1
            if rows:
                tables[heading] = rows
            continue
        i += 1
    return tables


def extract_score(raw: str) -> str:
    m = re.search(r"(\d+(?:\.\d+)?)", raw or "")
    return m.group(1) if m else "—"


def score_number(raw: str) -> float | None:
    m = re.search(r"(\d+(?:\.\d+)?)", raw or "")
    return float(m.group(1)) if m else None


def mark_class(status: str) -> str:
    key = (status or "").strip()
    return STATUS_CLASS.get(key, STATUS_CLASS.get(key.title(), "na"))


def project_name(path: str) -> str:
    if not path:
        return "untitled"
    cleaned = path.strip().strip("`").rstrip("/")
    return Path(cleaned).name or cleaned


def ticks(score: float | None) -> str:
    filled = 0 if score is None else max(0, min(10, round(score)))
    cells = []
    for i in range(10):
        cls = "on" if i < filled else "off"
        cells.append(f'<i class="{cls}"></i>')
    return '<span class="ticks">' + "".join(cells) + "</span>"


def render_scorecard(table: list[list[str]] | None) -> str:
    if not table or len(table) < 2:
        return ""
    header = [h.lower() for h in table[0]]
    try:
        i_cat = header.index("category")
        i_score = header.index("score")
        i_status = header.index("status")
    except ValueError:
        return ""
    i_notes = header.index("notes") if "notes" in header else None
    cards = []
    for row in table[1:]:
        if len(row) <= max(i_cat, i_score, i_status):
            continue
        cat = strip_inline_md(row[i_cat])
        score_raw = strip_inline_md(row[i_score])
        status = strip_inline_md(row[i_status])
        notes = (
            strip_inline_md(row[i_notes])
            if i_notes is not None and i_notes < len(row)
            else ""
        )
        n = score_number(score_raw)
        cls = mark_class(status)
        notes_html = f'<p class="notes">{inline(notes)}</p>' if notes else ""
        cards.append(
            f"""<article class="cat {cls}">
  <header>
    <span class="cat-name">{esc(cat)}</span>
    <span class="pill {cls}">{esc(status)}</span>
  </header>
  <div class="cat-score">
    <b>{esc(score_raw if n is None else str(int(n) if n == int(n) else score_raw))}</b>
    {ticks(n)}
  </div>
  {notes_html}
</article>"""
        )
    if not cards:
        return ""
    return (
        '<section class="scorecard"><h2>Category scores</h2><div class="cat-grid">'
        + "".join(cards)
        + "</div></section>"
    )


def render_gates(table: list[list[str]] | None) -> str:
    if not table or len(table) < 2:
        return ""
    header = [h.lower() for h in table[0]]
    try:
        i_gate = header.index("gate")
        i_status = header.index("status")
    except ValueError:
        return ""
    i_ev = header.index("evidence") if "evidence" in header else None
    tiles = []
    for row in table[1:]:
        if len(row) <= max(i_gate, i_status):
            continue
        gate = strip_inline_md(row[i_gate])
        status = strip_inline_md(row[i_status])
        evidence = (
            strip_inline_md(row[i_ev]) if i_ev is not None and i_ev < len(row) else ""
        )
        cls = mark_class(status)
        ev_html = f"<p>{inline(evidence)}</p>" if evidence else ""
        tiles.append(
            f"""<article class="gate {cls}">
  <span class="pill {cls}">{esc(status)}</span>
  <h3>{esc(gate)}</h3>
  {ev_html}
</article>"""
        )
    if not tiles:
        return ""
    return (
        '<section class="gates"><h2>Production gates</h2><div class="gate-grid">'
        + "".join(tiles)
        + "</div></section>"
    )


def split_cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def is_sep_row(cells: list[str]) -> bool:
    return bool(cells) and all(
        re.fullmatch(r":?-{3,}:?", c.replace(" ", "")) for c in cells
    )


def md_body_html(md: str) -> str:
    """Convert report markdown to HTML, skipping dashboard-duplicated sections."""
    lines = md.splitlines()
    out: list[str] = []
    i = 0
    skip = False
    in_dunks = False
    # Drop H1 + leading meta **Key:** lines
    while i < len(lines) and (not lines[i].strip() or lines[i].startswith("# ")):
        i += 1
    while i < len(lines):
        m = re.match(r"^\*\*([^:*]+):\*\*\s+", lines[i])
        if m and m.group(1) in META_LABELS:
            i += 1
            continue
        break

    para: list[str] = []

    def flush_para() -> None:
        nonlocal para
        if not para:
            return
        text = " ".join(para)
        para = []
        html_p = f"<p>{inline(text)}</p>"
        if in_dunks:
            pri = re.match(r"^\*\*(P[012])\b", text)
            if pri:
                html_p = f'<div class="dunk dunk-{pri.group(1).lower()}">{html_p}</div>'
        out.append(html_p)

    while i < len(lines):
        line = lines[i]
        heading = re.match(r"^(#{2,6})\s+(.+)$", line)
        if heading:
            flush_para()
            level = len(heading.group(1))
            title = heading.group(2).strip()
            key = re.sub(r"\s+", " ", title).strip().lower()
            key = re.sub(r"\s*\(.*\)$", "", key)
            skip = key in SKIP_BODY_HEADINGS
            in_dunks = key.startswith("why this dunks")
            if not skip:
                tag = f"h{min(level, 4)}"
                slug = re.sub(r"[^a-z0-9]+", "-", key).strip("-")
                out.append(f'<{tag} id="{esc(slug)}">{inline(title)}</{tag}>')
            i += 1
            continue

        if skip:
            i += 1
            continue

        if line.startswith("```"):
            flush_para()
            fence = line[3:].strip()
            i += 1
            buf: list[str] = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            lang = f' class="lang-{esc(fence)}"' if fence else ""
            out.append(f"<pre{lang}><code>{esc(chr(10).join(buf))}</code></pre>")
            continue

        if line.lstrip().startswith("|"):
            flush_para()
            rows: list[list[str]] = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                cells = split_cells(lines[i])
                if not is_sep_row(cells):
                    rows.append(cells)
                i += 1
            if rows:
                thead = "".join(f"<th>{inline(c)}</th>" for c in rows[0])
                body = []
                for row in rows[1:]:
                    tds = "".join(f"<td>{inline(c)}</td>" for c in row)
                    body.append(f"<tr>{tds}</tr>")
                out.append(
                    f"<div class='table-wrap'><table><thead><tr>{thead}</tr></thead><tbody>{''.join(body)}</tbody></table></div>"
                )
            continue

        ul = re.match(r"^[-*]\s+(.+)$", line)
        ol = re.match(r"^(\d+)\.\s+(.+)$", line)
        if ul or ol:
            flush_para()
            ordered = bool(ol)
            tag = "ol" if ordered else "ul"
            items: list[str] = []
            while i < len(lines):
                um = re.match(r"^[-*]\s+(.+)$", lines[i])
                om = re.match(r"^\d+\.\s+(.+)$", lines[i])
                if ordered and om:
                    items.append(f"<li>{inline(om.group(1))}</li>")
                elif not ordered and um:
                    items.append(f"<li>{inline(um.group(1))}</li>")
                elif not lines[i].strip():
                    break
                else:
                    break
                i += 1
            out.append(f"<{tag}>{''.join(items)}</{tag}>")
            continue

        if not line.strip():
            flush_para()
            i += 1
            continue

        para.append(line.strip())
        i += 1

    flush_para()
    return "\n".join(out)


def status_display(status: str) -> str:
    s = (status or "UNSET").strip()
    if s == "BLOCKED FOR PRODUCTION":
        return "BLOCKED<span>FOR PRODUCTION</span>"
    if s == "NEEDS HARDENING":
        return "NEEDS<span>HARDENING</span>"
    return esc(s)


CSS = """
:root {
  --bg: #0c0c0a;
  --paper: #14140f;
  --ink: #efe8d6;
  --muted: #b7ad96;
  --faint: #8a8373;
  --line: #2a281f;
  --line-strong: #3d3a2e;
  --blocked: #ff3b30;
  --harden: #e8a317;
  --ready: #c6f135;
  --pass: #c6f135;
  --partial: #e8a317;
  --fail: #ff3b30;
  --na: #8a8373;
  --font-display: ui-sans-serif, system-ui, "Segoe UI", sans-serif;
  --font-sans: ui-sans-serif, system-ui, "Segoe UI", sans-serif;
  --font-mono: ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  background: var(--bg);
  color: var(--ink);
  font-family: var(--font-sans);
  font-size: 17px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}
body::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 50;
  opacity: 0.04;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='4' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");
}
.sheet {
  max-width: 1080px;
  margin: 0 auto;
  padding: 28px 22px 80px;
}
.masthead {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px;
  border-bottom: 1px solid var(--line-strong);
  padding-bottom: 14px;
  margin-bottom: 28px;
}
.wordmark {
  font-family: var(--font-display);
  font-weight: 700;
  letter-spacing: -0.02em;
  font-size: 13px;
  line-height: 1.2;
}
.wordmark b { display: block; font-size: 22px; letter-spacing: -0.02em; }
.wordmark span { color: var(--muted); font-family: var(--font-mono); font-weight: 400; font-size: 11px; letter-spacing: 0.16em; text-transform: uppercase; }
.mast-meta {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.04em;
  color: var(--muted);
  text-align: right;
  line-height: 1.45;
}
.hero {
  display: grid;
  grid-template-columns: minmax(240px, 340px) 1fr;
  align-items: stretch;
  margin-bottom: 36px;
  border: 1px solid var(--line);
  background: var(--paper);
}
.score-block {
  padding: 22px 28px 24px;
  border-right: 1px solid var(--line);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 220px;
}
.score-block .label {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted);
}
.score {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: clamp(3.4rem, 7vw, 5.2rem);
  letter-spacing: -0.03em;
  line-height: 1;
  margin: 12px 0;
}
.denom {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted);
}
.status-block {
  padding: 22px 24px 20px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 18px;
}
.status-block.blocked { box-shadow: inset 6px 0 0 var(--blocked); }
.status-block.harden { box-shadow: inset 6px 0 0 var(--harden); }
.status-block.ready { box-shadow: inset 6px 0 0 var(--ready); }
.stamp {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: clamp(1.6rem, 3.6vw, 2.5rem);
  letter-spacing: -0.02em;
  line-height: 1.15;
  text-transform: uppercase;
}
.stamp span {
  display: block;
  color: var(--muted);
  font-size: 0.68em;
  letter-spacing: 0;
  line-height: 1.2;
  margin-top: 0.12em;
}
.stamp-blocked { color: var(--blocked); }
.stamp-harden { color: var(--harden); }
.stamp-ready { color: var(--ready); }
.stage-note {
  margin: 0;
  font-size: 17px;
  line-height: 1.5;
  max-width: 48ch;
  color: var(--ink);
}
.hero-kicker {
  color: var(--muted);
  font-size: 16px;
  line-height: 1.5;
  max-width: 48ch;
}
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  border: 1px solid var(--line-strong);
  padding: 5px 8px;
  color: var(--ink);
}
h2 {
  font-family: var(--font-mono);
  font-weight: 500;
  font-size: 13px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin: 0 0 14px;
  color: var(--muted);
}
.scorecard, .gates { margin-bottom: 36px; }
.cat-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1px;
  background: var(--line);
  border: 1px solid var(--line);
}
.cat {
  background: var(--paper);
  padding: 14px 16px 12px;
}
.cat header { display: flex; justify-content: space-between; gap: 8px; align-items: baseline; }
.cat-name { font-weight: 600; font-size: 15px; }
.cat-score { display: flex; align-items: center; gap: 12px; margin-top: 10px; }
.cat-score b {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.05;
  min-width: 1.4ch;
}
.ticks { display: flex; gap: 3px; flex: 1; }
.ticks i { display: block; height: 8px; flex: 1; background: var(--line-strong); }
.ticks i.on { background: var(--ink); }
.cat.fail .ticks i.on { background: var(--fail); }
.cat.partial .ticks i.on { background: var(--partial); }
.cat.pass .ticks i.on { background: var(--pass); }
.cat.na .cat-score b, .cat.na .cat-name { color: var(--faint); }
.notes { margin: 8px 0 0; color: var(--muted); font-size: 14px; line-height: 1.45; }
.pill {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 3px 7px;
  border: 1px solid currentColor;
  white-space: nowrap;
}
.pill.pass, .pill.ready { color: var(--pass); }
.pill.partial, .pill.harden { color: var(--partial); }
.pill.fail, .pill.blocked { color: var(--fail); }
.pill.na { color: var(--na); }
.gate-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1px;
  background: var(--line);
  border: 1px solid var(--line);
}
.gate {
  background: var(--paper);
  padding: 16px 16px 14px;
  min-height: 120px;
}
.gate h3 {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.01em;
  margin: 10px 0 8px;
  line-height: 1.25;
}
.gate p { margin: 0; color: var(--muted); font-size: 14px; line-height: 1.45; }
.article {
  border-top: 1px solid var(--line-strong);
  padding-top: 28px;
}
.article h2 {
  font-size: 13px;
  margin: 32px 0 12px;
  color: var(--ink);
  letter-spacing: 0.12em;
}
.article h3 {
  font-family: var(--font-sans);
  font-size: 20px;
  font-weight: 600;
  margin: 28px 0 10px;
  letter-spacing: -0.01em;
  line-height: 1.3;
}
.article h4 { font-size: 16px; margin: 20px 0 8px; line-height: 1.35; }
.article p { margin: 0 0 12px; max-width: 68ch; }
.article ul, .article ol { margin: 0 0 16px; padding-left: 1.2em; max-width: 68ch; }
.article li { margin: 0 0 8px; }
code {
  font-family: var(--font-mono);
  font-size: 0.9em;
  background: #1c1c16;
  border: 1px solid var(--line);
  padding: 0.05em 0.35em;
}
pre {
  background: #0a0a08;
  border: 1px solid var(--line-strong);
  padding: 16px 18px;
  overflow-x: auto;
  margin: 0 0 20px;
}
pre code { background: none; border: 0; padding: 0; font-size: 13.5px; line-height: 1.55; }
.table-wrap { overflow-x: auto; margin: 0 0 20px; border: 1px solid var(--line); }
table { width: 100%; border-collapse: collapse; font-size: 14px; line-height: 1.45; }
th, td {
  text-align: left;
  padding: 8px 10px;
  border-bottom: 1px solid var(--line);
  vertical-align: top;
}
th {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
  background: var(--paper);
}
.dunk {
  border-left: 3px solid var(--line-strong);
  padding: 4px 0 4px 14px;
  margin: 0 0 16px;
  max-width: 68ch;
  font-size: 17px;
  line-height: 1.55;
}
.dunk p { margin: 0; }
.dunk-p0 { border-left-color: var(--fail); }
.dunk-p1 { border-left-color: var(--partial); }
.dunk-p2 { border-left-color: var(--na); }
.foot {
  margin-top: 48px;
  padding-top: 14px;
  border-top: 1px solid var(--line);
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--faint);
  display: flex;
  justify-content: space-between;
  gap: 12px;
}
@media (max-width: 760px) {
  .hero, .cat-grid, .gate-grid { grid-template-columns: 1fr; }
  .score-block { border-right: 0; border-bottom: 1px solid var(--line); min-height: 0; }
  .masthead { flex-direction: column; align-items: flex-start; }
  .mast-meta { text-align: left; }
}
@media print {
  body { background: #fff; color: #111; }
  body::before { display: none; }
  .sheet { padding: 0; }
  .hero, .cat, .gate, pre, code { background: #fff; }
  .cat-grid, .gate-grid, .hero { border-color: #111; background: #111; }
  a { color: inherit; }
}
"""


def render_html(md: str) -> str:
    meta = parse_meta(md)
    tables = parse_tables(md)
    status = meta.get("Status", "")
    sclass = mark_class(status) if status in STATUS_CLASS else "na"
    score = extract_score(meta.get("Overall Score", ""))
    name = project_name(meta.get("Project", ""))
    kicker = ""
    m = re.search(r"(?im)^[-*]\s*verdict:\s*(.+)$", md)
    if m:
        kicker = f'<p class="hero-kicker">{inline(m.group(1))}</p>'
    stage_note = meta.get("Stage note", "")
    stage_html = f'<p class="stage-note">{inline(stage_note)}</p>' if stage_note else ""

    chips = []
    for key in ("Mode", "Audit mode", "Product type", "Date", "Evidence coverage"):
        val = meta.get(key)
        if val:
            label = val if key != "Evidence coverage" else f"coverage {val}"
            chips.append(f'<span class="chip">{esc(label)}</span>')

    title = f"{name} — {status or 'vibe-proof audit'}"
    path = meta.get("Project", "")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <style>{CSS}</style>
</head>
<body>
  <main class="sheet">
    <header class="masthead">
      <div class="wordmark"><b>Vibe-Proof</b><span>auditor</span></div>
      <div class="mast-meta">{esc(path)}<br>{esc(meta.get("Date", ""))}</div>
    </header>
    <section class="hero">
      <div class="score-block">
        <div class="label">Overall score</div>
        <div class="score">{esc(score)}</div>
        <div class="denom">/ 10</div>
      </div>
      <div class="status-block {sclass}">
        <div class="stamp stamp-{sclass}">{status_display(status)}</div>
        {stage_html}
        {kicker}
        <div class="chips">{"".join(chips)}</div>
      </div>
    </section>
    {render_scorecard(tables.get("category scores"))}
    {render_gates(tables.get("production gates"))}
    <div class="article">
      {md_body_html(md)}
    </div>
    <footer class="foot">
      <span>vibe-proof-auditor</span>
      <span>markdown + html · evidence only</span>
    </footer>
  </main>
</body>
</html>
"""


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] in {"-h", "--help"}:
        print("usage: render-report.py INPUT.md [OUTPUT.html]", file=sys.stderr)
        return 2
    src = Path(argv[1])
    if not src.is_file():
        print(f"error: markdown not found: {src}", file=sys.stderr)
        return 1
    dest = Path(argv[2]) if len(argv) > 2 else src.with_suffix(".html")
    try:
        dest.write_text(render_html(src.read_text(encoding="utf-8")), encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(str(dest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
