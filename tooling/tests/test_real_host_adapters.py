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


def test_ready_profile_requires_binary_and_credentials(tmp_path: Path) -> None:
    root = registry(tmp_path, {"fake": executable_profile()})
    result = adapters.preflight(
        "fake", environment={"FAKE_TOKEN": "test"}, root=root, binary_override="/bin/sh"
    )
    assert result["status"] == "READY"
    assert result["adapter"] == "fake-json"


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
