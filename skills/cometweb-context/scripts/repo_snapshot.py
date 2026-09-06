#!/usr/bin/env python3
"""Read-only Git snapshot for configured CometWeb repositories."""

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


def snapshot(root: pathlib.Path, rel: str) -> dict[str, Any]:
    repo = root / rel
    result: dict[str, Any] = {"repo": rel, "path": str(repo), "status": "ok"}
    if not repo.exists():
        result["status"] = "missing"
        return result
    try:
        inside = run_git(repo, "rev-parse", "--is-inside-work-tree")
        if inside != "true":
            result["status"] = "not_git"
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
    args = parser.parse_args()

    root = (args.root or default_root()).expanduser()
    registry = args.registry or (pathlib.Path(__file__).resolve().parent.parent / "references" / "repos.txt")
    repos = args.repo or load_registry(registry)
    payload = {
        "schema": "cometweb.repo-snapshot/v1",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "root": str(root),
        "repos": [snapshot(root, rel) for rel in repos],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
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
