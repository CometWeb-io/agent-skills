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
    "private-vault": rb"personal/(?:gtm-cometweb|nauka)(?:/|\b)|<COMETWEB_INTERNAL_ROOT>(?:/|\b)",
    "private-host": rb"app-eu1\.hubspot|api\.betterwebhub\.com|hpanel\.hostinger",
}
FORBIDDEN_NAMES = (
    ".env", ".env.*", "*.local.json", "*.pem", "*.key", "id_rsa*", "id_ed25519*",
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


def files(root: Path):
    """Walk without following links. Reject any symlink or special file, including directories."""
    if root.is_symlink() or not root.is_dir():
        raise ValueError("scan root must be a real directory")
    for base, dirs, names in os.walk(root, followlinks=False, onerror=lambda exc: (_ for _ in ()).throw(exc)):
        # Prune before inspecting, so a link inside a directory that is never
        # published cannot block the scan of the directories that are.
        dirs[:] = sorted(d for d in dirs if d not in TRANSIENT)
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


# These two files define the rules and exercise them with synthetic material,
# so they match themselves by construction. The exemption covers content rules
# only; a forbidden *name* is still reported here like anywhere else.
RULE_DEFINITIONS = frozenset({
    "tooling/public_safety.py",
    "tooling/tests/test_distribution_hardening.py",
})


def tracked_files(root: Path) -> set[str] | None:
    """Paths git tracks, or None when root is not a work tree.

    Pointed at a checkout rather than an export, the scan must judge what
    would actually be published. An ignored file - a local binding holding the
    real path into a private vault, for instance - exists precisely so that it
    never ships, and reporting it as a leak inverts the meaning of the gate.
    """
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            check=True, capture_output=True, timeout=120,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return None
    return {name for name in proc.stdout.decode("utf-8").split("\0") if name}


def scan(root: Path, *, public: bool = True) -> list[dict]:
    findings = []
    tracked = tracked_files(root)
    for path in files(root):
        rel = path.relative_to(root).as_posix()
        if tracked is not None and rel not in tracked:
            continue
        if path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError(f"file too large for bounded scan: {path.relative_to(root)}")
        blob = path.read_bytes()
        entries = check_blob(rel, blob, public=public)
        if rel in RULE_DEFINITIONS:
            entries = [f for f in entries if f["rule"] == "forbidden-name"]
        findings.extend(entries)
    return findings


def scan_history(root: Path, *, public: bool = True) -> list[dict]:
    """Scan reachable historical blobs and names, including deleted files; no shell interpolation."""
    def git(*args: str) -> bytes:
        return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, timeout=120).stdout
    if Path(git("rev-parse", "--show-toplevel").decode().strip()).resolve() != root.resolve():
        raise ValueError("--history requires the repository root, not a subdirectory")
    findings, seen = [], set()
    for commit in git("rev-list", "--all").decode().splitlines():
        for entry in git("ls-tree", "-rz", commit).split(b"\0"):
            if not entry:
                continue
            header, raw_name = entry.split(b"\t", 1)
            mode, kind, oid = header.decode().split()
            name = raw_name.decode("utf-8", errors="strict")
            key = (oid, name)
            if key in seen:
                continue
            seen.add(key)
            if mode == "120000" or kind != "blob":
                findings.append({"path": name, "revision": commit, "rule": "non-regular-git-entry"})
                continue
            if int(git("cat-file", "-s", oid)) > MAX_FILE_BYTES:
                raise ValueError(f"historical file exceeds scan budget: {name}")
            for item in check_blob(name, git("cat-file", "blob", oid), public=public):
                findings.append({**item, "revision": commit})
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
