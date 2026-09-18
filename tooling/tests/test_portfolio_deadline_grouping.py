"""Two hard commitments due the same day are a conflict however the date is written.

detect_capacity_conflicts grouped by the raw deadline string, so
"2026-10-01" and "2026-10-01T00:00:00" landed in different buckets and the
overlap was reported as no conflict — silently, which is the worst way for a
capacity check to be wrong. A one-day gap is still not a conflict: the rule is
explicitly "share the same deadline", and widening it would be inventing a
feature rather than fixing a defect.

This lives in tooling/tests because portfolio-operator keeps its coverage in
scripts/run_evals.py and has no tests/ directory.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def kernel():
    path = ROOT / "skills" / "portfolio-operator" / "scripts" / "portfolio_kernel.py"
    spec = importlib.util.spec_from_file_location("portfolio_kernel_probe", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def commitments(*deadlines):
    module = kernel()
    commitment = sorted(module.HARD_COMMITMENTS)[0]
    effort = sorted(module.LARGE_EFFORT)[0]
    return [
        {"id": f"item-{i}", "deadline": d, "commitment_type": commitment, "effort_class": effort}
        for i, d in enumerate(deadlines)
    ]


@pytest.mark.parametrize("second", [
    "2026-10-01",
    "2026-10-01T00:00:00",
    " 2026-10-01 ",
    "2026-10-01T09:30:00+02:00",
])
def test_same_calendar_day_is_one_conflict(second: str) -> None:
    conflicts = kernel().detect_capacity_conflicts(commitments("2026-10-01", second))
    assert len(conflicts) == 1, f"{second!r} was not grouped with 2026-10-01"
    assert conflicts[0]["type"] == "HARD_COMMITMENT_OVERLAP"


def test_different_days_are_not_a_conflict() -> None:
    assert kernel().detect_capacity_conflicts(commitments("2026-10-01", "2026-10-02")) == []


def test_unparseable_format_still_groups_with_itself() -> None:
    assert len(kernel().detect_capacity_conflicts(commitments("Q4/2026", "Q4/2026"))) == 1


def test_missing_deadlines_are_ignored() -> None:
    assert kernel().detect_capacity_conflicts(commitments(None, None)) == []
