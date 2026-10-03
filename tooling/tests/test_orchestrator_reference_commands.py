"""A command in a shared orchestrator reference must run from where it says.

`multiagent-execution.md` is copied byte-for-byte into both orchestrator
packages, but `orchestrate_multiagent_kernel.py` ships only in
`skill-orchestrator-multiagent`. A bare `python3 scripts/...` line there failed
for anyone reading the canonical `skill-orchestrator` copy.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PACKAGES = ("skill-orchestrator", "skill-orchestrator-multiagent")
COMMAND = re.compile(r"python3?\s+(scripts/[\w.-]+\.py)")
CD = re.compile(r"^\s*cd\s+\.\./([\w-]+)")


def commands(text: str) -> list[tuple[str | None, str]]:
    """(package a preceding `cd ../pkg` moved into, or None; script path) per command."""
    found = []
    for block in re.findall(r"```(?:bash|sh)?\n(.*?)```", text, re.S):
        moved = None
        for line in block.splitlines():
            if match := CD.match(line):
                moved = match.group(1)
            for script in COMMAND.findall(line):
                found.append((moved, script))
    return found


@pytest.mark.parametrize("package", PACKAGES)
def test_reference_commands_name_a_script_that_exists(package: str) -> None:
    references = sorted((ROOT / "skills" / package / "references").glob("*.md"))
    checked = 0
    for reference in references:
        for moved, script in commands(reference.read_text(encoding="utf-8")):
            owner = moved or package
            assert (ROOT / "skills" / owner / script).is_file(), (
                f"{package}/references/{reference.name}: {script} does not exist in {owner}"
            )
            checked += 1
    assert checked, "no commands found; the pattern no longer matches the references"


def test_detector_sees_a_script_from_another_package() -> None:
    text = "```bash\npython3 scripts/orchestrate_multiagent_kernel.py goal\n```\n"
    [(moved, script)] = commands(text)
    assert moved is None
    assert not (ROOT / "skills" / "skill-orchestrator" / script).is_file()
