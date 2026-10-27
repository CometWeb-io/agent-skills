from __future__ import annotations

import json
from pathlib import Path

import pytest

import real_host_adapters as adapters


def registry(tmp_path: Path, hosts: dict) -> Path:
    (tmp_path / "registry").mkdir()
    (tmp_path / "registry/runtime-hosts.json").write_text(
        json.dumps({"schema": adapters.SCHEMA, "hosts": hosts}), encoding="utf-8"
    )
    return tmp_path


def executable_profile() -> dict:
    return {
        "runtime_mode": "executable",
        "binary": "fake-host",
        "config_env": "FAKE_HOME",
        "credential_env": ["FAKE_TOKEN"],
        "adapter": "fake-json",
        "native_budget": False,
    }


def test_not_run_profile_is_explicit_and_never_executes(tmp_path: Path) -> None:
    root = registry(tmp_path, {
        "cursor": {
            "runtime_mode": "not_run",
            "credential_env": [],
            "adapter": None,
            "native_budget": False,
            "not_run_reason": "CURSOR_RUNTIME_ADAPTER_UNAVAILABLE",
        }
    })
    result = adapters.preflight("cursor", root=root)
    assert result["status"] == "NOT_RUN"
    assert result["reason"] == "CURSOR_RUNTIME_ADAPTER_UNAVAILABLE"


def test_missing_credentials_is_not_run(tmp_path: Path) -> None:
    root = registry(tmp_path, {"fake": executable_profile()})
    assert adapters.preflight("fake", environment={}, root=root)["reason"] == "MISSING_CREDENTIAL"
    assert adapters.preflight("fake", environment={}, root=root, binary_override="/bin/sh")["reason"] == "MISSING_CREDENTIAL"


def test_ready_profile_requires_binary_and_credentials(tmp_path: Path) -> None:
    root = registry(tmp_path, {"fake": executable_profile()})
    result = adapters.preflight(
        "fake", environment={"FAKE_TOKEN": "test"}, root=root, binary_override="/bin/sh"
    )
    assert result["status"] == "READY"
    assert result["adapter"] == "fake-json"
    assert result["authenticated"] == "not_assessed"


@pytest.mark.parametrize("mutation", [
    lambda profile: profile.update(runtime_mode="unsupported"),
    lambda profile: profile.update(runtime_mode="not_run", adapter=None, not_run_reason=""),
    lambda profile: profile.update(credential_env=["bad-name"]),
])
def test_registry_rejects_invalid_profiles(tmp_path: Path, mutation) -> None:
    profile = executable_profile()
    mutation(profile)
    root = registry(tmp_path, {"fake": profile})
    with pytest.raises(ValueError):
        adapters.load_profiles(root)


def test_three_arm_exposure_has_equal_tools_and_no_hidden_json_instructions(tmp_path):
    source = tmp_path / "source"
    files = {
        "skills/demo/SKILL.md": "Follow the specialist workflow.",
        "skills/demo/references/packs/strategy.json": '{"must_inspect": ["secret workflow"]}',
        "skills/demo/references/contract.json": '{"docs": ["workflow.md"]}',
        "skills/demo/references/result.schema.json": '{"type": "object"}',
        "skills/demo/scripts/helper.py": 'print("local helper")',
        "skills/demo/agents/openai.yaml": 'system_prompt: hidden instruction',
        "skills/demo/evals/cases.json": '{"answer": "hidden"}',
        ".claude-plugin/plugin.json": '{"name": "test"}',
    }
    for name, content in files.items():
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    arms = {c: adapters.stage_condition(source, tmp_path / c, c) for c in adapters.THREE_ARM_CONDITIONS}
    assert arms["native"]["files"] == {}
    assert arms["tools"]["bundled_tools"] == arms["skill"]["bundled_tools"]
    assert set(arms["tools"]["files"]) == {
        "skills/demo/scripts/helper.py", "skills/demo/references/result.schema.json"}
    assert "skills/demo/SKILL.md" in arms["skill"]["files"]
    for arm in arms.values():
        assert not any("strategy.json" in p or "contract.json" in p or "/evals/" in p or "/agents/" in p
                       for p in arm["files"])
    assert adapters.three_arm_execution_policy("claude")["reason"] == "ENFORCED_HELPER_BOUNDARY_UNAVAILABLE"
