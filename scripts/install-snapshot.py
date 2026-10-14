#!/usr/bin/env python3
"""Install one reviewed Git snapshot using the existing host installers."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
HOSTS = {host: f"{host.upper()}_SKILLS_DIR" for host in
         ("cursor", "claude", "codex", "qwen", "qoder", "lingma")}


def exists(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def remove(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif exists(path):
        path.unlink()


def path_arg(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute() or ".." in path.parts:
        raise argparse.ArgumentTypeError("use an absolute path without '..'")
    return path.resolve()


def overlaps(a: Path, b: Path) -> bool:
    return a == b or a in b.parents or b in a.parents


def committed_files(ref: str) -> dict[str, tuple[bytes, int]]:
    actual = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", f"{ref}^{{commit}}"],
                                     text=True).strip()
    if actual != ref:
        raise ValueError("--ref must identify exactly that commit")
    archive = subprocess.check_output(["git", "-C", str(ROOT), "archive", "--format=tar", ref])
    files = {}
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        for entry in source:
            path = Path(entry.name)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("unsafe Git archive path")
            if entry.isdir():
                continue
            if not entry.isfile():
                raise ValueError("snapshot installs require regular files, not archive links")
            files[entry.name] = (source.extractfile(entry).read(), entry.mode & 0o777)
    return files


def manifest(files: dict[str, tuple[bytes, int]]) -> dict:
    return {name: {"sha256": hashlib.sha256(data).hexdigest(), "mode": mode}
            for name, (data, mode) in sorted(files.items())}


def verify(snapshot: Path, expected: dict) -> None:
    if snapshot.is_symlink() or (snapshot / "tree").is_symlink() or (snapshot / "manifest.json").is_symlink():
        raise ValueError("snapshot directories must not be symlinks")
    if not (snapshot / "manifest.json").is_file():
        raise ValueError("snapshot manifest must be a regular file")
    if json.loads((snapshot / "manifest.json").read_text()) != expected:
        raise ValueError("snapshot manifest differs from the requested Git commit")
    actual = {}
    for path in (snapshot / "tree").rglob("*"):
        if path.is_symlink():
            raise ValueError("snapshot contains an unexpected symlink")
        if not path.is_dir() and not path.is_file():
            raise ValueError("snapshot contains an unexpected non-regular file")
        if path.is_file():
            actual[str(path.relative_to(snapshot / "tree"))] = {
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "mode": path.stat().st_mode & 0o7777,
            }
    if actual != expected:
        raise ValueError("snapshot bytes or permissions differ from the requested Git commit")


def materialize(tree: Path, files: dict[str, tuple[bytes, int]]) -> None:
    for name, (data, mode) in files.items():
        path = tree / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        path.chmod(mode)


def install(args: argparse.Namespace) -> None:
    if os.name != "posix":
        raise ValueError("snapshot installation requires POSIX file modes and Bash; use WSL on Windows")
    for a, b in ((args.store, ROOT), (args.target, ROOT), (args.store, args.target)):
        if overlaps(a, b):
            raise ValueError("store, target and source checkout must not overlap")
    if args.rules_target:
        for other in (ROOT, args.store, args.target):
            if overlaps(args.rules_target, other):
                raise ValueError("routing target must not overlap store, skills or source")
    files = committed_files(args.ref)
    expected = manifest(files)
    names = sorted(name.split("/")[1] for name in files
                   if re.fullmatch(r"skills/[^/]+/SKILL\.md", name))
    if not names or any(name not in names for name in args.skill):
        raise ValueError("no skill packages or an unknown --skill")
    selected = sorted(set(args.skill)) if args.skill else names
    script_name = f"scripts/install-{args.host}.sh"
    if script_name not in files:
        raise ValueError("requested commit lacks the host installer")
    if args.host == "cursor" and not args.skill and not args.rules_target:
        raise ValueError("full Cursor installs require --rules-target")
    snapshot = args.store / args.ref
    if exists(snapshot):
        verify(snapshot, expected)
    # No host installer may silently use a real user's backup or routing path.
    env = {**os.environ, HOSTS[args.host]: str(args.target),
           "SKILLS_REPLACE_CONFLICTS": "1" if args.replace_conflicts else "0",
           "CURSOR_RULES_DIR": str(args.rules_target or args.target.parent / "unused-rules")}
    paths = [args.target / name for name in selected]
    stale = []
    if not args.skill and args.target.is_dir():
        for path in args.target.iterdir():
            if path.name in names or not path.is_symlink():
                continue
            linked = Path(os.readlink(path))
            relative = linked.relative_to(args.store) if args.store in linked.parents else None
            if relative and len(relative.parts) == 4 and re.fullmatch(r"[0-9a-f]{40}", relative.parts[0]) \
                    and relative.parts[1:] == ("tree", "skills", path.name):
                stale.append(path)
        if stale and not args.replace_conflicts:
            raise ValueError("retired snapshot links require --replace-conflicts")
    paths.extend(stale)
    if args.host == "cursor" and not args.skill:
        paths.append(args.rules_target / "cometweb-agent-skills.mdc")
    # A scratch archive lets dry-run perform the real host checks without a store write.
    with tempfile.TemporaryDirectory(prefix="agent-skills-preview-") as scratch:
        preview = snapshot / "tree" if exists(snapshot) else Path(scratch) / "tree"
        if not exists(snapshot):
            materialize(preview, files)
        preview_env = {**env, "SKILLS_BACKUP_DIR": str(Path(scratch) / "backups")}
        command = ["bash", str(preview / script_name), "--dry-run"]
        for name in args.skill:
            command.extend(("--skill", name))
        subprocess.run(command, env=preview_env, check=True, capture_output=True, text=True)
    if args.dry_run:
        print(json.dumps({"ref": args.ref, "host": args.host, "skills": selected,
                          "target": str(args.target), "snapshot": str(snapshot),
                          "retired_links": [str(path) for path in stale], "writes": False}, indent=2))
        return
    args.store.mkdir(parents=True, exist_ok=True)
    lock = args.store / ".install-lock"
    lock.mkdir()  # Fail closed if another operation uses this store.
    try:
        if exists(snapshot):
            verify(snapshot, expected)
        else:
            with tempfile.TemporaryDirectory(prefix=".snapshot-", dir=args.store) as scratch:
                staged = Path(scratch) / "snapshot"
                materialize(staged / "tree", files)
                (staged / "manifest.json").write_text(json.dumps(expected, sort_keys=True) + "\n")
                verify(staged, expected)
                staged.rename(snapshot)
        transaction = Path(tempfile.mkdtemp(prefix="transaction-", dir=args.store))
        prior = {}
        for index, path in enumerate(paths):
            if exists(path):
                saved = transaction / str(index)
                if path.is_symlink():
                    saved.symlink_to(os.readlink(path))
                elif path.is_dir():
                    shutil.copytree(path, saved, symlinks=True)
                else:
                    shutil.copy2(path, saved)
                prior[path] = saved
        command = ["bash", str(snapshot / "tree" / script_name)]
        for name in args.skill:
            command.extend(("--skill", name))
        env["SKILLS_BACKUP_DIR"] = str(transaction / "host-backups")
        receipt = {"ref": args.ref, "host": args.host, "skills": selected,
                   "target": str(args.target), "snapshot": str(snapshot),
                   "prior_paths": [str(path) for path in prior],
                   "retired_links": [str(path) for path in stale],
                   "manifest_sha256": hashlib.sha256(json.dumps(expected, sort_keys=True).encode()).hexdigest(),
                   "status": "completed"}
        # shortcut: recovery excludes crashes and concurrent profile edits; use atomic profile switching if needed.
        try:
            for path in stale:
                path.unlink()
            result = subprocess.run(command, env=env, check=True, capture_output=True, text=True)
            (transaction / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        except (OSError, subprocess.CalledProcessError):
            for path in paths:
                remove(path)
                if path in prior:
                    prior[path].rename(path)
            raise
        print(result.stdout, end="")
        print(f"snapshot receipt: {transaction / 'receipt.json'}")
    finally:
        lock.rmdir()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--host", choices=HOSTS, required=True)
    parser.add_argument("--store", type=path_arg, required=True)
    parser.add_argument("--target", type=path_arg, required=True)
    parser.add_argument("--rules-target", type=path_arg)
    parser.add_argument("--skill", action="append", default=[])
    parser.add_argument("--replace-conflicts", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.ref):
        parser.error("--ref requires a full lowercase commit SHA")
    if any(not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) for name in args.skill):
        parser.error("--skill requires a skill ID")
    try:
        install(args)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        if isinstance(exc, subprocess.CalledProcessError) and exc.stderr:
            print(exc.stderr.rstrip(), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
