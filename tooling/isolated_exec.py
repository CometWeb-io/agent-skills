#!/usr/bin/env python3
"""Bounded Python helpers through a probed Codex macOS sandbox; never a model host."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import tempfile
from typing import Any

SCHEMA = "cometweb.isolated-helper/v1"
CAPTURE_MODULE = Path(__file__).with_name("real_host_eval.py")
PROFILE_NAME = "cw-assurance-helper"
PROFILE = ('{extends=":workspace",filesystem={":root"="deny",":minimal"="read",'
           '"/opt/homebrew"="read",":tmpdir"="deny",":slash_tmp"="deny"},network={enabled=false}}')
LIMITS = {"cpu_seconds": 5, "file_bytes": 8 * 1024 * 1024, "open_files": 64, "wall_seconds": 10}
# Limits are applied inside the confined interpreter before loading caller code.
WRAPPER = '''import resource,runpy,sys
for kind, ceiling in ((resource.RLIMIT_CPU,5),(resource.RLIMIT_FSIZE,8388608),(resource.RLIMIT_NOFILE,64)):
    _, hard = resource.getrlimit(kind)
    value = min(ceiling, hard) if hard != resource.RLIM_INFINITY else ceiling
    resource.setrlimit(kind,(value,value))
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0],run_name="__main__")
'''
PROBE = '''import errno,json,pathlib,socket,sys,tempfile
work, outside = map(pathlib.Path,sys.argv[1:])
with tempfile.TemporaryFile(mode="w+",dir=work) as inside:
    inside.write("inside")
    inside.seek(0)
    result = {"inside_write_read": inside.read() == "inside"}
for key,path,write in (("outside_read",outside/"canary.txt",False),("outside_write",outside/"created.txt",True)):
    try:
        path.write_text("changed") if write else path.read_text()
        result[key] = {"denied":False,"errno":None}
    except OSError as exc:
        result[key] = {"denied":exc.errno in (errno.EACCES,errno.EPERM),"errno":exc.errno}
try:
    with socket.socket() as connection:
        connection.settimeout(1)
        connection.connect(("127.0.0.1",9))
    result["network"] = {"denied":False,"errno":None}
except OSError as exc:
    result["network"] = {"denied":exc.errno in (errno.EACCES,errno.EPERM),"errno":exc.errno}
print(json.dumps(result))
'''


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_digest(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def helper_backend_policy() -> dict[str, Any]:
    return {"backend": SCHEMA, "scope": "local_python_helper_only",
            "status": "CANARY_PROOF_REQUIRED", "platform": "macOS",
            "profile_sha256": digest(PROFILE), "limits": dict(LIMITS),
            "native_host_execution": "NOT_RUN", "memory_limit": None}


def runtime_identity(codex_binary: str, python_binary: str) -> dict[str, Any]:
    def executable(value: str) -> Path:
        resolved = Path(shutil.which(value) or value).resolve(strict=True)
        if not resolved.is_file() or not os.access(resolved, os.X_OK):
            raise ValueError("runtime executable is not an executable file")
        return resolved

    codex, python = executable(codex_binary), executable(python_binary)
    if platform.system() != "Darwin" or not python.is_relative_to(Path("/opt/homebrew")):
        raise ValueError("this backend requires macOS and a Python runtime under /opt/homebrew")
    return {"codex": str(codex), "codex_sha256": file_digest(codex),
            "python": str(python), "python_sha256": file_digest(python),
            "system": platform.system(), "release": platform.release(), "machine": platform.machine(),
            "implementation_sha256": file_digest(Path(__file__)),
            "capture_implementation_sha256": file_digest(CAPTURE_MODULE), "profile": PROFILE,
            "profile_sha256": digest(PROFILE), "limits": dict(LIMITS),
            "runtime_identity_scope": "selected_executables_profile_wrapper_os_not_all_runtime_libraries"}


def sandbox_command(identity: dict[str, Any], workspace: Path, script: Path, args: list[str]) -> list[str]:
    return [identity["codex"], "sandbox", "-C", str(workspace), "-P", PROFILE_NAME,
            "-c", f"permissions.{PROFILE_NAME}={PROFILE}", identity["python"], "-B", "-c", WRAPPER,
            str(script), *args]


def environment(workspace: Path, evidence: Path) -> dict[str, str]:
    home, temporary = (workspace / name for name in (".helper-home", ".helper-tmp"))
    # Parent-only config cannot be rewritten by an earlier sandboxed helper.
    config = evidence / ".codex-profile"
    for path in (home, config, temporary):
        path.mkdir(mode=0o700, exist_ok=True)
        if path.is_symlink():
            raise ValueError("runtime directories cannot be symlinks")
    return {"PATH": "/usr/bin:/bin:/opt/homebrew/bin", "HOME": str(home), "CODEX_HOME": str(config),
            "TMPDIR": str(temporary), "LANG": "C.UTF-8", "CI": "1", "NO_COLOR": "1"}


def capture(command: list[str], workspace: Path, env: dict[str, str], evidence: Path, name: str) -> dict[str, Any]:
    # Reuse the runner's bounded capture and POSIX process-group cleanup.
    from real_host_eval import _run_capped

    stdout, stderr = evidence / f"{name}.stdout.txt", evidence / f"{name}.stderr.txt"
    try:
        code, timeout, limited = _run_capped(command, env, workspace, "", LIMITS["wall_seconds"], stdout, stderr)
        error = None
    except OSError as exc:
        code, timeout, limited, error = None, False, False, type(exc).__name__
    return {"command": command, "exit_code": code, "timeout": timeout, "capture_limit": limited,
            "error_type": error, "stdout": stdout.read_text(errors="replace") if stdout.exists() else None,
            "stderr": stderr.read_text(errors="replace") if stderr.exists() else None}


def new_evidence(path: Path, workspace: Path) -> None:
    if path.resolve().is_relative_to(workspace):
        raise ValueError("trusted evidence must be outside the helper workspace")
    path.mkdir(mode=0o700, parents=True, exist_ok=False)


def successful(receipt: dict[str, Any]) -> bool:
    return receipt["exit_code"] == 0 and not receipt["timeout"] and not receipt["capture_limit"]


def positive_observation(observation: Any, unchanged: bool) -> bool:
    return (isinstance(observation, dict) and observation.get("inside_write_read") is True and unchanged is True
            and all(isinstance(observation.get(key), dict) and observation[key].get("denied") is True
                    and type(observation[key].get("errno")) is int and observation[key]["errno"] in (1, 13)
                    for key in ("outside_read", "outside_write", "network")))


def probe_boundary(workspace: Path, evidence: Path, *, codex_binary: str = "codex",
                   python_binary: str = "/opt/homebrew/bin/python3") -> dict[str, Any]:
    """Local canaries only. No prompt, model session, credential or API request."""
    from real_host_eval import write_json, write_private

    workspace = workspace.resolve(strict=True)
    identity = runtime_identity(codex_binary, python_binary)
    new_evidence(evidence, workspace)
    env = environment(workspace, evidence)
    capabilities = {name: capture([identity["codex"], *arguments], workspace, env, evidence, name)
                    for name, arguments in (("version", ["--version"]), ("sandbox-help", ["sandbox", "--help"]),
                                            ("exec-help", ["exec", "--help"]))}
    supported = (all(successful(r) for r in capabilities.values())
                 and "--permission-profile" in (capabilities["sandbox-help"]["stdout"] or ""))
    observation: dict[str, Any] | None = None
    receipt: dict[str, Any] | None = None
    unchanged = False
    if supported:
        # Sibling paths are synthetic canaries, never the caller's personal files.
        with tempfile.TemporaryDirectory(prefix="cw-outside-canary-", dir=workspace.parent) as outside_text:
            outside = Path(outside_text)
            (outside / "canary.txt").write_text("synthetic-canary-only")
            script = workspace / ".helper-boundary-probe.py"
            if script.exists() or script.is_symlink():
                raise ValueError("probe script path is occupied")
            write_private(script, PROBE)
            try:
                receipt = capture(sandbox_command(identity, workspace, script, [str(workspace), str(outside)]),
                                  workspace, env, evidence, "boundary")
                if successful(receipt):
                    try:
                        observation = json.loads(receipt["stdout"] or "")
                    except ValueError:
                        observation = None
                unchanged = ((outside / "canary.txt").read_text() == "synthetic-canary-only"
                             and not (outside / "created.txt").exists())
            finally:
                script.unlink(missing_ok=True)
    passed = positive_observation(observation, unchanged)
    proof = {"schema": SCHEMA, "status": "VERIFIED" if passed else "NOT_RUN", "workspace": str(workspace),
             "reason": None if passed else "BOUNDARY_PROBE_FAILED", "runtime": identity,
             "capabilities": capabilities, "observation": observation, "outside_unchanged": unchanged,
             "boundary_receipt": receipt, "scope": "selected_local_canaries_not_model_or_full_host_qualification",
             "native_exec_profile": "NOT_VERIFIED", "native_host_execution": "NOT_RUN"}
    proof["proof_sha256"] = digest(proof)
    write_json(evidence / "proof.json", proof)
    return proof


def run_python(script: Path, args: list[str], workspace: Path, evidence: Path, *, proof: dict[str, Any],
               expected_proof_sha256: str) -> dict[str, Any]:
    """Execute only after a trusted, same-workspace/runtime/profile canary proof."""
    from real_host_eval import write_json

    workspace = workspace.resolve(strict=True)
    script = script.resolve(strict=True)
    if not script.is_relative_to(workspace) or script.suffix != ".py" or not script.is_file():
        raise ValueError("helper must be a Python file inside the owned workspace")
    if not isinstance(args, list) or any(not isinstance(v, str) or "\0" in v for v in args):
        raise ValueError("helper arguments must be plain strings")
    if not isinstance(proof, dict):
        raise ValueError("boundary proof must be an object")
    body = {key: value for key, value in proof.items() if key != "proof_sha256"}
    if (not expected_proof_sha256 or proof.get("proof_sha256") != expected_proof_sha256
            or digest(body) != expected_proof_sha256 or proof.get("status") != "VERIFIED"
            or proof.get("schema") != SCHEMA
            or not positive_observation(proof.get("observation"), proof.get("outside_unchanged"))
            or not isinstance(proof.get("boundary_receipt"), dict) or not successful(proof["boundary_receipt"])
            or proof.get("workspace") != str(workspace)):
        raise ValueError("missing, changed, unsuccessful or different-workspace boundary proof")
    old_identity = proof.get("runtime", {})
    identity = runtime_identity(old_identity.get("codex", ""), old_identity.get("python", ""))
    if identity != old_identity:
        raise ValueError("runtime/profile changed since boundary probe")
    new_evidence(evidence, workspace)
    script_sha256 = file_digest(script)
    result = capture(sandbox_command(identity, workspace, script, args), workspace,
                     environment(workspace, evidence), evidence, "helper")
    result.update(schema=SCHEMA, status="completed" if successful(result) else "error",
                  proof_sha256=expected_proof_sha256, runtime=identity, script_sha256=script_sha256,
                  task_success="not_assessed", model=None, input_tokens=None, output_tokens=None, cost_usd=None)
    write_json(evidence / "result.json", result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    probe = sub.add_parser("probe", help="local synthetic canaries; no model calls")
    probe.add_argument("--workspace", type=Path, required=True)
    probe.add_argument("--out", type=Path, required=True)
    probe.add_argument("--codex-bin", default="codex")
    probe.add_argument("--python-bin", default="/opt/homebrew/bin/python3")
    run = sub.add_parser("run-python", help="a local Python helper, never a model host")
    run.add_argument("--workspace", type=Path, required=True)
    run.add_argument("--out", type=Path, required=True)
    run.add_argument("--proof", type=Path, required=True)
    run.add_argument("--proof-sha256", required=True)
    run.add_argument("script", type=Path)
    run.add_argument("args", nargs=argparse.REMAINDER)
    options = parser.parse_args(argv)
    try:
        if options.command == "probe":
            result = probe_boundary(options.workspace, options.out, codex_binary=options.codex_bin,
                                    python_binary=options.python_bin)
            print(json.dumps({"status": result["status"], "proof_sha256": result["proof_sha256"],
                              "native_host_execution": "NOT_RUN"}))
            return 0 if result["status"] == "VERIFIED" else 3
        result = run_python(options.script, options.args, options.workspace, options.out,
                            proof=json.loads(options.proof.read_text()), expected_proof_sha256=options.proof_sha256)
        print(json.dumps({"status": result["status"], "task_success": "not_assessed"}))
        return 0 if result["status"] == "completed" else 1
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "NOT_RUN", "reason": str(exc)}))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
