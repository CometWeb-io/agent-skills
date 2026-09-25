"""Every published host adapter must identify the same bundle candidate."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_bundle_version_matches_manifests_and_lock() -> None:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"] == version
    for manifest in ("plugin.json", ".claude-plugin/plugin.json", ".cursor-plugin/plugin.json"):
        assert json.loads((ROOT / manifest).read_text(encoding="utf-8"))["version"] == version
    packages = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))["package"]
    assert next(p["version"] for p in packages if p["name"] == "cometweb-agent-skills") == version
