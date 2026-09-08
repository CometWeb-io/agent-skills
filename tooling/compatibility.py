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


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        fail(f"missing YAML frontmatter: {path}")
    block = match.group(1)
    result: dict[str, str] = {}
    key: str | None = None
    buf: list[str] = []
    for line in block.splitlines():
        if line.startswith("  ") and key:
            buf.append(line.strip())
            continue
        if key:
            result[key] = " ".join(buf).strip()
            buf = []
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            if val in (">", ">-", "|"):
                buf = []
            else:
                result[key] = val.strip('"').strip("'")
                key = None
    if key:
        result[key] = " ".join(buf).strip()
    return result


def check_openai_yaml(skill: str, path: Path, profile: dict) -> list[str]:
    warnings: list[str] = []
    if not path.is_file():
        return [f"{skill}: missing {profile['agents_file']}"]
    text = path.read_text(encoding="utf-8")
    data: dict
    if yaml is not None:
        data = yaml.safe_load(text) or {}
    else:
        # Minimal parse without PyYAML
        data = {"interface": {}, "raw": text}
        if "display_name:" in text:
            data["interface"]["display_name"] = True
        if "short_description:" in text:
            data["interface"]["short_description"] = True
        if "default_prompt:" in text:
            data["interface"]["default_prompt"] = True
        if "icon_small:" in text and "assets/" not in text:
            warnings.append(f"{skill}: openai.yaml icons should use ./assets/… paths")
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

        for host_name in entry.get("compatible_hosts", []):
            profile = hosts.get(host_name)
            if not profile:
                errors.append(f"{sid}: unknown host {host_name}")
                continue
            max_len = profile.get("description_max")
            if max_len is not None and len(desc) > max_len:
                errors.append(f"{sid}@{host_name}: description {len(desc)} > {max_len}")

            if host_name in {"openai-codex", "chatgpt"} and "agents_file" in profile:
                warnings.extend(check_openai_yaml(sid, skill_dir / profile["agents_file"], profile))

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
