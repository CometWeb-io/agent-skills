"""A scaffolded skill must satisfy the repository's own contracts immediately.

Adding a skill meant copying an existing one and discovering the contract by
watching checks fail. A scaffold is only worth having if what it emits actually
passes those checks, so this generates one into a temporary tree and runs the
repository's real validators against it rather than asserting on file names.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tooling" / "new_skill.py"

DESCRIPTION = (
    "Scaffold probe skill used to verify that a freshly generated package satisfies the shared "
    "package surface, the adapter icon contract and the executable coverage rule without any "
    "manual editing beforehand."
)


@pytest.fixture
def scaffolded():
    """Create the skill, yield its path, and remove it whatever happens."""
    import shutil
    skill_id = "scaffold-probe-skill"
    target = ROOT / "skills" / skill_id
    if target.exists():
        shutil.rmtree(target)
    proc = subprocess.run(
        [sys.executable, str(TOOL), skill_id, "--description", DESCRIPTION],
        cwd=ROOT, capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    try:
        yield target
    finally:
        shutil.rmtree(target, ignore_errors=True)


@pytest.mark.parametrize("relative", [
    "SKILL.md", "VERSION", "LICENSE", "CHANGELOG.md",
    "assets/icon.svg", "references/output-contract.md",
    "scripts/run_evals.py", "evals/cases.json",
])
def test_scaffold_ships_the_shared_package_surface(scaffolded: Path, relative: str) -> None:
    assert (scaffolded / relative).is_file(), f"scaffold omitted {relative}"


def test_scaffold_passes_the_repository_skill_validator(scaffolded: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tooling" / "validate_skill.py"), str(scaffolded)],
        cwd=ROOT, capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_scaffold_harness_is_executable_and_answers_help(scaffolded: Path) -> None:
    harness = scaffolded / "scripts" / "run_evals.py"
    assert harness.stat().st_mode & 0o111, "harness is not executable"
    proc = subprocess.run([sys.executable, str(harness), "--help"],
                          cwd=scaffolded, capture_output=True, text=True, timeout=120)
    assert proc.returncode == 2 and "usage" in (proc.stdout + proc.stderr).lower()


def test_scaffold_harness_fails_until_an_assertion_exists(scaffolded: Path) -> None:
    """A harness that passed while asserting nothing would be a decoration."""
    proc = subprocess.run([sys.executable, "scripts/run_evals.py"],
                          cwd=scaffolded, capture_output=True, text=True, timeout=120)
    assert proc.returncode == 1, proc.stdout + proc.stderr


@pytest.mark.parametrize("skill_id,description,reason", [
    ("Bad Id", DESCRIPTION, "invalid skill id"),
    ("fine-id", "too short", "at least 80 characters"),
    ("fine-id", "x" * 1100, "1024"),
])
def test_scaffold_rejects_input_the_validators_would_reject(skill_id, description, reason) -> None:
    proc = subprocess.run([sys.executable, str(TOOL), skill_id, "--description", description],
                          cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert proc.returncode != 0
    assert reason in (proc.stdout + proc.stderr)
