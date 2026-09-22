#!/usr/bin/env python3
"""Compare two Repo Roaster inventory snapshots without inferring whether changes are good or bad."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SET_FIELDS = (
    "top_level",
    "source_roots",
    "workspace_hints",
    "key_files",
    "manifest_files",
    "lock_files",
    "package_managers",
    "entrypoint_candidates",
    "test_files",
    "workflow_files",
    "migration_files",
    "env_example_files",
    "config_files",
    "infrastructure_files",
    "observability_files",
    "risk_surface_files",
    "auth_surface_files",
    "job_surface_files",
    "data_surface_files",
    "generated_or_vendor_candidates",
    "secretish_file_names",
    "symlinks",
)


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: inventory must be an object")
    return data


def _values(value: Any) -> set[str]:
    return {str(x) for x in value} if isinstance(value, list) else set()


def compare(base: dict[str, Any], head: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for field in SET_FIELDS:
        before = _values(base.get(field))
        after = _values(head.get(field))
        added = sorted(after - before)
        removed = sorted(before - after)
        if added or removed:
            fields[field] = {"added": added, "removed": removed}

    base_lang = {row.get("language"): row for row in base.get("languages", []) if isinstance(row, dict) and row.get("language")}
    head_lang = {row.get("language"): row for row in head.get("languages", []) if isinstance(row, dict) and row.get("language")}
    language_delta = []
    for language in sorted(set(base_lang) | set(head_lang)):
        b = base_lang.get(language, {})
        h = head_lang.get(language, {})
        files_delta = int(h.get("files", 0) or 0) - int(b.get("files", 0) or 0)
        bytes_delta = int(h.get("bytes", 0) or 0) - int(b.get("bytes", 0) or 0)
        if files_delta or bytes_delta:
            language_delta.append({"language": language, "files_delta": files_delta, "bytes_delta": bytes_delta})

    return {
        "base_root": base.get("root"),
        "head_root": head.get("root"),
        "file_count_delta": int(head.get("file_count", 0) or 0) - int(base.get("file_count", 0) or 0),
        "total_bytes_delta": int(head.get("total_bytes", 0) or 0) - int(base.get("total_bytes", 0) or 0),
        "surface_changes": fields,
        "language_delta": language_delta,
        "git_base": base.get("git"),
        "git_head": head.get("git"),
        "note": "Inventory deltas are topology signals, not defects. Re-run evidence/reachability analysis before changing a finding.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=Path)
    parser.add_argument("head", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        out = compare(load(args.base), load(args.head))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    if args.json:
        print(json.dumps(out, indent=2, sort_keys=True))
    else:
        print(f"file_count_delta: {out['file_count_delta']}")
        print(f"total_bytes_delta: {out['total_bytes_delta']}")
        for field, delta in out["surface_changes"].items():
            print(f"{field}: +{len(delta['added'])} -{len(delta['removed'])}")
        print(out["note"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
