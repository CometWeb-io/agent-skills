#!/usr/bin/env python3
"""Package a skill directory into dist/<skill>/skill.zip."""
from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".DS_Store", "__pycache__", ".pytest_cache"}


def should_skip(path: Path) -> bool:
    return any(part in SKIP or part.endswith(".pyc") for part in path.parts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill")
    args = parser.parse_args()
    skill_dir = ROOT / "skills" / args.skill
    if not skill_dir.is_dir():
        raise SystemExit(f"unknown skill: {args.skill}")
    out_dir = ROOT / "dist" / args.skill
    out_dir.mkdir(parents=True, exist_ok=True)
    out_zip = out_dir / "skill.zip"
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(skill_dir.rglob("*")):
            if path.is_dir() or should_skip(path.relative_to(skill_dir)):
                continue
            zf.write(path, arcname=str(path.relative_to(skill_dir)))
    print(f"OK: wrote {out_zip.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
