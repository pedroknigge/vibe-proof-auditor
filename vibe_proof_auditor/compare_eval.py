#!/usr/bin/env python3
"""Compare a computed report JSON to eval expected.json or a baseline JSON.

Stdlib only. Does not re-audit the tree.

  compare-eval.py EXPECTED.json REPORT.json
      Recall on must_find, gate Fail/N/A constraints. Exit 1 on misses.

  compare-eval.py --baseline OLD.json NEW.json
      Exit 1 if NEW has Fail gates or Fail findings that OLD did not.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def blob(finding: dict) -> str:
    return " ".join(
        str(finding.get(k) or "") for k in ("id", "mark", "path", "note")
    ).lower()


def finding_match(findings: list, spec: dict) -> bool:
    needle = (spec.get("path_substr") or spec.get("id") or "").lower()
    want = (spec.get("mark") or "Fail").lower()
    if not needle:
        return False
    for row in findings:
        if needle not in blob(row):
            continue
        if (row.get("mark") or "").lower() == want:
            return True
    return False


def eval_against_expected(expected: dict, report: dict) -> list[str]:
    errors: list[str] = []
    want_type = (expected.get("product_type") or "").strip().lower()
    got_type = (report.get("product_type") or "").strip().lower().strip("`")
    if want_type and want_type not in got_type:
        errors.append(f"product_type {got_type!r} does not include {want_type!r}")

    gates = {
        k.lower(): (v or "").strip().lower()
        for k, v in (report.get("gates") or {}).items()
    }
    for name in expected.get("must_fail_gates") or []:
        if gates.get(name.lower()) != "fail":
            errors.append(
                f"gate {name} should be Fail, got {gates.get(name.lower())!r}"
            )
    for name in expected.get("must_na_gates") or []:
        if gates.get(name.lower()) != "n/a":
            errors.append(f"gate {name} should be N/A, got {gates.get(name.lower())!r}")
    for name in expected.get("must_pass_gates") or []:
        if gates.get(name.lower()) != "pass":
            errors.append(
                f"gate {name} should be Pass, got {gates.get(name.lower())!r}"
            )

    findings = report.get("findings") or []
    must = expected.get("must_find") or []
    hits = 0
    for spec in must:
        if finding_match(findings, spec):
            hits += 1
        else:
            ident = spec.get("id") or spec.get("path_substr")
            errors.append(f"missing finding {ident}")
    for spec in expected.get("must_not_find_as_fail") or []:
        probe = dict(spec)
        probe["mark"] = "Fail"
        if finding_match(findings, probe):
            errors.append(f"false Fail on {spec.get('id') or spec.get('path_substr')}")

    if must:
        report["_recall"] = hits / len(must)
    return errors


def baseline_regressions(old: dict, new: dict) -> list[str]:
    errors: list[str] = []
    old_gates = {
        k.lower()
        for k, v in (old.get("gates") or {}).items()
        if (v or "").lower() == "fail"
    }
    new_gates = {
        k.lower()
        for k, v in (new.get("gates") or {}).items()
        if (v or "").lower() == "fail"
    }
    for gate in sorted(new_gates - old_gates):
        errors.append(f"new Fail gate: {gate}")

    def fail_keys(payload: dict) -> set[str]:
        out = set()
        for row in payload.get("findings") or []:
            if (row.get("mark") or "").lower() != "fail":
                continue
            out.add((row.get("id") or row.get("path") or row.get("note") or "").lower())
        return out

    for key in sorted(fail_keys(new) - fail_keys(old)):
        if key:
            errors.append(f"new Fail finding: {key}")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[1] in {"-h", "--help"}:
        print(
            "usage: compare-eval.py EXPECTED.json REPORT.json\n"
            "       compare-eval.py --baseline OLD.json NEW.json",
            file=sys.stderr,
        )
        return 2
    baseline = len(argv) >= 2 and argv[1] == "--baseline"
    paths = argv[2:] if baseline else argv[1:]
    if len(paths) != 2:
        print(
            "usage: compare-eval.py EXPECTED.json REPORT.json\n"
            "       compare-eval.py --baseline OLD.json NEW.json",
            file=sys.stderr,
        )
        return 2
    left = Path(paths[0])
    right = Path(paths[1])
    if not left.is_file() or not right.is_file():
        print("error: json not found", file=sys.stderr)
        return 1
    try:
        a = load(left)
        b = load(right)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    errors = baseline_regressions(a, b) if baseline else eval_against_expected(a, b)
    if errors:
        print(f"{len(errors)} error(s)", file=sys.stderr)
        for err in errors:
            print(f"- {err}", file=sys.stderr)
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
