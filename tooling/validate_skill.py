#!/usr/bin/env python3
"""Validate a single skill package path."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        fail(f"missing YAML frontmatter: {path}")
    block = match.group(1)
    result: dict[str, str] = {}
    key: str | None = None
    buf: list[str] = []
    for line in block.splitlines():
        if line.startswith("  ") and key:
            buf.append(line.strip())
            continue
        if key:
            result[key] = " ".join(buf).strip()
            buf = []
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            if val in (">", ">-", "|"):
                buf = []
            else:
                result[key] = val.strip('"').strip("'")
                key = None
    if key:
        result[key] = " ".join(buf).strip()
    return result


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
