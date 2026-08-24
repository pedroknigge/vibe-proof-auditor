#!/usr/bin/env python3
"""Scoring math + markdown contract drift. Stdlib only."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import scorelib  # noqa: E402

SCORING = (ROOT / "references" / "scoring.md").read_text(encoding="utf-8")
GATES = (ROOT / "references" / "gates.md").read_text(encoding="utf-8")


class ScorelibTests(unittest.TestCase):
    def test_half_up_not_bankers(self) -> None:
        self.assertEqual(scorelib.round_half_up(6.5, 0), 7.0)
        self.assertEqual(scorelib.round_half_up(5.4375, 1), 5.4)
        self.assertEqual(scorelib.round_half_up(6.6, 0), 7.0)

    def test_forgeboard_security_excludes_insufficient(self) -> None:
        # 14 Pass + 4 Partial + 6 Fail; 1 insufficient excluded.
        raw = scorelib.category_score(14, 4, 6, critical_fail=False, category="security")
        self.assertEqual(raw, 7)
        capped = scorelib.category_score(14, 4, 6, critical_fail=True, category="security")
        self.assertEqual(capped, 4)

    def test_forgeboard_overall(self) -> None:
        scores = {
            "security": 4,
            "comprehension": 7,
            "testing": 5,
            "architecture": 7,
            "maintainability": 6,
            "error handling": 7,
            "performance": 6,
            "dependencies": 8,
            "process / environments": 6,
            "product / scope": 5,
        }
        self.assertEqual(scorelib.overall(scores), 5.9)

    def test_na_category_drops_weight(self) -> None:
        scores = {"security": 10, "testing": 10}
        # D = 2.0 + 1.5 = 3.5; overall = 10
        self.assertEqual(scorelib.overall(scores), 10.0)

    def test_coverage_percent(self) -> None:
        rows = [
            {"pass": 14, "partial": 4, "fail": 6, "insufficient": 1},
            {"pass": 3, "partial": 2, "fail": 3, "insufficient": 0},
        ]
        cov = scorelib.evidence_coverage(rows)
        self.assertEqual(scorelib.coverage_pct(cov), 97)

    def test_product_below_six_does_not_block_ready(self) -> None:
        scores = {key: 10 for key in scorelib.WEIGHTS}
        scores["product / scope"] = 5
        overall = scorelib.overall(scores)
        self.assertGreaterEqual(overall, 8.0)
        status = scorelib.verdict(
            overall_score=overall,
            scores=scores,
            absolute_gate_status={k: "Pass" for k in scorelib.ABSOLUTE_GATES},
            coverage=0.95,
        )
        self.assertEqual(status, "READY")

    def test_low_coverage_blocks_ready(self) -> None:
        scores = {key: 9 for key in scorelib.WEIGHTS}
        status = scorelib.verdict(
            overall_score=9.0,
            scores=scores,
            absolute_gate_status={k: "Pass" for k in scorelib.ABSOLUTE_GATES},
            coverage=0.5,
        )
        self.assertEqual(status, "NEEDS HARDENING")

    def test_absolute_fail_is_blocked(self) -> None:
        scores = {key: 9 for key in scorelib.WEIGHTS}
        status = scorelib.verdict(
            overall_score=9.0,
            scores=scores,
            absolute_gate_status={
                "critical security": "Fail",
                "testing": "Pass",
                "error handling": "Pass",
                "environment isolation": "Pass",
            },
            coverage=1.0,
        )
        self.assertEqual(status, "BLOCKED FOR PRODUCTION")

    def test_stage_notes_match_gates_md(self) -> None:
        for (mode, status), note in scorelib.STAGE_NOTES.items():
            self.assertIn(note, GATES, f"missing stage note for {mode} {status}")

    def test_weights_match_scoring_md(self) -> None:
        found: dict[str, float] = {}
        for m in re.finditer(
            r"^\| \d+ \| ([^|]+) \| ([0-9.]+) \|$",
            SCORING,
            re.MULTILINE,
        ):
            found[m.group(1).strip().lower()] = float(m.group(2))
        self.assertEqual(found, scorelib.WEIGHTS)
        self.assertAlmostEqual(sum(scorelib.WEIGHTS.values()), 11.8)

    def test_floors_named_in_scoring_md(self) -> None:
        self.assertIn("cap Security at 4", SCORING)
        self.assertIn("cap Testing at 6", SCORING)
        self.assertIn("cap Error handling at 6", SCORING)

    def test_verdict_words_match_gates_md(self) -> None:
        for word in scorelib.VERDICTS:
            self.assertIn(f"`{word}`", GATES)


if __name__ == "__main__":
    unittest.main()
