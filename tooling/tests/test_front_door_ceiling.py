"""Every SKILL.md front door stays at or under 12,000 bytes.

The context-budget gate catches growth against the recorded baseline, but not a
front door that was already close to the line and crosses it through a small,
unrelated edit (a rewrapped description added 18 bytes once). Depth belongs in
`references/`, which a host reads only when the front door points there.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CEILING = 12_000
FRONT_DOORS = sorted(ROOT.glob("skills/*/SKILL.md"))


def test_front_doors_are_found() -> None:
    assert len(FRONT_DOORS) >= 30


@pytest.mark.parametrize("path", FRONT_DOORS, ids=lambda p: p.parent.name)
def test_front_door_is_within_the_ceiling(path: Path) -> None:
    size = path.stat().st_size
    assert size <= CEILING, f"{path.parent.name}/SKILL.md is {size:,} bytes; move depth into references/"
