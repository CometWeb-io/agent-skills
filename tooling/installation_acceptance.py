#!/usr/bin/env python3
"""Package installation acceptance — structural, not host/model acceptance.

Builds each skill that declares RUNTIME.json (or every skill with --all) into a
temporary clean Git fixture tree, installs the zip into an isolated directory,
and verifies required identity files plus RUNTIME.json round-trip.

This is NOT verified_runtime_acceptance for Cursor/ChatGPT/Codex sessions.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def skills_with_runtime(root: Path) -> list[str]:
    return sorted(
        path.parent.name
        for path in (root / "skills").glob("*/RUNTIME.json")
        if path.is_file()
    )


def all_skills(root: Path) -> list[str]:
    return sorted(
        path.parent.name
        for path in (root / "skills").glob("*/SKILL.md")
        if path.is_file()
    )


def accept_one(root: Path, skill: str, work: Path) -> dict:
    package_root = work / "repo"
    shutil.copytree(
        root,
        package_root,
        ignore=shutil.ignore_patterns(
            ".git", ".venv", "dist", "__pycache__", ".pytest_cache", ".ruff_cache", "node_modules"
        ),
        dirs_exist_ok=False,
    )
    subprocess.run(["git", "init"], cwd=package_root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "acceptance@example.invalid"], cwd=package_root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Acceptance"], cwd=package_root, check=True, capture_output=True)
    (package_root / ".gitignore").write_text("dist/\n")
    subprocess.run(["git", "add", "-A"], cwd=package_root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "acceptance"], cwd=package_root, check=True, capture_output=True)

    proc = subprocess.run(
        [sys.executable, "-B", str(package_root / "tooling" / "package_skill.py"), skill, "--root", str(package_root)],
        cwd=package_root,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return {"skill": skill, "status": "package_failed", "detail": proc.stderr[-500:]}

    report = json.loads(proc.stdout)
    archive = package_root / report["path"]
    install = work / "install" / skill
    install.mkdir(parents=True)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(install)
    required = ["SKILL.md", "VERSION", "LICENSE", "PACKAGE-MANIFEST.json"]
    missing = [name for name in required if not (install / name).is_file()]
    runtime_src = root / "skills" / skill / "RUNTIME.json"
    if runtime_src.is_file() and not (install / "RUNTIME.json").is_file():
        missing.append("RUNTIME.json")
    manifest = json.loads((install / "PACKAGE-MANIFEST.json").read_text(encoding="utf-8"))
    if manifest.get("runtime_acceptance") != "not_assessed":
        return {"skill": skill, "status": "false_acceptance_claim", "manifest": manifest.get("runtime_acceptance")}
    if missing:
        return {"skill": skill, "status": "missing_files", "missing": missing}
    return {
        "skill": skill,
        "status": "passed",
        "version": report["version"],
        "payload_sha256": report["payload_sha256"],
        "installation_acceptance": "passed",
        "verified_runtime_acceptance": "not_assessed",
        "host_acceptance": "not_assessed",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--all", action="store_true", help="Accept every skill, not only RUNTIME.json skills")
    parser.add_argument("--skill", action="append", default=[])
    args = parser.parse_args(argv)
    selected = args.skill or (all_skills(args.root) if args.all else skills_with_runtime(args.root))
    if not selected:
        print(json.dumps({"status": "failed", "reason": "no skills selected"}))
        return 1
    rows = []
    with tempfile.TemporaryDirectory(prefix="cw-install-accept-") as tmp:
        for skill in selected:
            rows.append(accept_one(args.root, skill, Path(tmp) / skill))
    failed = [row for row in rows if row["status"] != "passed"]
    result = {
        "schema": "cometweb.installation-acceptance/v1",
        "status": "passed" if not failed else "failed",
        "skills": rows,
        "note": "installation_acceptance confirms zip extract + identity files; host/model acceptance remains not_assessed",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
