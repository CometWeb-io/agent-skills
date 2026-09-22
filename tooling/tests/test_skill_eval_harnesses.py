"""Run the per-skill eval harnesses as part of the normal test suite.

Several skills carry their coverage in scripts/run_evals.py instead of pytest
tests. Without this, their suites are green only when somebody remembers to run
them by hand, and CI reports a skill as covered when nothing ran.

The harnesses are executed in-process rather than as a subprocess. A subprocess run is
invisible to coverage, which reported these kernels at 9-12% when the harnesses
actually exercise 56-63% of them — a number low enough to read as "untested"
and send someone rewriting tests that already exist.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def harness_skills() -> list[str]:
    return sorted(path.parents[1].name for path in ROOT.glob("skills/*/scripts/run_evals.py"))


def load_harness(skill: str):
    path = ROOT / "skills" / skill / "scripts" / "run_evals.py"
    directory = str(path.parent)
    name = f"run_evals_{skill.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    added = directory not in sys.path
    if added:
        sys.path.insert(0, directory)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
        if added:
            sys.path.remove(directory)
    return module


@pytest.mark.parametrize("skill", harness_skills())
def test_skill_eval_harness_passes(skill: str) -> None:
    module = load_harness(skill)
    assert hasattr(module, "main"), f"{skill} harness has no main()"
    stdout = io.StringIO()
    # At least one harness parses sys.argv; in-process it would otherwise
    # inherit pytest's own arguments.
    real_argv = sys.argv
    sys.argv = [str(ROOT / "skills" / skill / "scripts" / "run_evals.py")]
    try:
        with contextlib.redirect_stdout(stdout):
            code = module.main()
    finally:
        sys.argv = real_argv
    output = stdout.getvalue()
    assert code == 0, f"{skill} eval harness returned {code}:\n{output}"
    assert "FAIL" not in output, f"{skill} reported a failing case:\n{output}"
    assert output.strip(), f"{skill} harness produced no output; did it run any cases?"


def test_every_harness_skill_is_discovered() -> None:
    # Guards against a skill quietly losing its harness: if one disappears the
    # parametrized test above would simply stop running for it.
    assert harness_skills() == [
        "artifact-acceptance",
        "benchmark-curator",
        "brief-architect",
        "content-reviewer",
        "content-writer",
        "feedback-integrator",
        "longform-publisher",
        "portfolio-operator",
        "product-operator",
        "quality-loop-operator",
        "repair-operator",
        "rubric-designer",
        "skill-auditor",
        "skill-evaluator",
    ]
