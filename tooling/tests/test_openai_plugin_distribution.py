"""The OpenAI marketplace must expose the canonical skills tree without a mirror."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_codex_marketplace_points_at_the_repository_root() -> None:
    marketplace = read_json(".agents/plugins/marketplace.json")
    assert marketplace["name"] == "cometweb-agent-skills"
    assert marketplace["interface"]["displayName"] == "CometWeb Agent Skills"
    assert len(marketplace["plugins"]) == 1
    entry = marketplace["plugins"][0]
    assert entry["name"] == "cometweb-agent-skills"
    assert entry["source"] == {"source": "local", "path": "./"}


def test_portable_plugin_manifest_matches_repository_identity() -> None:
    plugin = read_json("plugin.json")
    assert plugin["name"] == "cometweb-agent-skills"
    assert plugin["version"] == (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert plugin["repository"] == "https://github.com/CometWeb-io/agent-skills"
    assert plugin["license"] == "MIT"


def test_openai_hosts_advertise_the_same_marketplace_contract() -> None:
    hosts = read_json("registry/hosts.json")["hosts"]
    for host in ("openai-codex", "chatgpt"):
        assert hosts[host]["marketplace_manifest"] == ".agents/plugins/marketplace.json"
        assert hosts[host]["plugin_root"] == "."
        assert hosts[host]["source_of_truth"] == "skills/"
    assert hosts["chatgpt"]["install_mode"] == "github_plugin_marketplace"
    assert hosts["chatgpt"]["sync"] == "daily_or_sync_now"


def test_plugin_uses_the_canonical_skill_directories() -> None:
    registry = read_json("registry/skills.json")
    registered = {entry["id"] for entry in registry["skills"]}
    on_disk = {
        path.name
        for path in (ROOT / "skills").iterdir()
        if path.is_dir() and not path.name.startswith(".")
    }
    assert on_disk == registered
    assert all((ROOT / "skills" / skill / "SKILL.md").is_file() for skill in registered)


def test_repository_does_not_introduce_a_second_plugin_skill_tree() -> None:
    assert not (ROOT / "plugins").exists()
