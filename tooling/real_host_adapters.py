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
    if binary_override is None and not any(environment.get(name) for name in profile["credential_env"]):
        return {"status": "NOT_RUN", "host": host, "reason": "MISSING_CREDENTIAL",
                "credential_names": list(profile["credential_env"])}
    if shutil.which(binary) is None and not Path(binary).is_file():
        return {"status": "NOT_RUN", "host": host, "reason": "HOST_BINARY_UNAVAILABLE",
                "binary": binary, "credential_names": list(profile["credential_env"])}
    return {
        "status": "READY",
        "host": host,
        "adapter": profile["adapter"],
        "binary": binary,
        "credential_names": list(profile["credential_env"]),
    }
