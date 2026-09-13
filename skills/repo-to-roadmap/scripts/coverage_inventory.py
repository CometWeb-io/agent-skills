#!/usr/bin/env python3
"""Pinned Git file accounting. Inventory is not proof of review or runtime behavior.

Only built-in, read-only Git commands are used; no checkout, hook, filter, fetch,
model invocation or remote write is performed. JSON output never includes source
file contents. A supplied ledger remains an unauthenticated record of review.
"""
from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
from typing import Any

VERSION = "1.0.0"
MAX_BYTES = 32 * 1024 * 1024
MAX_ENTRIES = 100_000
MODES = {"040000": "tree", "100644": "blob", "100755": "blob", "120000": "blob", "160000": "commit"}
STATES = {"INSPECTED", "EXCLUDED_GENERATED", "EXCLUDED_VENDOR", "BINARY_UNREADABLE", "UNAVAILABLE"}


class InventoryError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InventoryError(message)


def fields(value: Any, required: set[str], optional: set[str] = frozenset()) -> None:
    require(isinstance(value, dict), "expected an object")
    require(required <= value.keys() <= required | optional, "missing or unexpected fields")


def text(value: Any, limit: int = 4000) -> str:
    require(isinstance(value, str) and 0 < len(value.strip()) <= limit, "expected bounded nonempty text")
    return value


def canonical(value: Any) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise InventoryError("not finite UTF-8 JSON") from exc


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def pairs(rows):
    result = {}
    for key, value in rows:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def loads(blob: bytes) -> Any:
    require(len(blob) <= MAX_BYTES, "JSON exceeds byte limit")
    def invalid(_):
        raise InventoryError("non-finite JSON number")
    try:
        value = json.loads(blob, object_pairs_hook=pairs, parse_constant=invalid)
        canonical(value)
        return value
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise InventoryError("invalid JSON") from exc


def read_json(path: Path) -> Any:
    require(not path.is_symlink() and stat.S_ISREG(path.stat().st_mode), "input must be a regular non-symlink file")
    with path.open("rb") as handle:
        return loads(handle.read(MAX_BYTES + 1))


def timestamp(value: Any) -> dt.datetime:
    text(value, 64)
    require("T" in value, "timestamp requires time and timezone")
    try:
        result = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InventoryError("invalid timestamp") from exc
    require(result.tzinfo is not None, "timestamp requires timezone")
    return result.astimezone(dt.timezone.utc)


def oid(value: Any, algorithm: str) -> str:
    require(isinstance(algorithm, str), "unsupported object format")
    length = {"sha1": 40, "sha256": 64}.get(algorithm)
    require(length is not None and isinstance(value, str) and re.fullmatch(r"[0-9a-f]{%d}" % length, value) is not None,
            "invalid full object identity")
    return value


def repo_id(value: Any) -> str:
    text(value, 256)
    require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value) is not None, "repository must be owner/name")
    return value


def path_name(value: Any) -> str:
    text(value, 4096)
    # Paths are Git names, not host filesystem paths. Tabs/newlines/backslashes are
    # valid Git names and remain JSON-escaped. They are NEVER opened on disk here.
    require("\0" not in value and all(part not in {"", ".", "..", ".git"} for part in value.split("/")), "invalid Git path")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise InventoryError("non-UTF-8 Git path") from exc
    require(len(value.split("/")) <= 128, "path exceeds depth limit")
    return value


def verify_tree(entries: Any, expected_tree: str, algorithm: str) -> list[dict]:
    """Rebuild every Git tree object from its exact immediate children.

    Both directory and leaf entries must be present (ls-tree -rtz or a complete
    recursive GitHub tree). An omitted file, empty tree or whole subtree changes
    the object hash. SHA integrity does not authenticate the supplied anchor.
    """
    oid(expected_tree, algorithm)
    require(isinstance(entries, list) and len(entries) <= MAX_ENTRIES, "invalid tree entries")
    indexed, children = {}, {"": []}
    for row in entries:
        fields(row, {"path", "mode", "type", "sha"})
        name = path_name(row["path"])
        require(name not in indexed, "duplicate Git path")
        require(isinstance(row["mode"], str) and MODES.get(row["mode"]) == row["type"], "invalid Git object mode/type")
        oid(row["sha"], algorithm)
        indexed[name] = row
        if row["type"] == "tree":
            children[name] = []
    for name, row in indexed.items():
        parent, _, basename = name.rpartition("/")
        require(parent in children, "missing parent tree")
        children[parent].append((basename, row))
    calculated = {}
    for directory in sorted(children, key=lambda p: (p.count("/") + bool(p), p), reverse=True):
        body = bytearray()
        for basename, row in sorted(children[directory], key=lambda x: x[0].encode() + (b"/" if x[1]["type"] == "tree" else b"\0")):
            child_oid = calculated[row["path"]] if row["type"] == "tree" else row["sha"]
            if row["type"] == "tree":
                require(child_oid == row["sha"], "subtree identity mismatch: incomplete or modified inventory")
            body.extend(row["mode"].lstrip("0").encode() + b" " + basename.encode() + b"\0" + bytes.fromhex(child_oid))
        calculated[directory] = hashlib.new(algorithm, b"tree " + str(len(body)).encode() + b"\0" + body).hexdigest()
    require(calculated[""] == expected_tree, "root tree identity mismatch: incomplete or modified inventory")
    return [dict(indexed[name]) for name in sorted(indexed)]


def make_inventory(entries: list[dict], *, repository: str, commit: str, tree: str,
                   algorithm: str = "sha1", binding: str = "asserted_connector_pin", observed_at: str | None = None) -> dict:
    now = observed_at or dt.datetime.now(dt.timezone.utc).isoformat()
    require(timestamp(now) <= dt.datetime.now(dt.timezone.utc), "inventory timestamp is in the future")
    require(binding in {"local_git_object", "asserted_connector_pin"}, "unknown commit binding")
    data = {"schema": "cometweb.file-inventory/v1", "repository": repo_id(repository),
            "commit_sha": oid(commit, algorithm), "tree_sha": oid(tree, algorithm), "object_format": algorithm,
            "scope": "entire_commit_tree", "commit_binding": binding, "observed_at": now,
            "entries": verify_tree(entries, tree, algorithm)}
    data["inventory_sha256"] = digest(data)
    return data


def validate_inventory(data: Any, expected: str | None = None) -> dict:
    keys = {"schema", "repository", "commit_sha", "tree_sha", "object_format", "scope", "commit_binding", "observed_at", "entries", "inventory_sha256"}
    fields(data, keys)
    require(data["schema"] == "cometweb.file-inventory/v1" and data["scope"] == "entire_commit_tree", "unsupported inventory")
    clean = make_inventory(data["entries"], repository=data["repository"], commit=data["commit_sha"], tree=data["tree_sha"],
                           algorithm=data["object_format"], binding=data["commit_binding"], observed_at=data["observed_at"])
    require(canonical(clean) == canonical(data), "inventory is not canonical or fingerprint mismatched")
    if expected is not None:
        require(isinstance(expected, str) and re.fullmatch(r"[0-9a-f]{64}", expected) is not None and data["inventory_sha256"] == expected,
                "inventory does not match independently supplied pin")
    return clean


def from_github(data: Any, *, repository: str, commit: str, expected_tree: str) -> dict:
    require(isinstance(data, dict) and data.get("truncated") is False and isinstance(data.get("tree"), list), "complete non-truncated recursive GitHub tree required")
    require(data.get("sha") == expected_tree, "GitHub tree differs from expected pin")
    rows = []
    for row in data["tree"]:
        require(isinstance(row, dict), "invalid GitHub tree entry")
        try:
            rows.append({k: row[k] for k in ("path", "mode", "type", "sha")})
        except KeyError as exc:
            raise InventoryError("missing GitHub tree fields") from exc
    return make_inventory(rows, repository=repository, commit=commit, tree=expected_tree)


def git_read(repo: Path, *args: str) -> bytes:
    require(repo.is_dir() and not repo.is_symlink(), "repository directory is unavailable or a symlink")
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_NO_LAZY_FETCH="1",
               GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0", GIT_NO_REPLACE_OBJECTS="1")
    command = ["git", "--no-pager", "--no-replace-objects", "-C", str(repo), "-c", "core.fsmonitor=false",
               "-c", "core.hooksPath=" + os.devnull, "-c", "protocol.allow=never", *args]
    # Limit the bytes read into memory; timeout bounds a missing/corrupt repository.
    with tempfile.TemporaryFile() as output:
        try:
            proc = subprocess.run(command, env=env, stdout=output, stderr=subprocess.DEVNULL, timeout=60, check=False)
        except (OSError, subprocess.SubprocessError) as exc:
            raise InventoryError("Git inventory command unavailable or timed out") from exc
        require(proc.returncode == 0, "Git inventory command failed; no successful inventory")
        require(output.tell() <= MAX_BYTES, "Git output exceeds inventory budget")
        output.seek(0)
        return output.read(MAX_BYTES + 1)


def from_git(repo: Path, repository: str, commit: str) -> dict:
    repo_id(repository)
    algorithm = git_read(repo, "rev-parse", "--show-object-format").decode().strip()
    oid(commit, algorithm)
    require(git_read(repo, "cat-file", "-t", commit).strip() == b"commit", "pin must name a full commit object, not a tag/tree")
    tree = git_read(repo, "rev-parse", "--verify", commit + "^{tree}").decode().strip()
    rows = []
    raw = git_read(repo, "ls-tree", "-rtz", "--full-tree", commit)
    require(not raw or raw.endswith(b"\0"), "truncated Git output")
    try:
        for row in raw.split(b"\0"):
            if not row:
                continue
            metadata, name = row.split(b"\t", 1)
            mode, kind, sha = metadata.decode("ascii").split()
            rows.append({"path": name.decode("utf-8"), "mode": mode, "type": kind, "sha": sha})
    except (UnicodeError, ValueError) as exc:
        raise InventoryError("unsupported Git tree encoding") from exc
    return make_inventory(rows, repository=repository, commit=commit, tree=tree, algorithm=algorithm, binding="local_git_object")


def review_template(inventory: dict) -> dict:
    inv = validate_inventory(inventory)
    return {"schema": "cometweb.file-review/v1", "inventory_sha256": inv["inventory_sha256"],
            "rows": [{"path": r["path"], "sha": r["sha"], "status": "UNAVAILABLE", "reason": "Review not performed"}
                     for r in inv["entries"] if r["type"] != "tree"]}


def audit(inventory: dict, ledger: Any, *, expected: str | None = None) -> dict:
    inv = validate_inventory(inventory, expected)
    fields(ledger, {"schema", "inventory_sha256", "rows"})
    require(ledger["schema"] == "cometweb.file-review/v1" and ledger["inventory_sha256"] == inv["inventory_sha256"], "ledger is for a different inventory")
    require(isinstance(ledger["rows"], list) and len(ledger["rows"]) <= MAX_ENTRIES, "invalid review rows")
    leaves = {r["path"]: r for r in inv["entries"] if r["type"] != "tree"}
    seen, counts = set(), Counter()
    excluded, blocked = [], []
    for row in ledger["rows"]:
        fields(row, {"path", "sha", "status"}, {"reason", "reviewer", "reviewed_at", "evidence_ref", "summary", "scope_basis"})
        name = path_name(row["path"])
        require(name in leaves and name not in seen, "unknown, duplicate or directory review row")
        require(row["sha"] == leaves[name]["sha"], "review refers to different file bytes")
        state = row["status"]
        require(isinstance(state, str) and state in STATES, "invalid review status")
        if leaves[name]["type"] == "commit":
            require(state == "UNAVAILABLE", "submodule requires its own pinned inventory; it cannot be marked reviewed/excluded here")
        if state == "INSPECTED":
            for key in ("reviewer", "evidence_ref", "summary"):
                text(row.get(key))
            require(timestamp(row.get("reviewed_at")) <= dt.datetime.now(dt.timezone.utc), "review timestamp is in the future")
        elif state.startswith("EXCLUDED_"):
            for key in ("reason", "scope_basis", "evidence_ref"):
                text(row.get(key))
            excluded.append(name)
        else:
            text(row.get("reason"))
            blocked.append(name)
        seen.add(name)
        counts[state] += 1
    missing = sorted(leaves.keys() - seen)
    result = ("EMPTY_SCOPE" if not leaves else "EXHAUSTIVE_NOT_PROVEN" if missing or blocked else
              "ACCOUNTED_WITH_EXCLUSIONS" if excluded else "INSPECTION_RECORDS_COMPLETE")
    return {"schema": "cometweb.file-coverage-result/v1", "result": result,
            "repository": inv["repository"], "commit_sha": inv["commit_sha"], "tree_sha": inv["tree_sha"],
            "inventory_sha256": inv["inventory_sha256"], "ledger_sha256": digest(ledger),
            "anchor": "matched_external_pin" if expected is not None else "self_consistency_only",
            "commit_binding": inv["commit_binding"], "repository_identity": "caller_supplied_label",
            "source_authentication": "not_performed",
            "file_count": len(leaves), "accounted_count": len(seen), "counts": dict(sorted(counts.items())),
            "unaccounted_paths": missing, "blocked_paths": sorted(blocked), "excluded_paths": sorted(excluded),
            "submodule_paths": sorted(n for n, r in leaves.items() if r["type"] == "commit"),
            "symlink_paths": sorted(n for n, r in leaves.items() if r["mode"] == "120000"),
            "review_authentication": "not_performed", "runtime_verification": "not_performed",
            "note": "Complete inspection records do not prove review quality, source authority, runtime behavior or release readiness. Symlink targets are not followed."}


def delta(before: dict, after: dict) -> dict:
    a, b = validate_inventory(before), validate_inventory(after)
    require(a["repository"] == b["repository"] and a["object_format"] == b["object_format"], "inventories are not comparable")
    maps = [{r["path"]: r for r in inv["entries"] if r["type"] != "tree"} for inv in (a, b)]
    old, new = maps
    changed = sorted(n for n in old.keys() & new.keys() if old[n] != new[n])
    return {"schema": "cometweb.file-inventory-delta/v1", "repository": a["repository"],
            "before_inventory_sha256": a["inventory_sha256"], "after_inventory_sha256": b["inventory_sha256"],
            "added_paths": sorted(new.keys() - old.keys()), "removed_paths": sorted(old.keys() - new.keys()),
            "modified_paths": changed, "unchanged_content_paths": sorted(n for n in old.keys() & new.keys() if old[n] == new[n]),
            "review_required_paths": sorted((new.keys() - old.keys()) | set(changed)),
            "note": "Renames are not inferred. Unchanged bytes are not proof of unchanged behavior; dependency and claim revalidation remains required."}


def output_json(value: Any, path: Path | None) -> None:
    data = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False).encode() + b"\n"
    if path is None:
        sys.stdout.buffer.write(data)
    else:
        # Exclusive creation. No mkdir, existing-file replacement or implicit input overwrite.
        require(not any(p.is_symlink() for p in [path, *path.parents]), "output path contains a symlink")
        with path.open("xb") as handle:
            handle.write(data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    collect = commands.add_parser("inventory")
    collect.add_argument("--repo", type=Path, required=True)
    collect.add_argument("--repository", required=True)
    collect.add_argument("--commit", required=True)
    imp = commands.add_parser("import-tree")
    imp.add_argument("--tree", type=Path, required=True)
    imp.add_argument("--repository", required=True)
    imp.add_argument("--commit", required=True)
    imp.add_argument("--expected-tree", required=True)
    for name in ("template", "audit"):
        sub = commands.add_parser(name)
        sub.add_argument("--inventory", type=Path, required=True)
        if name == "audit":
            sub.add_argument("--ledger", type=Path, required=True)
            sub.add_argument("--expected-inventory-sha256")
            sub.add_argument("--require-inspected", action="store_true")
    diff = commands.add_parser("delta")
    diff.add_argument("--before", type=Path, required=True)
    diff.add_argument("--after", type=Path, required=True)
    for sub in (collect, imp, *[commands.choices[n] for n in ("template", "audit", "delta")]):
        sub.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "inventory":
            result = from_git(args.repo, args.repository, args.commit)
        elif args.command == "import-tree":
            result = from_github(read_json(args.tree), repository=args.repository, commit=args.commit, expected_tree=args.expected_tree)
        elif args.command == "template":
            result = review_template(read_json(args.inventory))
        elif args.command == "audit":
            result = audit(read_json(args.inventory), read_json(args.ledger), expected=args.expected_inventory_sha256)
        else:
            result = delta(read_json(args.before), read_json(args.after))
        output_json(result, args.output)
        if args.command == "audit":
            acceptable = {"INSPECTION_RECORDS_COMPLETE"} if args.require_inspected else {"INSPECTION_RECORDS_COMPLETE", "ACCOUNTED_WITH_EXCLUSIONS"}
            return 0 if result["result"] in acceptable else 1
        return 0
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        # Never echo arbitrary input, filenames or embedded secrets into error logs.
        print('{"status":"invalid","coverage":"not_assessed"}', file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
