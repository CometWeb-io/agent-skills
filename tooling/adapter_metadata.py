"""Lossless host-metadata merge: registry-owned fields win; extensions are never silently dropped."""
from __future__ import annotations

from copy import deepcopy

import yaml
from compatibility import UniqueLoader

MANAGED_INTERFACE_KEYS = frozenset({
    "display_name",
    "short_description",
    "default_prompt",
    "icon_small",
    "icon_large",
})


def merge_openai(entry: dict, existing: str | None, interface: dict) -> str:
    # UniqueLoader subclasses yaml.SafeLoader; duplicate keys are rejected.
    old = yaml.load(existing, Loader=UniqueLoader) if existing else {}  # nosec B506
    if old is None:
        old = {}
    if not isinstance(old, dict):
        raise ValueError("openai.yaml must be a mapping")
    data = deepcopy(old)
    for key in ("interface", "policy", "dependencies"):
        if key in data and not isinstance(data[key], dict):
            raise ValueError(f"openai.yaml {key} must be a mapping")
    managed = data.setdefault("interface", {})
    for key in MANAGED_INTERFACE_KEYS:
        managed.pop(key, None)
    managed.update(interface)
    policy = data.setdefault("policy", {})
    policy.setdefault("products", ["chatgpt", "codex", "api", "atlas"])
    policy["allow_implicit_invocation"] = not bool(entry.get("explicit_only"))
    if "tool_dependencies" in entry:
        data.setdefault("dependencies", {})["tools"] = deepcopy(entry["tool_dependencies"])
    if "dependencies" in data:
        tools = data["dependencies"].get("tools", [])
        if not isinstance(tools, list) or any(
            not isinstance(t, dict)
            or t.get("type") != "mcp"
            or not isinstance(t.get("value"), str)
            or not t["value"]
            for t in tools
        ):
            raise ValueError("invalid MCP dependency metadata")
    if old == data and existing is not None:
        return existing  # avoid format-only churn; semantic changes are still checked
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=10000)
