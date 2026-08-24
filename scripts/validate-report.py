#!/usr/bin/env python3
"""Verify a vibe-proof audit markdown report against scoring.md / gates.md.

Stdlib only. The agent classifies evidence; this script checks the arithmetic
and the verdict rule. It does not invent marks or re-read the audited tree.

Exit 0 if the census, scores, overall, coverage, gates, verdict, and stage note
are consistent. Exit 1 on mismatch or unreadable input. Exit 2 on usage.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import scorelib  # noqa: E402


def load_renderer():
    path = HERE / "render-report.py"
    spec = importlib.util.spec_from_file_location("vibe_proof_render_report", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def parse_int(raw: str, *, default: int = 0) -> int:
    text = (raw or "").strip()
    if not text or text == "—":
        return default
    return int(float(text))


def table_map(table: list[list[str]] | None) -> tuple[list[str], list[list[str]]]:
    if not table or len(table) < 2:
        return [], []
    header = [h.strip().lower() for h in table[0]]
    return header, table[1:]


def col(header: list[str], *names: str) -> int | None:
    for name in names:
        if name in header:
            return header.index(name)
    return None


def census_rows(table: list[list[str]] | None) -> list[dict]:
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
    out = []
    for row in rows:
        if i_cat >= len(row):
            continue
        name = scorelib.norm_cat(row[i_cat])
        if name not in scorelib.WEIGHTS:
            continue

        def cell(idx: int | None) -> str:
            if idx is None or idx >= len(row):
                return ""
            return row[idx]

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
        status = row[i_status].strip() if i_status is not None and i_status < len(row) else ""
        out[name] = (row[i_score].strip(), status)
    return out


def gate_status_map(table: list[list[str]] | None) -> dict[str, str]:
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
    text = (raw or "").strip()
    if not text:
        return None
    try:
        return float(text.split("/")[0].strip())
    except ValueError:
        return None


def parse_coverage(raw: str) -> int | None:
    text = (raw or "").strip().rstrip("%")
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def expected_cat_status(score: int | None, critical_fail: bool) -> str:
    if score is None:
        return "N/A"
    if critical_fail or score <= 4:
        return "Fail"
    if score <= 7:
        return "Partial"
    return "Pass"


def validate(md: str) -> tuple[list[str], dict]:
    renderer = load_renderer()
    meta = renderer.parse_meta(md)
    tables = renderer.parse_tables(md)
    errors: list[str] = []

    census = census_rows(tables.get("mark census"))
    if len(census) != len(scorelib.WEIGHTS):
        errors.append(
            "Mark census table required with one row per scored category "
            "(Pass, Partial, Fail, insufficient evidence, N/A, Critical Fail)."
        )
        if not census:
            return errors, {}

    computed: dict[str, int | None] = {}
    for row in census:
        known = row["pass"] + row["partial"] + row["fail"]
        if known + row["insufficient"] + row["na"] <= 0:
            errors.append(f"{row['category']}: census row is empty")
        score = scorelib.category_score(
            row["pass"],
            row["partial"],
            row["fail"],
            critical_fail=row["critical_fail"],
            category=row["category"],
        )
        computed[row["category"]] = score
        if row["reported_score"]:
            raw = row["reported_score"]
            if score is None:
                if raw.upper() not in {"N/A", "NA"}:
                    errors.append(
                        f"{row['category']}: census Score should be N/A, got {raw}"
                    )
            else:
                try:
                    reported = int(float(raw.split("/")[0].strip()))
                except ValueError:
                    errors.append(f"{row['category']}: census Score not an integer: {raw}")
                    continue
                if reported != score:
                    errors.append(
                        f"{row['category']}: census Score {reported} != computed {score}"
                    )

    for key in scorelib.WEIGHTS:
        if key not in computed:
            computed[key] = None
            errors.append(f"{key}: missing from Mark census")

    scores_table = category_score_map(tables.get("category scores"))
    for key, score in computed.items():
        if key not in scores_table:
            errors.append(f"{key}: missing from Category Scores table")
            continue
        reported_raw, reported_status = scores_table[key]
        if score is None:
            if reported_raw.upper() not in {"N/A", "NA"} and reported_status.upper() != "N/A":
                errors.append(f"{key}: table should be N/A, got score={reported_raw}")
            continue
        try:
            reported = int(float(reported_raw.split("/")[0].strip()))
        except ValueError:
            errors.append(f"{key}: Category Scores value not an integer: {reported_raw}")
            continue
        if reported != score:
            errors.append(f"{key}: table score {reported} != computed {score}")
        row = next((r for r in census if r["category"] == key), None)
        if row is None:
            continue
        expect_status = expected_cat_status(score, row["critical_fail"])
        if reported_status and reported_status != expect_status:
            errors.append(
                f"{key}: table status {reported_status} != expected {expect_status}"
            )

    overall = scorelib.overall(computed)
    reported_overall = parse_overall(meta.get("Overall Score", ""))
    if overall is None:
        errors.append("overall: no applicable categories")
    elif reported_overall is None:
        errors.append("Overall Score header missing")
    elif abs(reported_overall - overall) > 0.001:
        errors.append(f"Overall Score {reported_overall} != computed {overall}")

    coverage = scorelib.evidence_coverage(census)
    expect_pct = scorelib.coverage_pct(coverage)
    reported_pct = parse_coverage(meta.get("Evidence coverage", ""))
    if reported_pct is None:
        errors.append("Evidence coverage header missing (percent of known marks)")
    elif reported_pct != expect_pct:
        errors.append(f"Evidence coverage {reported_pct}% != computed {expect_pct}%")

    gates = gate_status_map(tables.get("production gates"))
    for key in scorelib.ABSOLUTE_GATES:
        if key not in gates:
            errors.append(f"absolute gate missing: {key}")

    sec = computed.get("security")
    if gates.get("critical security", "").lower() == "pass" and sec is not None:
        if sec < scorelib.SECURITY_GATE_MIN:
            errors.append(
                f"Critical security cannot be Pass with Security score {sec} (need ≥ {scorelib.SECURITY_GATE_MIN})"
            )
    tes = computed.get("testing")
    if gates.get("testing", "").lower() == "pass" and tes is not None:
        if tes < scorelib.TESTING_GATE_MIN:
            errors.append(
                f"Testing gate cannot be Pass with Testing score {tes} (need ≥ {scorelib.TESTING_GATE_MIN})"
            )
    err = computed.get("error handling")
    if gates.get("error handling", "").lower() == "pass" and err is not None:
        if err < scorelib.ERROR_GATE_MIN:
            errors.append(
                f"Error handling gate cannot be Pass with score {err} (need ≥ {scorelib.ERROR_GATE_MIN})"
            )

    expect_verdict = scorelib.verdict(
        overall_score=overall,
        scores=computed,
        absolute_gate_status=gates,
        coverage=coverage,
    )
    reported_status = (meta.get("Status") or "").strip()
    if reported_status not in scorelib.VERDICTS:
        errors.append(f"Status must be one of {scorelib.VERDICTS}, got {reported_status!r}")
    elif reported_status != expect_verdict:
        errors.append(f"Status {reported_status!r} != computed {expect_verdict!r}")

    mode = (meta.get("Mode") or "").strip()
    expect_note = scorelib.stage_note(mode, expect_verdict)
    reported_note = (meta.get("Stage note") or "").strip()
    if expect_note is None:
        errors.append(f"unknown Mode {mode!r} for stage note")
    elif reported_note != expect_note:
        errors.append(f"Stage note {reported_note!r} != {expect_note!r}")

    voice = "roast"
    if re.search(r"^##\s+Why this matters\b", md, re.MULTILINE | re.IGNORECASE):
        voice = "professional"

    findings = parse_findings(tables.get("findings"))

    payload = {
        "schema": "vibe-proof-report/0.6",
        "version": scorelib.VERSION,
        "project": meta.get("Project", ""),
        "date": meta.get("Date", ""),
        "mode": mode,
        "audit_mode": meta.get("Audit mode", ""),
        "product_type": meta.get("Product type", ""),
        "voice": voice,
        "overall": overall,
        "evidence_coverage": expect_pct,
        "status": expect_verdict,
        "stage_note": expect_note or "",
        "census": [
            {
                "category": r["category"],
                "pass": r["pass"],
                "partial": r["partial"],
                "fail": r["fail"],
                "insufficient": r["insufficient"],
                "na": r["na"],
                "critical_fail": r["critical_fail"],
                "score": computed.get(r["category"]),
            }
            for r in census
        ],
        "scores": computed,
        "gates": gates,
        "findings": findings,
        "errors": errors,
    }
    return errors, payload


def parse_findings(table: list[list[str]] | None) -> list[dict[str, str]]:
    header, rows = table_map(table)
    if not header:
        return []
    i_id = col(header, "id")
    i_mark = col(header, "mark")
    i_path = col(header, "path")
    i_note = col(header, "note")
    out: list[dict[str, str]] = []
    for row in rows:
        def cell(idx: int | None) -> str:
            if idx is None or idx >= len(row):
                return ""
            return row[idx].strip()

        ident = cell(i_id)
        mark = cell(i_mark)
        path = cell(i_path)
        note = cell(i_note)
        if not (ident or path or note):
            continue
        out.append({"id": ident, "mark": mark, "path": path, "note": note})
    return out


def to_sarif(payload: dict) -> dict:
    results = []
    for gate, status in (payload.get("gates") or {}).items():
        if (status or "").lower() != "fail":
            continue
        results.append(
            {
                "ruleId": f"gate/{gate.replace(' ', '-')}",
                "level": "error",
                "message": {"text": f"Absolute or recommended gate Fail: {gate}"},
            }
        )
    for finding in payload.get("findings") or []:
        if (finding.get("mark") or "").lower() != "fail":
            continue
        loc = []
        path = finding.get("path") or ""
        if path:
            loc.append({"physicalLocation": {"artifactLocation": {"uri": path}}})
        ident = finding.get("id") or "finding"
        results.append(
            {
                "ruleId": ident,
                "level": "error",
                "message": {"text": finding.get("note") or ident},
                "locations": loc,
            }
        )
    return {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "vibe-proof-auditor",
                        "version": scorelib.VERSION,
                        "informationUri": "https://github.com/pedroknigge/vibe-proof-auditor",
                    }
                },
                "results": results,
            }
        ],
    }


def main(argv: list[str]) -> int:
    import json

    if len(argv) < 2 or argv[1] in {"-h", "--help"}:
        print(
            "usage: validate-report.py INPUT.md [--json OUT.json] [--sarif OUT.sarif]",
            file=sys.stderr,
        )
        return 2
    src: Path | None = None
    json_out: Path | None = None
    sarif_out: Path | None = None
    args = argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--json" and i + 1 < len(args):
            json_out = Path(args[i + 1])
            i += 2
        elif args[i] == "--sarif" and i + 1 < len(args):
            sarif_out = Path(args[i + 1])
            i += 2
        elif args[i].startswith("-"):
            print(
                "usage: validate-report.py INPUT.md [--json OUT.json] [--sarif OUT.sarif]",
                file=sys.stderr,
            )
            return 2
        else:
            src = Path(args[i])
            i += 1
    if src is None:
        print("usage: validate-report.py INPUT.md [--json OUT.json] [--sarif OUT.sarif]", file=sys.stderr)
        return 2
    if not src.is_file():
        print(f"error: markdown not found: {src}", file=sys.stderr)
        return 1
    try:
        md = src.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    errors, payload = validate(md)
    if json_out:
        json_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if sarif_out:
        sarif_out.write_text(json.dumps(to_sarif(payload), indent=2) + "\n", encoding="utf-8")
    if errors:
        print(f"{src}: {len(errors)} error(s)", file=sys.stderr)
        for err in errors:
            print(f"- {err}", file=sys.stderr)
        return 1
    print(str(src))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
