"""Cross-runtime host compatibility contract for registry v2."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOSTS_PATH = ROOT / "registry" / "hosts.json"
COMPAT_PATH = ROOT / "tooling" / "compatibility.py"


def load_compat_module():
    spec = importlib.util.spec_from_file_location("compatibility", COMPAT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_host_registry_v2_covers_target_hosts():
    data = json.loads(HOSTS_PATH.read_text(encoding="utf-8"))
    assert data["schema"] == "cometweb.hosts/v2"
    hosts = data["hosts"]
    expected = {
        "chatgpt",
        "openai-codex",
        "claude-code",
        "cursor",
        "qwen-code",
        "qoder",
        "lingma",
        "alibaba-skills-portal",
    }
    assert expected <= set(hosts)


def test_local_hosts_declare_discovery_paths():
    hosts = json.loads(HOSTS_PATH.read_text(encoding="utf-8"))["hosts"]
    assert hosts["openai-codex"]["skill_dirs"] == ["~/.codex/skills"]
    assert hosts["claude-code"]["skill_dirs"] == ["~/.claude/skills"]
    assert hosts["cursor"]["skill_dirs"] == ["~/.cursor/skills"]
    assert hosts["qwen-code"]["skill_dirs"] == ["~/.qwen/skills"]
    assert hosts["qoder"]["skill_dirs"] == ["~/.qoder/skills"]
    assert hosts["lingma"]["skill_dirs"] == ["~/.lingma/skills"]


def test_compute_support_rejects_missing_required_capability():
    compat = load_compat_module()
    entry = {
        "required_capabilities": ["filesystem", "code_execution"],
        "optional_capabilities": [],
    }
    host = {"capabilities": ["filesystem"]}
    support = compat.compute_support(entry, host, format_ok=True)
    assert support["format"] == "FULL"
    assert support["runtime"] == "UNSUPPORTED"
    assert support["missing_required"] == ["code_execution"]


def test_compute_support_degrades_when_optional_capability_missing():
    compat = load_compat_module()
    entry = {
        "required_capabilities": ["filesystem"],
        "optional_capabilities": ["web", "github"],
    }
    host = {"capabilities": ["filesystem", "web"]}
    support = compat.compute_support(entry, host, format_ok=True)
    assert support["format"] == "FULL"
    assert support["runtime"] == "DEGRADED"
    assert support["missing_optional"] == ["github"]


def test_compute_support_full_when_capabilities_satisfied():
    compat = load_compat_module()
    entry = {
        "required_capabilities": ["filesystem"],
        "optional_capabilities": ["web"],
    }
    host = {"capabilities": ["filesystem", "web", "code_execution"]}
    support = compat.compute_support(entry, host, format_ok=True)
    assert support["format"] == "FULL"
    assert support["runtime"] == "FULL"
    assert support["format_support"] == "FULL"
    assert support["declared_runtime_support"] == "FULL"
    assert support["verified_runtime_acceptance"] == "NOT_TESTED"


def test_compute_support_marks_bad_format_unsupported():
    compat = load_compat_module()
    support = compat.compute_support({}, {"capabilities": []}, format_ok=False)
    assert support["format"] == "UNSUPPORTED"
    assert support["runtime"] == "UNSUPPORTED"
    assert support["verified_runtime_acceptance"] == "NOT_TESTED"


def test_pathological_routing_pattern_is_rejected():
    import sys

    sys.path.insert(0, str(ROOT / "tooling"))
    import route_skill as routing

    with __import__("pytest").raises(ValueError, match="unsafe nested quantifier"):
        routing._pattern("(a+)+$")

