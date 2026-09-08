#!/usr/bin/env python3
"""Read-only Git snapshot for configured CometWeb repositories."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import subprocess
from typing import Any


def run_git(repo: pathlib.Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=15,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git command failed")
    return proc.stdout.strip()


def default_root() -> pathlib.Path:
    value = os.environ.get("COMETWEB_ROOT") or os.environ.get("COMETWEB_CENTRUM")
    if value:
        return pathlib.Path(value).expanduser()
    return pathlib.Path.home() / "Github" / "CometWeb"


def load_registry(path: pathlib.Path) -> list[str]:
    repos: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            repos.append(line)
    return repos


def count_lines(value: str) -> int:
    return len([line for line in value.splitlines() if line.strip()])


def redact_path(path: pathlib.Path, root: pathlib.Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return path.name


def remote_info(repo: pathlib.Path) -> dict[str, Any]:
    info: dict[str, Any] = {
        "remote": None,
        "remote_head_sha": None,
        "ahead_by": None,
        "behind_by": None,
        "detached_head": False,
    }
    try:
        branch = run_git(repo, "rev-parse", "--abbrev-ref", "HEAD")
        info["detached_head"] = branch == "HEAD"
        remotes = run_git(repo, "remote").splitlines()
        if remotes:
            info["remote"] = remotes[0]
        upstream = run_git(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
        info["upstream"] = upstream
        counts = run_git(repo, "rev-list", "--left-right", "--count", f"HEAD...{upstream}")
        left, right = counts.split()
        info["ahead_by"] = int(left)
        info["behind_by"] = int(right)
        info["remote_head_sha"] = run_git(repo, "rev-parse", upstream)
    except Exception:
        # No upstream / offline — leave nulls
        pass
    return info


def snapshot(root: pathlib.Path, rel: str, *, redact_paths: bool) -> dict[str, Any]:
    repo = root / rel
    result: dict[str, Any] = {
        "repo": rel,
        "path": redact_path(repo, root) if redact_paths else str(repo),
        "status": "ok",
    }
    if not repo.exists():
        result["status"] = "missing"
        return result
    try:
        inside = run_git(repo, "rev-parse", "--is-inside-work-tree")
        if inside != "true":
            result["status"] = "not_git"
            return result
        branch = run_git(repo, "rev-parse", "--abbrev-ref", "HEAD")
        head_sha = run_git(repo, "rev-parse", "HEAD")
        result.update(
            branch=branch,
            head_sha=head_sha,
            last_commit_at=run_git(repo, "log", "-1", "--format=%cI"),
            subject=run_git(repo, "log", "-1", "--format=%s")[:120],
            dirty_count=count_lines(run_git(repo, "status", "--porcelain")),
            commits_7d=count_lines(run_git(repo, "log", "--since=7 days ago", "--format=%H")),
            commits_30d=count_lines(run_git(repo, "log", "--since=30 days ago", "--format=%H")),
        )
        result.update(remote_info(repo))
        fingerprint_src = f"{rel}:{head_sha}:{result.get('remote_head_sha')}:{result['dirty_count']}"
        result["snapshot_fingerprint"] = hashlib.sha256(fingerprint_src.encode()).hexdigest()[:16]
    except Exception as exc:
        result["status"] = "error"
        result["error"] = str(exc)[:300]
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path, default=None)
    parser.add_argument("--registry", type=pathlib.Path, default=None)
    parser.add_argument("--repo", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--redact-paths",
        dest="redact_paths",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Omit absolute local paths from output (default: true)",
    )
    parser.add_argument(
        "--as-of",
        default=None,
        help="Optional ISO timestamp label recorded on the snapshot (does not time-travel git)",
    )
    args = parser.parse_args()

    root = (args.root or default_root()).expanduser()
    registry = args.registry or (
        pathlib.Path(__file__).resolve().parent.parent / "references" / "repos.txt"
    )
    repos = args.repo or load_registry(registry)
    generated_at = dt.datetime.now(dt.timezone.utc).isoformat()
    payload = {
        "schema": "cometweb.repo-snapshot/v1",
        "generated_at": generated_at,
        "as_of": args.as_of or generated_at,
        "root": "<redacted>" if args.redact_paths else str(root),
        "repos": [snapshot(root, rel, redact_paths=args.redact_paths) for rel in repos],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for item in payload["repos"]:
            if item["status"] != "ok":
                print(f"{item['repo']}: {item['status']}")
                continue
            ahead = item.get("ahead_by")
            behind = item.get("behind_by")
            sync = f" ahead={ahead} behind={behind}" if ahead is not None else ""
            print(
                f"{item['repo']}: {item['branch']} {item['head_sha'][:8]} "
                f"dirty={item['dirty_count']} 7d={item['commits_7d']} 30d={item['commits_30d']}{sync}"
            )


if __name__ == "__main__":
    main()
