"""Versioned scored-row inventory for current audit reports."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TypedDict

from vibe_proof_auditor import scorelib

CHECKLIST = Path(__file__).resolve().parents[1] / "references" / "checklist.md"


class ScoredItem(TypedDict):
    id: str
    category: str
    critical: bool
    gate: str
    finding_id: str


def scored_items() -> list[ScoredItem]:
    items: list[ScoredItem] = []
    category = ""
    number = 0
    index = 0
    human_interview = False
    for line in CHECKLIST.read_text(encoding="utf-8").splitlines():
        if line.startswith("## Extras"):
            break
        heading = re.match(r"^## (\d+)\. (.+)$", line)
        if heading:
            number = int(heading.group(1))
            category = scorelib.norm_cat(heading.group(2))
            index = 0
            human_interview = False
            continue
        if line.startswith("### Human interview"):
            human_interview = True
            continue
        if not category or human_interview or not line.startswith("- [ ] "):
            continue
        index += 1
        gate_match = re.search(r"Gate: ([a-z /]+)\.", line)
        finding_match = re.search(r"Finding id: `([^`]+)`", line)
        items.append(
            {
                "id": f"{number}.{index:02d}",
                "category": category,
                "critical": "[C]" in line,
                "gate": gate_match.group(1) if gate_match else "",
                "finding_id": finding_match.group(1) if finding_match else "",
            }
        )
    return items
