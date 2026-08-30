#!/usr/bin/env python3
"""Validator contract tests. Stdlib only."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "vibe_proof_auditor" / "validate_report.py"
EXAMPLE = ROOT / "references" / "example-report.md"


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", f"vibe_proof_auditor.{SCRIPT.stem}", *args],
        capture_output=True,
        env={"PYTHONPATH": str(ROOT), **__import__("os").environ},
        text=True,
        check=False,
    )


class ValidateReportTests(unittest.TestCase):
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
        proc = run([str(EXAMPLE)])
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
            proc = run([str(src)])
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
