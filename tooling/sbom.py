#!/usr/bin/env python3
"""Write a CycloneDX 1.6 SBOM for the plugin: every shipped skill and its declared runtime deps.

    uv run python tooling/sbom.py --output dist/agent-skills.cdx.json
    uv run python tooling/sbom.py --dist dist --output dist/agent-skills.cdx.json   # with zip hashes
    uv run python tooling/sbom.py --check     # build and schema-check only (a check_all gate)

The plugin ships no Python dependency of its own. What a user installs is the
skill set, and a few skills declare optional third-party packages in
RUNTIME.json; those are listed as optional libraries with the declared range
(a `cometweb:version-range` property in vers syntax), because the user's resolver picks the version, not this repo.
With `--dist`, each skill carries the SHA-256 of its built `skill.zip`, the same
file the release workflow attests.

The output is deterministic for a given tree: no wall-clock timestamp (the
metadata time is the HEAD commit time, or SOURCE_DATE_EPOCH when set), and the
serial number is derived from the content. Every document is validated against
the bundled CycloneDX 1.6 JSON schema before it is written.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess  # nosec B404 - fixed git argv, no shell
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
SPEC_VERSION = "1.6"
PLUGIN_NAME = "cometweb-agent-skills"
REPOSITORY = "https://github.com/CometWeb-io/agent-skills"
# PEP 508 name, then a PEP 440 specifier set; RUNTIME.json entries are plain requirements.
REQUIREMENT = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*((?:[<>=!~]=?[^,;\s]+\s*,?\s*)*)$")
NAMESPACE = uuid.UUID("6f1c8f43-3c55-4a43-8f3e-4c1e0b9c5a10")


class SbomError(ValueError):
    pass


def read_version(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


LICENSE_IDS = {"MIT License": "MIT"}


def license_id(path: Path) -> str:
    first = path.read_text(encoding="utf-8").splitlines()[0].strip() if path.is_file() else ""
    if first not in LICENSE_IDS:
        raise SbomError(f"{path}: unrecognised license heading {first!r}")
    return LICENSE_IDS[first]


def shipped_skills(root: Path) -> list[str]:
    return sorted(p.parent.name for p in (root / "skills").glob("*/SKILL.md"))


def parse_requirement(text: str) -> tuple[str, str]:
    """Return (normalized name, vers range) for a RUNTIME.json requirement."""
    match = REQUIREMENT.match(text)
    if not match:
        raise SbomError(f"unsupported requirement {text!r}")
    name = re.sub(r"[-_.]+", "-", match.group(1)).lower()
    constraints = [c.strip() for c in match.group(2).split(",") if c.strip()]
    if not constraints:
        return name, "vers:pypi/*"
    for constraint in constraints:
        if constraint.startswith(("~=", "===")) or "*" in constraint:
            raise SbomError(f"{text!r}: {constraint} has no vers equivalent; spell the range out")
    # vers uses "=" for equality and "|" between constraints.
    vers = "|".join(c[1:] if c.startswith("==") else c for c in constraints)
    return name, f"vers:pypi/{vers}"


def runtime_requirements(skill_dir: Path) -> list[str]:
    path = skill_dir / "RUNTIME.json"
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    deps = data.get("dependencies") or {}
    return sorted({req for group in deps.values() for req in group})


def commit_time(root: Path) -> str | None:
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch:
        stamp = dt.datetime.fromtimestamp(int(epoch), tz=dt.timezone.utc)
        return stamp.strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%ct"], cwd=root, capture_output=True,  # nosec B603 B607
                             text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    if not out:
        return None
    return dt.datetime.fromtimestamp(int(out), tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def zip_digest(dist: Path, skill: str, version: str) -> str:
    path = dist / skill / version / "skill.zip"
    if not path.is_file() or path.is_symlink():
        raise SbomError(f"missing package {path}; build it with tooling/package_skill.py {skill}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(root: Path = ROOT, dist: Path | None = None) -> dict:
    plugin_version = read_version(root / "VERSION")
    components: list[dict] = []
    libraries: dict[str, dict] = {}
    dependencies: list[dict] = []
    skill_refs: list[str] = []
    for skill in shipped_skills(root):
        skill_dir = root / "skills" / skill
        version = read_version(skill_dir / "VERSION")
        ref = f"skill:{skill}@{version}"
        skill_refs.append(ref)
        component: dict = {
            "type": "application",
            "bom-ref": ref,
            "name": skill,
            "version": version,
            "licenses": [{"license": {"id": license_id(skill_dir / "LICENSE")}}],
            "properties": [{"name": "cometweb:package-path", "value": f"dist/{skill}/{version}/skill.zip"}],
        }
        if dist is not None:
            component["hashes"] = [{"alg": "SHA-256", "content": zip_digest(dist, skill, version)}]
        components.append(component)
        dep_refs = []
        for requirement in runtime_requirements(skill_dir):
            name, vers = parse_requirement(requirement)
            lib_ref = f"pypi:{name}#{vers}"
            libraries.setdefault(lib_ref, {
                "type": "library",
                "bom-ref": lib_ref,
                "name": name,
                "scope": "optional",
                "purl": f"pkg:pypi/{name}",
                # CycloneDX 1.6 has no versionRange field (it arrives in 1.7).
                "properties": [{"name": "cometweb:version-range", "value": vers}],
            })
            dep_refs.append(lib_ref)
        dependencies.append({"ref": ref, "dependsOn": sorted(set(dep_refs))})
    components.extend(libraries[key] for key in sorted(libraries))
    dependencies.insert(0, {"ref": "plugin", "dependsOn": sorted(skill_refs)})
    dependencies.extend({"ref": key, "dependsOn": []} for key in sorted(libraries))

    metadata: dict = {
        "component": {
            "type": "application",
            "bom-ref": "plugin",
            "name": PLUGIN_NAME,
            "version": plugin_version,
            "licenses": [{"license": {"id": license_id(root / "LICENSE")}}],
            "purl": f"pkg:github/cometweb-io/agent-skills@v{plugin_version}",
            "externalReferences": [{"type": "vcs", "url": REPOSITORY}],
        },
        "tools": {"components": [{"type": "application", "name": "tooling/sbom.py", "version": plugin_version}]},
    }
    stamp = commit_time(root)
    if stamp:
        metadata["timestamp"] = stamp
    bom = {
        "bomFormat": "CycloneDX",
        "specVersion": SPEC_VERSION,
        "version": 1,
        "metadata": metadata,
        "components": components,
        "dependencies": dependencies,
    }
    digest = hashlib.sha256(json.dumps(bom, sort_keys=True).encode()).hexdigest()
    bom["serialNumber"] = f"urn:uuid:{uuid.uuid5(NAMESPACE, digest)}"
    return bom


def validate(bom: dict) -> None:
    from cyclonedx.schema import SchemaVersion
    from cyclonedx.validation.json import JsonStrictValidator

    error = JsonStrictValidator(SchemaVersion.V1_6).validate_str(json.dumps(bom))
    if error is not None:
        first = str(error).splitlines()[0] if str(error) else repr(error)
        raise SbomError(f"SBOM does not match the CycloneDX {SPEC_VERSION} schema: {first}")


def render(bom: dict) -> str:
    return json.dumps(bom, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--output", type=Path, help="write here instead of stdout")
    parser.add_argument("--dist", type=Path, help="directory of built packages; adds each skill.zip SHA-256")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true", help="build and validate only; write nothing")
    args = parser.parse_args(argv)
    try:
        bom = build(args.root.resolve(), args.dist)
        validate(bom)
    except SbomError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    text = render(bom)
    if args.check:
        print(f"OK: CycloneDX {SPEC_VERSION} SBOM valid ({len(bom['components'])} components)")
    elif args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"OK: wrote {args.output} ({len(bom['components'])} components)")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
