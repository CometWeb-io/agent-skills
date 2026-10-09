"""check_all.py is the one gate list; CI and the local runners may not drift from it.

The workflow used to spell out its own steps, validate_local.py kept a third
list, and CONTRIBUTING a fourth. Gates added to one were missing from the
others (sync_skill_registry, routing_coverage and the policy evals ran in no CI
step). These tests pin the single list and the runner's own failure paths.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "validate.yml"
CI_COMMAND = "uv run python tooling/check_all.py --ci"


def load(name: str):
    spec = importlib.util.spec_from_file_location(f"cw_{name}", ROOT / "tooling" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolve string annotations through sys.modules.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


check_all = load("check_all")


def run_steps() -> list[str]:
    data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    return [" ".join(step["run"].split()) for job in data["jobs"].values()
            for step in job.get("steps", []) if "run" in step]


def test_ci_runs_check_all_and_nothing_else() -> None:
    """A gate step written straight into the workflow would be a second list."""
    assert run_steps() == ["uv sync --frozen --group dev", CI_COMMAND]


def test_ci_mode_selects_every_gate() -> None:
    args = check_all.argparse.Namespace(only=None, skip=None, fast=False)
    assert [g.id for g in check_all.select(args)] == list(check_all.GATE_IDS)


def test_gate_ids_are_unique_and_scripts_exist() -> None:
    assert len(set(check_all.GATE_IDS)) == len(check_all.GATE_IDS)
    for gate in check_all.GATES:
        for argv in (gate.argv, gate.fix or ()):
            for token in argv:
                if token.startswith("tooling/") and token.endswith(".py"):
                    assert (ROOT / token).is_file(), f"{gate.id}: {token} does not exist"


def gate_scripts() -> set[str]:
    return {token for gate in check_all.GATES for token in gate.argv
            if token.startswith("tooling/") and token.endswith(".py")}


def test_every_tool_with_a_check_mode_is_a_gate() -> None:
    """A new `--check` mode that no gate calls is a check nobody runs."""
    declared = {f"tooling/{p.name}" for p in (ROOT / "tooling").glob("*.py")
                if re.search(r"add_argument\(\s*[\"']--check[\"']", p.read_text(encoding="utf-8"))}
    declared -= {"tooling/check_all.py"}
    missing = declared - gate_scripts()
    assert not missing, f"tools with --check that check_all.py never runs: {sorted(missing)}"


def test_validate_local_runs_a_subset_of_the_gates() -> None:
    local = load("validate_local")
    gates = {tuple(t for t in g.argv if t not in {check_all.PY, "-B"}) for g in check_all.GATES}
    for name, script, args in local.CHECKS:
        assert (script, *args) in gates, f"validate_local check {name} is not a check_all gate"
    for name, args in local.MODULE_CHECKS:
        assert ("-m", *args) in gates, f"validate_local check {name} is not a check_all gate"


def test_fast_leaves_out_only_the_slow_or_networked_gates() -> None:
    slow = {g.id for g in check_all.GATES if not g.fast}
    assert slow == {"pip_audit", "sast", "eval_strength", "plugin_release", "public_safety_history", "pytest",
                    "installation_acceptance", "skill_change_history"}


def test_fix_never_accepts_a_baseline() -> None:
    """Recording a baseline is a decision; --fix only regenerates derived files."""
    for gate in check_all.GATES:
        assert "--update" not in (gate.fix or ()), gate.id


def test_pre_commit_hook_runs_the_fast_gates() -> None:
    config = yaml.safe_load((ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    entries = [hook["entry"] for repo in config["repos"] for hook in repo["hooks"]]
    assert "uv run python tooling/check_all.py --fast" in entries


def test_contributing_points_at_check_all() -> None:
    text = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "tooling/check_all.py" in text


# The runner itself, against fake gates in a scratch Git repository.

def fake_gate(gate_id: str, code: str, **options):
    return check_all.Gate(gate_id, (check_all.PY, "-c", code), gate_id, **options)


@pytest.fixture
def scratch(tmp_path: Path) -> Path:
    for args in (("init", "-q"), ("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                                  "commit", "-q", "--allow-empty", "-m", "baseline")):
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)
    return tmp_path


def run(monkeypatch, root: Path, gates, *argv: str) -> int:
    monkeypatch.setattr(check_all, "GATES", tuple(gates))
    monkeypatch.setattr(check_all, "GATE_IDS", tuple(g.id for g in gates))
    return check_all.main(["--root", str(root), *argv])


def test_any_failing_gate_fails_the_run(monkeypatch, scratch, capsys) -> None:
    gates = [fake_gate("good", "pass"), fake_gate("bad", "import sys; print('boom'); sys.exit(3)")]
    assert run(monkeypatch, scratch, gates) == 1
    out = capsys.readouterr().out
    assert "boom" in out and "1 passed, 1 failed" in out


def test_only_and_fast_select_gates(monkeypatch, scratch, capsys) -> None:
    gates = [fake_gate("quick", "pass"), fake_gate("slow", "raise SystemExit(1)", fast=False)]
    assert run(monkeypatch, scratch, gates, "--fast") == 0
    assert run(monkeypatch, scratch, gates, "--only", "quick") == 0
    assert run(monkeypatch, scratch, gates, "--only", "slow") == 1
    with pytest.raises(SystemExit, match="unknown gate"):
        run(monkeypatch, scratch, gates, "--only", "nope")


def test_missing_tool_skips_locally_and_fails_in_ci(monkeypatch, scratch, capsys) -> None:
    gates = [check_all.Gate("needs_tool", ("definitely-not-installed-tool",), "x",
                            tool="definitely-not-installed-tool")]
    assert run(monkeypatch, scratch, gates) == 0
    assert "0 passed, 0 failed, 1 skipped" in capsys.readouterr().out
    assert run(monkeypatch, scratch, gates, "--ci") == 1


def test_a_gate_that_writes_into_the_checkout_fails(monkeypatch, scratch, capsys) -> None:
    gates = [fake_gate("writer", "open('stray.txt', 'w').write('x')")]
    assert run(monkeypatch, scratch, gates) == 1
    assert "tree_unchanged" in capsys.readouterr().out


def test_fix_runs_the_generator_before_the_check(monkeypatch, scratch, capsys) -> None:
    check = "import pathlib, sys; sys.exit(0 if pathlib.Path('generated.txt').exists() else 1)"
    gates = [fake_gate("generated", check, fix=(check_all.PY, "-c", "open('generated.txt', 'w').write('x')"))]
    assert run(monkeypatch, scratch, gates) == 1
    assert "regenerate with --fix" in capsys.readouterr().out
    assert run(monkeypatch, scratch, gates, "--fix") == 0
    assert (scratch / "generated.txt").is_file()


def test_ci_mode_cannot_be_narrowed(monkeypatch, scratch) -> None:
    with pytest.raises(SystemExit):
        run(monkeypatch, scratch, [fake_gate("one", "pass")], "--ci", "--fast")


def test_list_names_every_gate() -> None:
    proc = subprocess.run([sys.executable, str(ROOT / "tooling" / "check_all.py"), "--list"],
                          capture_output=True, text=True, timeout=60, check=False)
    assert proc.returncode == 0
    listed = [line.split()[0] for line in proc.stdout.splitlines() if line.strip()]
    assert listed == list(check_all.GATE_IDS)


def test_plugin_release_requires_a_base_only_under_ci(monkeypatch) -> None:
    """Locally a missing merge base is a note; CI must prove the version bump."""
    gate = next(g for g in check_all.GATES if g.id == "plugin_release")
    seen: list[list[str]] = []
    monkeypatch.setattr(check_all, "run_command", lambda argv, root, timeout: (seen.append(argv) or (0, "", 0.0)))
    check_all.run_gate(gate, ROOT, 10, ci=False)
    check_all.run_gate(gate, ROOT, 10, ci=True)
    assert "--require-base" not in seen[0]
    assert seen[1][-1] == "--require-base"


def test_fast_runs_the_per_skill_package_tests() -> None:
    """A harness broken by a new rule, or a skill missing its untrusted-content
    block, used to pass --fast and surface only in the three-minute full run."""
    gate = next(g for g in check_all.GATES if g.id == "skill_package_tests")
    assert gate.fast
    named = [t for t in gate.argv if t.startswith("tooling/tests/")]
    for required in ("test_skill_eval_harnesses.py", "test_untrusted_content_rules.py",
                     "test_front_door_rules.py", "test_bundle_version.py"):
        assert f"tooling/tests/{required}" in named
    for path in named:
        assert (ROOT / path).is_file(), path


def test_fast_context_gate_checks_the_generated_table() -> None:
    gate = next(g for g in check_all.GATES if g.id == "context_budget")
    assert gate.fast and "--verify-table" in gate.argv


def test_full_suite_leaves_the_package_tests_to_their_own_gate() -> None:
    """Under --ci both gates run; the package modules were collected and run twice."""
    pytest_gate = next(g for g in check_all.GATES if g.id == "pytest")
    package_gate = next(g for g in check_all.GATES if g.id == "skill_package_tests")
    both = frozenset({"pytest", "skill_package_tests"})
    ignored = {t.removeprefix("--ignore=") for t in check_all.gate_argv(pytest_gate, True, both)
               if t.startswith("--ignore=")}
    named = {t for t in package_gate.argv if t.startswith("tooling/tests/")}
    # What the full suite skips is exactly what the package gate runs, so nothing is lost.
    assert ignored == named
    # Run alone (--only pytest), the full suite still runs every module.
    assert not any(t.startswith("--ignore=") for t in check_all.gate_argv(pytest_gate, True, frozenset({"pytest"})))


def test_the_runner_passes_the_selection_to_each_gate(monkeypatch, scratch) -> None:
    calls: list[list[str]] = []

    def fake_run(argv, root, timeout):
        calls.append(argv)
        return 0, "", 0.0

    gates = [check_all.Gate("main", (check_all.PY, "-c", "pass"), "main", defer=("helper", ("--extra",))),
             fake_gate("helper", "pass")]
    monkeypatch.setattr(check_all, "run_command", fake_run)
    assert run(monkeypatch, scratch, gates) == 0
    assert any("--extra" in argv for argv in calls)
    calls.clear()
    assert run(monkeypatch, scratch, gates, "--only", "main") == 0
    assert calls and not any("--extra" in argv for argv in calls)
