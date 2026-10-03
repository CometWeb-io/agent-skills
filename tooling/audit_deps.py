#!/usr/bin/env python3
"""Audit every locked dependency, and prove skill runtime dependencies are among them.

    uv run python tooling/audit_deps.py               # coverage check, then pip-audit (network)
    uv run python tooling/audit_deps.py --coverage    # the offline coverage check only

pip-audit reads the exact pins exported from uv.lock, with their hashes
(`--require-hashes --disable-pip`), for each dependency group: `dev` and the
isolated `sast` group, which cannot share one environment. Auditing the lock
rather than the active virtualenv means a package installed by hand cannot hide
or add a result, and the `sast` engine's dependencies are audited although they
are never installed into the dev venv.

Skills declare optional third-party packages in RUNTIME.json (and, for some,
requirements.txt) as ranges: the user's resolver picks the version. A range
cannot be audited, so the coverage check requires that every declared package
is locked here at a version inside its declared range. pip-audit then audits
that version, and the runtime matrix tests the same range on each supported
Python. A runtime dependency missing from the lock fails the gate.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import tempfile
import tomllib

from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

ROOT = Path(__file__).resolve().parents[1]
GROUPS = ("dev", "sast")


def locked_versions(root: Path) -> dict[str, set[Version]]:
    data = tomllib.loads((root / "uv.lock").read_text(encoding="utf-8"))
    versions: dict[str, set[Version]] = {}
    for package in data.get("package", []):
        if "version" in package:
            versions.setdefault(canonicalize_name(package["name"]), set()).add(Version(package["version"]))
    return versions


def declared_runtime(root: Path) -> list[tuple[str, str]]:
    """(source file, requirement) for every skill-declared third-party package."""
    found: list[tuple[str, str]] = []
    for path in sorted((root / "skills").glob("*/RUNTIME.json")):
        deps = json.loads(path.read_text(encoding="utf-8")).get("dependencies") or {}
        for group in sorted(deps):
            found.extend((path.relative_to(root).as_posix(), req) for req in deps[group])
    for path in sorted((root / "skills").glob("*/requirements.txt")):
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                found.append((path.relative_to(root).as_posix(), line))
    return found


def coverage_errors(root: Path = ROOT) -> list[str]:
    locked = locked_versions(root)
    errors: list[str] = []
    for source, text in declared_runtime(root):
        try:
            requirement = Requirement(text)
        except InvalidRequirement as error:
            errors.append(f"{source}: invalid requirement {text!r}: {error}")
            continue
        name = canonicalize_name(requirement.name)
        if name not in locked:
            errors.append(f"{source}: {requirement.name} is not in uv.lock, so pip-audit never sees it; "
                          "add it to the dev dependency group")
            continue
        inside = [v for v in locked[name] if requirement.specifier.contains(v, prereleases=True)]
        if not inside:
            have = ", ".join(str(v) for v in sorted(locked[name]))
            errors.append(f"{source}: {text} but uv.lock has {requirement.name} {have}; "
                          "the audited version is not one this skill accepts")
    return errors


def export(root: Path, group: str, out: Path) -> None:
    subprocess.run(  # nosec B603 B607
        ["uv", "export", "--frozen", "--no-emit-project", "--format", "requirements-txt",
         "--only-group", group, "--output-file", str(out), "--quiet"],
        cwd=root, check=True,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--coverage", action="store_true", help="only check runtime deps are locked (offline)")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    errors = coverage_errors(root)
    for error in errors:
        print(f"FAIL: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"OK: {len(declared_runtime(root))} skill runtime requirements are locked at an accepted version")
    if args.coverage:
        return 0
    failed: list[str] = []
    with tempfile.TemporaryDirectory(prefix="cw-audit-") as tmp:
        # One run per group: the groups pin different versions of shared packages,
        # and pip-audit refuses one package pinned twice in a single run.
        for group in GROUPS:
            path = Path(tmp) / f"{group}.txt"
            export(root, group, path)
            hashes = path.read_text(encoding="utf-8").count("--hash=")
            print(f"pip-audit: {group} group ({hashes} hashes)", flush=True)
            command = [sys.executable, "-m", "pip_audit", "--require-hashes", "--disable-pip", "--strict",
                       "--progress-spinner", "off", "--cache-dir", str(Path(tmp) / "cache"), "-r", str(path)]
            if subprocess.run(command, cwd=root, check=False).returncode != 0:  # nosec B603
                failed.append(group)
    if failed:
        print(f"FAIL: pip-audit reported on group(s): {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
