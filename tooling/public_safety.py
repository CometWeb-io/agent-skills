#!/usr/bin/env python3
"""Fail-closed release-tree scanner. Findings never echo matched secret values."""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath

SECRET_RULES = {
    "api-key": rb"sk-(?:proj-|ant-|live-|test-)?[A-Za-z0-9_-]{24,}",
    "github-token": rb"gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}",
    "slack-token": rb"xox[baprs]-[A-Za-z0-9-]{10,}|hooks\.slack\.com/services/[A-Z0-9]",
    "google-key": rb"AIza[0-9A-Za-z_-]{35}",
    "aws-key": rb"(?:AKIA|ASIA)[0-9A-Z]{16}",
    "private-key": rb"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "bearer-token": rb"Bearer [A-Za-z0-9._-]{30,}",
    "database-credentials": rb"(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^\s\"']*:[^\s@\"']+@",
}
PRIVATE_RULES = {
    "notion-binding": rb"collection://[0-9a-f-]{36}|app\.notion\.com/p/[0-9a-f]{20,}|notion\.so/[0-9a-f]{32}",
    "linear-binding": rb"linear\.app/|(?:^|[^A-Za-z0-9])COM-[0-9]{1,5}(?:[^A-Za-z0-9]|$)",
    "owner-path": rb"/Users/[A-Za-z0-9._-]+/(?:Github|Documents|Desktop)/",
    # Assembled from fragments so this rule never contains, as a literal, the
    # path it searches for. A history rewrite that scrubs those paths would
    # otherwise rewrite the rule too and silently disarm the check.
    "private-vault": rb"personal/(?:gtm-cometweb|nauka)(?:/|\b)|internal/" + rb"comet" + rb"base(?:/|\b)",
    "private-host": rb"app-eu1\.hubspot|api\.betterwebhub\.com|hpanel\.hostinger",
}
FORBIDDEN_NAMES = (
    ".bootstrap", ".env", ".env.*", "*.local.json", "*.pem", "*.key", "*.b64", "*.base64", "id_rsa*", "id_ed25519*",
    "*client_secret*", "*credentials*.json", "*service-account*.json", ".DS_Store",
)
PUBLIC_NAMES = (
    "*promotion-playbook*", "*GTM-COUNCIL*", "*gtm-council-memo*", "*KROKI-PROMOCJA*",
    "*linear-*", "*boardroom*", "*pilot-queue*", "*evidence-register*",
)
# Only transient development trees are excluded; hidden files are otherwise scanned.
# Never shipped, so never scanned. A virtualenv in particular is full of
# symlinks, which used to abort the whole scan when the gate was pointed at a
# working tree rather than at an export directory.
TRANSIENT = {
    ".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".venv", "venv", "node_modules", ".tmp",
}
MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_FILES = 50_000
MAX_TOTAL_BYTES = 512 * 1024 * 1024


def tracked_directories(tracked: set[str] | None) -> set[str]:
    result: set[str] = set()
    for name in tracked or ():
        parts = PurePosixPath(name).parts[:-1]
        for index in range(1, len(parts) + 1):
            result.add(PurePosixPath(*parts[:index]).as_posix())
    return result


def files(root: Path, *, tracked: set[str] | None = None):
    """Walk without following links. Reject any symlink or special file, including directories.

    Transient directory names are pruned unless Git tracks content inside them.
    """
    if root.is_symlink() or not root.is_dir():
        raise ValueError("scan root must be a real directory")
    tracked_dirs = tracked_directories(tracked)
    for base, dirs, names in os.walk(root, followlinks=False, onerror=lambda exc: (_ for _ in ()).throw(exc)):
        filtered = []
        for directory in dirs:
            rel = (Path(base) / directory).relative_to(root).as_posix()
            if directory in TRANSIENT and rel not in tracked_dirs:
                continue
            filtered.append(directory)
        dirs[:] = sorted(filtered)
        for name in sorted(dirs + names):
            path = Path(base) / name
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise ValueError(f"symlink is not permitted: {path.relative_to(root)}")
            if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                raise ValueError(f"special file is not permitted: {path.relative_to(root)}")
        for name in sorted(names):
            path = Path(base) / name
            if path.suffix != ".pyc":
                yield path


def check_blob(name: str, blob: bytes, *, public: bool = True) -> list[dict]:
    findings = []
    parts = PurePosixPath(name).parts
    patterns = FORBIDDEN_NAMES + (PUBLIC_NAMES if public else ())
    if any(fnmatch.fnmatchcase(part.casefold(), pattern.casefold()) for part in parts for pattern in patterns):
        findings.append({"path": name, "rule": "forbidden-name"})
    rules = {**SECRET_RULES, **(PRIVATE_RULES if public else {})}
    for label, pattern in rules.items():
        for match in re.finditer(pattern, blob):
            findings.append({"path": name, "rule": label, "line": blob[:match.start()].count(b"\n") + 1})
            break
    return findings


def _git_env() -> dict[str, str]:
    try:
        from core.git import git_env

        return git_env()
    except ImportError:
        env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        env.update(
            GIT_CONFIG_NOSYSTEM="1",
            GIT_CONFIG_GLOBAL=os.devnull,
            GIT_OPTIONAL_LOCKS="0",
            GIT_TERMINAL_PROMPT="0",
            GIT_NO_REPLACE_OBJECTS="1",
        )
        return env


def _git_read(root: Path, *args: str, timeout: int = 120) -> bytes:
    """Hardened git read; works when tooling/core is unavailable (packaged scanner copy)."""
    try:
        from core.git import read_git

        return read_git(root, *args, timeout=timeout).stdout
    except ImportError:
        return subprocess.run(
            [
                "git",
                "--no-pager",
                "-c",
                "core.fsmonitor=false",
                "-c",
                f"core.hooksPath={os.devnull}",
                "-C",
                str(root),
                *args,
            ],
            check=True,
            capture_output=True,
            timeout=timeout,
            env=_git_env(),
            stdin=subprocess.DEVNULL,
        ).stdout


def tracked_files(root: Path) -> set[str] | None:
    """Paths git tracks, or None when root is not a work tree.

    Pointed at a checkout rather than an export, the scan must judge what
    would actually be published. An ignored file - a local binding holding the
    real path into a private vault, for instance - exists precisely so that it
    never ships, and reporting it as a leak inverts the meaning of the gate.
    """
    try:
        stdout = _git_read(root, "ls-files", "-z", timeout=120)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return None
    return {name for name in stdout.decode("utf-8").split("\0") if name}


def scan(root: Path, *, public: bool = True) -> list[dict]:
    findings = []
    tracked = tracked_files(root)
    count = 0
    total = 0
    for path in files(root, tracked=tracked):
        rel = path.relative_to(root).as_posix()
        if tracked is not None and rel not in tracked:
            continue
        count += 1
        if count > MAX_FILES:
            raise ValueError("file-count scan budget exceeded")
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            raise ValueError(f"file too large for bounded scan: {path.relative_to(root)}")
        total += size
        if total > MAX_TOTAL_BYTES:
            raise ValueError("aggregate scan budget exceeded")
        blob = path.read_bytes()
        findings.extend(check_blob(rel, blob, public=public))
    return findings


def _read_blobs_batch(root: Path, oids: list[str]) -> dict[str, bytes]:
    if not oids:
        return {}
    request = ("\n".join(oids) + "\n").encode()
    proc = subprocess.run(
        ["git", "-C", str(root), "cat-file", "--batch"],
        input=request,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_git_env(),
        check=True,
        timeout=120,
    )
    raw = proc.stdout
    offset = 0
    by_oid: dict[str, bytes] = {}
    for oid in oids:
        end = raw.find(b"\n", offset)
        if end < offset:
            raise ValueError("truncated Git batch header")
        header = raw[offset:end].decode()
        parts = header.split()
        if len(parts) != 3 or parts[0] != oid or parts[1] != "blob":
            raise ValueError("Git batch header mismatch")
        size = int(parts[2])
        if size > MAX_FILE_BYTES:
            raise ValueError(f"historical file exceeds scan budget: {oid}")
        start = end + 1
        value = raw[start:start + size]
        if len(value) != size or raw[start + size:start + size + 1] != b"\n":
            raise ValueError("truncated Git blob")
        by_oid[oid] = value
        offset = start + size + 1
    if offset != len(raw):
        raise ValueError("unexpected extra Git batch output")
    return by_oid


def scan_history(root: Path, *, public: bool = True) -> list[dict]:
    """Scan reachable historical blobs and names, including deleted files; no shell interpolation."""
    if Path(_git_read(root, "rev-parse", "--show-toplevel").decode().strip()).resolve() != root.resolve():
        raise ValueError("--history requires the repository root, not a subdirectory")

    findings: list[dict] = []
    blob_paths: dict[str, set[str]] = {}
    first_revision: dict[tuple[str, str], str] = {}
    file_count = 0
    total_bytes = 0

    for commit in _git_read(root, "rev-list", "--all", timeout=120).decode().splitlines():
        for entry in _git_read(root, "ls-tree", "-rz", commit, timeout=120).split(b"\0"):
            if not entry:
                continue
            header, raw_name = entry.split(b"\t", 1)
            mode, kind, oid = header.decode().split()
            name = raw_name.decode("utf-8", errors="strict")
            name_key = (oid, name)
            if name_key in first_revision:
                continue
            first_revision[name_key] = commit
            if mode == "120000" or kind != "blob":
                findings.append({"path": name, "revision": commit, "rule": "non-regular-git-entry"})
                continue
            blob_paths.setdefault(oid, set()).add(name)
            file_count += 1
            if file_count > MAX_FILES:
                raise ValueError("history file-count scan budget exceeded")

    unique_oids = list(blob_paths)
    chunk_size = 256
    for index in range(0, len(unique_oids), chunk_size):
        chunk = unique_oids[index:index + chunk_size]
        blobs = _read_blobs_batch(root, chunk)
        for oid, blob in blobs.items():
            total_bytes += len(blob)
            if total_bytes > MAX_TOTAL_BYTES:
                raise ValueError("history aggregate scan budget exceeded")
            for path_name in sorted(blob_paths[oid]):
                for item in check_blob(path_name, blob, public=public):
                    findings.append({**item, "revision": first_revision[(oid, path_name)]})
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--history", action="store_true")
    parser.add_argument("--package", action="store_true", help="Private package mode: secrets still forbidden")
    args = parser.parse_args()
    try:
        findings = scan(args.root, public=not args.package)
        if args.history:
            findings.extend(scan_history(args.root, public=not args.package))
        print(json.dumps({"status": "blocked" if findings else "passed", "findings": findings}, ensure_ascii=False, indent=2))
        return 1 if findings else 0
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"Scanner could not complete ({type(exc).__name__}); release blocked.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
