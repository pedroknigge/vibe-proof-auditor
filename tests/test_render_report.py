#!/usr/bin/env python3
"""Renderer contract tests. Stdlib only."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render-report.py"
EXAMPLE = ROOT / "references" / "example-report.md"


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class RenderReportTests(unittest.TestCase):
    def test_help_exits_2(self) -> None:
        proc = run(["-h"])
        self.assertEqual(proc.returncode, 2)
        self.assertIn("usage:", proc.stderr)

    def test_missing_file_exits_1(self) -> None:
        proc = run(["/no/such/vibe-proof-report.md"])
        self.assertEqual(proc.returncode, 1)
        self.assertIn("not found", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)

    def test_example_report_contains_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "out.html"
            proc = run([str(EXAMPLE), str(dest)])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            html = dest.read_text(encoding="utf-8")
            self.assertIn("BLOCKED FOR PRODUCTION", html)

    def test_script_tag_is_escaped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "in.md"
            dest = Path(tmp) / "out.html"
            src.write_text(
                "# Vibe-Proof Audit Report\n\n"
                "**Project:** /tmp/x\n"
                "**Date:** 2026-08-24\n"
                "**Mode:** Production\n"
                "**Audit mode:** Quick\n"
                "**Product type:** `cli`\n"
                "**Overall Score:** 1.0 / 10\n"
                "**Status:** READY\n\n"
                "## Why this dunks (plain language)\n\n"
                "**P0 — xss.** <script>alert(1)</script>\n",
                encoding="utf-8",
            )
            proc = run([str(src), str(dest)])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            html = dest.read_text(encoding="utf-8")
            self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
            self.assertNotIn("<script>alert(1)</script>", html)

    def test_invalid_utf8_exits_1_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "bad.md"
            src.write_bytes(b"\xff\xfe not utf-8")
            proc = run([str(src)])
            self.assertEqual(proc.returncode, 1)
            self.assertIn("error:", proc.stderr)
            self.assertNotIn("Traceback", proc.stderr)


if __name__ == "__main__":
    unittest.main()
