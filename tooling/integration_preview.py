#!/usr/bin/env python3
"""Create a local, conflict-aware candidate without modifying a source checkout.

Reads two pinned Git trees; merges overlay changes into HEAD in a NEW directory.
No fetch, checkout, commit, push, hooks, install, test or repository script execution.
Hashes bind bytes, not authorship. A conflict-free merge is NOT semantic validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import stat
import subprocess
import tempfile
import unicodedata
from pathlib import Path, PurePosixPath

MAX_FILE = 16 * 1024 * 1024
MAX_TOTAL = 128 * 1024 * 1024
MAX_ENTRIES = 20000
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
RETIRED = {"ai-antipattern-writing", "ai-anti-pattern", "ai-anti-pattern-writing"}


def require(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError(why)


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def unique(items):
    result = {}
    for key, value in items:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def path_name(name: str) -> str:
    require(isinstance(name, str) and 0 < len(name) <= 1024, "invalid relative filename")
    require(
        not PurePosixPath(name).is_absolute()
        and "\\" not in name
        and ":" not in name
        and not any(ord(c) < 32 for c in name),
        "nonportable filename",
    )
    parts = name.split("/")
    require(all(p not in {"", ".", ".."} and p.casefold() != ".git" for p in parts), "unsafe path")
    require(not any(p.endswith((" ", ".")) for p in parts), "nonportable trailing dot or space")
    return name


def real_path(path: Path) -> Path:
    from core.paths import canonical_input

    return canonical_input(path)


def read_regular(path: Path) -> bytes:
    path = real_path(path)
    require(path.is_file() and stat.S_ISREG(path.stat().st_mode), "missing or special file")
    require(path.stat().st_size <= MAX_FILE, "file exceeds size budget")
    with path.open("rb") as stream:
        blob = stream.read(MAX_FILE + 1)
    require(len(blob) <= MAX_FILE, "file grew beyond size budget")
    return blob


def git_env() -> dict:
    from core.git import git_env as hardened_git_env

    return hardened_git_env()


def git(root: Path, *args: str, check: bool = True) -> bytes:
    from core.git import read_git

    return read_git(root, *args, timeout=60, check=check).stdout


def object_format(root: Path) -> str:
    value = git(root, "rev-parse", "--show-object-format").decode().strip()
    require(value in {"sha1", "sha256"}, f"unsupported Git object format: {value}")
    return value


def validate_oid(value: str, algorithm: str) -> None:
    length = {"sha1": 40, "sha256": 64}[algorithm]
    require(bool(re.fullmatch(rf"[0-9a-f]{{{length}}}", value)), "invalid Git object ID")


def blob_oid(blob: bytes, algorithm: str) -> str:
    hasher = hashlib.new(algorithm)
    hasher.update(f"blob {len(blob)}\0".encode())
    hasher.update(blob)
    return hasher.hexdigest()


def tree(root: Path, revision: str, algorithm: str) -> dict:
    validate_oid(revision, algorithm)
    rows = git(root, "ls-tree", "-r", "-z", "-l", "--full-tree", revision).split(b"\0")
    require(len(rows) - 1 <= MAX_ENTRIES, "tree has too many files")
    output, names, total = {}, set(), 0
    for row in rows:
        if not row:
            continue
        header, raw_name = row.split(b"\t", 1)
        mode, kind, oid, size = header.decode("ascii").split()
        name = path_name(raw_name.decode("utf-8"))
        folded = unicodedata.normalize("NFC", name).casefold()
        require(folded not in names, "case/Unicode-normalized tree path collision")
        names.add(folded)
        require(
            kind == "blob" and mode in {"100644", "100755"},
            "symlinks/submodules/special Git entries require manual integration",
        )
        validate_oid(oid, algorithm)
        length = int(size)
        require(0 <= length <= MAX_FILE, "Git blob exceeds file budget")
        total += length
        require(total <= MAX_TOTAL, "Git tree exceeds byte budget")
        output[name] = {"oid": oid, "size": length, "mode": mode}
    return output


def blobs(root: Path, entries: dict, algorithm: str) -> dict[str, bytes]:
    wanted = {meta["oid"]: meta["size"] for meta in entries.values()}
    if not wanted:
        return {}
    proc = subprocess.run(
        ["git", "-C", str(root), "cat-file", "--batch"],
        input=("\n".join(wanted) + "\n").encode(),
        env=git_env(),
        capture_output=True,
        check=True,
        timeout=60,
    )
    raw, offset, by_oid = proc.stdout, 0, {}
    require(len(raw) <= MAX_TOTAL + MAX_ENTRIES * 100, "batch output exceeds budget")
    for oid, size in wanted.items():
        end = raw.find(b"\n", offset)
        require(end >= offset, "truncated Git batch header")
        require(raw[offset:end].decode() == f"{oid} blob {size}", "Git batch header mismatch")
        value = raw[end + 1 : end + 1 + size]
        require(raw[end + 1 + size : end + 2 + size] == b"\n", "truncated Git blob")
        require(blob_oid(value, algorithm) == oid, "Git object bytes do not match their ID")
        by_oid[oid] = value
        offset = end + 2 + size
    require(offset == len(raw), "unexpected extra Git batch output")
    return {name: by_oid[meta["oid"]] for name, meta in entries.items()}


def overlay_files(
    overlay: Path,
    manifest_path: Path,
    algorithm: str,
    expected_hash: str | None = None,
) -> tuple[dict, dict]:
    raw = read_regular(manifest_path)
    if expected_hash is not None:
        require(bool(HEX64.fullmatch(expected_hash)) and digest(raw) == expected_hash, "overlay manifest pin mismatch")
    manifest = json.loads(raw, object_pairs_hook=unique)
    require(isinstance(manifest, dict) and manifest.get("schema") == "cometweb.overlay/v1", "unknown overlay manifest")
    validate_oid(str(manifest.get("canonical_base", "")), algorithm)
    expected = manifest.get("files")
    require(isinstance(expected, dict) and 0 < len(expected) <= 4096, "empty/oversized overlay manifest")
    real_path(overlay)
    output, total, normalized = {}, 0, set()
    for name, sha in expected.items():
        path_name(name)
        folded = unicodedata.normalize("NFC", name).casefold()
        require(folded not in normalized, "overlay path collision")
        normalized.add(folded)
        require(isinstance(sha, str) and bool(HEX64.fullmatch(sha)), "invalid file hash")
        value = read_regular(overlay / name)
        require(digest(value) == sha, "overlay file does not match manifest")
        total += len(value)
        require(total <= MAX_TOTAL, "overlay exceeds byte budget")
        output[name] = value
    return manifest, output


def merge_file(current: bytes, base: bytes, incoming: bytes) -> tuple[str, bytes | None]:
    if current == incoming:
        return "already_present", current
    if current == base:
        return "replace_unchanged_base", incoming
    if incoming == base:
        return "preserve_newer_head", current
    try:
        for value in (current, base, incoming):
            require(b"\0" not in value, "binary")
            value.decode("utf-8")
    except (ValueError, UnicodeError):
        return "conflict_binary", None
    with tempfile.TemporaryDirectory(prefix="cw-three-way-") as tmp:
        paths = [Path(tmp) / name for name in ("current", "base", "incoming")]
        for path, value in zip(paths, (current, base, incoming), strict=True):
            path.write_bytes(value)
        proc = subprocess.run(
            [
                "git",
                "merge-file",
                "-p",
                "--diff3",
                "-L",
                "current",
                "-L",
                "base",
                "-L",
                "overlay",
                *map(str, paths),
            ],
            cwd=tmp,
            env=git_env(),
            capture_output=True,
            timeout=30,
        )
        if proc.returncode == 0:
            require(len(proc.stdout) <= MAX_FILE, "merged file exceeds budget")
            return "merged_text_review_required", proc.stdout
        if 1 <= proc.returncode <= 127:
            return "conflict_text", None
        raise ValueError("three-way merge could not complete")


def working_tree_clean(checkout: Path, head_tree: dict, algorithm: str) -> None:
    """Reject working-tree drift using filter-free object hashes (not `git diff`).

    Clean/smudge filters and local hook config must not make a byte-identical
    tree look dirty, and must not execute during the check.
    """
    names = sorted(head_tree)
    for name in names:
        path = checkout / name
        if not path.is_file():
            raise ValueError("tracked working-tree changes require separate review; no files exported")
        if bool(path.stat().st_mode & 0o111) != (head_tree[name]["mode"] == "100755"):
            raise ValueError("tracked working-tree changes require separate review; no files exported")
    if not names:
        return
    proc = subprocess.run(
        ["git", "-C", str(checkout), "hash-object", "--no-filters", "--stdin-paths"],
        input=("\n".join(names) + "\n").encode(),
        env=git_env(),
        capture_output=True,
        check=True,
        timeout=60,
    )
    oids = proc.stdout.decode().splitlines()
    require(len(oids) == len(names), "hash-object path count mismatch")
    for name, oid in zip(names, oids, strict=True):
        validate_oid(oid, algorithm)
        if oid != head_tree[name]["oid"]:
            raise ValueError("tracked working-tree changes require separate review; no files exported")


def preview(
    checkout: Path,
    overlay: Path,
    manifest_path: Path,
    output: Path,
    *,
    include_workflows: bool = False,
    expected_manifest_sha256: str | None = None,
) -> dict:
    from core.paths import canonical_output

    checkout, overlay = map(real_path, (checkout, overlay))
    output = canonical_output(output)
    require(checkout.is_dir() and overlay.is_dir(), "checkout and overlay must be directories")
    require(not output.exists() and output.parent.is_dir(), "output must be a new directory with an existing parent")
    for source in (checkout, overlay):
        require(
            not output.is_relative_to(source) and not source.is_relative_to(output),
            "output must not overlap source directories",
        )
    root = Path(git(checkout, "rev-parse", "--show-toplevel").decode().strip()).absolute()
    require(root == checkout, "checkout must be the Git root")
    algorithm = object_format(checkout)
    manifest, incoming = overlay_files(overlay, manifest_path, algorithm, expected_manifest_sha256)
    base_sha = manifest["canonical_base"]
    head = git(checkout, "rev-parse", "HEAD").decode().strip()
    validate_oid(head, algorithm)
    git(checkout, "merge-base", "--is-ancestor", base_sha, head)
    base_tree, head_tree = tree(checkout, base_sha, algorithm), tree(checkout, head, algorithm)
    working_tree_clean(checkout, head_tree, algorithm)
    affected = set(incoming)
    base = blobs(checkout, {n: meta for n, meta in base_tree.items() if n in affected}, algorithm)
    current = blobs(checkout, {n: meta for n, meta in head_tree.items() if n in affected}, algorithm)
    untracked = git(checkout, "ls-files", "--others", "--exclude-standard", "-z")
    untracked_count = sum(bool(p) for p in untracked.split(b"\0"))
    overrides: dict[str, bytes] = {}
    plan, conflicts, omitted = [], [], []
    for name, value in sorted(incoming.items()):
        if name.startswith(".github/workflows/") and not include_workflows:
            omitted.append(name)
            status = "excluded_workflow_review"
        elif name not in base:
            if name in current and current[name] != value:
                status = "conflict_added_on_both_sides"
                conflicts.append(name)
            else:
                status = "already_present" if name in current else "add"
                if name not in current:
                    overrides[name] = value
        elif name not in current:
            if value == base[name]:
                status = "preserve_upstream_deletion"
            else:
                status = "conflict_deleted_upstream"
                conflicts.append(name)
        else:
            status, merged = merge_file(current[name], base[name], value)
            if merged is None:
                conflicts.append(name)
            else:
                overrides[name] = merged
        plan.append(
            {
                "path": name,
                "status": status,
                "incoming_sha256": digest(value),
                "current_sha256": digest(current[name]) if name in current else None,
            }
        )
    names = set(head_tree) | set(overrides)
    folded = [unicodedata.normalize("NFC", n).casefold() for n in names]
    require(len(folded) == len(set(folded)), "merged tree has a case/Unicode collision")
    folded_names = set(folded)
    for name in names:
        require(
            not any(
                unicodedata.normalize("NFC", str(parent)).casefold() in folded_names
                for parent in PurePosixPath(name).parents
                if str(parent) != "."
            ),
            "merged tree has file/directory collision",
        )
        parts = PurePosixPath(name).parts
        require(
            not (len(parts) > 1 and parts[0] == "skills" and parts[1] in RETIRED),
            "retired skill is present; manual reconciliation required",
        )
    require(git(checkout, "rev-parse", "HEAD").decode().strip() == head, "HEAD changed during preview")
    result = {
        "schema": "cometweb.integration-preview/v1",
        "base_revision": base_sha,
        "head_revision": head,
        "object_format": algorithm,
        "status": "conflicts" if conflicts else "prepared_with_workflow_exclusions" if omitted else "prepared",
        "manifest_pin": "matched" if expected_manifest_sha256 else "not_requested",
        "conflicts": conflicts,
        "excluded_workflows": omitted,
        "untracked_files_not_exported": untracked_count,
        "plan": plan,
        "source_checkout_modified": False,
        "remote_write_attempted": False,
        "source_authentication": "not_performed",
        "semantic_validation": "not_run",
        "visibility": "local_private_export",
        "snapshot_basis": "pinned_HEAD_not_untracked_work",
        "source_revision_in_export": "recorded_in_preview_not_a_git_checkout",
        "full_repository_tests": "not_run",
        "model_calls": 0,
    }
    output.mkdir(mode=0o700)
    try:
        if not conflicts:
            target = output / "candidate"
            target.mkdir()
            total = 0
            file_digests = {}
            for name in sorted(names):
                if name in overrides:
                    value = overrides[name]
                else:
                    value = read_regular(checkout / name)
                total += len(value)
                require(total <= MAX_TOTAL, "candidate exceeds total budget")
                path = target / name
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("xb") as stream:
                    stream.write(value)
                mode_meta = head_tree.get(name) or {"mode": "100644"}
                path.chmod(0o755 if mode_meta.get("mode") == "100755" else 0o644)
                file_digests[name] = digest(value)
            (output / "candidate-files.json").write_bytes(canonical(file_digests))
            result["candidate_file_count"] = len(names)
        (output / "preview.json").write_bytes(canonical(result))
    except BaseException:
        shutil.rmtree(output)
        raise
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--overlay", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-manifest-sha256")
    parser.add_argument("--include-workflows", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = preview(
            args.checkout,
            args.overlay,
            args.manifest,
            args.output,
            include_workflows=args.include_workflows,
            expected_manifest_sha256=args.expected_manifest_sha256,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result["status"] == "conflicts" else 0
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError):
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "source_checkout_modified": False,
                    "remote_write_attempted": False,
                    "reason": "preflight_or_preview_failed; inspect inputs and local logs without exposing secrets",
                }
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
