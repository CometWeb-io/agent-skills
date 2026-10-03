"""Every host sees the same skills, described within that host's limits.

The registry is the one source. Cursor's plugin manifest names the skills in its
description, Codex and ChatGPT list them by `agents/openai.yaml`, and Cursor and
AGENTS.md hosts route with the generated rule and snippet. A hand-written
Cursor fallback once lagged the registry by 18 skills; these checks make each
host artefact answer to the registry instead of to the previous copy.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling"))
import generate_adapters as adapters  # noqa: E402
from compatibility import parse_frontmatter  # noqa: E402

REGISTRY = json.loads((ROOT / "registry" / "skills.json").read_text(encoding="utf-8"))["skills"]
HOSTS = json.loads((ROOT / "registry" / "hosts.json").read_text(encoding="utf-8"))["hosts"]
ACTIVE = [entry for entry in REGISTRY if entry.get("lifecycle", "active") == "active"]
ACTIVE_IDS = sorted(entry["id"] for entry in ACTIVE)


def frontmatter_description(skill: str) -> str:
    # The repository's own parser: hosts see the folded scalar without its trailing newline.
    return parse_frontmatter(ROOT / "skills" / skill / "SKILL.md")["description"]


def test_every_shipped_package_is_an_active_registry_skill() -> None:
    shipped = sorted(path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md"))
    assert shipped == ACTIVE_IDS


@pytest.mark.parametrize("manifest", adapters.HOST_PLUGIN_MANIFESTS)
def test_host_plugin_manifest_names_exactly_the_registry_skills(manifest: str) -> None:
    description = json.loads((ROOT / manifest).read_text(encoding="utf-8"))["description"]
    match = re.fullmatch(r"CometWeb Labs specialist skills \((\d+) packages\): (.+)\.", description)
    assert match, f"{manifest}: description is not the generated skill list"
    names = match.group(2).split(", ")
    assert int(match.group(1)) == len(names) == len(ACTIVE)
    assert names == [adapters.title_case_skill(skill) for skill in ACTIVE_IDS]


@pytest.mark.parametrize("skill", ACTIVE_IDS)
def test_skill_description_is_identical_and_fits_every_targeted_host(skill: str) -> None:
    entry = next(row for row in REGISTRY if row["id"] == skill)
    assert frontmatter_description(skill) == entry["description"], f"{skill}: SKILL.md and registry differ"
    targets = entry.get("host_targets") or entry.get("compatible_hosts") or list(HOSTS)
    for host in targets:
        limit = HOSTS.get(host, {}).get("description_max")
        if limit:
            assert len(entry["description"]) <= limit, f"{skill}: {len(entry['description'])} > {host} {limit}"


@pytest.mark.parametrize("host", [name for name, profile in HOSTS.items() if profile.get("agents_file")])
@pytest.mark.parametrize("skill", ACTIVE_IDS)
def test_openai_interface_fits_the_host_listing(host: str, skill: str) -> None:
    profile = HOSTS[host]
    data = yaml.safe_load((ROOT / "skills" / skill / profile["agents_file"]).read_text(encoding="utf-8"))
    interface = data["interface"]
    for key in profile.get("recommended_interface_keys", []):
        assert isinstance(interface.get(key), str) and interface[key].strip(), f"{skill}: {key} missing"
    short = interface["short_description"]
    low, high = profile.get("short_description_min", 0), profile.get("short_description_max", 10_000)
    assert low <= len(short) <= high, f"{skill}: short_description is {len(short)} chars, {host} wants {low}-{high}"
    assert data["policy"]["allow_implicit_invocation"] is not bool(
        next(row for row in REGISTRY if row["id"] == skill).get("explicit_only")
    )


def test_generator_limits_match_the_host_profiles() -> None:
    for host in ("openai-codex", "chatgpt"):
        assert HOSTS[host]["short_description_min"] == adapters.SHORT_DESCRIPTION_MIN
        assert HOSTS[host]["short_description_max"] == adapters.SHORT_DESCRIPTION_MAX


@pytest.mark.parametrize(
    ("owns", "expected"),
    [
        (["support triage", "incident candidate", "eng handoff", "one item too many to fit"],
         "support triage; incident candidate; eng handoff"),
        # A first item under the minimum lets the next one in, clipped at a word.
        (["skill experiment design", "behavioral lift and resource measurement"],
         "skill experiment design; behavioral lift and resource"),
        # One item longer than the maximum is clipped, never cut mid-word.
        (["a " * 40], "a " * 31 + "a"),
    ],
)
def test_short_description_is_built_from_whole_words(owns: list[str], expected: str) -> None:
    text = adapters.short_description({"owns": owns, "description": "x " * 100})
    assert text == expected.strip()
    assert adapters.SHORT_DESCRIPTION_MIN <= len(text) <= adapters.SHORT_DESCRIPTION_MAX


def table_ids(text: str) -> list[str]:
    return re.findall(r"^\| .+ \| `([a-z0-9-]+)` \|$", text, flags=re.MULTILINE)


@pytest.mark.parametrize("relative", ["extras/cursor-routing.mdc", "extras/AGENTS.snippet.md", "docs/generated-cursor-routing.mdc"])
def test_routing_artefact_routes_to_exactly_the_registry_skills(relative: str) -> None:
    text = (ROOT / relative).read_text(encoding="utf-8")
    assert "generated by tooling/generate_adapters.py" in text
    assert table_ids(text) == ACTIVE_IDS


def test_agents_snippet_has_one_replaceable_block() -> None:
    text = (ROOT / "extras" / "AGENTS.snippet.md").read_text(encoding="utf-8")
    assert text.count(adapters.AGENTS_BEGIN) == 1 and text.count(adapters.AGENTS_END) == 1
    assert text.index(adapters.AGENTS_BEGIN) < text.index(adapters.AGENTS_END)


def test_routing_artefacts_carry_no_local_paths() -> None:
    """The old fallback pointed at a workspace-specific checkout path."""
    for relative in ("extras/cursor-routing.mdc", "extras/AGENTS.snippet.md"):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "platforms/" not in text and "~/" not in text and "/Users/" not in text


def test_registry_change_reaches_every_host_artefact(monkeypatch: pytest.MonkeyPatch) -> None:
    """A new registry skill shows up in each generated host artefact, not only some."""
    extra = dict(ACTIVE[0], id="zz-new-skill", owns=["brand-new routing intent"], alias_of=None)
    skills = [*REGISTRY, extra]
    for path, text in adapters.host_artifacts(skills).items():
        assert "zz-new-skill" in text or "Zz New Skill" in text, f"{path.name} did not pick up the new skill"


def test_plugin_manifest_rewrite_touches_only_the_description() -> None:
    current = (ROOT / ".cursor-plugin" / "plugin.json").read_text(encoding="utf-8")
    renamed = [dict(REGISTRY[0], id="renamed-skill"), *REGISTRY[1:]]
    before, after = json.loads(current), json.loads(adapters.render_plugin_manifest(current, renamed))
    assert list(before) == list(after)
    assert {key for key in before if before[key] != after[key]} == {"description"}
    assert adapters.render_plugin_manifest(current, REGISTRY) == current
