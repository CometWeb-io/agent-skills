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


def _reject_duplicate_keys(node) -> None:
    """Walk a composed YAML node tree and fail on a repeated mapping key.

    yaml.safe_load keeps the last of two equal keys without a word, so a skill
    could declare two descriptions and have the quieter tooling read the wrong
    one. Composing builds nodes only, never Python objects, so this pass runs
    no constructors and needs no custom loader.
    """
    stack = [node]
    seen_nodes: set[int] = set()
    while stack:
        current = stack.pop()
        if current is None or id(current) in seen_nodes:
            continue
        seen_nodes.add(id(current))  # anchors/aliases reuse a node
        if isinstance(current, yaml.MappingNode):
            keys = set()
            for key_node, value_node in current.value:
                if isinstance(key_node, yaml.ScalarNode):
                    key = (key_node.tag, key_node.value)
                    if key in keys:
                        raise ValueError(f"duplicate YAML key: {key_node.value}")
                    keys.add(key)
                stack.extend((key_node, value_node))
        elif isinstance(current, yaml.SequenceNode):
            stack.extend(current.value)


def safe_load_unique(text: str):
    """yaml.safe_load, except that a duplicate mapping key is an error."""
    if yaml is None:  # pragma: no cover - yaml is a declared dev dependency
        raise RuntimeError("PyYAML is required to read YAML frontmatter")
    _reject_duplicate_keys(yaml.compose(text, Loader=yaml.SafeLoader))
    return yaml.safe_load(text)


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def parse_frontmatter(path: Path) -> dict:
    """Parse and validate a skill's YAML frontmatter.

    Parsed with safe_load_unique rather than a hand-rolled line reader so that a
    duplicate key is an error instead of silently resolving to whichever copy
    happened to come last, and so the name/description contract is enforced
    at the point of reading rather than by whoever remembers to check.
    """
    match = FRONTMATTER_RE.match(path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"missing YAML frontmatter: {path}")
    data = safe_load_unique(match.group(1))
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


def read_frontmatter(path: Path) -> dict:
    """Return a SKILL.md frontmatter mapping without applying any host's rules."""
    match = FRONTMATTER_RE.match(path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"missing YAML frontmatter: {path}")
    data = safe_load_unique(match.group(1))
    if not isinstance(data, dict):
        raise ValueError("frontmatter must be a mapping")
    return data


def frontmatter_rules(hosts: dict, host_name: str) -> dict | None:
    """Resolve a host's documented frontmatter constraints, following `inherits`."""
    seen: list[str] = []
    rules: dict = {}
    current: str | None = host_name
    while current is not None:
        if current in seen:
            raise ValueError(f"frontmatter inheritance cycle: {' -> '.join([*seen, current])}")
        seen.append(current)
        block = (hosts.get(current) or {}).get("frontmatter")
        if block is None:
            return None if current == host_name else rules
        rules = {**{k: v for k, v in block.items() if k != "inherits"}, **rules}
        current = block.get("inherits")
    return rules


def frontmatter_violations(data: dict, dir_name: str, rules: dict) -> list[str]:
    """List every way one parsed frontmatter breaks one host's documented rules."""
    problems: list[str] = []
    for key in rules.get("required", []):
        if key not in data:
            problems.append(f"missing required key {key!r}")
    allowed = rules.get("allowed_keys")
    if allowed is not None:
        for key in sorted(set(data) - set(allowed)):
            problems.append(f"key {key!r} is not documented for this host")
    name = data.get("name", dir_name)
    if not isinstance(name, str) or not name:
        problems.append("name must be a non-empty string")
    else:
        pattern = rules.get("name_pattern")
        if pattern and not re.fullmatch(pattern, name):
            problems.append(f"name {name!r} does not match {pattern}")
        name_max = rules.get("name_max")
        if name_max is not None and len(name) > name_max:
            problems.append(f"name is {len(name)} characters, over {name_max}")
        if rules.get("name_matches_dir") and name != dir_name:
            problems.append(f"name {name!r} differs from directory {dir_name!r}")
        if name.casefold() in {n.casefold() for n in rules.get("reserved_names", [])}:
            problems.append(f"name {name!r} is reserved")
    if "description" in data:
        desc = data["description"]
        if not isinstance(desc, str) or not desc.strip():
            problems.append("description must be a non-empty string")
        else:
            desc_max = rules.get("description_max")
            if desc_max is not None and len(desc) > desc_max:
                problems.append(f"description is {len(desc)} characters, over {desc_max}")
    if "compatibility" in data and rules.get("compatibility_max") is not None:
        compat = data["compatibility"]
        if not isinstance(compat, str) or not 1 <= len(compat) <= rules["compatibility_max"]:
            problems.append(f"compatibility must be 1-{rules['compatibility_max']} characters")
    return problems


def frontmatter_matrix(hosts: dict, skills_dir: Path = SKILLS) -> dict[str, dict[str, list[str]]]:
    """Check every SKILL.md against every host that documents frontmatter rules.

    Returns {skill: {host: [violations]}}; an empty list is a pass.
    """
    host_rules = {
        name: rules for name in sorted(hosts) if (rules := frontmatter_rules(hosts, name)) is not None
    }
    matrix: dict[str, dict[str, list[str]]] = {}
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        data = read_frontmatter(skill_md)
        matrix[skill_md.parent.name] = {
            host: frontmatter_violations(data, skill_md.parent.name, rules) for host, rules in host_rules.items()
        }
    return matrix


def load_runtime(skill_dir: Path) -> dict | None:
    path = skill_dir / "RUNTIME.json"
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "cometweb.skill-runtime/v1":
        raise ValueError(f"{skill_dir.name}: unsupported RUNTIME.json schema")
    if not isinstance(data.get("python"), str) or not data["python"].strip():
        raise ValueError(f"{skill_dir.name}: RUNTIME.json missing python")
    deps = data.get("dependencies", {})
    if not isinstance(deps, dict):
        raise ValueError(f"{skill_dir.name}: RUNTIME.json dependencies must be an object")
    return data


def verify_runtime_imports(requirements: dict) -> str:
    """Best-effort local import probe — not a substitute for host acceptance."""
    mapping = {
        "pypdf": "pypdf",
        "jsonschema": "jsonschema",
    }
    deps = requirements.get("dependencies") or {}
    if not deps:
        return "NONE"
    missing: list[str] = []
    for stage, rows in deps.items():
        for spec in rows:
            name = re.split(r"[<>=!~\[]", spec, maxsplit=1)[0].strip()
            module = mapping.get(name, name.replace("-", "_"))
            try:
                __import__(module)
            except ImportError:
                missing.append(f"{stage}:{spec}")
    if missing:
        return "MISSING:" + ",".join(missing)
    return "PRESENT"


def compute_support(entry: dict, host: dict, *, format_ok: bool, runtime: dict | None = None) -> dict[str, object]:
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
            "python_requirement": None,
            "dependencies": [],
            "runtime_dependency_status": "NONE",
            "missing_required": [],
            "missing_optional": [],
        }

    available = set(host.get("capabilities") or [])
    required = list(entry.get("required_capabilities") or [])
    optional = list(entry.get("optional_capabilities") or [])
    missing_required = sorted(cap for cap in required if cap not in available)
    missing_optional = sorted(cap for cap in optional if cap not in available)

    if missing_required:
        runtime_status = "UNSUPPORTED"
    elif missing_optional:
        runtime_status = "DEGRADED"
    else:
        runtime_status = "FULL"

    deps: list[str] = []
    for rows in (runtime or {}).get("dependencies", {}).values():
        deps.extend(rows)

    return {
        "format_support": "FULL",
        "format": "FULL",
        "declared_runtime_support": runtime_status,
        "runtime": runtime_status,
        "verified_runtime_acceptance": "NOT_TESTED",
        "python_requirement": (runtime or {}).get("python"),
        "dependencies": deps,
        "runtime_dependency_status": verify_runtime_imports(runtime or {}),
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
        try:
            runtime = load_runtime(skill_dir)
        except ValueError as exc:
            errors.append(str(exc))
            runtime = None

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

            support = compute_support(entry, profile, format_ok=format_ok, runtime=runtime)
            if support["runtime"] == "UNSUPPORTED" and support["missing_required"]:
                missing = ", ".join(support["missing_required"])
                warnings.append(f"{sid}@{host_name}: runtime unsupported; missing required capabilities: {missing}")
            if isinstance(support.get("runtime_dependency_status"), str) and support["runtime_dependency_status"].startswith("MISSING:"):
                warnings.append(
                    f"{sid}@{host_name}: declared runtime deps not importable here "
                    f"({support['runtime_dependency_status']})"
                )

        for rel in hosts["package"]["required_files"]:
            if not (skill_dir / rel).is_file():
                errors.append(f"{sid}@package: missing {rel}")

    matrix = frontmatter_matrix(hosts)
    for sid, per_host in matrix.items():
        for host_name, problems in per_host.items():
            errors.extend(f"{sid}@{host_name}: frontmatter {problem}" for problem in problems)

    for w in warnings:
        print(f"WARN: {w}")
    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
    hosts_checked = len(next(iter(matrix.values()), {}))
    print(f"OK: compatibility ({len(registry['skills'])} skills; frontmatter checked against {hosts_checked} host profiles)")


if __name__ == "__main__":
    main()
