from __future__ import annotations

import json
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("workflow_ledger", ROOT / "scripts/workflow_ledger.py")
assert SPEC and SPEC.loader
ledger = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ledger)


def plan() -> dict:
    return {"archetype": "orchestrated_goal", "execution_mode": "single_thread",
            "steps": [{"skill": "evidence-researcher"}]}


def test_create_replay_and_idempotent_completion(tmp_path: Path) -> None:
    run_dir = ledger.create_run(tmp_path, "run-1", plan())
    event = ledger.complete_step(run_dir, "step-1", "env-1", "sha256:abc")
    assert event["event_type"] == "step_completed"
    duplicate = ledger.complete_step(run_dir, "step-1", "env-1", "sha256:abc")
    assert duplicate["status"] == "COMPLETED"
    assert ledger.replay(run_dir)["steps"]["step-1"]["status"] == "COMPLETED"


def test_conflicting_duplicate_completion_fails_closed(tmp_path: Path) -> None:
    run_dir = ledger.create_run(tmp_path, "run-1", plan())
    ledger.complete_step(run_dir, "step-1", "env-1", "sha256:abc")
    with pytest.raises(ValueError, match="conflicting"):
        ledger.complete_step(run_dir, "step-1", "env-2", "sha256:different")


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
    root.mkdir()
    (root / "run-1").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        ledger.create_run(root, "run-1", plan())
