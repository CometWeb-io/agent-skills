"""Fail-closed runtime host capability profiles for real-host evaluation."""
from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "cometweb.runtime-hosts/v1"
HOST_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
RUNTIME_MODES = {"executable", "not_run"}


def load_profiles(root: Path = ROOT) -> dict[str, dict[str, Any]]:
    path = root / "registry" / "runtime-hosts.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError("invalid runtime host registry schema")
    hosts = data.get("hosts")
    if not isinstance(hosts, dict) or not hosts:
        raise ValueError("runtime host registry must contain hosts")
    for host, profile in hosts.items():
        if not isinstance(host, str) or not HOST_ID.fullmatch(host) or not isinstance(profile, dict):
            raise ValueError("invalid runtime host profile")
        mode = profile.get("runtime_mode")
        if mode not in RUNTIME_MODES:
            raise ValueError(f"{host}: invalid runtime_mode")
        credentials = profile.get("credential_env")
        if not isinstance(credentials, list) or any(
            not isinstance(name, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]*", name)
            for name in credentials
        ):
            raise ValueError(f"{host}: invalid credential_env")
        if mode == "executable":
            if not isinstance(profile.get("binary"), str) or not profile["binary"]:
                raise ValueError(f"{host}: executable profile needs binary")
            if not isinstance(profile.get("config_env"), str) or not profile["config_env"]:
                raise ValueError(f"{host}: executable profile needs config_env")
            if not isinstance(profile.get("adapter"), str) or not profile["adapter"]:
                raise ValueError(f"{host}: executable profile needs adapter")
        else:
            if not isinstance(profile.get("not_run_reason"), str) or not profile["not_run_reason"].strip():
                raise ValueError(f"{host}: not_run profile needs not_run_reason")
            if profile.get("adapter") is not None:
                raise ValueError(f"{host}: not_run profile cannot declare adapter")
    return hosts


def preflight(host: str, environment: dict[str, str] | None = None,
              root: Path = ROOT, binary_override: str | None = None) -> dict[str, Any]:
    profiles = load_profiles(root)
    if host not in profiles:
        raise ValueError(f"unknown runtime host: {host}")
    profile = profiles[host]
    if profile["runtime_mode"] == "not_run":
        return {
            "status": "NOT_RUN",
            "host": host,
            "reason": profile["not_run_reason"],
            "credential_names": list(profile["credential_env"]),
        }
    environment = os.environ if environment is None else environment
    binary = binary_override or profile["binary"]
    if not any(environment.get(name) for name in profile["credential_env"]):
        return {"status": "NOT_RUN", "host": host, "reason": "MISSING_CREDENTIAL",
                "credential_names": list(profile["credential_env"])}
    if shutil.which(binary) is None and not Path(binary).is_file():
        return {"status": "NOT_RUN", "host": host, "reason": "HOST_BINARY_UNAVAILABLE",
                "binary": binary, "credential_names": list(profile["credential_env"])}
    return {
        "status": "READY",
        "readiness_scope": "binary_and_credential_presence_only",
        "authenticated": "not_assessed",
        "runtime_acceptance": "not_assessed",
        "host": host,
        "adapter": profile["adapter"],
        "binary": binary,
        "credential_names": list(profile["credential_env"]),
    }


THREE_ARM_CONTRACT = "cometweb.real-host-three-arm/v1"
THREE_ARM_CONDITIONS = ("native", "tools", "skill")
# B and C share every non-instruction file. Tests/evals are not runtime tools.
INSTRUCTION_SUFFIXES = {".md", ".mdc", ".txt", ".rst"}
EXCLUDED_PARTS = {"agents", "evals", "evaluation", "tests", "__pycache__"}


def stage_condition(source: Path, destination: Path, condition: str) -> dict[str, Any]:
    """Expose different local payloads; this is not filesystem confinement."""
    import hashlib

    if condition not in THREE_ARM_CONDITIONS:
        raise ValueError("unknown three-arm condition")
    destination.mkdir(parents=True, exist_ok=False)
    files: dict[str, str] = {}
    tools: dict[str, str] = {}
    if condition != "native":
        for path in sorted(source.rglob("*")):
            relative = path.relative_to(source)
            if not path.is_file() or any(part in EXCLUDED_PARTS for part in relative.parts):
                continue
            # Copy reviewed runtime categories only, never JSON policy packs, evals,
            # source maps, prompts or contract bindings under a "data" label.
            runtime_tree = relative.parts[0] in {"skills", "resources"}
            tool_file = runtime_tree and (
                ("scripts" in relative.parts and path.suffix.lower() in {".py", ".sh", ".js", ".mjs", ".ts"})
                or path.name.endswith(".schema.json") or path.name == "requirements.txt")
            instruction = not tool_file
            if not tool_file:
                if runtime_tree and path.suffix.lower() not in {".md", ".mdc", ".rst"}:
                    continue
                if condition == "tools":
                    continue
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            files[relative.as_posix()] = digest
            if not instruction:
                tools[relative.as_posix()] = digest
    return {"contract": THREE_ARM_CONTRACT, "condition": condition, "files": files,
            "bundled_tools": tools, "instructions_exposed": condition == "skill",
            "access_boundary": "fresh_profile_and_payload_exposure_not_os_sandbox"}


def three_arm_execution_policy(host: str) -> dict[str, Any]:
    """Helper probes do not yet qualify the profile across every native host tool."""
    from isolated_exec import helper_backend_policy

    return {"status": "NOT_RUN", "host": host,
            "reason": "ENFORCED_HELPER_BOUNDARY_UNAVAILABLE",
            "required_policy": {"filesystem": "owned_job_directory_only",
                                "network": "deny", "environment": "credential_allowlist"},
            "boundary_verified": False, "helper_backend": helper_backend_policy(),
            "native_exec_profile": "CONFIG_SELECTION_NOT_YET_VERIFIED"}
