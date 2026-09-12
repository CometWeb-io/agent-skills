#!/usr/bin/env python3
"""Read-only Git snapshot for configured CometWeb repositories.

Local filesystem paths are omitted by default to avoid leaking workstation paths into
ContextEnvelope artifacts. Pass --include-paths only for local debugging.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import subprocess
from typing import Any


def run_git(repo: pathlib.Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-c", "core.fsmonitor=false", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=15,
        check=False,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git command failed")
    return proc.stdout.strip()


def default_root() -> tuple[pathlib.Path, str]:
    if os.environ.get("COMETWEB_ROOT"):
        return pathlib.Path(os.environ["COMETWEB_ROOT"]).expanduser(), "COMETWEB_ROOT"
    if os.environ.get("COMETWEB_CENTRUM"):
        return pathlib.Path(os.environ["COMETWEB_CENTRUM"]).expanduser(), "COMETWEB_CENTRUM"
    return pathlib.Path.home() / "Github" / "CometWeb", "fallback"


def load_registry(path: pathlib.Path) -> list[str]:
    repos: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            repos.append(line)
    return repos


def count_lines(value: str) -> int:
    return len([line for line in value.splitlines() if line.strip()])


def snapshot(root: pathlib.Path, rel: str, include_paths: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {"repo": rel, "status": "ok"}
    try:
        if not isinstance(rel, str) or not rel.strip() or pathlib.Path(rel).is_absolute():
            raise ValueError("absolute or empty path")
        base = root.resolve()
        repo = (base / rel).resolve()
        repo.relative_to(base)
        if ".." in pathlib.Path(rel).parts:
            raise ValueError("parent traversal")
    except (OSError, ValueError, RuntimeError):
        result["status"] = "invalid_path"
        return result
    if include_paths:
        result["path"] = str(repo)
    if not repo.exists():
        result["status"] = "missing"
        return result
    try:
        inside = run_git(repo, "rev-parse", "--is-inside-work-tree")
        if inside != "true":
            result["status"] = "not_git"
            return result
        top = pathlib.Path(run_git(repo, "rev-parse", "--show-toplevel")).resolve()
        if top != repo:
            result["status"] = "not_repo_root"
            return result
        result.update(
            branch=run_git(repo, "rev-parse", "--abbrev-ref", "HEAD"),
            head_sha=run_git(repo, "rev-parse", "HEAD"),
            last_commit_at=run_git(repo, "log", "-1", "--format=%cI"),
            subject=run_git(repo, "log", "-1", "--format=%s")[:120],
            dirty_count=count_lines(run_git(repo, "status", "--porcelain")),
            commits_7d=count_lines(run_git(repo, "log", "--since=7 days ago", "--format=%H")),
            commits_30d=count_lines(run_git(repo, "log", "--since=30 days ago", "--format=%H")),
        )
    except Exception as exc:  # keep the full snapshot resilient
        result["status"] = "error"
        result["error"] = str(exc)[:300] if include_paths else "git snapshot unavailable"
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path, default=None)
    parser.add_argument("--registry", type=pathlib.Path, default=None)
    parser.add_argument("--repo", action="append", default=[])
    parser.add_argument("--include-paths", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.root is None:
        root, root_source = default_root()
    else:
        root, root_source = args.root.expanduser(), "argument"
    registry = args.registry or (pathlib.Path(__file__).resolve().parent.parent / "references" / "repos.txt")
    repos = args.repo or load_registry(registry)
    root_available = root.exists()
    payload = {
        "schema": "cometweb.repo-snapshot/v2",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "root_source": root_source,
        "root_available": root_available,
        "repos": [snapshot(root, rel, args.include_paths) for rel in repos] if root_available else [],
        "fallback": None if root_available else "use-current-github-connector",
    }
    if args.include_paths:
        payload["root"] = str(root)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        if not root_available:
            print("local CometWeb root unavailable; use current GitHub connector")
            return
        for item in payload["repos"]:
            if item["status"] != "ok":
                print(f"{item['repo']}: {item['status']}")
                continue
            print(
                f"{item['repo']}: {item['branch']} {item['head_sha'][:8]} "
                f"dirty={item['dirty_count']} 7d={item['commits_7d']} 30d={item['commits_30d']}"
            )


if __name__ == "__main__":
    main()
