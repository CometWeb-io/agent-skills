#!/usr/bin/env python3
"""Validate a single skill package path."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from compatibility import parse_frontmatter as _parse_frontmatter
from package_skill import VERSION as VERSION_RE


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def parse_frontmatter(path: Path) -> dict:
    try:
        return _parse_frontmatter(path)
    except ValueError as exc:
        fail(str(exc))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill_dir", type=Path)
    args = parser.parse_args()
    skill_dir = args.skill_dir.resolve()
    if not skill_dir.is_dir():
        fail(f"not a directory: {skill_dir}")
    name = skill_dir.name
    for rel in ("SKILL.md", "VERSION", "LICENSE"):
        if not (skill_dir / rel).is_file():
            fail(f"missing {rel}")
    version = (skill_dir / "VERSION").read_text(encoding="utf-8").strip()
    if not VERSION_RE.fullmatch(version):
        # package_skill.py refuses such a VERSION, so passing here would only
        # move the failure to release time.
        fail(f"VERSION is not a semantic version: {version!r}")
    fm = parse_frontmatter(skill_dir / "SKILL.md")
    if fm.get("name") != name:
        fail(f"name mismatch: {fm.get('name')!r} != {name!r}")
    desc = fm.get("description", "")
    if len(desc) < 80:
        fail(f"description too short ({len(desc)})")
    if len(desc) > 1024:
        fail(f"description exceeds Codex limit 1024 ({len(desc)})")
    print(f"OK: validate_skill {name}")


if __name__ == "__main__":
    main()
