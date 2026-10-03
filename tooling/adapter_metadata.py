"""Lossless host-metadata merge: registry-owned fields win; extensions are never silently dropped."""
from __future__ import annotations

from copy import deepcopy

import yaml
from compatibility import safe_load_unique

MANAGED_INTERFACE_KEYS = frozenset({
    "display_name",
    "short_description",
    "default_prompt",
    "icon_small",
    "icon_large",
})


def merge_openai(entry: dict, existing: str | None, interface: dict) -> str:
    old = safe_load_unique(existing) if existing else {}
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
    return yaml.dump(_quote_values(data), Dumper=_Dumper, allow_unicode=True, sort_keys=False, width=10000)


class _Quoted(str):
    """A string value; keys stay plain."""


class _Dumper(yaml.SafeDumper):
    pass


# Codex's skill-creator reference asks for every string value in openai.yaml to
# be quoted and keys left bare. Quoting also keeps values such as "#2-style" or
# "Use $x: ..." from being read as comments or mappings by a looser parser.
_Dumper.add_representer(_Quoted, lambda dumper, value: dumper.represent_scalar("tag:yaml.org,2002:str", str(value), style='"'))


def _quote_values(value):
    if isinstance(value, dict):
        return {key: _quote_values(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_quote_values(item) for item in value]
    if isinstance(value, str):
        return _Quoted(value)
    return value
