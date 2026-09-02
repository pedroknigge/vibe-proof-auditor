"""Scoring and verdict math. Stdlib only.

Public pre-1.0 version lives in ``VERSION``. Contract numbers live in
``references/scoring.md`` and ``references/gates.md``.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

VERSION = "0.9.3"

# Must match references/scoring.md weight table (sum 12.1).
WEIGHTS: dict[str, float] = {
    "security": 2.0,
    "comprehension": 1.0,
    "testing": 1.5,
    "architecture": 1.3,
    "maintainability": 1.3,
    "error handling": 1.0,
    "performance": 1.0,
    "dependencies": 1.0,
    "process / environments": 1.0,
    "product / scope": 1.0,
}

# Must match references/scoring.md critical floors.
FLOORS: dict[str, int] = {
    "security": 4,
    "testing": 6,
    "error handling": 6,
}

# Product / scope sits in overall but does not trip the <6 READY clause.
# Must match references/gates.md verdict rule.
ENGINEERING_READY_MIN = 6
OVERALL_READY_MIN = 8.0
COVERAGE_READY_MIN = 0.80
SECURITY_GATE_MIN = 8
TESTING_GATE_MIN = 7
ERROR_GATE_MIN = 6

VERDICTS = (
    "READY",
    "NEEDS HARDENING",
    "BLOCKED FOR PRODUCTION",
)

ABSOLUTE_GATES = (
    "critical security",
    "testing",
    "error handling",
    "environment isolation",
)

# Must match references/gates.md stage-note table exactly.
STAGE_NOTES: dict[tuple[str, str], str] = {
    ("Prototype", "BLOCKED FOR PRODUCTION"): (
        "Expected for Prototype. Ship the demo. Do not put users on it."
    ),
    ("Prototype", "NEEDS HARDENING"): (
        "Ahead of a typical Prototype, still not production."
    ),
    ("Prototype", "READY"): (
        "Unusual for Prototype — re-check mode. Production gates already pass."
    ),
    ("MVP", "BLOCKED FOR PRODUCTION"): (
        "Expected for MVP when absolute gates fail. Closed beta only if you "
        "accept the failed gates. Do not open public signups."
    ),
    ("MVP", "NEEDS HARDENING"): "Typical for MVP. Harden before public users.",
    ("MVP", "READY"): "Rare for MVP: production gates already pass.",
    ("Production", "BLOCKED FOR PRODUCTION"): "Not expected. Do not ship.",
    ("Production", "NEEDS HARDENING"): "Do not ship as-is. Harden first.",
    ("Production", "READY"): "Ship.",
}


def round_half_up(value: float, ndigits: int = 0) -> float:
    quant = Decimal(1) if ndigits == 0 else Decimal("0." + "0" * (ndigits - 1) + "1")
    return float(Decimal(str(value)).quantize(quant, rounding=ROUND_HALF_UP))


def norm_cat(name: str) -> str:
    text = (name or "").strip().lower()
    text = text.split("(")[0].strip()
    for prefix in ("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10."):
        if text.startswith(prefix):
            text = text[len(prefix) :].strip()
            break
    return text


def norm_gate(name: str) -> str:
    return (name or "").strip().lower()


def category_ratio(n_pass: int, n_partial: int, n_fail: int) -> float | None:
    """Known marks only. ``insufficient evidence`` is excluded (coverage, not score)."""
    known = n_pass + n_partial + n_fail
    if known <= 0:
        return None
    return (n_pass * 1.0 + n_partial * 0.5 + n_fail * 0.0) / known


def category_score(
    n_pass: int,
    n_partial: int,
    n_fail: int,
    *,
    critical_fail: bool,
    category: str,
) -> int | None:
    ratio = category_ratio(n_pass, n_partial, n_fail)
    if ratio is None:
        return None
    raw = int(round_half_up(ratio * 10, 0))
    if critical_fail:
        floor = FLOORS.get(norm_cat(category))
        if floor is not None:
            return min(raw, floor)
    return raw


def overall(scores: dict[str, int | None]) -> float | None:
    num = 0.0
    den = 0.0
    for key, weight in WEIGHTS.items():
        score = scores.get(key)
        if score is None:
            continue
        num += weight * score
        den += weight
    if den == 0:
        return None
    return round_half_up(num / den, 1)


def evidence_coverage(rows: list[dict[str, int]]) -> float:
    known = 0
    insufficient = 0
    for row in rows:
        known += row["pass"] + row["partial"] + row["fail"]
        insufficient += row["insufficient"]
    denom = known + insufficient
    if denom == 0:
        return 1.0
    return known / denom


def coverage_pct(coverage: float) -> int:
    return int(round_half_up(coverage * 100, 0))


def verdict(
    *,
    overall_score: float | None,
    scores: dict[str, int | None],
    absolute_gate_status: dict[str, str],
    coverage: float,
) -> str:
    for key in ABSOLUTE_GATES:
        status = (absolute_gate_status.get(key) or "").strip()
        if status.lower() == "fail":
            return "BLOCKED FOR PRODUCTION"
    if overall_score is None or overall_score < OVERALL_READY_MIN:
        return "NEEDS HARDENING"
    if coverage < COVERAGE_READY_MIN:
        return "NEEDS HARDENING"
    for key, score in scores.items():
        if key == "product / scope":
            continue
        if score is not None and score < ENGINEERING_READY_MIN:
            return "NEEDS HARDENING"
    return "READY"


def stage_note(mode: str, status: str) -> str | None:
    return STAGE_NOTES.get(((mode or "").strip(), (status or "").strip()))


def parse_yes(raw: str) -> bool:
    return (raw or "").strip().lower() in {"yes", "y", "true", "1"}
