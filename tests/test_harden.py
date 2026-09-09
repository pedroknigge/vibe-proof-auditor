#!/usr/bin/env python3
"""harden: extract remediation prompt and build argv. Stdlib only."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from vibe_proof_auditor import harden

EXAMPLE = ROOT / "references" / "example-report.md"


class HardenTests(unittest.TestCase):
    def test_extract_from_example_report(self) -> None:
        text = EXAMPLE.read_text(encoding="utf-8")
        prompt = harden.extract_remediation_prompt(text)
        self.assertIn("BLOCKED FOR PRODUCTION", prompt)
        self.assertIn("Enable RLS", prompt)
        self.assertNotIn("```", prompt)

    def test_missing_section_raises(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            harden.extract_remediation_prompt("# No remediation here\\n")
        self.assertIn("Remediation Prompt", str(ctx.exception))

    def test_build_adapter_argv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            argv = harden.build_adapter_argv(
                "agy",
                "fix the P0",
                project=project,
                model="gemini-3",
                effort="high",
                skip_permissions=True,
            )
        self.assertEqual(argv[0], "agy")
        self.assertIn("--print", argv)
        self.assertIn("--add-dir", argv)
        self.assertIn(str(project.resolve()), argv)
        self.assertIn("--model", argv)
        self.assertIn("gemini-3", argv)
        self.assertIn("--effort", argv)
        self.assertIn("high", argv)
        self.assertIn("--dangerously-skip-permissions", argv)
        self.assertEqual(argv[-1], "fix the P0")

    def test_build_adapter_grok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            argv = harden.build_adapter_argv(
                "grok",
                "fix",
                project=project,
                model="grok-4.6",
                effort=None,
                skip_permissions=False,
            )
        self.assertEqual(argv[0], "grok")
        self.assertIn("--always-approve", argv)
        self.assertIn("grok-4.6", argv)
        self.assertEqual(argv[2], "fix")

    def test_print_prompt_cli(self) -> None:
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = harden.main([str(EXAMPLE), "--print-prompt"])
        self.assertEqual(code, 0)
        self.assertIn("Enable RLS", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
