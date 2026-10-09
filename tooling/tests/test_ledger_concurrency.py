"""Contending processes must never write two claims or completions for one attempt."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills/skill-orchestrator/scripts/workflow_ledger.py"
SPEC = importlib.util.spec_from_file_location("audit_ledger", SCRIPT)
ledger = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ledger)


def race(run, barrier, action):
    code = """
import importlib.util, pathlib, sys, time
spec = importlib.util.spec_from_file_location('worker_ledger', sys.argv[1])
ledger = importlib.util.module_from_spec(spec); spec.loader.exec_module(ledger)
run = pathlib.Path(sys.argv[2]); barrier = pathlib.Path(sys.argv[3])
while not barrier.exists(): time.sleep(0.01)
try:
    exec(sys.argv[4])
except ValueError:
    sys.exit(3)
"""
    workers = [subprocess.Popen([sys.executable, "-c", code, str(SCRIPT), str(run), str(barrier), action],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(8)]  # nosec B603
    barrier.touch()
    results = []
    try:
        for worker in workers:
            stdout, stderr = worker.communicate(timeout=30)
            assert worker.returncode in {0, 3}, (stdout, stderr)
            results.append(worker.returncode)
    finally:
        for worker in workers:
            if worker.poll() is None:
                worker.kill()
                worker.wait()
    return results


def test_atomic_claim_and_idempotent_completion(tmp_path):
    run = ledger.create_run(tmp_path, "race", {"steps": [{"skill": "evidence-researcher"}]})
    assert race(run, tmp_path / "claim-start", "ledger.claim_next(run)").count(0) == 1
    state = ledger.replay(run)
    assert state["events"] == 2
    attempt = state["steps"]["step-1"]["attempt_id"]
    action = f"ledger.complete_step(run, 'step-1', 'envelope', 'sha256:fixture', {attempt!r})"
    assert race(run, tmp_path / "complete-start", action) == [0] * 8
    assert ledger.replay(run)["status"] == "COMPLETED"
    assert ledger.replay(run)["events"] == 4


@pytest.mark.skipif(os.name == "nt", reason="POSIX modes do not represent Windows ACLs")
def test_existing_root_permissions_never_change(tmp_path):
    root = tmp_path / "shared"
    root.mkdir(mode=0o755)
    with pytest.raises(ValueError, match="workflow root has insecure permissions"):
        ledger.create_run(root, "run", {"steps": []})
    assert root.stat().st_mode & 0o777 == 0o755
    assert not (root / "run").exists()


def test_symlink_transaction_lock_is_rejected(tmp_path):
    run = ledger.create_run(tmp_path, "run", {"steps": []})
    lock = run / "transaction.lock"
    lock.unlink()
    outside = tmp_path / "outside"
    outside.write_bytes(b"unchanged")
    lock.symlink_to(outside)
    with pytest.raises(ValueError, match="transaction lock must not be a symlink"):
        ledger.claim_next(run)
    assert outside.read_bytes() == b"unchanged"


def test_process_exit_releases_transaction_lock(tmp_path):
    run = ledger.create_run(tmp_path, "crash", {"steps": [{"skill": "evidence-researcher"}]})
    marker = tmp_path / "locked"
    code = """
import importlib.util, pathlib, sys, time
spec = importlib.util.spec_from_file_location('crash_ledger', sys.argv[1])
ledger = importlib.util.module_from_spec(spec); spec.loader.exec_module(ledger)
@ledger._serialized
def interrupted(run):
    pathlib.Path(sys.argv[3]).touch()
    time.sleep(60)
interrupted(pathlib.Path(sys.argv[2]))
"""
    worker = subprocess.Popen([sys.executable, "-c", code, str(SCRIPT), str(run), str(marker)])  # nosec B603
    try:
        deadline = time.monotonic() + 10
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert marker.exists()
    finally:
        worker.kill()
        worker.wait(timeout=10)
    assert ledger.claim_next(run)["event_type"] == "step_claimed"
