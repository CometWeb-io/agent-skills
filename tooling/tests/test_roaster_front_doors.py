"""Roaster front doors: structure the shared rule inventory cannot express.

The must-keep rules themselves (front-door and deferred) are inventoried per
skill in ``skills/<roaster>/tests/front-door-rules.json`` and enforced by
``tooling/tests/test_front_door_rules.py``, the same mechanism every slimmed
front door uses. This file keeps reference reachability and shared formal-operation rules.
All three front doors use compact checklists; fixed rule counts and workflow
step numbering are not part of their prose contract.
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


def test_shared_operations_rules_are_identical_across_roasters() -> None:
    """Formal operations stay shared; front-door procedures may differ."""
    def carried(skill: str) -> set[tuple[str, str, str]]:
        return {
            (rule["id"], rule["text"], rule["where"])
            for rule in _inventory(skill)["rules"]
            if rule["id"].startswith("shared-")
        }

    first, *rest = (carried(skill) for skill in ("repo-roaster", "science-roaster"))
    assert first, "no shared- rules inventoried"
    assert {where for _, _, where in first if where != "SKILL.md"} == {"references/review-operations.md"}
    for other in rest:
        assert other == first, sorted(first ^ other)


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
