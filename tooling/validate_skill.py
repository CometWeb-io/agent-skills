#!/usr/bin/env python3
"""Validate a single skill package path."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from compatibility import parse_frontmatter as _parse_frontmatter


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
