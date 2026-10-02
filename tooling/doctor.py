#!/usr/bin/env python3
"""Read-only installation diagnostics. A local directory is not proof of session discovery."""
from __future__ import annotations
import argparse
import datetime as dt
import zipfile
import json
import shutil
import sys
from pathlib import Path
from package_skill import ROOT, MANIFEST, digest, identifier, inspect_archive, safe_path, payload


def inspect(root: Path, skill: str, installed_root: Path | None = None, session_inventory: dict | None = None) -> dict:
    identifier(skill)
    registry = json.loads((root / "registry/skills.json").read_text())
    entry = next((s for s in registry["skills"] if s["id"] == skill), None)
    result = {"schema":"cometweb.skill-doctor/v1", "skill":skill,
              "registry_version": entry.get("version") if entry else None,
              "source":"missing", "package":"missing", "installed":"not_checked",
              "host_discovery":"unknown", "session_visibility":"unknown", "tools":"unknown",
              "runtime_acceptance":"not_assessed", "issues":[]}
    # An unknown or deleted skill must not come back as a clean bill of health.
    if entry is None:
        result["issues"].append("not_in_registry")
    source = safe_path(root, f"skills/{skill}")
    if (source / "SKILL.md").is_file() and (source / "VERSION").is_file():
        result["source"] = "present"
        result["source_version"] = (source / "VERSION").read_text().strip()
        if entry is not None and result["source_version"] != result["registry_version"]:
            result["issues"].append("registry_source_version_mismatch")
    else:
        result["issues"].append("source_missing")
    archive = safe_path(root, f"dist/{skill}/skill.zip")
    manifest = None
    if archive.is_file():
        try:
            manifest = inspect_archive(archive.read_bytes())
            if manifest["skill"] != skill:
                raise ValueError("wrong package identity")
            result.update(package="verified_structurally", package_version=manifest["version"], package_sha256=digest(archive.read_bytes()))
            if result.get("source_version") != manifest["version"]:
                result["issues"].append("source_package_version_mismatch")
        except (ValueError, KeyError, OSError, json.JSONDecodeError, zipfile.BadZipFile):
            manifest = None
            result["package"] = "invalid"
            result["issues"].append("invalid_package")
    if manifest and result["source"] == "present":
        try:
            _, current = payload(root, skill)
            if current["payload_sha256"] != manifest["payload_sha256"]:
                result["issues"].append("source_package_content_mismatch")
        except (ValueError, OSError, KeyError):
            result["issues"].append("source_not_packageable")
    if installed_root is not None:
        path = safe_path(installed_root, skill)
        result["installed"] = "present_unverified" if (path / "SKILL.md").is_file() else "missing"
        if result["installed"] == "missing":
            result["issues"].append("not_installed")
        else:
            if (path / "VERSION").is_file():
                result["installed_version"] = (path / "VERSION").read_text().strip()
            if manifest:
                expected = manifest["files"]
                from public_safety import files
                actual = {p.relative_to(path).as_posix():digest(p.read_bytes()) for p in files(path) if p.relative_to(path).as_posix() != MANIFEST}
                result["installed"] = "matches_package" if actual == expected else "drifted"
                if actual != expected:
                    result["issues"].append("installed_content_mismatch")
    # A supplied export remains a report, not an independently authenticated runtime observation.
    if session_inventory is not None:
        if not isinstance(session_inventory, dict):
            raise ValueError("session inventory must be a JSON object")
        if session_inventory.get("schema") != "cometweb.session-inventory/v1" or not session_inventory.get("observed_at") or not session_inventory.get("session_id") or not session_inventory.get("host"):
            raise ValueError("session inventory requires schema, host, session_id and observed_at")
        if not isinstance(session_inventory["observed_at"], str):
            raise ValueError("session observed_at must be an ISO 8601 timestamp string")
        try:
            observed = dt.datetime.fromisoformat(session_inventory["observed_at"].replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("session observed_at must be an ISO 8601 timestamp") from exc
        if observed.tzinfo is None or observed > dt.datetime.now(dt.timezone.utc):
            raise ValueError("session observation must be timezone-aware and not in the future")
        if not isinstance(session_inventory.get("skills"), list) or any(not isinstance(x, str) for x in session_inventory["skills"]):
            raise ValueError("session skills must be an explicit list of identifiers")
        result["session_visibility"] = "reported_visible" if skill in session_inventory.get("skills", []) else "reported_absent"
        result["session_evidence"] = {k:session_inventory[k] for k in ("host","session_id","observed_at")}
        result["host_discovery"] = "reported_by_inventory"
        if isinstance(session_inventory.get("tools"), list):
            result["tools"] = "reported_inventory_available"
    result["local_executables"] = {name: bool(shutil.which(name)) for name in ("python3", "git", "codex", "claude")}
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--installed-root", type=Path)
    parser.add_argument("--session-inventory", type=Path)
    args = parser.parse_args(argv)
    try:
        inventory = json.loads(args.session_inventory.read_text(encoding="utf-8")) if args.session_inventory else None
        result = inspect(args.root, args.skill, args.installed_root, inventory)
    except (OSError, ValueError) as exc:  # ValueError covers malformed JSON too
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(bool(result["issues"]))


if __name__ == "__main__":
    raise SystemExit(main())
