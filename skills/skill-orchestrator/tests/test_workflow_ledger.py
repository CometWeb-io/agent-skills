from __future__ import annotations

import json
import importlib.util
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("workflow_ledger", ROOT / "scripts/workflow_ledger.py")
assert SPEC and SPEC.loader
ledger = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ledger)


def plan() -> dict:
    return {"archetype": "orchestrated_goal", "execution_mode": "single_thread",
            "steps": [{"step_id": "research", "skill": "evidence-researcher"},
                      {"step_id": "council", "skill": "ai-council"}]}


def test_create_replay_and_idempotent_completion(tmp_path: Path) -> None:
    run_dir = ledger.create_run(tmp_path, "run-1", plan())
    claim = ledger.claim_next(run_dir, plan())
    assert claim["event_type"] == "step_claimed"
    assert claim["data"]["step_id"] == "research"
    assert claim["data"]["attempt_id"]
    attempt_id = claim["data"]["attempt_id"]
    event = ledger.complete_step(run_dir, "research", "env-1", "sha256:abc", attempt_id)
    assert event["event_type"] == "step_completed"
    duplicate = ledger.complete_step(run_dir, "research", "env-1", "sha256:abc", attempt_id)
    assert duplicate["status"] == "COMPLETED"
    next_claim = ledger.claim_next(run_dir, plan())
    assert next_claim["data"]["step_id"] == "council"
    assert ledger.replay(run_dir)["steps"]["research"]["status"] == "COMPLETED"
    ledger.complete_step(run_dir, "council", "env-2", "sha256:def", next_claim["data"]["attempt_id"])
    assert ledger.replay(run_dir)["status"] == "COMPLETED"
    assert ledger.claim_next(run_dir, plan())["status"] == "COMPLETED"


def test_conflicting_duplicate_completion_fails_closed(tmp_path: Path) -> None:
    run_dir = ledger.create_run(tmp_path, "run-1", plan())
    attempt_id = ledger.claim_next(run_dir, plan())["data"]["attempt_id"]
    ledger.complete_step(run_dir, "research", "env-1", "sha256:abc", attempt_id)
    with pytest.raises(ValueError, match="conflicting"):
        ledger.complete_step(run_dir, "research", "env-2", "sha256:different", attempt_id)


def test_orphaned_attempt_and_completed_steps_are_not_rerun(tmp_path: Path) -> None:
    run_dir = ledger.create_run(tmp_path, "run-1", plan())
    with pytest.raises(ValueError, match="orphan"):
        ledger.complete_step(run_dir, "research", "env-1", "sha256:abc")

    claim = ledger.claim_next(run_dir, plan())
    with pytest.raises(ValueError, match="orphan"):
        ledger.complete_step(run_dir, "research", "env-1", "sha256:abc")
    with pytest.raises(ValueError, match="attempt_id"):
        ledger.fail_step(run_dir, "research", "missing attempt")
    with pytest.raises(ValueError, match="orphaned running attempt"):
        ledger.claim_next(run_dir, plan())
    ledger.complete_step(run_dir, "research", "env-1", "sha256:abc", claim["data"]["attempt_id"])
    next_claim = ledger.claim_next(run_dir, plan())
    assert next_claim["data"]["step_id"] == "council"


def test_fail_block_and_cancel_have_explicit_duplicate_semantics(tmp_path: Path) -> None:
    run_dir = ledger.create_run(tmp_path, "run-1", plan())
    claim = ledger.claim_next(run_dir, plan())
    attempt_id = claim["data"]["attempt_id"]
    failed = ledger.fail_step(run_dir, "research", "network timeout", attempt_id)
    assert failed["event_type"] == "step_failed"
    assert ledger.fail_step(run_dir, "research", "network timeout", attempt_id)["status"] == "FAILED"
    with pytest.raises(ValueError, match="conflicting duplicate"):
        ledger.fail_step(run_dir, "research", "different error", attempt_id)

    retry = ledger.claim_next(run_dir, plan())
    blocked = ledger.block_step(run_dir, "research", "needs approval", retry["data"]["attempt_id"])
    assert blocked["event_type"] == "step_blocked"
    with pytest.raises(ValueError, match="blocked"):
        ledger.claim_next(run_dir, plan())

    cancelled = ledger.cancel_run(run_dir, "operator stopped run")
    assert cancelled["event_type"] == "run_cancelled"
    assert ledger.cancel_run(run_dir, "operator stopped run")["status"] == "CANCELLED"
    with pytest.raises(ValueError, match="conflicting duplicate"):
        ledger.cancel_run(run_dir, "another reason")


def test_stale_plan_is_recorded_and_resume_stops(tmp_path: Path) -> None:
    run_dir = ledger.create_run(tmp_path, "run-1", plan())
    changed_plan = {**plan(), "goal": "changed"}
    state = ledger.claim_next(run_dir, changed_plan)
    assert state["status"] == "STALE_PLAN"
    assert ledger.replay(run_dir)["status"] == "STALE_PLAN"
    with pytest.raises(ValueError, match="stale plan"):
        ledger.claim_next(run_dir, plan())


def test_tampered_chain_is_rejected(tmp_path: Path) -> None:
    run_dir = ledger.create_run(tmp_path, "run-1", plan())
    path = run_dir / "events.jsonl"
    event = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    event["data"]["plan_hash"] = "sha256:tampered"
    path.write_text(json.dumps(event) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hash"):
        ledger.replay(run_dir)


def test_symlink_run_directory_is_rejected(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "runs"
    root.mkdir(mode=0o700)
    (root / "run-1").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        ledger.create_run(root, "run-1", plan())


def test_path_traversal_and_permissions_are_rejected(tmp_path: Path) -> None:
    root = tmp_path / "runs"
    with pytest.raises(ValueError, match="unsafe"):
        ledger.create_run(root, "../escape", plan())
    assert not (tmp_path / "escape").exists()

    run_dir = ledger.create_run(root, "run-1", plan())
    if os.name != "nt":  # POSIX mode assertions cannot validate Windows ACLs.
        assert os.stat(root).st_mode & 0o777 == 0o700
        assert os.stat(run_dir).st_mode & 0o777 == 0o700
        assert os.stat(run_dir / "manifest.json").st_mode & 0o777 == 0o600
        assert os.stat(run_dir / "events.jsonl").st_mode & 0o777 == 0o600

        os.chmod(run_dir / "manifest.json", 0o644)
        with pytest.raises(ValueError, match="permissions"):
            ledger.replay(run_dir)



def test_truncated_event_log_is_rejected(tmp_path: Path) -> None:
    run_dir = ledger.create_run(tmp_path, "run-1", plan())
    path = run_dir / "events.jsonl"
    path.write_bytes(path.read_bytes().rstrip(b"\n"))
    with pytest.raises(ValueError, match="truncated"):
        ledger.replay(run_dir)


def test_cli_resume_and_step_commands(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan()), encoding="utf-8")
    assert ledger.main(["create", "--root", str(tmp_path), "--run-id", "cli-run",
                        "--plan-json", str(plan_path)]) == 0
    capsys.readouterr()
    run_dir = tmp_path / "cli-run"
    assert ledger.main(["resume", str(run_dir), "--plan-json", str(plan_path)]) == 0
    claim = json.loads(capsys.readouterr().out)
    attempt_id = claim["data"]["attempt_id"]
    assert ledger.main(["fail-step", str(run_dir), "--step-id", "research",
                        "--attempt-id", attempt_id, "--reason", "test failure"]) == 0
    assert json.loads(capsys.readouterr().out)["event_type"] == "step_failed"
    assert ledger.main(["cancel", str(run_dir), "--reason", "test cleanup"]) == 0
    assert json.loads(capsys.readouterr().out)["event_type"] == "run_cancelled"
