"""Every SKILL.md frontmatter must satisfy every host's documented constraints.

The constraints live in `registry/hosts.json` under each host's `frontmatter`
block, each with the documentation page it was read from. One table, one
check: a skill that passes the Agent Skills spec can still use a key Cursor
does not document, or a name Claude Code reserves, so each host is checked on
its own terms rather than through the strictest common subset.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling"))
import compatibility  # noqa: E402

HOSTS = json.loads((ROOT / "registry" / "hosts.json").read_text(encoding="utf-8"))["hosts"]
MATRIX = compatibility.frontmatter_matrix(HOSTS)
# Hosts a skill package is installed into, either from a skills directory or a marketplace.
DISTRIBUTION_HOSTS = sorted(
    name for name, profile in HOSTS.items() if profile.get("skill_dirs") or profile.get("marketplace_manifest")
)


def test_matrix_covers_every_skill_and_every_distribution_host() -> None:
    shipped = sorted(path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md"))
    assert sorted(MATRIX) == shipped
    for host in DISTRIBUTION_HOSTS:
        assert compatibility.frontmatter_rules(HOSTS, host) is not None, f"{host}: no frontmatter rules"
        assert all(host in row for row in MATRIX.values())


@pytest.mark.parametrize("skill", sorted(MATRIX))
def test_skill_frontmatter_fits_every_host(skill: str) -> None:
    failures = {host: problems for host, problems in MATRIX[skill].items() if problems}
    assert not failures, f"{skill}: {failures}"


def test_documented_rules_name_their_source() -> None:
    for name, profile in HOSTS.items():
        block = profile.get("frontmatter")
        if block is None or "inherits" in block:
            continue
        assert block["source"].startswith("https://"), name
        assert block["verified_at"], name


def test_inherited_rules_take_the_parent_and_keep_their_own_overrides() -> None:
    hosts = {
        "base": {"frontmatter": {"required": ["name"], "description_max": 1024}},
        "child": {"frontmatter": {"inherits": "base", "description_max": 500}},
        "plain": {},
    }
    assert compatibility.frontmatter_rules(hosts, "child") == {"required": ["name"], "description_max": 500}
    assert compatibility.frontmatter_rules(hosts, "plain") is None


def test_inheritance_cycle_is_an_error() -> None:
    hosts = {"a": {"frontmatter": {"inherits": "b"}}, "b": {"frontmatter": {"inherits": "a"}}}
    with pytest.raises(ValueError, match="cycle"):
        compatibility.frontmatter_rules(hosts, "a")


SPEC = compatibility.frontmatter_rules(HOSTS, "agentskills-common")
CURSOR = compatibility.frontmatter_rules(HOSTS, "cursor")
CLAUDE = compatibility.frontmatter_rules(HOSTS, "claude-code")
GOOD = {"name": "good-skill", "description": "Does one thing. Use when that thing is needed."}


@pytest.mark.parametrize(
    ("rules", "data", "dir_name", "expected"),
    [
        (SPEC, GOOD, "good-skill", []),
        (SPEC, {"description": "x"}, "good-skill", ["missing required key 'name'"]),
        (SPEC, {**GOOD, "name": "Bad_Name"}, "Bad_Name",
         ["name 'Bad_Name' does not match ^[a-z0-9]+(?:-[a-z0-9]+)*$"]),
        (SPEC, {**GOOD, "name": "pdf--tools"}, "pdf--tools",
         ["name 'pdf--tools' does not match ^[a-z0-9]+(?:-[a-z0-9]+)*$"]),
        (SPEC, {**GOOD, "name": "a" * 65}, "a" * 65, ["name is 65 characters, over 64"]),
        (SPEC, GOOD, "other-dir", ["name 'good-skill' differs from directory 'other-dir'"]),
        (SPEC, {**GOOD, "description": "d" * 1025}, "good-skill", ["description is 1025 characters, over 1024"]),
        (SPEC, {**GOOD, "description": "   "}, "good-skill", ["description must be a non-empty string"]),
        (SPEC, {**GOOD, "compatibility": "c" * 501}, "good-skill", ["compatibility must be 1-500 characters"]),
        (SPEC, {**GOOD, "model": "x"}, "good-skill", ["key 'model' is not documented for this host"]),
        # Cursor documents fewer keys than the spec, so `license` is not something it reads.
        (CURSOR, {**GOOD, "license": "MIT"}, "good-skill", ["key 'license' is not documented for this host"]),
        (CURSOR, {**GOOD, "description": "d" * 5000}, "good-skill", []),
        # Claude Code makes every key optional, but reserves two names and truncates the listing.
        (CLAUDE, {"description": "x"}, "anything", []),
        (CLAUDE, {**GOOD, "name": "Synced"}, "Synced", ["name 'Synced' is reserved"]),
        (CLAUDE, {**GOOD, "description": "d" * 1537}, "good-skill", ["description is 1537 characters, over 1536"]),
    ],
)
def test_violations_name_the_exact_rule(rules: dict, data: dict, dir_name: str, expected: list[str]) -> None:
    assert compatibility.frontmatter_violations(data, dir_name, rules) == expected


def test_matrix_reads_a_broken_package(tmp_path: Path) -> None:
    skill = tmp_path / "Bad_Name"
    skill.mkdir()
    (skill / "SKILL.md").write_text("---\nname: Bad_Name\ndescription: x\nlicense: MIT\n---\nbody\n", encoding="utf-8")
    row = compatibility.frontmatter_matrix(HOSTS, tmp_path)["Bad_Name"]
    assert any("does not match" in problem for problem in row["agentskills-common"])
    assert "key 'license' is not documented for this host" in row["cursor"]
    assert row["claude-code"] == []
