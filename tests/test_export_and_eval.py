#!/usr/bin/env python3
"""JSON/SARIF export and compare-eval contract. Stdlib only."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATE = ROOT / "vibe_proof_auditor" / "validate_report.py"
COMPARE = ROOT / "vibe_proof_auditor" / "compare_eval.py"
EXAMPLE = ROOT / "references" / "example-report.md"
FORGE = ROOT / "evals" / "expected" / "forgeboard.json"


def run(script: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", f"vibe_proof_auditor.{script.stem}", *args],
        capture_output=True,
        env={"PYTHONPATH": str(ROOT), **__import__("os").environ},
        text=True,
        check=False,
    )


class ExportAndEvalTests(unittest.TestCase):
    def test_example_json_and_forgeboard_eval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.json"
            sarif = Path(tmp) / "report.sarif"
            proc = run(VALIDATE, [str(EXAMPLE), "--json", str(report), "--sarif", str(sarif)])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema"], "vibe-proof-report/0.6")
            self.assertEqual(payload["status"], "BLOCKED FOR PRODUCTION")
            self.assertEqual(payload["overall"], 5.9)
            self.assertEqual(payload["voice"], "roast")
            ids = {f["id"] for f in payload["findings"]}
            self.assertIn("idor", ids)
            sarif_doc = json.loads(sarif.read_text(encoding="utf-8"))
            self.assertEqual(sarif_doc["version"], "2.1.0")
            self.assertTrue(sarif_doc["runs"][0]["results"])
            ev = run(COMPARE, [str(FORGE), str(report)])
            self.assertEqual(ev.returncode, 0, ev.stderr)

    def test_eval_miss_exits_1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.json"
            report.write_text(
                json.dumps(
                    {
                        "product_type": "cli",
                        "gates": {"environment isolation": "N/A"},
                        "findings": [],
                    }
                ),
                encoding="utf-8",
            )
            proc = run(COMPARE, [str(ROOT / "evals" / "expected" / "cli.json"), str(report)])
        self.assertEqual(proc.returncode, 1)
        self.assertIn("missing finding", proc.stderr)

    def test_baseline_new_gate_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old = Path(tmp) / "old.json"
            new = Path(tmp) / "new.json"
            old.write_text(json.dumps({"gates": {"testing": "Pass"}, "findings": []}), encoding="utf-8")
            new.write_text(json.dumps({"gates": {"testing": "Fail"}, "findings": []}), encoding="utf-8")
            proc = run(COMPARE, ["--baseline", str(old), str(new)])
        self.assertEqual(proc.returncode, 1)
        self.assertIn("new Fail gate", proc.stderr)

    def test_baseline_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old = Path(tmp) / "old.json"
            payload = {"gates": {"testing": "Fail"}, "findings": [{"id": "idor", "mark": "Fail"}]}
            old.write_text(json.dumps(payload), encoding="utf-8")
            proc = run(COMPARE, ["--baseline", str(old), str(old)])
        self.assertEqual(proc.returncode, 0)

    def test_compare_help_exits_2(self) -> None:
        proc = run(COMPARE, ["-h"])
        self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
