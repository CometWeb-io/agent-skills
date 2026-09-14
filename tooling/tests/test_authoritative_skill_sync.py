"""Release identities that this synchronization must preserve."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Metadata for a release is written into sync_skill_registry.OVERRIDES before
# the package body is staged, so some of these are declared but not yet on
# disk. Landed releases must match exactly; pending ones must be absent
# everywhere rather than half-registered.
EXPECTED = {
    "founder-led-sales-operator": ("1.1.2", "FROZEN"),
    "research-program-operator": ("1.3.1", "FROZEN"),
    "portfolio-operator": ("1.1.0", "ACTIVE"),
    "longform-publisher": ("1.0.0", "FROZEN"),
    "product-operator": ("2.2.0", "ACTIVE"),
}

SUPPORTED_HOSTS = {
    "chatgpt",
    "openai-codex",
    "claude-code",
    "cursor",
    "qwen-code",
    "qoder",
    "lingma",
    "alibaba-skills-portal",
}


def _sync_module():
    spec = importlib.util.spec_from_file_location(
        "sync_skill_registry", ROOT / "tooling" / "sync_skill_registry.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pending() -> set[str]:
    return set(_sync_module().pending_packages())


def landed() -> dict[str, tuple[str, str]]:
    skipped = pending()
    return {k: v for k, v in EXPECTED.items() if k not in skipped}


def registry_by_id() -> dict[str, dict]:
    data = json.loads((ROOT / "registry" / "skills.json").read_text(encoding="utf-8"))
    return {entry["id"]: entry for entry in data["skills"]}


def test_authoritative_releases_are_registered_and_on_disk():
    registry = registry_by_id()
    for skill_id, (version, release_status) in landed().items():
        assert skill_id in registry
        entry = registry[skill_id]
        assert entry["version"] == version
        assert entry["release_status"] == release_status
        skill_dir = ROOT / "skills" / skill_id
        assert (skill_dir / "SKILL.md").is_file()
        assert (skill_dir / "VERSION").read_text(encoding="utf-8").strip() == version
        assert (skill_dir / "CHANGELOG.md").is_file()
        assert (skill_dir / "LICENSE").is_file()


def test_pending_releases_are_absent_not_half_registered():
    registry = registry_by_id()
    for skill_id in pending():
        assert skill_id not in registry, f"{skill_id} registered without a package"
        assert not (ROOT / "skills" / skill_id).exists(), (
            f"{skill_id} has a directory but no SKILL.md"
        )


def test_authoritative_releases_target_all_supported_hosts():
    registry = registry_by_id()
    for skill_id in landed():
        assert set(registry[skill_id]["host_targets"]) == SUPPORTED_HOSTS


def test_new_entries_declare_capability_contract():
    registry = registry_by_id()
    for skill_id in landed():
        entry = registry[skill_id]
        assert isinstance(entry["required_capabilities"], list)
        assert isinstance(entry["optional_capabilities"], list)
