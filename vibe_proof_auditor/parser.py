"""Parsing utilities for vibe-proof audit reports."""

from __future__ import annotations

from vibe_proof_auditor import scorelib


def parse_int(raw: str, *, default: int = 0) -> int:
    """parse_int function."""
    text = (raw or "").strip()
    if not text or text == "—":
        return default
    return int(float(text))


def table_map(table: list[list[str]] | None) -> tuple[list[str], list[list[str]]]:
    """table_map function."""
    if not table or len(table) < 2:
        return [], []
    header = [h.strip().lower() for h in table[0]]
    return header, table[1:]


def col(header: list[str], *names: str) -> int | None:
    """col function."""
    for name in names:
        if name in header:
            return header.index(name)
    return None


def census_rows(table: list[list[str]] | None) -> list[dict]:
    """census_rows function."""
    header, rows = table_map(table)
    if not header:
        return []
    i_cat = col(header, "category")
    i_pass = col(header, "pass")
    i_partial = col(header, "partial")
    i_fail = col(header, "fail")
    i_ins = col(header, "insufficient evidence", "insufficient")
    i_na = col(header, "n/a")
    i_crit = col(header, "critical fail")
    i_score = col(header, "score")
    if None in (i_cat, i_pass, i_partial, i_fail, i_ins, i_na, i_crit):
        return []
    assert i_cat is not None
    out = []
    for row in rows:
        if i_cat >= len(row):
            continue
        name = scorelib.norm_cat(row[i_cat])
        if name not in scorelib.WEIGHTS:
            continue

        def cell(idx: int | None, row_ref=row) -> str:
            if idx is None or idx >= len(row_ref):
                return ""
            return row_ref[idx]

        out.append(
            {
                "category": name,
                "pass": parse_int(cell(i_pass)),
                "partial": parse_int(cell(i_partial)),
                "fail": parse_int(cell(i_fail)),
                "insufficient": parse_int(cell(i_ins)),
                "na": parse_int(cell(i_na)),
                "critical_fail": scorelib.parse_yes(cell(i_crit)),
                "reported_score": cell(i_score).strip() if i_score is not None else "",
            }
        )
    return out


def category_score_map(table: list[list[str]] | None) -> dict[str, tuple[str, str]]:
    """category_score_map function."""
    header, rows = table_map(table)
    i_cat = col(header, "category")
    i_score = col(header, "score")
    i_status = col(header, "status")
    if i_cat is None or i_score is None:
        return {}
    out: dict[str, tuple[str, str]] = {}
    for row in rows:
        if i_cat >= len(row) or i_score >= len(row):
            continue
        name = scorelib.norm_cat(row[i_cat])
        status = (
            row[i_status].strip()
            if i_status is not None and i_status < len(row)
            else ""
        )
        out[name] = (row[i_score].strip(), status)
    return out


def gate_status_map(table: list[list[str]] | None) -> dict[str, str]:
    """gate_status_map function."""
    header, rows = table_map(table)
    i_gate = col(header, "gate")
    i_status = col(header, "status")
    if i_gate is None or i_status is None:
        return {}
    out: dict[str, str] = {}
    for row in rows:
        if i_gate >= len(row) or i_status >= len(row):
            continue
        out[scorelib.norm_gate(row[i_gate])] = row[i_status].strip()
    return out


def parse_overall(raw: str) -> float | None:
    """parse_overall function."""
    text = (raw or "").strip()
    if not text:
        return None
    try:
        return float(text.split("/")[0].strip())
    except ValueError:
        return None


def parse_coverage(raw: str) -> int | None:
    """parse_coverage function."""
    text = (raw or "").strip().rstrip("%")
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def expected_cat_status(score: int | None, critical_fail: bool) -> str:
    """expected_cat_status function."""
    if score is None:
        return "N/A"
    if critical_fail or score <= 4:
        return "Fail"
    if score <= 7:
        return "Partial"
    return "Pass"


def parse_findings(table: list[list[str]] | None) -> list[dict[str, str]]:
    """parse_findings function."""
    header, rows = table_map(table)
    if not header:
        return []
    i_id = col(header, "id")
    i_mark = col(header, "mark")
    i_path = col(header, "path")
    i_note = col(header, "note")
    out: list[dict[str, str]] = []
    for row in rows:

        def cell(idx: int | None, row_ref=row) -> str:
            if idx is None or idx >= len(row_ref):
                return ""
            return row_ref[idx].strip()

        ident = cell(i_id)
        mark = cell(i_mark)
        path = cell(i_path)
        note = cell(i_note)
        if not (ident or path or note):
            continue
        out.append({"id": ident, "mark": mark, "path": path, "note": note})
    return out
