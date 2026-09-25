"""Offline executable ZIP checks do not assert live host/model acceptance."""
import importlib.util
from pathlib import Path

import pytest
import yaml

SPEC = importlib.util.spec_from_file_location(
    "install_acceptance", Path(__file__).resolve().parents[1] / "installation_acceptance.py"
)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def script(tmp_path, content):
    install = tmp_path / "installed"
    path = install / "scripts/run_evals.py"
    path.parent.mkdir(parents=True)
    path.write_text(content)
    return install


def test_no_helper_is_not_assessed(tmp_path):
    result = mod.helper_smoke(tmp_path, "fixture")
    assert result["status"] == "not_assessed" and not result["checks"]


def test_helper_runs_outside_package_without_inherited_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv("CW_TEST_SECRET", "must-not-inherit")
    monkeypatch.setenv("PYTHONPATH", str(tmp_path))
    install = script(tmp_path, """import os
from pathlib import Path
assert 'CW_TEST_SECRET' not in os.environ
assert 'PYTHONPATH' not in os.environ
assert not Path.cwd().is_relative_to(Path(__file__).resolve().parents[1])
""")
    assert mod.helper_smoke(install, "fixture")["status"] == "passed"


def test_helper_failure_propagates(tmp_path):
    install = script(tmp_path, "raise SystemExit(7)")
    result = mod.helper_smoke(install, "fixture")
    assert result["status"] == "failed"
    assert result["checks"][0]["returncode"] == 7


def test_helper_timeout_is_not_a_pass(tmp_path):
    install = script(tmp_path, "import time; time.sleep(10)")
    result = mod.helper_smoke(install, "fixture", timeout=1)
    assert result["status"] == "failed"
    assert result["checks"][0]["status"] == "timeout"


def test_missing_validator_cannot_satisfy_negative_smoke(tmp_path):
    result = mod.helper_smoke(tmp_path, "skill-orchestrator-multiagent")
    assert result["status"] == "failed"
    assert all(row["status"] == "failed" for row in result["checks"])


def test_helper_execution_requires_explicit_trusted_checkout():
    with pytest.raises(SystemExit) as exc:
        mod.main(["--run-helpers"])
    assert exc.value.code == 2


@pytest.mark.parametrize("skill", ["../outside", "/tmp", "unknown", ""])
def test_unknown_skill_rejected_before_build(skill, monkeypatch, capsys):
    monkeypatch.setattr(mod, "accept_one", lambda *a, **kw: pytest.fail("must not package"))
    assert mod.main(["--skill", skill]) == 1
    assert '"status": "failed"' in capsys.readouterr().out


def test_real_zip_executes_helpers_and_keeps_host_unassessed(tmp_path):
    result = mod.accept_one(mod.ROOT, "product-operator", tmp_path / "fixture", run_helpers=True)
    assert result["status"] == "passed", result
    assert result["helper_smoke"]["status"] == "passed"
    assert {row["check"] for row in result["helper_smoke"]["checks"]} == {"run_evals.py", "self_check.py"}
    assert result["verified_runtime_acceptance"] == result["host_acceptance"] == "not_assessed"


@pytest.mark.parametrize("workflow", ["validate.yml", "attest-packages.yml"])
def test_ci_runs_all_package_helpers_not_only_runtime_manifests(workflow):
    data = yaml.safe_load((mod.ROOT / ".github/workflows" / workflow).read_text())
    commands = [step.get("run", "") for job in data["jobs"].values() for step in job["steps"]]
    assert any("installation_acceptance.py --all --run-helpers --trusted-checkout" in cmd for cmd in commands)


def test_attestation_cannot_precede_release_checks():
    data = yaml.safe_load((mod.ROOT / ".github/workflows/attest-packages.yml").read_text())
    steps = data["jobs"]["attest"]["steps"]
    gate = next(i for i, step in enumerate(steps) if "validate_local.py" in step.get("run", ""))
    attest = next(i for i, step in enumerate(steps) if step.get("uses", "").startswith("actions/attest@"))
    assert gate < attest
    assert "public_safety.py --root . --history" in steps[gate]["run"]
