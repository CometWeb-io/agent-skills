"""Require changed skill instructions/scripts to have versioned change history."""
from __future__ import annotations

import argparse
from pathlib import Path
import re

from plugin_release import ROOT, ReleaseError, _git, merge_base, parse_version, shipped_skills, shipped_skills_at


def check_package(package: Path, old_version: str | None, old_history: str,
                  behavioral_change: bool) -> list[str]:
    version = (package / "VERSION").read_text().strip()
    parse_version(version)
    errors = []
    if old_version is not None and behavioral_change and parse_version(version) <= parse_version(old_version):
        errors.append(f"{package.name}: changed instructions/scripts require a newer package VERSION")
    changed = old_version is None or behavioral_change or version != old_version
    if not changed:
        return errors
    history_file = package / "CHANGELOG.md"
    history = history_file.read_text() if history_file.is_file() else ""
    if not re.search(r"(?m)^##\s+\[?" + re.escape(version) + r"\]?(?:\s|$)", history):
        errors.append(f"{package.name}: CHANGELOG.md must describe VERSION {version}")
    if old_version is not None and history == old_history:
        errors.append(f"{package.name}: changed package requires a changed CHANGELOG.md")
    return errors


def check(root: Path, base: str, require_base: bool) -> list[str]:
    revision = merge_base(root, base)
    if revision is None:
        return [f"no merge base with {base}; package change history was not checked"]
    _, old_skills = shipped_skills_at(root, revision)
    changed = _git(root, "diff", "--name-only", revision, "--", "skills/")
    if changed.returncode:
        raise ReleaseError("cannot read changed skill paths")
    paths = set(changed.stdout.splitlines())
    errors = []
    for sid, version in shipped_skills(root).items():
        prefix = f"skills/{sid}/"
        behavioral = any(path == prefix + "SKILL.md" or path.startswith(prefix + "scripts/") for path in paths)
        old = old_skills.get(sid)
        if old is not None and not behavioral and old == version:
            continue
        history = _git(root, "show", f"{revision}:{prefix}CHANGELOG.md").stdout if old is not None else ""
        errors.extend(check_package(root / prefix, old, history, behavioral))
    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--require-base", action="store_true")
    args = parser.parse_args(argv)
    try:
        errors = check(args.root, args.base, args.require_base)
    except (OSError, ValueError, ReleaseError) as exc:
        errors = [str(exc)]
    for error in errors:
        print("FAIL: " + error)
    if not errors:
        print("OK: changed skill instructions/scripts have versioned change history")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
