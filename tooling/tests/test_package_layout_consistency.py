"""Every registered skill ships the same package surface.

A skill that quietly lacks a piece the others have does not fail any validator
— it just presents differently in a host. Two publication skills reached the
public repo with no icon, so their generated adapters carried none while the
other sixteen did. These assertions make that kind of drift a failure instead
of something noticed by eye.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def registered_skills() -> list[str]:
    data = json.loads((ROOT / "registry" / "skills.json").read_text(encoding="utf-8"))
    return sorted(entry["id"] for entry in data["skills"])


REQUIRED_FILES = ("SKILL.md", "VERSION", "LICENSE", "CHANGELOG.md", "assets/icon.svg")


@pytest.mark.parametrize("skill", registered_skills())
@pytest.mark.parametrize("relative", REQUIRED_FILES)
def test_skill_ships_the_common_package_surface(skill: str, relative: str) -> None:
    path = ROOT / "skills" / skill / relative
    assert path.is_file(), f"{skill} is missing {relative}"
    assert not path.is_symlink(), f"{skill}:{relative} must be a real file"


@pytest.mark.parametrize("skill", registered_skills())
def test_generated_adapter_declares_an_icon(skill: str) -> None:
    """The icon is optional to the generator, which is how two skills lost it."""
    adapter = ROOT / "skills" / skill / "agents" / "openai.yaml"
    assert adapter.is_file(), f"{skill} has no generated openai.yaml"
    text = adapter.read_text(encoding="utf-8")
    assert "icon_small:" in text and "icon_large:" in text, f"{skill} adapter has no icon"


@pytest.mark.parametrize("skill", registered_skills())
def test_skill_declares_some_executable_coverage(skill: str) -> None:
    """Either pytest cases or a run_evals harness — never neither."""
    directory = ROOT / "skills" / skill
    has_tests = any(directory.glob("tests/test_*.py"))
    has_harness = (directory / "scripts" / "run_evals.py").is_file()
    assert has_tests or has_harness, f"{skill} ships no executable coverage"
