"""Opt-in, integrity-checked doctrine attachment; never execute vendor code."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROLE_IDS = {"product_customer", "offer_pricing", "sales"}
SCHEMA = "cometweb.capability-packs/pilot-v1"


def _file(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("pack path must be relative")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("pack file missing or outside root")
    return path


def load_registry(root: Path, registry_path: str = "registry/capability-packs.json") -> dict:
    registry = json.loads(_file(root, registry_path).read_text())
    if not isinstance(registry, dict) or registry.get("schema") != SCHEMA:
        raise ValueError("invalid capability registry")
    if registry.get("status") != "LOCAL_PILOT":
        raise ValueError("experimental registry status required")
    packs = registry.get("packs")
    if not isinstance(packs, list) or not packs:
        raise ValueError("empty capability registry")
    seen = set()
    for pack in packs:
        if not isinstance(pack, dict) or not isinstance(pack.get("id"), str) or not pack["id"]:
            raise ValueError("invalid pack id")
        if pack["id"] in seen:
            raise ValueError("duplicate pack id")
        seen.add(pack["id"])
        if pack.get("role_id") not in ROLE_IDS or pack.get("license") != "MIT":
            raise ValueError("unsupported role or license in pilot")
        if not re.fullmatch(r"[0-9a-f]{40}", str(pack.get("source_commit", ""))):
            raise ValueError("source commit must be pinned")
        patterns = pack.get("match_any")
        if not isinstance(patterns, list) or not patterns:
            raise ValueError("pack needs routing patterns")
        for pattern in patterns:
            if not isinstance(pattern, str) or not pattern:
                raise ValueError("invalid routing pattern")
            re.compile(pattern)
        inventory = pack.get("files")
        if not isinstance(inventory, dict) or not inventory:
            raise ValueError("missing pack inventory")
        if pack.get("entrypoint") not in inventory or pack.get("license_file") not in inventory:
            raise ValueError("entrypoint and license must be locked")
        for relative, digest in inventory.items():
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ValueError("invalid file digest")
            if hashlib.sha256(_file(root, relative).read_bytes()).hexdigest() != digest:
                raise ValueError(f"pack integrity mismatch: {relative}")
    return registry


def select(root: Path, goal: str, role_ids: list[str] | None = None) -> list[dict]:
    if not isinstance(goal, str) or not goal.strip():
        raise ValueError("goal must be nonempty text")
    if role_ids is not None and (not isinstance(role_ids, list) or any(not isinstance(role, str) for role in role_ids)):
        raise ValueError("role_ids must be a list of strings")
    registry = load_registry(root)
    result = []; assigned = set()
    for pack in registry["packs"]:
        role = pack["role_id"]
        if role_ids is not None and role not in role_ids:
            continue
        if role in assigned or not any(re.search(pattern, goal, re.I) for pattern in pack["match_any"]):
            continue
        assigned.add(role)
        result.append({key: pack[key] for key in ("id", "role_id", "entrypoint", "source_repository", "source_commit", "license", "license_file", "claim_class")})
    return result
