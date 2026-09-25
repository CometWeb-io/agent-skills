#!/usr/bin/env python3
"""Package installation acceptance — structural, not host/model acceptance.

Builds each skill that declares RUNTIME.json (or every skill with --all) into a
temporary clean Git fixture tree, installs the zip into an isolated directory,
and verifies required identity files plus RUNTIME.json round-trip. Opt-in helper
smokes execute bundled offline checks from the extracted ZIP, outside the repo.

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


def helper_smoke(install: Path, skill: str, timeout: int = 120) -> dict:
    """Execute only known offline entrypoints in a trusted package, not host QA."""
    from core.subprocess_env import build_runner_env

    commands = []
    for script in ("run_evals.py", "self_check.py"):
        path = install / "scripts" / script
        if path.is_file():
            commands.append((script, [sys.executable, "-B", str(path)], 0, None))
    with tempfile.TemporaryDirectory(prefix="cw-helper-smoke-") as tmp:
        cwd = Path(tmp)
        if skill == "skill-orchestrator-multiagent":
            validator = install / "scripts/validate_envelope.py"
            envelope = {
                "id": "fixture:EvidenceEnvelope:smoke", "type": "EvidenceEnvelope",
                "producer": "fixture", "protocol_version": "1.0", "subject": "synthetic smoke",
                "as_of": "2026-09-25T00:00:00Z", "payload": {},
            }
            valid, invalid = cwd / "valid.json", cwd / "invalid.json"
            valid.write_text(json.dumps(envelope), encoding="utf-8")
            invalid.write_text(json.dumps({**envelope, "id": 17}), encoding="utf-8")
            commands.extend([
                ("valid_envelope", [sys.executable, "-B", str(validator), str(valid)], 0, "OK:"),
                ("invalid_envelope", [sys.executable, "-B", str(validator), str(invalid)], 1, "FAIL: schema:"),
                ("missing_dependency", [sys.executable, "-B", "-S", str(validator), str(valid)],
                 1, "jsonschema dependency is required"),
            ])
        rows = []
        for name, command, expected, marker in commands:
            try:
                proc = subprocess.run(command, cwd=cwd, env=build_runner_env(set()),
                                      stdin=subprocess.DEVNULL, capture_output=True, text=True,
                                      timeout=timeout)
                output = proc.stdout + proc.stderr
                passed = proc.returncode == expected and (marker is None or marker in output)
                rows.append({"check": name, "status": "passed" if passed else "failed",
                             "returncode": proc.returncode, "expected_returncode": expected,
                             "output": output[-4000:]})
            except subprocess.TimeoutExpired:
                rows.append({"check": name, "status": "timeout"})
            except OSError:
                rows.append({"check": name, "status": "execution_error"})
    return {
        "status": ("not_assessed" if not rows else
                   "passed" if all(row["status"] == "passed" for row in rows) else "failed"),
        "scope": "offline_bundled_helpers_only", "checks": rows,
    }


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


def accept_one(root: Path, skill: str, work: Path, *, run_helpers: bool = False) -> dict:
    from package_skill import identifier, inspect_archive

    identifier(skill)
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
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false",
                    "commit", "-m", "acceptance"], cwd=package_root, check=True, capture_output=True)

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
    manifest = inspect_archive(archive.read_bytes())
    install = work / "install" / skill
    install.mkdir(parents=True)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(install)
    required = ["SKILL.md", "VERSION", "LICENSE", "PACKAGE-MANIFEST.json"]
    missing = [name for name in required if not (install / name).is_file()]
    runtime_src = root / "skills" / skill / "RUNTIME.json"
    if runtime_src.is_file() and not (install / "RUNTIME.json").is_file():
        missing.append("RUNTIME.json")
    if manifest.get("runtime_acceptance") != "not_assessed":
        return {"skill": skill, "status": "false_acceptance_claim", "manifest": manifest.get("runtime_acceptance")}
    if missing:
        return {"skill": skill, "status": "missing_files", "missing": missing}
    smoke = helper_smoke(install, skill) if run_helpers else {"status": "not_assessed", "checks": []}
    return {
        "skill": skill,
        "status": "helper_failed" if smoke["status"] == "failed" else "passed",
        "version": report["version"],
        "payload_sha256": report["payload_sha256"],
        "installation_acceptance": "passed",
        "helper_smoke": smoke,
        "verified_runtime_acceptance": "not_assessed",
        "host_acceptance": "not_assessed",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--all", action="store_true", help="Accept every skill, not only RUNTIME.json skills")
    parser.add_argument("--skill", action="append", default=[])
    parser.add_argument("--run-helpers", action="store_true", help="Run bundled offline checks after extraction")
    parser.add_argument("--trusted-checkout", action="store_true", help="Acknowledge execution of trusted package code")
    args = parser.parse_args(argv)
    if args.run_helpers and not args.trusted_checkout:
        parser.error("--run-helpers requires --trusted-checkout; this is not a sandbox")
    selected = list(dict.fromkeys(args.skill)) or (all_skills(args.root) if args.all else skills_with_runtime(args.root))
    if not selected or not set(selected) <= set(all_skills(args.root)):
        print(json.dumps({"status": "failed", "reason": "no skills selected or unknown skill"}))
        return 1
    rows = []
    with tempfile.TemporaryDirectory(prefix="cw-install-accept-") as tmp:
        for skill in selected:
            rows.append(accept_one(args.root, skill, Path(tmp) / skill, run_helpers=args.run_helpers))
    failed = [row for row in rows if row["status"] != "passed"]
    result = {
        "schema": "cometweb.installation-acceptance/v1",
        "status": "passed" if not failed else "failed",
        "skills": rows,
        "note": "installation_acceptance confirms zip admission, extraction and identity files; helper_smoke separately records offline execution; host/model acceptance remains not_assessed",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
