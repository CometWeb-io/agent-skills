#!/usr/bin/env python3
"""Refuse a shipped skill change that does not bump the plugin version.

Claude Code and Codex cache an installed plugin under its manifest `version`.
`claude plugin update` replaces the cached copy only when that version changes;
with the same version it reports "already at the latest version" and keeps the
old skills. So any change to what the plugin ships -- a skill added, removed or
renamed, or any skill `VERSION` changed -- must come with a new plugin version,
or users who installed the plugin never receive it.

Two checks, both comparing the *shipped set*: every `skills/<id>/` that has a
`SKILL.md`, with the contents of its `VERSION`.

1. Recorded fingerprint (`registry/plugin-release.json`). It names the plugin
   version and the shipped set that version was cut with. The working tree must
   match it exactly. Works offline and in shallow clones.
2. Merge base (git). If the shipped set differs from the one at the merge base
   with `origin/main` (or `--base`), the plugin `VERSION` must be strictly
   greater than the base's. This catches a record edited in place without a
   bump, which check 1 alone cannot see.

    python tooling/plugin_release.py --check                 # both checks; base skipped if unavailable
    python tooling/plugin_release.py --check --require-base  # CI: a missing base is a failure
    python tooling/plugin_release.py --record                # after bumping VERSION, record the new set
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "cometweb.plugin-release/v1"
RECORD = Path("registry/plugin-release.json")
DEFAULT_BASE = "origin/main"
SEMVER = re.compile(r"(\d+)\.(\d+)\.(\d+)")


class ReleaseError(Exception):
    pass


def parse_version(text: str) -> tuple[int, int, int]:
    match = SEMVER.fullmatch(text.strip())
    if not match:
        raise ReleaseError(f"not a semantic version: {text.strip()!r}")
    major, minor, patch = (int(part) for part in match.groups())
    return major, minor, patch


def shipped_skills(root: Path) -> dict[str, str]:
    """{skill id: VERSION} for every package the plugin ships."""
    skills: dict[str, str] = {}
    for skill_md in sorted((root / "skills").glob("*/SKILL.md")):
        version_file = skill_md.parent / "VERSION"
        if not version_file.is_file():
            raise ReleaseError(f"skills/{skill_md.parent.name}: SKILL.md without VERSION")
        skills[skill_md.parent.name] = version_file.read_text(encoding="utf-8").strip()
    return skills


def plugin_version(root: Path) -> str:
    return (root / "VERSION").read_text(encoding="utf-8").strip()


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - fixed git argv, no shell
        ["git", *args], cwd=root, capture_output=True, text=True, check=False  # noqa: S607
    )


def merge_base(root: Path, base: str) -> str | None:
    result = _git(root, "merge-base", "HEAD", base)
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else None


def shipped_skills_at(root: Path, commit: str) -> tuple[str, dict[str, str]]:
    """Plugin VERSION and shipped set as committed at `commit`."""
    listing = _git(root, "ls-tree", "-r", "--name-only", commit, "--", "skills/")
    if listing.returncode != 0:
        raise ReleaseError(f"git ls-tree {commit} failed: {listing.stderr.strip()}")
    paths = set(listing.stdout.split())
    skills: dict[str, str] = {}
    for path in sorted(paths):
        parts = path.split("/")
        if len(parts) == 3 and parts[2] == "SKILL.md":
            version_path = f"skills/{parts[1]}/VERSION"
            if version_path not in paths:
                raise ReleaseError(f"{commit[:12]}: {version_path} missing")
            skills[parts[1]] = _git(root, "show", f"{commit}:{version_path}").stdout.strip()
    version = _git(root, "show", f"{commit}:VERSION")
    if version.returncode != 0:
        raise ReleaseError(f"{commit[:12]}: no VERSION file")
    return version.stdout.strip(), skills


def describe_diff(old: dict[str, str], new: dict[str, str]) -> list[str]:
    lines = [f"added {sid} {new[sid]}" for sid in sorted(new.keys() - old.keys())]
    lines += [f"removed {sid} {old[sid]}" for sid in sorted(old.keys() - new.keys())]
    lines += [
        f"changed {sid} {old[sid]} -> {new[sid]}"
        for sid in sorted(old.keys() & new.keys())
        if old[sid] != new[sid]
    ]
    return lines


def load_record(root: Path) -> dict:
    path = root / RECORD
    if not path.is_file():
        raise ReleaseError(f"{RECORD} is missing; run tooling/plugin_release.py --record")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA or not isinstance(data.get("skills"), dict):
        raise ReleaseError(f"{RECORD}: expected schema {SCHEMA} with a skills map")
    return data


def render_record(version: str, skills: dict[str, str]) -> str:
    data = {"schema": SCHEMA, "plugin_version": version, "skills": dict(sorted(skills.items()))}
    return json.dumps(data, indent=2) + "\n"


def check_record(root: Path) -> list[str]:
    record = load_record(root)
    version, skills = plugin_version(root), shipped_skills(root)
    errors: list[str] = []
    diff = describe_diff(record["skills"], skills)
    if record.get("plugin_version") != version:
        errors.append(
            f"{RECORD} records plugin {record.get('plugin_version')!r} but VERSION is {version!r}; "
            "run tooling/plugin_release.py --record"
        )
    elif diff:
        errors.append(
            f"shipped skills changed since plugin {version} was recorded ("
            + "; ".join(diff)
            + "). Bump VERSION and every plugin manifest, then run tooling/plugin_release.py --record"
        )
    return errors


def check_base(root: Path, base: str, *, require: bool) -> tuple[list[str], str]:
    commit = merge_base(root, base)
    if commit is None:
        note = f"no merge base with {base}"
        return ([note] if require else []), f"SKIP base comparison: {note}"
    base_version, base_skills = shipped_skills_at(root, commit)
    version, skills = plugin_version(root), shipped_skills(root)
    diff = describe_diff(base_skills, skills)
    if not diff:
        return [], f"base {commit[:12]}: shipped skills unchanged"
    if parse_version(version) <= parse_version(base_version):
        return [
            f"shipped skills differ from {base} ({commit[:12]}): "
            + "; ".join(diff)
            + f" -- but plugin VERSION {version} is not greater than {base_version}. "
            "`claude plugin update` would keep users on the old skills."
        ], ""
    return [], f"base {commit[:12]}: {len(diff)} skill change(s), plugin {base_version} -> {version}"


def record(root: Path, base: str) -> str:
    version, skills = plugin_version(root), shipped_skills(root)
    parse_version(version)
    path = root / RECORD
    commit = merge_base(root, base)
    base_version, base_skills = shipped_skills_at(root, commit) if commit is not None else (None, None)
    # A version newer than the merge base has not shipped yet, so the branch that
    # bumped it may keep recording its own later skill changes under it. Without
    # a base nothing tells released from unreleased, so the record is final.
    unreleased = base_version is not None and parse_version(version) > parse_version(base_version)
    if path.is_file():
        old = load_record(root)
        if old.get("plugin_version") == version and old["skills"] != skills and not unreleased:
            raise ReleaseError(
                f"plugin {version} was already recorded with a different skill set ("
                + "; ".join(describe_diff(old["skills"], skills))
                + "). Bump VERSION first; a recorded version is never reused."
            )
        if parse_version(version) < parse_version(old.get("plugin_version", "0.0.0")):
            raise ReleaseError(f"VERSION {version} is older than the recorded {old['plugin_version']}")
    if base_skills is not None and base_skills != skills and not unreleased:
        raise ReleaseError(
            f"shipped skills differ from {base} but VERSION {version} is not greater than {base_version}"
        )
    path.write_text(render_record(version, skills), encoding="utf-8")
    return f"recorded plugin {version} with {len(skills)} skills in {RECORD}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--record", action="store_true")
    parser.add_argument("--base", default=DEFAULT_BASE, help=f"git ref to compare with (default {DEFAULT_BASE})")
    parser.add_argument("--require-base", action="store_true", help="fail when no merge base can be found")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.record:
            print("OK: " + record(root, args.base))
            return 0
        errors = check_record(root)
        base_errors, note = check_base(root, args.base, require=args.require_base)
        errors += base_errors
    except ReleaseError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"OK: plugin_release --check (plugin {plugin_version(root)}; {note})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
