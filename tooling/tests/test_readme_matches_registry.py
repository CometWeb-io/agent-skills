"""The README's skill list, counts and badges must match the repository.

generate_adapters.py renders the catalog and every skill count from the
registry (README_FACTS); these tests read the committed README directly, so a
hand edit or a skipped regeneration fails here as well as in `--check`.
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


def test_installer_example_count_matches_the_registry() -> None:
    match = re.search(r"`OK: (\d+) Claude Code skills installed in ", readme())
    assert match, "README no longer shows the installer's success line"
    assert int(match.group(1)) == len(registry_ids())


def test_every_badge_is_backed_by_something_this_repository_configures() -> None:
    # A badge is a claim rendered by a third party. Allow only the ones whose
    # source is in this tree: a GitHub Actions workflow that exists, the
    # license in LICENSE, and the generated skill count. A badge for a service
    # nobody configured (coverage, PyPI, docs hosting) fails here.
    badges = re.findall(r"!\[[^\]]*\]\((https://[^)\s]+)\)", readme())
    assert badges, "README carries no badges"
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    for url in badges:
        if workflow := re.fullmatch(
            r"https://github\.com/CometWeb-io/agent-skills/actions/workflows/([\w.-]+\.ya?ml)/badge\.svg", url
        ):
            assert (ROOT / ".github" / "workflows" / workflow.group(1)).is_file(), url
        elif lic := re.fullmatch(r"https://img\.shields\.io/badge/license-(\w+)-\w+", url):
            assert license_text.startswith(f"{lic.group(1)} License"), url
        elif not re.fullmatch(r"https://img\.shields\.io/badge/skills-\d+-\w+\.svg", url):
            raise AssertionError(f"badge with no configured source: {url}")
