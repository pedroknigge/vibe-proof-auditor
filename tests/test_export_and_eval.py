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
FIXTURES = ROOT / "evals" / "fixtures"
EXPECTED = ROOT / "evals" / "expected"
CHECKLIST = ROOT / "references" / "checklist.md"

# Rows exist for these in references/checklist.md, but none of them carries a
# `Finding id:` yet, so the manifests name ids the checklist never declares.
# Ratchet: the set may shrink, never grow. Shrinking it needs a checklist edit.
KNOWN_UNDECLARED = frozenset({"empty-catch", "slopsquat", "no-tests"})


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
            proc = run(
                VALIDATE, [str(EXAMPLE), "--json", str(report), "--sarif", str(sarif)]
            )
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
            proc = run(
                COMPARE, [str(ROOT / "evals" / "expected" / "cli.json"), str(report)]
            )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("missing finding", proc.stderr)

    def test_baseline_new_gate_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old = Path(tmp) / "old.json"
            new = Path(tmp) / "new.json"
            old.write_text(
                json.dumps({"gates": {"testing": "Pass"}, "findings": []}),
                encoding="utf-8",
            )
            new.write_text(
                json.dumps({"gates": {"testing": "Fail"}, "findings": []}),
                encoding="utf-8",
            )
            proc = run(COMPARE, ["--baseline", str(old), str(new)])
        self.assertEqual(proc.returncode, 1)
        self.assertIn("new Fail gate", proc.stderr)

    def test_baseline_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old = Path(tmp) / "old.json"
            payload = {
                "gates": {"testing": "Fail"},
                "findings": [{"id": "idor", "mark": "Fail"}],
            }
            old.write_text(json.dumps(payload), encoding="utf-8")
            proc = run(COMPARE, ["--baseline", str(old), str(old)])
        self.assertEqual(proc.returncode, 0)

    def test_compare_help_exits_2(self) -> None:
        proc = run(COMPARE, ["-h"])
        self.assertEqual(proc.returncode, 2)


class EvalFixtureContractTests(unittest.TestCase):
    """Every expected manifest pairs with a fixture tree and a checklist id."""

    def manifests(self) -> dict:
        return {
            path.stem: json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(EXPECTED.glob("*.json"))
        }

    def test_every_manifest_has_a_fixture_tree(self) -> None:
        names = set(self.manifests())
        trees = {p.name for p in FIXTURES.iterdir() if p.is_dir()}
        # forgeboard is the golden for the worked example, not a planted tree.
        self.assertEqual(names - {"forgeboard"}, trees)

    def test_every_must_find_id_resolves_in_the_checklist(self) -> None:
        checklist = CHECKLIST.read_text(encoding="utf-8")
        undeclared = set()
        for manifest in self.manifests().values():
            for key in ("must_find", "must_not_find_as_fail"):
                for spec in manifest.get(key) or []:
                    ident = spec["id"]
                    if f"`{ident}`" not in checklist:
                        undeclared.add(ident)
        self.assertLessEqual(undeclared, KNOWN_UNDECLARED)

    def test_worker_protocol_plants_a_skipped_step(self) -> None:
        source = (FIXTURES / "worker-protocol" / "src" / "consumer.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("broker.receive()", source)
        # The lease protocol's intermediate steps are defined but never invoked:
        # that omission is what `step-skipped` names.
        for step in ("renew", "ack", "nack"):
            with self.subTest(step=step):
                self.assertIn(f"def {step}(", source)
                self.assertNotIn(f"broker.{step}(", source)

    def test_worker_protocol_manifest_drives_compare_eval(self) -> None:
        manifest = EXPECTED / "worker-protocol.json"
        gates = {"environment isolation": "N/A"}
        found = {
            "product_type": "cli",
            "gates": gates,
            "findings": [
                {
                    "id": "step-skipped",
                    "mark": "Fail",
                    "path": "src/consumer.py",
                    "note": "lease acked nowhere; at-least-once becomes redelivery",
                }
            ],
        }
        missed = {"product_type": "cli", "gates": gates, "findings": []}
        with tempfile.TemporaryDirectory() as tmp:
            hit = Path(tmp) / "hit.json"
            miss = Path(tmp) / "miss.json"
            hit.write_text(json.dumps(found), encoding="utf-8")
            miss.write_text(json.dumps(missed), encoding="utf-8")

            ok = run(COMPARE, [str(manifest), str(hit)])
            self.assertEqual(ok.returncode, 0, ok.stderr)

            bad = run(COMPARE, [str(manifest), str(miss)])
            self.assertEqual(bad.returncode, 1)
            self.assertIn("missing finding step-skipped", bad.stderr)


if __name__ == "__main__":
    unittest.main()
