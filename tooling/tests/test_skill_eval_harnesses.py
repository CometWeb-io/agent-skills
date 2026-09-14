"""Run the per-skill eval harnesses as part of the normal test suite.

Three skills carry their coverage in scripts/run_evals.py instead of pytest
tests. Without this, their suites are green only when somebody remembers to
run them by hand, and CI reports a skill as covered when nothing ran.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def harness_skills() -> list[str]:
    return sorted(
        path.parents[1].name
        for path in ROOT.glob("skills/*/scripts/run_evals.py")
    )


@pytest.mark.parametrize("skill_id", harness_skills())
def test_skill_eval_harness_passes(skill_id: str) -> None:
    script = ROOT / "skills" / skill_id / "scripts" / "run_evals.py"
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = proc.stdout + proc.stderr
    assert proc.returncode == 0, f"{skill_id} eval harness failed:\n{output}"
    assert "FAIL" not in proc.stdout, f"{skill_id} reported a failing case:\n{output}"


def test_every_harness_skill_is_discovered() -> None:
    # Guards against a skill quietly losing its harness: if one disappears the
    # parametrized test above would simply stop running for it.
    assert harness_skills() == [
        "longform-publisher",
        "portfolio-operator",
        "product-operator",
    ]
