#!/usr/bin/env python3
"""Verify a vibe-proof audit markdown report against the current rubric.

Stdlib only. The agent classifies evidence; this script checks item coverage,
arithmetic, and the verdict rule. It does not re-read the audited tree or prove
that an evidence claim is true. --legacy checks historical report math only.

Exit 0 if the census, scores, overall, coverage, gates, verdict, and stage note
are consistent. Exit 1 on mismatch or unreadable input. Exit 2 on usage.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from vibe_proof_auditor import checklist_contract, parser, render_report, scorelib

USAGE = (
    "usage: validate-report.py INPUT.md [--json OUT.json] "
    "[--sarif OUT.sarif] [--legacy]"
)


def validate_checklist_evidence(
    table: list[list[str]] | None, census: list[dict]
) -> tuple[list[str], dict[str, str]]:
    """Match every current scored row to one evidence-backed mark."""
    errors: list[str] = []
    if not table or len(table) < 2:
        return ["Checklist evidence table required for the current skill version"], {}
    header = [cell.strip().lower() for cell in table[0]]
    needed = ("item", "category", "mark", "path", "proof")
    if any(column not in header for column in needed):
        return [
            "Checklist evidence needs Item, Category, Mark, Path, and Proof columns"
        ], {}
    col = {name: header.index(name) for name in needed}
    expected = {item["id"]: item for item in checklist_contract.scored_items()}
    seen: dict[str, str] = {}
    marks: dict[str, dict[str, int | bool]] = {
        category: {
            "pass": 0,
            "partial": 0,
            "fail": 0,
            "insufficient": 0,
            "na": 0,
            "critical_fail": False,
        }
        for category in scorelib.WEIGHTS
    }
    aliases = {
        "pass": "pass",
        "partial": "partial",
        "fail": "fail",
        "n/a": "na",
        "insufficient evidence": "insufficient",
    }
    for row in table[1:]:

        def cell(name: str, row_ref: list[str] = row) -> str:
            position = col[name]
            return row_ref[position].strip() if position < len(row_ref) else ""

        item_id = cell("item").strip("`")
        if item_id in seen:
            errors.append(f"Checklist evidence duplicate item {item_id}")
            continue
        item = expected.get(item_id)
        if item is None:
            errors.append(f"Checklist evidence unknown item {item_id}")
            continue
        seen[item_id] = cell("mark")
        category = scorelib.norm_cat(cell("category"))
        if category != item["category"]:
            errors.append(f"Checklist evidence {item_id}: wrong category")
        mark = aliases.get(cell("mark").lower())
        if mark is None:
            errors.append(
                f"Checklist evidence {item_id}: invalid mark {cell('mark')!r}"
            )
            continue
        if not cell("proof") or cell("proof") in {"—", "-"}:
            errors.append(f"Checklist evidence {item_id}: proof required")
        if mark in {"pass", "partial", "fail"} and (
            not cell("path") or cell("path") in {"—", "-"}
        ):
            errors.append(f"Checklist evidence {item_id}: path required")
        counts = marks[item["category"]]
        counts[mark] += 1
        if mark == "fail" and item["critical"]:
            counts["critical_fail"] = True
    for item_id in sorted(expected.keys() - seen.keys()):
        errors.append(f"Checklist evidence missing item {item_id}")
    for census_row in census:
        category = census_row["category"]
        census_counts = marks.get(category)
        if census_counts is None:
            continue
        for name in ("pass", "partial", "fail", "insufficient", "na", "critical_fail"):
            if census_row[name] != census_counts[name]:
                errors.append(
                    f"{category}: census {name} {census_row[name]} != Checklist evidence {census_counts[name]}"
                )
    return errors, seen


def validate(md: str, *, legacy: bool = False) -> tuple[list[str], dict]:
    meta = render_report.parse_meta(md)
    tables = render_report.parse_tables(md)
    errors: list[str] = []

    census = parser.census_rows(tables.get("mark census"))
    if len(census) != len(scorelib.WEIGHTS):
        errors.append(
            "Mark census table required with one row per scored category "
            "(Pass, Partial, Fail, insufficient evidence, N/A, Critical Fail)."
        )
        if not census:
            return errors, {}

    skill_version = meta.get("Skill version", "")
    if not skill_version:
        errors.append("Skill version header required")
    elif legacy and skill_version == scorelib.VERSION:
        errors.append("--legacy cannot bypass current-version Checklist evidence")
    elif skill_version != scorelib.VERSION and not legacy:
        errors.append(
            f"Skill version {skill_version} differs from current {scorelib.VERSION}; "
            "use --legacy only for historical reports"
        )
    evidence_marks: dict[str, str] = {}
    if not legacy and skill_version == scorelib.VERSION:
        evidence_errors, evidence_marks = validate_checklist_evidence(
            tables.get("checklist evidence"), census
        )
        errors.extend(evidence_errors)

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
                    errors.append(
                        f"{row['category']}: census Score not an integer: {raw}"
                    )
                    continue
                if reported != score:
                    errors.append(
                        f"{row['category']}: census Score {reported} != computed {score}"
                    )

    for key in scorelib.WEIGHTS:
        if key not in computed:
            computed[key] = None
            errors.append(f"{key}: missing from Mark census")

    scores_table = parser.category_score_map(tables.get("category scores"))
    for key, score in computed.items():
        if key not in scores_table:
            errors.append(f"{key}: missing from Category Scores table")
            continue
        reported_raw, reported_status = scores_table[key]
        if score is None:
            if (
                reported_raw.upper() not in {"N/A", "NA"}
                and reported_status.upper() != "N/A"
            ):
                errors.append(f"{key}: table should be N/A, got score={reported_raw}")
            continue
        try:
            reported = int(float(reported_raw.split("/")[0].strip()))
        except ValueError:
            errors.append(
                f"{key}: Category Scores value not an integer: {reported_raw}"
            )
            continue
        if reported != score:
            errors.append(f"{key}: table score {reported} != computed {score}")
        row_match = next((r for r in census if r["category"] == key), None)
        if row_match is None:
            continue
        expect_status = parser.expected_cat_status(score, row_match["critical_fail"])
        if reported_status and reported_status != expect_status:
            errors.append(
                f"{key}: table status {reported_status} != expected {expect_status}"
            )

    overall = scorelib.overall(computed)
    reported_overall = parser.parse_overall(meta.get("Overall Score", ""))
    if overall is None:
        errors.append("overall: no applicable categories")
    elif reported_overall is None:
        errors.append("Overall Score header missing")
    elif abs(reported_overall - overall) > 0.001:
        errors.append(f"Overall Score {reported_overall} != computed {overall}")

    coverage = scorelib.evidence_coverage(census)
    expect_pct = scorelib.coverage_pct(coverage)
    reported_pct = parser.parse_coverage(meta.get("Evidence coverage", ""))
    if reported_pct is None:
        errors.append("Evidence coverage header missing (percent of known marks)")
    elif reported_pct != expect_pct:
        errors.append(f"Evidence coverage {reported_pct}% != computed {expect_pct}%")

    gates = parser.gate_status_map(tables.get("production gates"))
    for key in scorelib.ABSOLUTE_GATES:
        if key not in gates:
            errors.append(f"absolute gate missing: {key}")

    gate_items: dict[str, list[str]] = {gate: [] for gate in scorelib.ABSOLUTE_GATES}
    for item in checklist_contract.scored_items():
        gate = item["gate"]
        if gate in gate_items:
            gate_items[gate].append(item["id"])
    if evidence_marks:
        for gate, item_ids in gate_items.items():
            if gates.get(gate, "").lower() != "pass":
                continue
            for item_id in item_ids:
                mark = evidence_marks.get(item_id, "").lower()
                if mark not in {"pass", "n/a"}:
                    errors.append(
                        f"{gate} cannot be Pass with Checklist evidence {item_id} {mark or 'missing'}"
                    )

    sec = computed.get("security")
    if (
        gates.get("critical security", "").lower() == "pass"
        and sec is not None
        and sec < scorelib.SECURITY_GATE_MIN
    ):
        errors.append(
            f"Critical security cannot be Pass with Security score {sec} (need ≥ {scorelib.SECURITY_GATE_MIN})"
        )
    tes = computed.get("testing")
    if (
        gates.get("testing", "").lower() == "pass"
        and tes is not None
        and tes < scorelib.TESTING_GATE_MIN
    ):
        errors.append(
            f"Testing gate cannot be Pass with Testing score {tes} (need ≥ {scorelib.TESTING_GATE_MIN})"
        )
    err = computed.get("error handling")
    if (
        gates.get("error handling", "").lower() == "pass"
        and err is not None
        and err < scorelib.ERROR_GATE_MIN
    ):
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
        errors.append(
            f"Status must be one of {scorelib.VERDICTS}, got {reported_status!r}"
        )
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

    findings = parser.parse_findings(tables.get("findings"))

    payload = {
        "schema": "vibe-proof-report/0.6",
        "version": skill_version,
        "validator_version": scorelib.VERSION,
        "legacy_validation": legacy,
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


def to_sarif(payload: dict) -> dict:
    results: list[dict] = [
        {
            "ruleId": f"gate/{gate.replace(' ', '-')}",
            "level": "error",
            "message": {"text": f"Absolute or recommended gate Fail: {gate}"},
        }
        for gate, status in (payload.get("gates") or {}).items()
        if (status or "").lower() == "fail"
    ]
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
        print(USAGE, file=sys.stderr)
        return 2
    src: Path | None = None
    json_out: Path | None = None
    sarif_out: Path | None = None
    legacy = False
    args = argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--json" and i + 1 < len(args):
            json_out = Path(args[i + 1])
            i += 2
        elif args[i] == "--sarif" and i + 1 < len(args):
            sarif_out = Path(args[i + 1])
            i += 2
        elif args[i] == "--legacy":
            legacy = True
            i += 1
        elif args[i].startswith("-"):
            print(USAGE, file=sys.stderr)
            return 2
        else:
            src = Path(args[i])
            i += 1
    if src is None:
        print(USAGE, file=sys.stderr)
        return 2
    if not src.is_file():
        print(f"error: markdown not found: {src}", file=sys.stderr)
        return 1
    try:
        md = src.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    errors, payload = validate(md, legacy=legacy)
    if json_out:
        json_out.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    if sarif_out:
        sarif_out.write_text(
            json.dumps(to_sarif(payload), indent=2) + "\n", encoding="utf-8"
        )
    if errors:
        print(f"{src}: {len(errors)} error(s)", file=sys.stderr)
        for err in errors:
            print(f"- {err}", file=sys.stderr)
        return 1
    print(str(src))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
