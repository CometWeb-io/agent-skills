"""Release identities that this synchronization must preserve."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

# Metadata for a release is written into sync_skill_registry.OVERRIDES before
# the package body is staged, so some of these are declared but not yet on
# disk. Landed releases must match exactly; pending ones must be absent
# everywhere rather than half-registered.
EXPECTED = {
    "founder-led-sales-operator": ("1.1.2", "FROZEN"),
    "research-program-operator": ("1.3.1", "FROZEN"),
    "portfolio-operator": ("1.2.4", "ACTIVE"),
    # 1.1.0 moved a frozen baseline. The freeze rationale in
    # docs/acceptance/longform-publisher-1.0.0.md allows a contract change, and
    # validate_report declares "-> list[str]" yet raised TypeError on a list or
    # dict field. No behaviour on valid input changed. See the exception note in
    # that acceptance record. 1.1.1 made the description host-neutral and
    # bounded it against ebook-publisher; see the 1.1.1 exception there. 1.1.2
    # turned tracebacks on wrongly typed nested fields into error codes; see the
    # 1.1.2 exception, which also covers the untrusted-content rules added to
    # its front door in the same unreleased version. 1.1.3 rejects lower-case
    # claim and gap enums that skipped the support checks; see the 1.1.3 exception.
    # 1.1.4 fits the description, whole boundary included, in the shortest
    # observed host cut and gives each reference a load trigger; see the 1.1.4
    # exception.
    "longform-publisher": ("1.1.5", "FROZEN"),
    "product-operator": ("2.4.3", "ACTIVE"),
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


def test_documented_regeneration_is_a_no_op():
    # CONTRIBUTING tells contributors to run `sync_skill_registry.py --apply`
    # after any registry change. OVERRIDES replaces routing signals wholesale,
    # so a signal added only to registry/skills.json is silently reverted by
    # that command. The two must agree for the documented workflow to be safe.
    module = _sync_module()
    current = json.loads((ROOT / "registry" / "skills.json").read_text(encoding="utf-8"))
    desired = module.desired_registry(current)
    before = {entry["id"]: entry for entry in current["skills"]}
    drift = {
        entry["id"]: key
        for entry in desired["skills"]
        for key in entry
        if entry.get(key) != before.get(entry["id"], {}).get(key)
    }
    assert desired == current, f"sync_skill_registry --apply would rewrite: {drift}"


def test_descriptions_do_not_route_to_unshipped_packages():
    # A description is what a host reads to pick a skill, so naming a package
    # that has not landed sends users to something they cannot install.
    unshipped = pending()
    for skill_id, entry in registry_by_id().items():
        named = sorted(p for p in unshipped if p in entry["description"])
        assert not named, f"{skill_id} description routes to unshipped {named}"


def _yaml_description(skill_md: Path) -> str:
    import yaml

    text = skill_md.read_text(encoding="utf-8")
    block = text.split("---", 2)[1]
    return " ".join(yaml.safe_load(block)["description"].split())


def test_registry_description_is_what_a_yaml_host_reads():
    # Hosts parse SKILL.md with YAML; the registry must carry the same text.
    module = _sync_module()
    for skill_md in sorted((ROOT / "skills").glob("*/SKILL.md")):
        assert module.parse_description(skill_md) == _yaml_description(skill_md), skill_md


@pytest.mark.parametrize("frontmatter", [
    "description: >\n  First paragraph.\n\n  Second paragraph.\n",
    "description: |\n  Line one\n  line two\n",
    'description: "Quoted: with a \\"nested\\" quote"\n',
    "description: Plain text  # trailing comment\n",
    "description: >-\n  Folded\n    more-indented line\n  back\n",
])
def test_parse_description_agrees_with_yaml_on_edge_cases(tmp_path, frontmatter):
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text(f"---\nname: x\n{frontmatter}---\n\n# X\n", encoding="utf-8")
    assert _sync_module().parse_description(skill_md) == _yaml_description(skill_md)


def test_parse_description_rejects_a_duplicate_description(tmp_path):
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("---\nname: x\ndescription: one\ndescription: two\n---\n", encoding="utf-8")
    with pytest.raises(ValueError):
        _sync_module().parse_description(skill_md)
def test_version_sync_covers_packages_without_routing_overrides(tmp_path, monkeypatch):
    module = _sync_module()
    package = tmp_path / "sample"
    package.mkdir()
    (package / "SKILL.md").write_text("placeholder")
    (package / "VERSION").write_text("1.0.1\n")
    monkeypatch.setattr(module, "SKILLS", tmp_path)
    monkeypatch.setattr(module, "OVERRIDES", {})
    current = {"skills": [{"id": "sample", "version": "1.0.0", "description": "kept", "routing_signals": []}]}
    result = module.desired_registry(current)
    assert result["skills"][0] == {"id": "sample", "version": "1.0.1", "description": "kept", "routing_signals": []}
    assert current["skills"][0]["version"] == "1.0.0"
