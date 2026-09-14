"""Generated host adapter and compatibility-matrix contract."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEN_PATH = ROOT / "tooling" / "generate_adapters.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("generate_adapters", GEN_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_generator_declares_compatibility_matrix_output():
    gen = load_generator()
    assert gen.OUT_COMPAT == ROOT / "docs" / "generated-compatibility-matrix.md"


def test_compatibility_matrix_contains_every_target_host():
    gen = load_generator()
    registry = json.loads((ROOT / "registry" / "skills.json").read_text(encoding="utf-8"))
    hosts = json.loads((ROOT / "registry" / "hosts.json").read_text(encoding="utf-8"))["hosts"]
    text = gen.build_compatibility_matrix(registry["skills"], hosts)
    for host in (
        "chatgpt",
        "openai-codex",
        "claude-code",
        "cursor",
        "qwen-code",
        "qoder",
        "lingma",
        "alibaba-skills-portal",
    ):
        assert host in text
    assert "FULL" in text


def test_openai_yaml_omits_missing_icon_asset(tmp_path: Path):
    gen = load_generator()
    skill_dir = tmp_path / "example"
    skill_dir.mkdir()
    entry = {
        "id": "example",
        "description": "Use when a sufficiently long example description is needed for adapter testing and validation behavior.",
        "owns": ["example"],
        "explicit_only": False,
    }
    text = gen.render_openai_yaml(entry, existing=None, skill_dir=skill_dir)
    assert "icon_small:" not in text
    assert "icon_large:" not in text


def test_openai_yaml_includes_existing_icon_asset(tmp_path: Path):
    gen = load_generator()
    skill_dir = tmp_path / "example"
    (skill_dir / "assets").mkdir(parents=True)
    (skill_dir / "assets" / "icon.svg").write_text("<svg/>", encoding="utf-8")
    entry = {
        "id": "example",
        "description": "Use when a sufficiently long example description is needed for adapter testing and validation behavior.",
        "owns": ["example"],
        "explicit_only": False,
    }
    text = gen.render_openai_yaml(entry, existing=None, skill_dir=skill_dir)
    assert "icon_small: ./assets/icon.svg" in text
    assert "icon_large: ./assets/icon.svg" in text


def test_expected_artifacts_include_compatibility_matrix():
    gen = load_generator()
    data = json.loads((ROOT / "registry" / "skills.json").read_text(encoding="utf-8"))
    artifacts = gen.expected_artifacts(data["skills"])
    assert gen.OUT_COMPAT in artifacts
