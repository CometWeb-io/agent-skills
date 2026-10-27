"""Local fixture processes test receipts/limits; only a native canary tests OS enforcement."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import pytest

import isolated_exec as isolated

REAL_RUNTIME_IDENTITY = isolated.runtime_identity

pytestmark = pytest.mark.skipif(os.name != "posix", reason="runner process-group fixture requires POSIX")


@pytest.fixture
def fixture_runtime(tmp_path, monkeypatch):
    workspace = tmp_path / "work"
    workspace.mkdir()
    binary = tmp_path / "fixture-codex"
    log = tmp_path / "fixture.log"
    binary.write_text(f'''#!{sys.executable}
import json,os,pathlib,subprocess,sys
argv=sys.argv[1:]
with open({str(log)!r},"a") as log:
    log.write(json.dumps({{"argv":argv,"env":dict(os.environ)}})+"\\n")
if argv == ["--version"]:
    print("fixture-codex-no-model 0.0")
elif argv == ["sandbox","--help"]:
    print("--permission-profile -P --cd -C --config -c")
elif argv == ["exec","--help"]:
    print("--config -c --sandbox --ignore-user-config")
elif argv[0] == "sandbox":
    if any(pathlib.Path(a).name==".helper-boundary-probe.py" for a in argv):
        # Canned boundary observation, explicitly not OS-enforcement proof.
        print(json.dumps({{"inside_write_read":True,"outside_read":{{"denied":True,"errno":1}},
                          "outside_write":{{"denied":True,"errno":1}},"network":{{"denied":True,"errno":1}}}}))
    else:
        sys.exit(subprocess.call(argv[7:]))
else:
    sys.exit(99)
''')
    binary.chmod(0o700)

    def fixture_identity(codex_binary, python_binary):
        selected = Path(codex_binary).resolve()
        return {"codex": str(selected), "codex_sha256": isolated.file_digest(selected),
                "python": sys.executable, "python_sha256": isolated.file_digest(Path(sys.executable)),
                "system": "FIXTURE_UNQUALIFIED", "implementation_sha256": isolated.file_digest(Path(isolated.__file__)),
                "profile": isolated.PROFILE, "profile_sha256": isolated.digest(isolated.PROFILE),
                "limits": dict(isolated.LIMITS), "runtime_identity_scope": "portable_fixture_only"}

    monkeypatch.setattr(isolated, "runtime_identity", fixture_identity)
    return workspace, binary, log


def fixture_proof(tmp_path, fixture_runtime):
    workspace, binary, _ = fixture_runtime
    return isolated.probe_boundary(workspace, tmp_path / "probe-evidence", codex_binary=str(binary))


def test_fixture_capabilities_canary_and_actual_helper_limits(tmp_path, fixture_runtime, monkeypatch):
    workspace, binary, log = fixture_runtime
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-must-not-inherit")
    proof = fixture_proof(tmp_path, fixture_runtime)
    assert proof["status"] == "VERIFIED"
    assert proof["native_host_execution"] == "NOT_RUN"
    assert proof["native_exec_profile"] == "NOT_VERIFIED"
    helper = workspace / "helper.py"
    helper.write_text('''import json,resource
from pathlib import Path
try:
    with Path("large.bin").open("wb") as output:
        output.write(b"x" * (9 * 1024 * 1024))
    file_limit_enforced = False
except OSError:
    file_limit_enforced = True
print(json.dumps({"value":42,"file_limit_enforced":file_limit_enforced,
                  "cpu":resource.getrlimit(resource.RLIMIT_CPU)[1],
                  "fds":resource.getrlimit(resource.RLIMIT_NOFILE)[1]}))
''')
    result = isolated.run_python(helper, [], workspace, tmp_path / "helper-evidence", proof=proof,
                                 expected_proof_sha256=proof["proof_sha256"])
    assert result["status"] == "completed" and result["task_success"] == "not_assessed"
    observed = json.loads(result["stdout"])
    assert observed == {"value": 42, "file_limit_enforced": True, "cpu": 5, "fds": 64}
    assert (workspace / "large.bin").stat().st_size <= isolated.LIMITS["file_bytes"]
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    assert all("OPENAI_API_KEY" not in call["env"] for call in calls)
    assert all(call["argv"][0] in {"--version", "sandbox", "exec"} for call in calls)
    assert all(call["argv"] == ["exec", "--help"] for call in calls if call["argv"][0] == "exec")
    assert not Path(calls[-1]["env"]["CODEX_HOME"]).is_relative_to(workspace)
    assert "--permission-profile" not in calls[2]["argv"]  # no invented exec flags


def test_failed_or_tampered_or_different_workspace_proof_starts_no_helper(tmp_path, fixture_runtime):
    workspace, _, log = fixture_runtime
    proof = fixture_proof(tmp_path, fixture_runtime)
    helper = workspace / "helper.py"
    helper.write_text('print("local")')
    before = log.read_text()
    changed = json.loads(json.dumps(proof))
    changed["observation"]["network"]["denied"] = False
    for altered, pin in ((changed, proof["proof_sha256"]), (proof, "0" * 64)):
        with pytest.raises(ValueError, match="boundary proof"):
            isolated.run_python(helper, [], workspace, tmp_path / "no-result", proof=altered,
                                expected_proof_sha256=pin)
    sibling = tmp_path / "sibling"
    sibling.mkdir()
    sibling_helper = sibling / "helper.py"
    sibling_helper.write_text('print("local")')
    with pytest.raises(ValueError, match="boundary proof"):
        isolated.run_python(sibling_helper, [], sibling, tmp_path / "no-result", proof=proof,
                            expected_proof_sha256=proof["proof_sha256"])
    assert log.read_text() == before and not (tmp_path / "no-result").exists()


def test_runtime_change_refuses_reusing_proof(tmp_path, fixture_runtime):
    workspace, binary, log = fixture_runtime
    proof = fixture_proof(tmp_path, fixture_runtime)
    helper = workspace / "helper.py"
    helper.write_text('print("local")')
    binary.write_text(binary.read_text() + "\n# changed runtime\n")
    before = log.read_text()
    with pytest.raises(ValueError, match="runtime/profile changed"):
        isolated.run_python(helper, [], workspace, tmp_path / "no-result", proof=proof,
                            expected_proof_sha256=proof["proof_sha256"])
    assert log.read_text() == before


def test_unconfined_fixture_fails_real_canary_observations(tmp_path, fixture_runtime):
    workspace, binary, _ = fixture_runtime
    # Forward the actual probe to Python, without an OS sandbox: outside access
    # succeeds and the synthetic canary changes, so the backend must refuse it.
    binary.write_text(f'''#!{sys.executable}
import subprocess,sys
argv=sys.argv[1:]
if argv==["--version"]: print("unconfined fixture")
elif argv==["sandbox","--help"]: print("--permission-profile")
elif argv==["exec","--help"]: print("--config")
else: sys.exit(subprocess.call(argv[7:]))
''')
    proof = isolated.probe_boundary(workspace, tmp_path / "denied-evidence", codex_binary=str(binary))
    assert proof["status"] == "NOT_RUN" and proof["outside_unchanged"] is False
    assert proof["observation"]["outside_read"]["denied"] is False


def test_helper_timeout_does_not_fallback_to_unconfined_execution(tmp_path, fixture_runtime, monkeypatch):
    workspace, _, log = fixture_runtime
    monkeypatch.setitem(isolated.LIMITS, "wall_seconds", 1)
    proof = fixture_proof(tmp_path, fixture_runtime)
    helper = workspace / "slow.py"
    helper.write_text('import time\nprint("started",flush=True)\ntime.sleep(60)\n')
    before = len(log.read_text().splitlines())
    result = isolated.run_python(helper, [], workspace, tmp_path / "timeout-evidence", proof=proof,
                                 expected_proof_sha256=proof["proof_sha256"])
    assert result["status"] == "error" and result["timeout"] is True
    assert result["stdout"] == "started\n"
    calls = [json.loads(line) for line in log.read_text().splitlines()[before:]]
    assert len(calls) == 1 and calls[0]["argv"][0] == "sandbox"


def test_helper_paths_and_evidence_cannot_cross_trust_boundary(tmp_path, fixture_runtime):
    workspace, _, log = fixture_runtime
    proof = fixture_proof(tmp_path, fixture_runtime)
    external = tmp_path / "outside.py"
    external.write_text('print("outside")')
    before = log.read_text()
    with pytest.raises(ValueError, match="inside the owned workspace"):
        isolated.run_python(external, [], workspace, tmp_path / "no-result", proof=proof,
                            expected_proof_sha256=proof["proof_sha256"])
    internal = workspace / "inside.py"
    internal.write_text('print("inside")')
    with pytest.raises(ValueError, match="trusted evidence"):
        isolated.run_python(internal, [], workspace, workspace / "evidence", proof=proof,
                            expected_proof_sha256=proof["proof_sha256"])
    assert log.read_text() == before


def test_capture_implementation_change_invalidates_proof_before_helper_start(tmp_path, fixture_runtime, monkeypatch):
    workspace, binary, log = fixture_runtime
    capture_source = tmp_path / "capture-source.py"
    capture_source.write_bytes(isolated.CAPTURE_MODULE.read_bytes())
    monkeypatch.setattr(isolated, "CAPTURE_MODULE", capture_source)
    # Exercise the production identity function with portable fixture executables;
    # only its macOS/runtime-root admission is simulated, not source hashing.
    monkeypatch.setattr(isolated, "runtime_identity", REAL_RUNTIME_IDENTITY)
    monkeypatch.setattr(isolated.platform, "system", lambda: "Darwin")
    relative = Path.is_relative_to
    monkeypatch.setattr(Path, "is_relative_to", lambda path, other:
                        True if other == Path("/opt/homebrew") else relative(path, other))
    proof = isolated.probe_boundary(workspace, tmp_path / "probe-evidence", codex_binary=str(binary),
                                    python_binary=sys.executable)
    assert proof["runtime"]["capture_implementation_sha256"] == isolated.file_digest(capture_source)
    helper = workspace / "helper.py"
    helper.write_text('print("must not run")')
    capture_source.write_text(capture_source.read_text() + "\n# changed capture implementation\n")
    before = log.read_text()
    with pytest.raises(ValueError, match="runtime/profile changed"):
        isolated.run_python(helper, [], workspace, tmp_path / "no-result", proof=proof,
                            expected_proof_sha256=proof["proof_sha256"])
    assert log.read_text() == before and not (tmp_path / "no-result").exists()
