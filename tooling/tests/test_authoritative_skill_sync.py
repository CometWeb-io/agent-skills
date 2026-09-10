"""Release identities that this synchronization must preserve."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {
    "founder-led-sales-operator": ("1.1.2", "FROZEN"),
    "research-program-operator": ("1.3.1", "FROZEN"),
    "portfolio-operator": ("1.1.0", "ACTIVE"),
    "longform-publisher": ("1.0.0", "RELEASE_CANDIDATE"),
    "product-operator": ("2.2.0", "ACTIVE"),
}


def registry_by_id() -> dict[str, dict]:
    data = json.loads((ROOT / "registry" / "skills.json").read_text(encoding="utf-8"))
    return {entry["id"]: entry for entry in data["skills"]}


def test_authoritative_releases_are_registered_and_on_disk():
    registry = registry_by_id()
    for skill_id, (version, release_status) in EXPECTED.items():
        assert skill_id in registry
        entry = registry[skill_id]
        assert entry["version"] == version
        assert entry["release_status"] == release_status
        skill_dir = ROOT / "skills" / skill_id
        assert (skill_dir / "SKILL.md").is_file()
        assert (skill_dir / "VERSION").read_text(encoding="utf-8").strip() == version
        assert (skill_dir / "CHANGELOG.md").is_file()
        assert (skill_dir / "LICENSE").is_file()


def test_authoritative_releases_target_all_supported_hosts():
    registry = registry_by_id()
    expected_hosts = {
        "chatgpt",
        "openai-codex",
        "claude-code",
        "cursor",
        "qwen-code",
        "qoder",
        "lingma",
        "alibaba-skills-portal",
    }
    for skill_id in EXPECTED:
        assert set(registry[skill_id]["host_targets"]) == expected_hosts


def test_new_entries_declare_capability_contract():
    registry = registry_by_id()
    for skill_id in EXPECTED:
        entry = registry[skill_id]
        assert isinstance(entry["required_capabilities"], list)
        assert isinstance(entry["optional_capabilities"], list)
