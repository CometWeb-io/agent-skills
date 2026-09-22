#!/usr/bin/env python3
"""Run local repository checks, without Actions, installation or publication.

Execute only in a trusted checkout: repository tests are executable code, not a
sandbox. Reports contain local command output; review before sharing them.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CHECKS = (
    ("openai_plugin", "tooling/validate_openai_plugin.py", ()),
    ("registry", "tooling/validate_repo.py", ()),
    ("orchestrator", "tooling/sync_orchestrator.py", ("--check",)),
    ("compatibility", "tooling/compatibility.py", ()),
    ("adapters", "tooling/generate_adapters.py", ("--check",)),
    ("routing", "tooling/run_routing_evals.py", ()),
    ("context_fixtures", "tooling/run_behavior_evals.py", ()),
    ("protocol", "tooling/validate_envelope.py", ("fixtures/cwaip-v2/evidence-final.json", "--final")),
    ("context_budget", "tooling/context_budget.py", ("--check",)),
    ("eval_strength", "tooling/eval_strength.py", ("--check",)),
)
# Gates that run as an installed module rather than a repo script. They are kept
# apart from CHECKS because every CHECKS entry is also validated as a file on
# disk and watched for changes, which cannot apply to a third-party tool.
MODULE_CHECKS = (
    ("lint", ("ruff", "check", ".")),
)
REQUIRED = ("plugin.json", ".agents/plugins/marketplace.json", "registry/skills.json", "registry/hosts.json", "requirements-dev.txt",
            "fixtures/cwaip-v2/evidence-final.json", "tooling/validate_local.py")
MAX_FILE = 32 * 1024 * 1024


def encoded(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def unique_pairs(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def safe_file(root: Path, relative: str) -> Path:
    if (not isinstance(relative, str) or not relative or relative.startswith("/")
            or "\\" in relative or any(p in {"", ".", ".."} for p in relative.split("/"))):
        raise ValueError("invalid repository path")
    path = root
    for part in relative.split("/"):
        path = path / part
        if path.is_symlink():
            raise ValueError(f"symlink not supported: {relative}")
    if not path.is_file() or not stat.S_ISREG(path.stat().st_mode):
        raise ValueError(f"missing regular file: {relative}")
    return path


def require_module_tools() -> None:
    """Fail with the reason, not just a red check, when a gate's tool is absent.

    A missing ruff makes the lint step exit non-zero like any other failure,
    which reads as "your code is broken" rather than "install the dev
    requirements". Say which it is.
    """
    for name, args in MODULE_CHECKS:
        module = args[0]
        if importlib.util.find_spec(module) is None:
            raise ValueError(
                f"{name} gate needs the {module!r} package: "
                f"pip install -r requirements-dev.txt"
            )


def inventory(root: Path) -> dict:
    """Reject incomplete overlays before executing any check."""
    require_module_tools()
    for relative in (*REQUIRED, *(row[1] for row in CHECKS)):
        safe_file(root, relative)
    data = json.loads((root / "registry/skills.json").read_bytes(), object_pairs_hook=unique_pairs)
    rows = data.get("skills") if isinstance(data, dict) else None
    if not isinstance(rows, list) or not rows:
        raise ValueError("registry.skills must be a nonempty list")
    names = [row.get("id") if isinstance(row, dict) else None for row in rows]
    if any(not isinstance(n, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", n) for n in names):
        raise ValueError("invalid registry skill identifier")
    if len(names) != len(set(names)):
        raise ValueError("duplicate registry skill identifier")
    disk = {p.name for p in (root / "skills").iterdir() if p.is_dir() and not p.name.startswith(".")}
    if disk != set(names):
        raise ValueError("registry and skill directories differ")
    test_dirs, no_tests = ["tooling/tests"], []
    for name in sorted(names):
        for filename in ("SKILL.md", "VERSION", "LICENSE"):
            safe_file(root, f"skills/{name}/{filename}")
        directory = root / "skills" / name / "tests"
        if directory.is_dir():
            test_dirs.append(f"skills/{name}/tests")
        else:
            no_tests.append(name)
    for directory in test_dirs:
        path = root / directory
        if path.is_symlink() or not any(path.rglob("test_*.py")):
            raise ValueError(f"missing tests: {directory}")
    return {"skills": sorted(names), "test_directories": test_dirs, "skills_without_tests": no_tests}


def git(root: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True,
                          stdin=subprocess.DEVNULL, timeout=30).stdout


def source_state(root: Path) -> dict:
    if Path(os.fsdecode(git(root, "rev-parse", "--show-toplevel")).strip()).resolve() != root:
        raise ValueError("--root must be the full Git working-tree root")
    if git(root, "ls-files", "-u"):
        raise ValueError("unresolved Git merge conflicts")
    revision = git(root, "rev-parse", "HEAD").decode().strip()
    tracked = git(root, "ls-files", "--cached", "-z").split(b"\0")
    untracked = git(root, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0")
    hashes = {}
    for raw in sorted(set(tracked + untracked) - {b""}):
        relative = os.fsdecode(raw)
        path = safe_file(root, relative)
        if path.stat().st_size > MAX_FILE:
            raise ValueError("source file exceeds fingerprint budget")
        with path.open("rb") as handle:
            blob = handle.read(MAX_FILE + 1)
        if len(blob) > MAX_FILE:
            raise ValueError("source grew beyond fingerprint budget")
        hashes[relative] = {"sha256": hashlib.sha256(blob).hexdigest(),
                            "executable": bool(path.stat().st_mode & 0o111)}
    return {"revision": revision, "index_fingerprint": hashlib.sha256(git(root, "ls-files", "--stage", "-z")).hexdigest(),
            "fingerprint": hashlib.sha256(encoded(hashes)).hexdigest(),
            "fingerprint_scope": "tracked_and_nonignored_untracked_files",
            "files": hashes, "dirty": bool(git(root, "status", "--porcelain", "--untracked-files=all"))}


def commands(scope: dict, output: Path) -> list[tuple[str, list[str]]]:
    rows = [(name, [sys.executable, "-B", "-m", *args]) for name, args in MODULE_CHECKS]
    rows += [(name, [sys.executable, "-B", script, *args]) for name, script, args in CHECKS]
    rows.append(("pytest", [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                            "--import-mode=importlib", "-o", "addopts=", f"--junitxml={output / 'junit.xml'}",
                            *scope["test_directories"]]))
    return rows


def junit_counts(path: Path) -> dict:
    with path.open("rb") as handle:
        blob = handle.read(MAX_FILE + 1)
    if len(blob) > MAX_FILE or b"<!DOCTYPE" in blob.upper() or b"<!ENTITY" in blob.upper():
        raise ValueError("unsupported or oversized JUnit")
    root = ET.fromstring(blob)
    if root.tag not in {"testsuite", "testsuites"}:
        raise ValueError("invalid JUnit root")
    cases = list(root.iter("testcase"))
    if not cases:
        raise ValueError("JUnit contains no executed test cases")
    return {"tests": len(cases), **{key: sum(case.find(tag) is not None for case in cases)
            for key, tag in (("failures", "failure"), ("errors", "error"), ("skipped", "skipped"))}}


def run_step(root: Path, command: list[str], log: Path, timeout: int) -> dict:
    started = time.monotonic()
    environment = os.environ.copy()
    environment.update(PYTHONDONTWRITEBYTECODE="1", PYTEST_ADDOPTS="")
    # Keep test selection in the command visible; do not inherit PYTEST_ADDOPTS.
    with log.open("xb") as handle:
        try:
            result = subprocess.run(command, cwd=root, stdout=handle, stderr=subprocess.STDOUT,
                                    stdin=subprocess.DEVNULL, timeout=timeout, env=environment)
            status, code = ("passed" if result.returncode == 0 else "failed"), result.returncode
        except subprocess.TimeoutExpired:
            status, code = "timeout", None
        except OSError:
            status, code = "execution_error", None
    return {"status": status, "returncode": code, "seconds": round(time.monotonic() - started, 3),
            "log": log.name, "command": command}


def run(root: Path, output: Path, timeout: int = 300) -> dict:
    root = root.absolute()
    if any(p.is_symlink() for p in (root, *root.parents)):
        raise ValueError("checkout path contains a symlink")
    root = root.resolve()
    if type(timeout) is not int or not 1 <= timeout <= 1800:
        raise ValueError("timeout must be an integer between 1 and 1800")
    scope = inventory(root)
    before = source_state(root)
    required_sources = {*REQUIRED, *(row[1] for row in CHECKS)}
    required_sources.update(f"skills/{sid}/{name}" for sid in scope["skills"] for name in ("SKILL.md", "VERSION", "LICENSE"))
    if not required_sources <= before["files"].keys():
        raise ValueError("required source file is ignored and not captured in the fingerprint")
    if output.resolve().is_relative_to(root) or output.exists() or output.is_symlink():
        raise ValueError("output must be a new directory outside the checkout")
    if not output.parent.is_dir() or any(p.is_symlink() for p in (output.parent, *output.parents)):
        raise ValueError("output parent must exist without symlink ancestors")
    output.mkdir(mode=0o700)
    report = {"schema": "cometweb.local-validation/v1", "status": "running",
              "started_at": datetime.now(timezone.utc).isoformat(), "python": sys.version,
              "scope": scope, "source_before": before, "checks": [],
              "not_assessed": ["model_behavior", "host_acceptance", "package_installation", "release_readiness"],
              "environment_fingerprint": "not_captured",
              "github_actions_used": False, "publication_performed": False}
    try:
        # Compile in memory: syntax checking must not create .pyc files in the source tree.
        syntax_errors = []
        for relative in before["files"]:
            if relative.endswith(".py") and relative.startswith(("tooling/", "skills/")):
                try:
                    compile(safe_file(root, relative).read_bytes(), relative, "exec")
                except SyntaxError:
                    syntax_errors.append(relative)
        report["checks"].append({"id": "syntax", "status": "failed" if syntax_errors else "passed", "files_with_errors": syntax_errors})
        for name, command in commands(scope, output):
            result = run_step(root, command, output / f"{name}.log", timeout)
            if name == "pytest" and result["status"] == "passed":
                try:
                    counts = junit_counts(output / "junit.xml")
                    result["junit"] = counts
                    if counts["failures"] or counts["errors"]:
                        result["status"] = "failed"
                    elif counts["skipped"]:
                        result["status"] = "incomplete"
                except (OSError, ValueError, ET.ParseError):
                    result["status"] = "invalid_test_report"
            report["checks"].append({"id": name, **result})
            if result["status"] in {"timeout", "execution_error"}:
                report["status"] = "incomplete"
                break
            after = source_state(root)
            if before != after:
                report["status"] = "source_changed"
                break
        else:
            report["status"] = "passed" if all(c["status"] == "passed" for c in report["checks"]) else "failed"
        report["source_after"] = source_state(root)
        if before != report["source_after"]:
            report["status"] = "source_changed"
    except KeyboardInterrupt:
        report.update(status="interrupted")
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        report.update(status="incomplete", error_type=type(exc).__name__)
    finally:
        completed = {c["id"] for c in report["checks"]}
        report["not_run"] = [name for name, _ in commands(scope, output) if name not in completed]
        report["completed_at"] = datetime.now(timezone.utc).isoformat()
        with (output / "report.json").open("xb") as handle:
            handle.write(encoded(report))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--plan", action="store_true", help="Validate inventory and print commands without running them")
    parser.add_argument("--timeout", type=int, default=300, help="Per-command timeout in seconds (1-1800)")
    args = parser.parse_args(argv)
    if not 1 <= args.timeout <= 1800 or (not args.plan and args.output is None):
        parser.error("provide --output for execution and a timeout between 1 and 1800")
    try:
        root = args.root.absolute()
        if any(p.is_symlink() for p in (root, *root.parents)):
            raise ValueError("checkout path contains a symlink")
        root = root.resolve()
        if args.plan:
            scope = inventory(root)
            print(encoded({"status": "plan_only", "scope": scope,
                           "commands": commands(scope, Path("<report-directory>"))}).decode(), end="")
            return 0
        result = run(root, args.output.absolute(), args.timeout)
        print(json.dumps({"status": result["status"], "report": str(args.output / "report.json")}))
        return 0 if result["status"] == "passed" else 1
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "preflight_failed", "error_type": type(exc).__name__, "detail": str(exc) if isinstance(exc, ValueError) else "Local checkout or tool unavailable"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
