"""Retire discovery while preserving context helper and CW-AIP contracts."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
RESOURCE = ROOT / "resources/context"
sys.path.insert(0, str(ROOT / "tooling"))
import generate_adapters  # noqa: E402
import skill_contracts  # noqa: E402
from route_skill import route  # noqa: E402


def test_context_is_not_a_skill_or_dependency():
    assert not (ROOT / "skills/cometweb-context").exists()
    assert not (RESOURCE / "SKILL.md").exists()
    registry = json.loads((ROOT / "registry/skills.json").read_text())
    for entry in registry["skills"]:
        assert entry["id"] != "cometweb-context"
        assert entry.get("alias_of") != "cometweb-context"
        assert "cometweb-context" not in [name.rstrip("?") for name in entry.get("dependencies", [])]
    assert "cometweb-context" not in generate_adapters.DISPLAY_NAMES
    assert "cometweb-context" not in generate_adapters.DEFAULT_PROMPTS


def test_context_helper_contract_is_still_checked(monkeypatch):
    monkeypatch.setattr(skill_contracts, "SKILLS", ROOT / "resources")
    assert skill_contracts.check("context") == []


@pytest.mark.parametrize("script", sorted((RESOURCE / "scripts").glob("*.py")), ids=lambda p: p.name)
def test_relocated_helpers_keep_their_cli(script):
    result = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_public_snapshot_still_skips_private_workspace():
    result = subprocess.run(
        [sys.executable, str(RESOURCE / "scripts/repo_snapshot.py"), "--context-scope", "public_example", "--json"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["execution_status"] == "NOT_RUN"


def test_formal_context_still_runs_semantic_validation(monkeypatch):
    spec = importlib.util.spec_from_file_location("context_resource_receiver", ROOT / "tooling/validate_envelope.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    data = json.loads((ROOT / "fixtures/cwaip-v2/conformance/valid/context-portfolio-governance.json").read_text())
    module.validate_envelope(data, final=True)
    data["payload"]["facts"][0]["source_ids"] = ["absent-source"]
    data["payload_hash"] = module.payload_hash(data["payload"])
    monkeypatch.setattr(module, "validate_jsonschema", lambda *args: False)
    with pytest.raises(ValueError, match="unknown source_ids"):
        module.validate_envelope(data, final=True)


def test_retired_skill_cannot_be_selected():
    registry = json.loads((ROOT / "registry/skills.json").read_text())
    policy = json.loads((ROOT / "registry/routing-policy.json").read_text())
    for prompt in ("Użyj cometweb-context", "Odśwież kontekst CometWeb przed spotkaniem"):
        result = route(prompt, registry=registry, policy=policy)
        assert "cometweb-context" not in json.dumps(result)
    with pytest.raises(ValueError, match="unavailable skill"):
        route("Use this skill", registry=registry, policy=policy, invoked=("cometweb-context",))
