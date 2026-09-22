#!/usr/bin/env python3
"""Validate the GitHub-backed ChatGPT/Codex plugin distribution contract."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = ROOT / ".agents/plugins/marketplace.json"
PLUGIN = ROOT / "plugin.json"
REGISTRY = ROOT / "registry/skills.json"
SKILLS = ROOT / "skills"
PLUGIN_NAME = "cometweb-agent-skills"
REPOSITORY = "https://github.com/CometWeb-io/agent-skills"


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def load(path: Path) -> dict:
    if not path.is_file() or path.is_symlink():
        fail(f"missing or unsafe file: {path.relative_to(ROOT)}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"JSON root must be an object: {path.relative_to(ROOT)}")
    return value


def string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{label} must be a non-empty string")
    return value


def main() -> None:
    marketplace = load(MARKETPLACE)
    plugin = load(PLUGIN)
    registry = load(REGISTRY)

    if marketplace.get("name") != PLUGIN_NAME:
        fail("marketplace.name must match the plugin name")
    interface = marketplace.get("interface")
    if not isinstance(interface, dict) or interface.get("displayName") != "CometWeb Agent Skills":
        fail("marketplace.interface.displayName is invalid")
    entries = marketplace.get("plugins")
    if not isinstance(entries, list) or len(entries) != 1:
        fail("marketplace must expose exactly one canonical plugin")
    entry = entries[0]
    if not isinstance(entry, dict) or entry.get("name") != PLUGIN_NAME:
        fail("marketplace plugin entry has the wrong name")
    source = entry.get("source")
    if source != {"source": "local", "path": "./"}:
        fail("marketplace plugin must point at the repository root with source.path='./'")

    if plugin.get("name") != PLUGIN_NAME:
        fail("plugin.name is invalid")
    version = string(plugin.get("version"), "plugin.version")
    declared_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if version != declared_version or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        fail("plugin.version must match VERSION and use semantic versioning")
    if plugin.get("repository") != REPOSITORY or plugin.get("homepage") != REPOSITORY:
        fail("plugin repository/homepage must point at the canonical public repository")
    if plugin.get("license") != "MIT":
        fail("plugin.license must be MIT")

    rows = registry.get("skills")
    if not isinstance(rows, list) or not rows:
        fail("registry.skills must be a non-empty list")
    skill_ids = [row.get("id") if isinstance(row, dict) else None for row in rows]
    if any(not isinstance(skill, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", skill) for skill in skill_ids):
        fail("registry contains an invalid skill id")
    if len(skill_ids) != len(set(skill_ids)):
        fail("registry contains duplicate skill ids")
    on_disk = {path.name for path in SKILLS.iterdir() if path.is_dir() and not path.name.startswith(".")}
    if on_disk != set(skill_ids):
        fail("the plugin does not expose exactly the registry skill directories")
    for skill in skill_ids:
        skill_md = SKILLS / skill / "SKILL.md"
        if not skill_md.is_file() or skill_md.is_symlink():
            fail(f"{skill}: missing or unsafe SKILL.md")

    print(f"OK: validate_openai_plugin ({len(skill_ids)} skills, version {version})")


if __name__ == "__main__":
    main()
