"""Local-validation runner regressions. Fixtures are not evidence of real skill behavior."""
from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

SPEC = importlib.util.spec_from_file_location("cw_validate_local", Path(__file__).parents[1] / "validate_local.py")
local = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(local)


def put(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


@pytest.fixture
def checkout(tmp_path):
    root = tmp_path / "checkout"
    root.mkdir()
    for relative in (*local.REQUIRED, *(row[1] for row in local.CHECKS)):
        if relative == "pyproject.toml":
            put(root, relative, '[project]\nname = "fixture"\nversion = "0.0.0"\nrequires-python = ">=3.12"\n')
        elif relative == "uv.lock":
            put(root, relative, 'version = 1\nrequires-python = ">=3.12"\n')
        else:
            put(root, relative, "pass\n" if relative.endswith(".py") else "{}\n")
    put(root, "registry/skills.json", json.dumps({"skills": [{"id": "example"}]}))
    for name in ("SKILL.md", "VERSION", "LICENSE"):
        put(root, "skills/example/" + name, "fixture\n")
    put(root, "tooling/tests/test_fixture.py", "def test_fixture():\n    assert True\n")
    put(root, "skills/example/tests/test_fixture.py", "def test_fixture():\n    assert True\n")
    put(root, ".gitignore", "__pycache__/\n.pytest_cache/\n")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                    "-c", "core.hooksPath=/dev/null", "commit", "-qm", "synthetic baseline"], check=True)
    return root


def test_inventory_declares_actual_test_directories(checkout):
    result = local.inventory(checkout)
    assert result["skills"] == ["example"]
    assert result["test_directories"] == ["tooling/tests", "skills/example/tests"]
    assert result["skills_without_tests"] == []


@pytest.mark.parametrize("name", ["registry/hosts.json", "tooling/generate_adapters.py", "skills/example/LICENSE",
                                  "skills/example/VERSION", "skills/example/SKILL.md"])
def test_incomplete_checkout_rejected_before_output(checkout, name):
    (checkout / name).unlink()
    out = checkout.parent / "report"
    with pytest.raises(ValueError):
        local.run(checkout, out)
    assert not out.exists()


@pytest.mark.parametrize("rows", [[], None, [None], [{"id": "../outside"}], [{"id": "a/b"}],
                                  [{"id": "example"}, {"id": "example"}], [{"id": "different"}]])
def test_invalid_registry_rejected(checkout, rows):
    put(checkout, "registry/skills.json", json.dumps({"skills": rows}))
    with pytest.raises(ValueError):
        local.inventory(checkout)


def test_duplicate_registry_key_rejected(checkout):
    put(checkout, "registry/skills.json", '{"skills":[],"skills":[{"id":"example"}]}')
    with pytest.raises(ValueError):
        local.inventory(checkout)


def test_sources_changed_and_untracked_additions_affect_fingerprint(checkout):
    first = local.source_state(checkout)
    put(checkout, "tooling/added.py", "VALUE = 1\n")
    added = local.source_state(checkout)
    put(checkout, "tooling/added.py", "VALUE = 2\n")
    edited = local.source_state(checkout)
    assert len({s["fingerprint"] for s in (first, added, edited)}) == 3
    assert not first["dirty"] and added["dirty"]


def test_modes_affect_fingerprint(checkout):
    first = local.source_state(checkout)
    (checkout / "tooling/validate_repo.py").chmod(0o755)
    assert local.source_state(checkout)["fingerprint"] != first["fingerprint"]


def test_symlink_source_rejected(checkout):
    path = checkout / "tooling/generate_adapters.py"
    path.unlink()
    path.symlink_to(checkout / "tooling/validate_repo.py")
    with pytest.raises(ValueError):
        local.inventory(checkout)


def test_command_plan_does_not_generate_publish_or_install(checkout):
    rows = dict(local.commands(local.inventory(checkout), Path("/report")))
    assert rows["adapters"][-1] == "--check"
    assert rows["orchestrator"][-1] == "--check"
    assert "--import-mode=importlib" in rows["pytest"]
    assert "addopts=" in rows["pytest"]
    for command in rows.values():
        text = " ".join(command)
        assert "publish" not in text and "sync_public" not in text and "pip install" not in text
    assert "--write-report" not in " ".join(sum(rows.values(), []))


def test_plan_does_not_run_or_write(checkout, monkeypatch, capsys):
    monkeypatch.setattr(local, "run_step", lambda *a: pytest.fail("plan executed a step"))
    out = checkout.parent / "report"
    assert local.main(["--root", str(checkout), "--plan", "--output", str(out)]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "plan_only"
    assert not out.exists()


@pytest.mark.parametrize("location", ["inside", "existing", "symlink"])
def test_output_never_overwrites_existing_data(checkout, location):
    out = checkout / "result" if location == "inside" else checkout.parent / "result"
    if location == "existing":
        out.mkdir()
        (out / "keep.txt").write_text("keep")
    if location == "symlink":
        out.symlink_to(checkout, target_is_directory=True)
    with pytest.raises(ValueError):
        local.run(checkout, out)
    if location == "existing":
        assert (out / "keep.txt").read_text() == "keep"


@pytest.mark.parametrize("xml", ['<testsuites/>', '<wrong><testcase/></wrong>', '<!DOCTYPE x><testsuite><testcase/></testsuite>', 'broken'])
def test_empty_or_invalid_junit_rejected(tmp_path, xml):
    path = put(tmp_path, "junit.xml", xml)
    with pytest.raises((ValueError, ET.ParseError)):
        local.junit_counts(path)


def test_junit_counts_test_nodes_not_trusted_summary_attributes(tmp_path):
    path = put(tmp_path, "junit.xml", '<testsuite tests="900" failures="0"><testcase/><testcase><failure/></testcase><testcase><skipped/></testcase></testsuite>')
    assert local.junit_counts(path) == {"tests": 3, "failures": 1, "errors": 0, "skipped": 1}


def mock_steps(monkeypatch, *, failed=None, junit='<testsuite><testcase/></testsuite>', modify=None):
    def step(root, command, log, timeout):
        name = log.stem
        log.write_text("synthetic test runner result\n")
        if name == "pytest" and junit is not None:
            put(log.parent, "junit.xml", junit)
        if modify and name == "registry":
            modify(root)
        return {"status": failed[1] if failed and failed[0] == name else "passed", "returncode": 0,
                "command": command, "log": log.name, "seconds": 0}
    monkeypatch.setattr(local, "run_step", step)


@pytest.mark.parametrize("status", ["failed", "timeout", "execution_error"])
def test_failure_never_turns_into_pass(checkout, monkeypatch, status):
    mock_steps(monkeypatch, failed=("registry", status))
    report = local.run(checkout, checkout.parent / "report")
    assert report["status"] in {"failed", "incomplete"}
    assert bool(report["not_run"]) == (status != "failed")


@pytest.mark.parametrize("xml,expected", [(None, "invalid_test_report"), ('<testsuite><testcase><failure/></testcase></testsuite>', "failed"),
                                         ('<testsuite><testcase><skipped/></testcase></testsuite>', "incomplete")])
def test_zero_exit_is_insufficient_for_pass(checkout, monkeypatch, xml, expected):
    mock_steps(monkeypatch, junit=xml)
    report = local.run(checkout, checkout.parent / "report")
    assert report["checks"][-1]["status"] == expected
    assert report["status"] == "failed"


def test_source_change_stops_remaining_steps(checkout, monkeypatch):
    mock_steps(monkeypatch, modify=lambda root: put(root, "tooling/change.py", "pass\n"))
    report = local.run(checkout, checkout.parent / "report")
    assert report["status"] == "source_changed"
    assert report["not_run"]
    assert report["source_before"] != report["source_after"]


def test_report_written_after_interruption(checkout, monkeypatch):
    monkeypatch.setattr(local, "run_step", lambda *args: (_ for _ in ()).throw(KeyboardInterrupt()))
    report = local.run(checkout, checkout.parent / "report")
    assert report["status"] == "interrupted"
    assert json.loads((checkout.parent / "report/report.json").read_text())["status"] == "interrupted"


def test_syntax_failure_is_not_hidden(checkout, monkeypatch):
    put(checkout, "skills/example/broken.py", "def :\n")
    mock_steps(monkeypatch)
    report = local.run(checkout, checkout.parent / "report")
    assert report["status"] == "failed"
    assert report["checks"][0]["files_with_errors"] == ["skills/example/broken.py"]


def test_real_local_pipeline_on_synthetic_repository(checkout, monkeypatch):
    # Seven stub checks plus two actual pytest tests with the same module name.
    # This exercises the runner, NOT the canonical repository's validations.
    monkeypatch.setenv("PYTEST_ADDOPTS", "-k nonexistent_test_filter")
    put(checkout, "pytest.ini", "[pytest]\naddopts = -k nonexistent_test_filter\n")
    before = local.source_state(checkout)
    out = checkout.parent / "actual-report"
    report = local.run(checkout, out, timeout=30)
    assert report["status"] == "passed", report
    assert report["checks"][-1]["junit"]["tests"] == 2
    assert local.source_state(checkout) == before
    assert not (checkout / ".pytest_cache").exists()
    assert not list(checkout.rglob("*.pyc"))
    assert report["not_assessed"] and report["github_actions_used"] is False
    assert stat_mode(out) == 0o700


def stat_mode(path):
    return path.stat().st_mode & 0o777


def test_real_timeout_is_explicit(checkout):
    result = local.run_step(checkout, [sys.executable, "-c", "import time; time.sleep(10)"], checkout.parent / "timeout.log", 1)
    assert result["status"] == "timeout" and result["returncode"] is None


def test_error_exit_codes_are_nonzero(checkout, capsys):
    assert local.main(["--root", str(checkout.parent / "missing"), "--plan"]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "preflight_failed"


@pytest.mark.parametrize("timeout", [0, -1, 1801, True, 1.5])
def test_invalid_timeout_rejected_without_output(checkout, timeout):
    with pytest.raises(ValueError):
        local.run(checkout, checkout.parent / "invalid-report", timeout)
    assert not (checkout.parent / "invalid-report").exists()


def test_ignored_required_entrypoint_rejected(checkout):
    subprocess.run(["git", "-C", str(checkout), "rm", "--cached", "tooling/validate_repo.py"], check=True, capture_output=True)
    with (checkout / ".gitignore").open("a") as handle:
        handle.write("tooling/validate_repo.py\n")
    with pytest.raises(ValueError, match="ignored"):
        local.run(checkout, checkout.parent / "ignored-report")


def test_oversized_junit_rejected_without_unbounded_read(tmp_path, monkeypatch):
    monkeypatch.setattr(local, "MAX_FILE", 8)
    with pytest.raises(ValueError):
        local.junit_counts(put(tmp_path, "large.xml", "<testsuite><testcase/></testsuite>"))


def test_staged_change_is_recorded_even_if_worktree_bytes_unchanged(checkout):
    put(checkout, "tooling/validate_repo.py", "value = 42\n")
    before = local.source_state(checkout)
    subprocess.run(["git", "-C", str(checkout), "add", "tooling/validate_repo.py"], check=True)
    after = local.source_state(checkout)
    assert before["fingerprint"] == after["fingerprint"]
    assert before["dirty"] == after["dirty"]
    assert before["index_fingerprint"] != after["index_fingerprint"]


def test_direct_api_rejects_symlink_checkout(checkout):
    alias = checkout.parent / "checkout-link"
    alias.symlink_to(checkout, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        local.run(alias, checkout.parent / "linked-report")
