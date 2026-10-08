#!/usr/bin/env python3
"""Run every repository gate from one place: the list CI runs, and nothing else.

    uv run python tooling/check_all.py            # every gate, in parallel
    uv run python tooling/check_all.py --fast     # the quick ones, for each commit
    uv run python tooling/check_all.py --fix      # regenerate derived files, then check
    uv run python tooling/check_all.py --only routing_evals,adapters
    uv run python tooling/check_all.py --list     # what runs, and what --fast leaves out

GATES below is the single source of truth. `.github/workflows/validate.yml`
calls this script with `--ci` instead of listing commands of its own, and
`tooling/tests/test_check_all.py` fails if the workflow grows a gate step of its
own, so the local and CI gate lists cannot drift apart.

`--fix` runs only generators: tools whose output is a pure function of tracked
sources (registry sync, adapters, shared copies, the lockfile). Baselines that
record a decision -- the context budget and eval strength -- are never
accepted automatically; a failing gate prints the command that accepts it.

This executes repository code (tests, harnesses) and is not a sandbox.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
PY = "{python}"


@dataclass(frozen=True)
class Gate:
    id: str
    argv: tuple[str, ...]
    summary: str
    fast: bool = True
    # Generator command that brings the checked files back in line. Run by --fix.
    fix: tuple[str, ...] | None = None
    # What to run when the gate fails on a deliberate baseline, not a defect.
    hint: str | None = None
    # A non-Python executable the gate needs. Missing locally: reported as
    # skipped. Missing under --ci: a failure, because CI must prove every gate.
    tool: str | None = None
    # Rough seconds on a laptop; the slowest gates start first.
    cost: float = 1.0
    # Extra arguments under --ci only, where a check must not be skipped.
    ci_args: tuple[str, ...] = ()
    # (other gate id, arguments): appended when that other gate runs in the same
    # invocation, so work it already does is not done twice.
    defer: tuple[str, tuple[str, ...]] | None = None


def _python(*args: str) -> tuple[str, ...]:
    return (PY, "-B", *args)


# Test modules that check one skill package at a time and finish in seconds.
# This list is what --fast adds; a full run leaves them out of the pytest gate
# (see Gate.defer) so they are not collected and run twice.
PACKAGE_TESTS = (
    "test_skill_eval_harnesses.py",
    "test_untrusted_content_rules.py",
    "test_front_door_rules.py",
    "test_front_door_ceiling.py",
    "test_skill_doc_references.py",
    "test_package_layout_consistency.py",
    "test_scripts_are_executable.py",
    "test_skill_scripts_import.py",
    "test_skill_script_cli_contract.py",
    "test_bundle_version.py",
)

GATES: tuple[Gate, ...] = (
    # Static analysis and supply chain.
    Gate("ruff", _python("-m", "ruff", "check", "."), "lint (defect rules only)"),
    Gate("bandit", _python("-m", "bandit", "-c", ".bandit", "-q", "-ll", "-r", "tooling", "skills",
                           "-x", "*/tests/*"), "Python security static analysis", cost=2),
    Gate("shellcheck", ("shellcheck", "{shell_scripts}"), "shell scripts", tool="shellcheck", cost=1.5),
    Gate("uv_lock", ("uv", "lock", "--check"), "uv.lock matches pyproject.toml", tool="uv",
         fix=("uv", "lock")),
    # Locally a clean result is reused while every input hashes the same; CI
    # always runs the engine.
    Gate("sast", _python("tooling/sast.py"), "semgrep rules for Python and shell (pinned engine, offline)",
         tool="uv", fast=False, cost=25, ci_args=("--no-cache",)),
    Gate("runtime_deps_locked", _python("tooling/audit_deps.py", "--coverage"),
         "skill RUNTIME.json dependencies are locked, so pip-audit covers them"),
    Gate("sbom", _python("tooling/sbom.py", "--check"), "plugin CycloneDX SBOM builds and validates"),
    Gate("pip_audit", _python("tooling/audit_deps.py"), "known vulnerabilities in every locked group, "
         "hash-checked (network)", fast=False, cost=12),
    # Registry, generated files and copies that must stay byte-identical.
    Gate("registry_sync", _python("tooling/sync_skill_registry.py", "--check"),
         "registry entries owned by sync_skill_registry.OVERRIDES",
         fix=_python("tooling/sync_skill_registry.py", "--apply")),
    Gate("orchestrator_sync", _python("tooling/sync_orchestrator.py", "--check"),
         "orchestrator kernel copies", fix=_python("tooling/sync_orchestrator.py")),
    Gate("roaster_shared", _python("tooling/sync_roaster_shared.py", "--check"),
         "shared roaster files", fix=_python("tooling/sync_roaster_shared.py", "--sync")),
    Gate("adapters", _python("tooling/generate_adapters.py", "--check"),
         "generated adapters, tables and README catalog",
         fix=_python("tooling/generate_adapters.py")),
    Gate("validate_repo", _python("tooling/validate_repo.py"), "registry agrees with packages"),
    Gate("skill_contracts", _python("tooling/skill_contracts.py", "--check"),
         "skill scripts, docs and eval cases match references/contract.json"),
    Gate("compatibility", _python("tooling/compatibility.py"), "host capability contract"),
    Gate("openai_plugin", _python("tooling/validate_openai_plugin.py"), "OpenAI plugin manifest"),
    # Not fast: a skill change is recorded once per pull request, after its
    # VERSION bumps, the same way a deliberate baseline change is.
    Gate("plugin_release", _python("tooling/plugin_release.py", "--check"),
         "plugin version covers shipped skill changes", fast=False, ci_args=("--require-base",),
         hint="bump and record in one step: uv run python tooling/plugin_release.py --bump patch "
              "(minor for a new skill or behaviour)"),
    Gate("skill_change_history", _python("tooling/skill_change_history.py", "--check"),
         "changed instructions/scripts have package versions and changelogs", fast=False, ci_args=("--require-base",)),
    Gate("context_budget", _python("tooling/context_budget.py", "--check",
                                   "--verify-table", "docs/generated-context-budget.md"),
         "SKILL.md front-door cost against the baseline",
         fix=_python("tooling/context_budget.py", "--table", "docs/generated-context-budget.md"),
         hint="only if a front door grew on purpose, accept it: uv run python tooling/context_budget.py --update "
              "--table docs/generated-context-budget.md"),
    # Deterministic evals.
    Gate("routing_evals", _python("tooling/run_routing_evals.py"), "routing suite"),
    Gate("routing_coverage", _python("tooling/routing_coverage.py", "--check"),
         "routing floors per skill"),
    Gate("routing_holdout", _python("tooling/routing_holdout.py", "--check"),
         "frozen routing holdout unchanged and unseen by tuned sets"),
    Gate("policy_evals", _python("tooling/run_policy_evals.py"), "routing policy admission"),
    Gate("routing_adversarial", _python("tooling/run_policy_evals.py", "--suite",
                                        "evals/routing/adversarial-suite.json"),
         "injection-style prompts cannot invoke or lift a denial"),
    Gate("behavior_evals", _python("tooling/run_behavior_evals.py"), "behavior fixtures",
         ci_args=("--require-runtime",)),
    Gate("blind_eval_harness", _python("tooling/run_blind_eval_harness.py"),
         "behavior suites are well formed"),
    Gate("output_grading", _python("tooling/grade_output.py", "--self-test"),
         "golden skill outputs: good ones pass, broken ones fail with their exact codes"),
    Gate("envelope", _python("tooling/validate_envelope.py", "fixtures/cwaip-v2/evidence-final.json",
                             "--final"), "CW-AIP final envelope fixture"),
    Gate("eval_strength", _python("tooling/eval_strength.py", "--check"),
         "harnesses still pin every recorded guard", fast=False, cost=40,
         hint="only if a held count changed on purpose, record it: uv run python tooling/eval_strength.py --update "
              "--table docs/generated-eval-strength.md"),
    # The package-level slice of the test suite: per skill and quick, so a
    # harness a new rule broke, a missing untrusted-content block or a manifest
    # left behind by a version bump fails the inner loop, not only the full run.
    Gate("skill_package_tests", _python("-m", "pytest", "-q", "--tb=short", "-n", "4", "-p", "no:cacheprovider",
                                        *(f"tooling/tests/{name}" for name in PACKAGE_TESTS)),
         "per-skill package tests: eval harnesses, front-door rules, script CLIs, manifests", cost=5),
    # Leak gates.
    Gate("public_safety", _python("tooling/public_safety.py", "--root", "."), "leak scan, working tree",
         cost=1.5),
    Gate("public_safety_history", _python("tooling/public_safety.py", "--root", ".", "--history"),
         "leak scan, every reachable commit", fast=False, cost=6),
    # Tests and packaging.
    # When skill_package_tests runs too, the full suite leaves those modules to
    # it instead of collecting and running them a second time.
    Gate("pytest", _python("-m", "pytest", "-q", "-n", "auto", "-p", "no:cacheprovider"),
         "full test suite", fast=False, cost=60,
         defer=("skill_package_tests", tuple(f"--ignore=tooling/tests/{name}" for name in PACKAGE_TESTS))),
    Gate("installation_acceptance", _python("tooling/installation_acceptance.py", "--all",
                                            "--run-helpers", "--trusted-checkout"),
         "build, extract and run every package", fast=False, cost=150),
)
GATE_IDS = tuple(g.id for g in GATES)


@dataclass
class Result:
    gate: Gate
    status: str  # passed | failed | skipped
    seconds: float
    output: str
    returncode: int | None = None


def shell_scripts(root: Path) -> list[str]:
    try:
        listed = subprocess.run(["git", "ls-files", "-z", "--", "*.sh"], cwd=root, capture_output=True,
                                check=True, timeout=30).stdout.decode().split("\0")
        return sorted(p for p in listed if p)
    except (OSError, subprocess.SubprocessError):
        return sorted(p.relative_to(root).as_posix() for p in root.rglob("*.sh")
                      if ".venv" not in p.parts and ".git" not in p.parts)


def expand(argv: tuple[str, ...], root: Path) -> list[str]:
    out: list[str] = []
    for token in argv:
        if token == PY:
            out.append(sys.executable)
        elif token == "{shell_scripts}":
            out.extend(shell_scripts(root))
        else:
            out.append(token)
    return out


def tree_state(root: Path) -> str | None:
    """Porcelain status plus a diff digest; None outside a Git checkout."""
    try:
        status = subprocess.run(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=root,
                                capture_output=True, check=True, timeout=60).stdout
        diff = subprocess.run(["git", "diff", "--binary", "HEAD"], cwd=root, capture_output=True,
                              check=False, timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    return status.decode(errors="replace") + hashlib.sha256(diff).hexdigest()


def run_command(argv: list[str], root: Path, timeout: int) -> tuple[int | None, str, float]:
    started = time.monotonic()
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
    env.pop("PYTEST_ADDOPTS", None)
    try:
        proc = subprocess.run(argv, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              stdin=subprocess.DEVNULL, env=env, timeout=timeout, check=False)
        code, output = proc.returncode, proc.stdout.decode("utf-8", errors="replace")
    except subprocess.TimeoutExpired as exc:
        code = None
        output = (exc.stdout or b"").decode("utf-8", errors="replace") + f"\nTIMEOUT after {timeout}s"
    except OSError as exc:
        code, output = None, f"could not start {argv[0]}: {exc}"
    return code, output, time.monotonic() - started


def gate_argv(gate: Gate, ci: bool, selected: frozenset[str] = frozenset()) -> tuple[str, ...]:
    argv = (*gate.argv, *gate.ci_args) if ci else gate.argv
    if gate.defer and gate.defer[0] in selected:
        argv = (*argv, *gate.defer[1])
    return argv


def run_gate(gate: Gate, root: Path, timeout: int, ci: bool, selected: frozenset[str] = frozenset()) -> Result:
    if gate.tool and shutil.which(gate.tool) is None:
        message = f"{gate.tool} is not installed"
        return Result(gate, "failed" if ci else "skipped", 0.0, message)
    if gate.id == "shellcheck" and not shell_scripts(root):
        return Result(gate, "passed", 0.0, "no shell scripts")
    argv = gate_argv(gate, ci, selected)
    code, output, seconds = run_command(expand(argv, root), root, timeout)
    return Result(gate, "passed" if code == 0 else "failed", seconds, output, code)


def select(args: argparse.Namespace) -> list[Gate]:
    def ids(raw: str | None) -> set[str]:
        chosen = {part.strip() for part in (raw or "").split(",") if part.strip()}
        unknown = sorted(chosen - set(GATE_IDS))
        if unknown:
            raise SystemExit(f"unknown gate(s): {', '.join(unknown)}; see --list")
        return chosen

    only, skip = ids(args.only), ids(args.skip)
    gates = [g for g in GATES if (not only or g.id in only) and g.id not in skip]
    if args.fast and not only:
        gates = [g for g in gates if g.fast]
    return gates


def print_list() -> None:
    width = max(len(g.id) for g in GATES)
    for gate in GATES:
        mode = "fast" if gate.fast else "full"
        fix = "  [--fix]" if gate.fix else ""
        print(f"{gate.id:<{width}}  {mode}  {gate.summary}{fix}")


def fix(gates: list[Gate], root: Path, timeout: int) -> bool:
    """Run each selected gate's generator once, in GATES order (registry before adapters)."""
    ok = True
    for gate in gates:
        if not gate.fix or (gate.tool and shutil.which(gate.tool) is None):
            continue
        code, output, seconds = run_command(expand(gate.fix, root), root, timeout)
        print(f"fix   {gate.id:<24} {'ok' if code == 0 else 'FAILED'} {seconds:6.1f}s", flush=True)
        if code != 0:
            ok = False
            print(output.rstrip())
    return ok


def report(results: list[Result], wall: float, show_output: bool) -> None:
    in_actions = os.environ.get("GITHUB_ACTIONS") == "true"
    for result in results:
        if result.status == "failed" or show_output or in_actions:
            if in_actions:
                print(f"::group::{result.gate.id} ({result.status})")
            else:
                print(f"\n----- {result.gate.id} ({result.status}) -----")
            print(result.output.rstrip())
            if in_actions:
                print("::endgroup::")
    width = max(len(r.gate.id) for r in results)
    print()
    print(f"{'gate':<{width}}  {'status':<7}  {'time':>7}")
    print(f"{'-' * width}  -------  -------")
    for result in results:
        mark = {"passed": "ok", "failed": "FAIL", "skipped": "skip"}[result.status]
        print(f"{result.gate.id:<{width}}  {mark:<7}  {result.seconds:6.1f}s")
    failed = [r for r in results if r.status == "failed"]
    skipped = [r for r in results if r.status == "skipped"]
    print()
    print(f"{len(results) - len(failed) - len(skipped)} passed, {len(failed)} failed, "
          f"{len(skipped)} skipped in {wall:.1f}s wall "
          f"({sum(r.seconds for r in results):.1f}s of gate time)")
    for result in skipped:
        print(f"skipped {result.gate.id}: {result.output}")
    for result in failed:
        if result.gate.fix:
            print(f"{result.gate.id}: regenerate with --fix")
        if result.gate.hint:
            print(f"{result.gate.id}: {result.gate.hint}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fast", action="store_true",
                        help="only the quick gates: the per-skill package tests, but not the full pytest "
                             "suite, eval strength, package builds or network")
    parser.add_argument("--only", metavar="IDS", help="comma-separated gate ids to run")
    parser.add_argument("--skip", metavar="IDS", help="comma-separated gate ids to leave out")
    parser.add_argument("--fix", action="store_true",
                        help="run the generators of the selected gates before checking")
    parser.add_argument("--ci", action="store_true",
                        help="every gate; a missing tool fails instead of skipping")
    parser.add_argument("--jobs", type=int, default=min(8, os.cpu_count() or 2),
                        help="gates to run at once (default: CPU count, at most 8)")
    parser.add_argument("--timeout", type=int, default=1200, help="per-gate timeout in seconds")
    parser.add_argument("--verbose", action="store_true", help="print the output of passing gates too")
    parser.add_argument("--list", action="store_true", help="list the gates and exit")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.list:
        print_list()
        return 0
    if args.ci and (args.fast or args.only or args.skip or args.fix):
        parser.error("--ci runs every gate unchanged; it cannot be combined with --fast/--only/--skip/--fix")
    if args.jobs < 1:
        parser.error("--jobs must be at least 1")
    root = args.root.resolve()
    gates = select(args)
    if not gates:
        parser.error("no gates selected")

    started = time.monotonic()
    if args.fix and not fix(gates, root, args.timeout):
        print("FAIL: a generator failed; not running the checks")
        return 1
    before = tree_state(root)
    results: dict[str, Result] = {}
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        selected = frozenset(g.id for g in gates)
        futures = {pool.submit(run_gate, gate, root, args.timeout, args.ci, selected): gate
                   for gate in sorted(gates, key=lambda g: -g.cost)}
        for future in as_completed(futures):
            result = future.result()
            results[result.gate.id] = result
            print(f"{result.status:<7} {result.gate.id:<24} {result.seconds:6.1f}s", flush=True)
    ordered = [results[g.id] for g in gates]
    if before is not None and tree_state(root) != before:
        ordered.append(Result(Gate("tree_unchanged", (), "gates leave the checkout untouched"), "failed", 0.0,
                              "a gate modified the working tree; see `git status`"))
    report(ordered, time.monotonic() - started, args.verbose)
    return 1 if any(r.status == "failed" for r in ordered) else 0


if __name__ == "__main__":
    raise SystemExit(main())
