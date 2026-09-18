"""The README's skill list and counts must match the registry.

Both the prose count, the badge and the tables are written by hand, so each is
a claim that silently goes stale the first time a skill is added or renamed.
The registry is the source of truth everywhere else in this repo; make the
README answer to it too.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"


def registry_ids() -> set[str]:
    data = json.loads((ROOT / "registry" / "skills.json").read_text(encoding="utf-8"))
    return {entry["id"] for entry in data["skills"]}


def readme() -> str:
    return README.read_text(encoding="utf-8")


def test_every_skill_is_listed_and_nothing_extra() -> None:
    listed = set(re.findall(r"\[`([a-z0-9-]+)`\]\(skills/", readme()))
    registry = registry_ids()
    assert listed == registry, {
        "missing_from_readme": sorted(registry - listed),
        "not_in_registry": sorted(listed - registry),
    }


def test_prose_count_matches_the_registry() -> None:
    count = len(registry_ids())
    match = re.search(r"contains (\d+) reusable skill packages", readme())
    assert match, "README no longer states how many skill packages it contains"
    assert int(match.group(1)) == count


def test_badge_count_matches_the_registry() -> None:
    count = len(registry_ids())
    match = re.search(r"badge/skills-(\d+)-", readme())
    assert match, "README no longer carries a skills-count badge"
    assert int(match.group(1)) == count


def test_every_listed_skill_link_resolves() -> None:
    for skill in sorted(registry_ids()):
        assert (ROOT / "skills" / skill).is_dir(), f"README links to missing skills/{skill}/"
