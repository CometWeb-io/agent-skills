"""Roaster front doors: structure the shared rule inventory cannot express.

The must-keep rules themselves (front-door and deferred) are inventoried per
skill in ``skills/<roaster>/tests/front-door-rules.json`` and enforced by
``tooling/tests/test_front_door_rules.py``, the same mechanism every slimmed
front door uses. This file keeps only the roaster-specific structure: the
21-rule core contract, the workflow step index, reference reachability, and the
rules all three roasters must carry identically.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ROASTERS = ("repo-roaster", "science-roaster", "content-roaster")


def _inventory(skill: str) -> dict:
    path = ROOT / "skills" / skill / "tests" / "front-door-rules.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("skill", ROASTERS)
def test_roaster_ships_a_rule_inventory(skill: str) -> None:
    assert _inventory(skill)["skill"] == skill


def test_common_and_shared_rules_are_identical_across_roasters() -> None:
    """common-* rules sit in every front door; shared-* in the synced review-operations.md."""
    def carried(skill: str) -> set[tuple[str, str, str]]:
        return {
            (rule["id"], rule["text"], rule["where"])
            for rule in _inventory(skill)["rules"]
            if rule["id"].startswith(("common-", "shared-"))
        }

    first, *rest = (carried(skill) for skill in ROASTERS)
    assert first, "no common-/shared- rules inventoried"
    assert {where for _, _, where in first if where != "SKILL.md"} == {"references/review-operations.md"}
    for other in rest:
        assert other == first, sorted(first ^ other)


@pytest.mark.parametrize("skill", ROASTERS)
def test_core_contract_keeps_all_21_rules(skill: str) -> None:
    text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    section = text.split("## Core contract", 1)[1].split("\n## ", 1)[0]
    numbers = [int(n) for n in re.findall(r"^(\d+)\. ", section, re.M)]
    assert numbers == list(range(1, 22)), numbers


@pytest.mark.parametrize("skill", ROASTERS)
def test_step_index_matches_full_workflow(skill: str) -> None:
    """Adding a step to references/workflow.md without indexing it in SKILL.md fails."""
    package = ROOT / "skills" / skill
    front = (package / "SKILL.md").read_text(encoding="utf-8")
    index = front.split("\n## Workflow\n", 1)[1].split("\n## ", 1)[0]
    indexed = {int(n) for n in re.findall(r"^(\d+)\. ", index, re.M)}
    detailed = (package / "references" / "workflow.md").read_text(encoding="utf-8")
    steps = {int(n) for n in re.findall(r"^### (\d+)\. ", detailed, re.M)}
    assert steps and indexed == steps, (sorted(indexed), sorted(steps))


@pytest.mark.parametrize("skill", ROASTERS)
def test_every_reference_is_reachable_from_the_front_door(skill: str) -> None:
    """A reference nothing points at is never loaded; progressive disclosure needs a path in."""
    package = ROOT / "skills" / skill
    pointer = re.compile(r"`(references/[\w./-]+\.(?:md|json))`")
    seen: set[str] = set()
    queue = ["SKILL.md"]
    while queue:
        current = queue.pop()
        for ref in pointer.findall((package / current).read_text(encoding="utf-8")):
            if ref not in seen and (package / ref).is_file():
                seen.add(ref)
                queue.append(ref)
    on_disk = {p.relative_to(package).as_posix() for p in (package / "references").glob("*.md")}
    assert not on_disk - seen, sorted(on_disk - seen)


def test_shared_operations_reference_is_synced() -> None:
    sync = (ROOT / "tooling" / "sync_roaster_shared.py").read_text(encoding="utf-8")
    assert '"references/review-operations.md"' in sync
