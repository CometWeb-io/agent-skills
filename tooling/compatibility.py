#!/usr/bin/env python3
"""Host compatibility profiles for every skill package."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "skills.json"
HOSTS = ROOT / "registry" / "hosts.json"
SKILLS = ROOT / "skills"
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


if yaml is not None:

    class UniqueLoader(yaml.SafeLoader):
        """SafeLoader that rejects duplicate keys instead of silently
        keeping the last one, so a skill cannot declare two descriptions
        and have the quieter tooling read the wrong one."""

    def _unique_mapping(loader, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in result:
                raise ValueError(f"duplicate YAML key: {key}")
            result[key] = loader.construct_object(value_node, deep=deep)
        return result

    UniqueLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping
    )
else:  # pragma: no cover - yaml is a declared dev dependency
    UniqueLoader = None


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def parse_frontmatter(path: Path) -> dict:
    """Parse and validate a skill's YAML frontmatter.

    Parsed with UniqueLoader rather than a hand-rolled line reader so that a
    duplicate key is an error instead of silently resolving to whichever copy
    happened to come last, and so the name/description contract is enforced
    at the point of reading rather than by whoever remembers to check.
    """
    match = FRONTMATTER_RE.match(path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"missing YAML frontmatter: {path}")
    # UniqueLoader subclasses yaml.SafeLoader; duplicate keys are rejected.
    data = yaml.load(match.group(1), Loader=UniqueLoader)  # nosec B506
    if not isinstance(data, dict):
        raise ValueError("frontmatter must be a mapping")
    name, desc = data.get("name"), data.get("description")
    if (
        not isinstance(name, str)
        or not 1 <= len(name) <= 64
        or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)
    ):
        raise ValueError("invalid skill name")
    if name != path.parent.name:
        raise ValueError("skill name must match its directory")
    if not isinstance(desc, str) or not 1 <= len(desc.strip()) <= 1024:
        raise ValueError("description must contain 1-1024 characters")
    if "compatibility" in data and (
        not isinstance(data["compatibility"], str)
        or not 1 <= len(data["compatibility"]) <= 500
    ):
        raise ValueError("invalid compatibility text")
    return data


def compute_support(entry: dict, host: dict, *, format_ok: bool) -> dict[str, object]:
    """Return deterministic format/runtime support for one skill x host pair.

    Host capabilities describe the platform-level surface, not a guarantee that a
    specific session has every connector authenticated. Missing required capability
    makes the default runtime unsupported; missing optional capability degrades it.
    """
    if not format_ok:
        return {
            "format_support": "UNSUPPORTED",
            "format": "UNSUPPORTED",
            "declared_runtime_support": "UNSUPPORTED",
            "runtime": "UNSUPPORTED",
            "verified_runtime_acceptance": "NOT_TESTED",
            "missing_required": [],
            "missing_optional": [],
        }

    available = set(host.get("capabilities") or [])
    required = list(entry.get("required_capabilities") or [])
    optional = list(entry.get("optional_capabilities") or [])
    missing_required = sorted(cap for cap in required if cap not in available)
    missing_optional = sorted(cap for cap in optional if cap not in available)

    if missing_required:
        runtime = "UNSUPPORTED"
    elif missing_optional:
        runtime = "DEGRADED"
    else:
        runtime = "FULL"

    return {
        "format_support": "FULL",
        "format": "FULL",
        "declared_runtime_support": runtime,
        "runtime": runtime,
        "verified_runtime_acceptance": "NOT_TESTED",
        "missing_required": missing_required,
        "missing_optional": missing_optional,
    }


def check_openai_yaml(skill: str, path: Path, profile: dict) -> list[str]:
    warnings: list[str] = []
    if not path.is_file():
        return [f"{skill}: missing {profile['agents_file']}"]
    text = path.read_text(encoding="utf-8")
    data: dict
    if yaml is not None:
        data = yaml.safe_load(text) or {}
    else:
        data = {"interface": {}, "raw": text}
        if "display_name:" in text:
            data["interface"]["display_name"] = True
        if "short_description:" in text:
            data["interface"]["short_description"] = True
        if "default_prompt:" in text:
            data["interface"]["default_prompt"] = True
        if "icon_small:" in text and "assets/" not in text:
            warnings.append(f"{skill}: openai.yaml icons should use ./assets/... paths")
        return warnings

    interface = data.get("interface") or {}
    for key in profile.get("recommended_interface_keys", []):
        if key not in interface:
            warnings.append(f"{skill}: openai.yaml missing recommended interface.{key}")
    for icon_key in ("icon_small", "icon_large"):
        val = interface.get(icon_key)
        if isinstance(val, str) and val and not val.startswith(("./", "assets/")):
            warnings.append(f"{skill}: {icon_key} should be relative under ./assets/")
    return warnings


def host_targets(entry: dict) -> list[str]:
    return list(entry.get("host_targets") or entry.get("compatible_hosts") or [])


def format_compatible(desc: str, host: dict, skill_dir: Path) -> tuple[bool, list[str]]:
    errors: list[str] = []
    max_len = host.get("description_max")
    if max_len is not None and len(desc) > max_len:
        errors.append(f"description {len(desc)} > {max_len}")
    agents_file = host.get("agents_file")
    if agents_file and not (skill_dir / agents_file).is_file():
        errors.append(f"missing {agents_file}")
    return not errors, errors


def main() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    hosts = json.loads(HOSTS.read_text(encoding="utf-8"))["hosts"]
    errors: list[str] = []
    warnings: list[str] = []

    for entry in registry["skills"]:
        sid = entry["id"]
        skill_dir = SKILLS / sid
        fm = parse_frontmatter(skill_dir / "SKILL.md")
        desc = fm.get("description", "")

        for host_name in host_targets(entry):
            profile = hosts.get(host_name)
            if not profile:
                errors.append(f"{sid}: unknown host {host_name}")
                continue
            format_ok, format_errors = format_compatible(desc, profile, skill_dir)
            for detail in format_errors:
                errors.append(f"{sid}@{host_name}: {detail}")

            if host_name in {"openai-codex", "chatgpt"} and "agents_file" in profile:
                warnings.extend(check_openai_yaml(sid, skill_dir / profile["agents_file"], profile))

            support = compute_support(entry, profile, format_ok=format_ok)
            if support["runtime"] == "UNSUPPORTED" and support["missing_required"]:
                missing = ", ".join(support["missing_required"])
                warnings.append(f"{sid}@{host_name}: runtime unsupported; missing required capabilities: {missing}")

        for rel in hosts["package"]["required_files"]:
            if not (skill_dir / rel).is_file():
                errors.append(f"{sid}@package: missing {rel}")

    for w in warnings:
        print(f"WARN: {w}")
    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
    print(f"OK: compatibility ({len(registry['skills'])} skills)")


if __name__ == "__main__":
    main()
