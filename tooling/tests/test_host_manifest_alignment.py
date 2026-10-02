"""Cursor, Claude Code and Codex manifests must describe the same plugin.

The three marketplaces are maintained by hand. The Codex entry once carried an
older description than the Cursor and Claude entries, so a user comparing hosts
saw two different products. These checks pin every shared field to plugin.json.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

PLUGIN_MANIFESTS = ("plugin.json", ".claude-plugin/plugin.json", ".cursor-plugin/plugin.json")
MARKETPLACES = (
    ".claude-plugin/marketplace.json",
    ".cursor-plugin/marketplace.json",
    ".agents/plugins/marketplace.json",
)
SHARED_FIELDS = ("name", "version", "author", "homepage", "repository", "license")


def read_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def skill_count() -> int:
    return len(list((ROOT / "skills").glob("*/SKILL.md")))


@pytest.mark.parametrize("manifest", PLUGIN_MANIFESTS[1:])
def test_host_plugin_manifest_shares_identity_with_root(manifest: str) -> None:
    root, host = read_json("plugin.json"), read_json(manifest)
    for field in SHARED_FIELDS:
        assert host[field] == root[field], f"{manifest}: {field} drifted from plugin.json"


def test_cursor_and_claude_plugin_manifests_are_identical() -> None:
    assert read_json(".cursor-plugin/plugin.json") == read_json(".claude-plugin/plugin.json")


@pytest.mark.parametrize("manifest", PLUGIN_MANIFESTS[1:])
def test_host_plugin_description_counts_every_skill(manifest: str) -> None:
    description = read_json(manifest)["description"]
    match = re.search(r"\((\d+) packages\): (.+)\.$", description)
    assert match, f"{manifest}: description must state '(N packages): A, B, ...'"
    assert int(match.group(1)) == skill_count()
    assert len(match.group(2).split(", ")) == skill_count()


@pytest.mark.parametrize("marketplace", MARKETPLACES)
def test_marketplace_lists_the_one_canonical_plugin(marketplace: str) -> None:
    data = read_json(marketplace)
    root = read_json("plugin.json")
    assert data["name"] == root["name"]
    assert len(data["plugins"]) == 1
    entry = data["plugins"][0]
    assert entry["name"] == root["name"]
    assert entry["description"] == root["description"], f"{marketplace}: description drifted"


def test_github_marketplace_points_at_the_repository_in_plugin_json() -> None:
    source = read_json(".claude-plugin/marketplace.json")["plugins"][0]["source"]
    repository = read_json("plugin.json")["repository"]
    assert source["source"] == "github"
    assert repository == f"https://github.com/{source['repo']}"


@pytest.mark.parametrize("marketplace", (".cursor-plugin/marketplace.json", ".agents/plugins/marketplace.json"))
def test_local_marketplaces_point_at_the_repository_root(marketplace: str) -> None:
    source = read_json(marketplace)["plugins"][0]["source"]
    path = source if isinstance(source, str) else source["path"]
    assert (ROOT / path).resolve() == ROOT
