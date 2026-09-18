"""Context is the resource that decides whether a skill can be used at all.

This repository gates correctness ten ways and, until now, cost none — so
SKILL.md files grew until one reached ~4,900 estimated tokens of front door and
nobody found out. The gate is deliberately about growth rather than an absolute
ceiling: the right ceiling depends on the host, and asserting one here would
claim something the repo cannot evidence.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tooling" / "context_budget.py"


def module():
    spec = importlib.util.spec_from_file_location("context_budget", TOOL)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


def run(*args) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOL), *args], cwd=ROOT,
                          capture_output=True, text=True, timeout=300)


def test_baseline_exists_and_covers_every_skill() -> None:
    mod = module()
    baseline = mod.load_baseline()
    assert baseline is not None, "run tooling/context_budget.py --update"
    on_disk = {p.name for p in (ROOT / "skills").iterdir() if p.is_dir() and (p / "SKILL.md").is_file()}
    assert {row["id"] for row in baseline["skills"]} == on_disk


def test_check_passes_on_the_recorded_baseline() -> None:
    proc = run("--check")
    assert proc.returncode == 0, proc.stderr


def test_measurement_is_deterministic() -> None:
    mod = module()
    assert mod.measure() == mod.measure()


def test_growth_beyond_tolerance_is_reported() -> None:
    mod = module()
    baseline = mod.load_baseline()
    shrunk = copy.deepcopy(baseline)
    # Halve the recorded size of one skill: the live file is then "growth".
    target = shrunk["skills"][0]
    target["front_door_bytes"] = max(1, target["front_door_bytes"] // 2)
    problems = mod.compare(mod.measure(), shrunk, tolerance=0.10)
    assert any(target["id"] in p and "grew" in p for p in problems), problems


def test_a_new_skill_must_be_recorded_before_it_passes() -> None:
    mod = module()
    baseline = copy.deepcopy(mod.load_baseline())
    dropped = baseline["skills"].pop()
    problems = mod.compare(mod.measure(), baseline, tolerance=0.10)
    assert any(dropped["id"] in p and "not in the baseline" in p for p in problems), problems


def test_a_removed_skill_is_reported() -> None:
    mod = module()
    baseline = copy.deepcopy(mod.load_baseline())
    baseline["skills"].append({"id": "skill-that-was-deleted", "front_door_bytes": 100,
                               "front_door_tokens_estimated": 25})
    problems = mod.compare(mod.measure(), baseline, tolerance=0.10)
    assert any("skill-that-was-deleted" in p for p in problems), problems


def test_deferred_ratio_describes_where_the_weight_sits() -> None:
    """0.0 means everything is paid at the front door; 1.0 means nothing is."""
    mod = module()
    rows = {row["id"]: row for row in mod.measure()["skills"]}
    for row in rows.values():
        assert 0.0 <= row["deferred_ratio"] <= 1.0
        total = row["front_door_bytes"] + row["depth_bytes"]
        if total:
            assert row["deferred_ratio"] == pytest.approx(row["depth_bytes"] / total, abs=1e-4)


def test_generated_table_is_current() -> None:
    """Same contract as the other generated tables: never hand-edited."""
    table = ROOT / "docs" / "generated-context-budget.md"
    assert table.is_file(), "run tooling/context_budget.py --table docs/generated-context-budget.md"
    assert table.read_text(encoding="utf-8") == module().render_table(module().measure())
