#!/usr/bin/env python3
"""Validator contract tests. Stdlib only."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from vibe_proof_auditor import checklist_contract, scorelib, validate_report

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "vibe_proof_auditor" / "validate_report.py"
EXAMPLE = ROOT / "references" / "example-report.md"


def current_report() -> str:
    items = checklist_contract.scored_items()
    counts = {category: 0 for category in scorelib.WEIGHTS}
    for item in items:
        counts[item["category"]] += 1
    lines = [
        "# Vibe-Proof Audit Report",
        "**Project:** /tmp/fixture",
        "**Date:** 2026-09-26",
        f"**Skill version:** {scorelib.VERSION}",
        "**Mode:** Production",
        "**Audit mode:** Deep",
        "**Product type:** cli",
        "**Overall Score:** 10.0 / 10",
        "**Evidence coverage:** 100%",
        "**Status:** READY",
        "**Stage note:** Ship.",
        "",
        "## Checklist evidence",
        "| Item | Category | Mark | Path | Proof |",
        "|------|----------|------|------|-------|",
    ]
    lines.extend(
        f"| {item['id']} | {item['category']} | Pass | src/fixture.py | verified path |"
        for item in items
    )
    lines.extend(
        [
            "",
            "## Mark census",
            "| Category | Pass | Partial | Fail | insufficient evidence | N/A | Critical Fail | Score |",
            "|----------|------|---------|------|-----------------------|-----|---------------|-------|",
        ]
    )
    lines.extend(
        f"| {category} | {count} | 0 | 0 | 0 | 0 | no | 10 |"
        for category, count in counts.items()
    )
    lines.extend(
        [
            "",
            "## Category Scores",
            "| Category | Score | Status | Notes |",
            "|----------|-------|--------|-------|",
        ]
    )
    lines.extend(f"| {category} | 10 | Pass | verified |" for category in counts)
    lines.extend(
        [
            "",
            "## Production Gates",
            "| Gate | Status | Evidence |",
            "|------|--------|----------|",
        ]
    )
    lines.extend(f"| {gate} | Pass | fixture |" for gate in scorelib.ABSOLUTE_GATES)
    return "\n".join(lines) + "\n"


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", f"vibe_proof_auditor.{SCRIPT.stem}", *args],
        capture_output=True,
        env={"PYTHONPATH": str(ROOT), **__import__("os").environ},
        text=True,
        check=False,
    )


class ValidateReportTests(unittest.TestCase):
    def test_current_report_reconciles_every_scored_item(self) -> None:
        errors, _ = validate_report.validate(current_report())
        self.assertEqual(errors, [])

    def test_current_report_rejects_omitted_item(self) -> None:
        text = current_report()
        first = checklist_contract.scored_items()[0]
        row = f"| {first['id']} | {first['category']} | Pass | src/fixture.py | verified path |\n"
        errors, _ = validate_report.validate(text.replace(row, "", 1))
        self.assertTrue(any("missing item" in error for error in errors), errors)

    def test_current_report_rejects_unreconciled_critical_fail(self) -> None:
        text = current_report()
        first = next(
            item for item in checklist_contract.scored_items() if item["critical"]
        )
        before = f"| {first['id']} | {first['category']} | Pass |"
        after = f"| {first['id']} | {first['category']} | Fail |"
        errors, _ = validate_report.validate(text.replace(before, after, 1))
        self.assertTrue(any("critical_fail" in error for error in errors), errors)

    def test_environment_gate_requires_rollback_and_restore_proof(self) -> None:
        for finding_id in ("rollback-unproven", "restore-unproven"):
            with self.subTest(finding_id=finding_id):
                item = next(
                    item
                    for item in checklist_contract.scored_items()
                    if item["finding_id"] == finding_id
                )
                text = current_report().replace(
                    f"| {item['id']} | process / environments | Pass |",
                    f"| {item['id']} | process / environments | Partial |",
                    1,
                )
                errors, _ = validate_report.validate(text)
                self.assertTrue(
                    any(
                        "environment isolation cannot be Pass" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_legacy_flag_does_not_skip_current_ledger(self) -> None:
        errors, _ = validate_report.validate(current_report(), legacy=True)
        self.assertTrue(any("cannot bypass" in error for error in errors), errors)

    def test_historical_example_requires_legacy_flag(self) -> None:
        proc = run([str(EXAMPLE)])
        self.assertEqual(proc.returncode, 1)
        self.assertIn("--legacy", proc.stderr)

    def test_help_exits_2(self) -> None:
        proc = run(["-h"])
        self.assertEqual(proc.returncode, 2)
        self.assertIn("usage:", proc.stderr)

    def test_missing_file_exits_1(self) -> None:
        proc = run(["/no/such/vibe-proof-report.md"])
        self.assertEqual(proc.returncode, 1)
        self.assertIn("not found", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)

    def test_example_report_passes(self) -> None:
        proc = run([str(EXAMPLE), "--legacy"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("example-report.md", proc.stdout)

    def test_wrong_overall_fails(self) -> None:
        text = EXAMPLE.read_text(encoding="utf-8")
        text = text.replace(
            "**Overall Score:** 5.9 / 10", "**Overall Score:** 9.9 / 10"
        )
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "bad.md"
            src.write_text(text, encoding="utf-8")
            proc = run([str(src), "--legacy"])
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Overall Score", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)

    def test_missing_census_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "in.md"
            src.write_text(
                "# Vibe-Proof Audit Report\n\n"
                "**Project:** /tmp/x\n"
                "**Date:** 2026-08-24\n"
                "**Mode:** Production\n"
                "**Audit mode:** Deep\n"
                "**Product type:** `cli`\n"
                "**Overall Score:** 8.0 / 10\n"
                "**Evidence coverage:** 100%\n"
                "**Status:** READY\n"
                "**Stage note:** Ship.\n\n"
                "## Category Scores\n\n"
                "| Category | Score | Status |\n"
                "|----------|-------|--------|\n"
                "| 1. Security | 8 | Pass |\n",
                encoding="utf-8",
            )
            proc = run([str(src)])
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Mark census", proc.stderr)


if __name__ == "__main__":
    unittest.main()
