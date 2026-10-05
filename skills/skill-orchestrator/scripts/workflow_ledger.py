#!/usr/bin/env python3
"""Append-only, hash-chained local workflow run ledger."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path
import sys
from typing import Any
from uuid import uuid4

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows uses single-writer fixtures.
    fcntl = None

RUN_SCHEMA = "cometweb.workflow-run/v1"
EVENT_SCHEMA = "cometweb.workflow-event/v1"
RUN_STATES = {"PENDING", "RUNNING", "BLOCKED", "FAILED", "CANCELLED", "COMPLETED", "STALE_PLAN"}
TERMINAL_STATES = {"CANCELLED", "COMPLETED", "STALE_PLAN"}
STEP_EVENT_TYPES = {"step_claimed", "step_completed", "step_failed", "step_blocked"}


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def safe_component(value: str) -> str:
    if not isinstance(value, str) or not value or value in {".", ".."} or "/" in value or "\\" in value:
        raise ValueError("unsafe workflow path component")
    return value


def plan_hash(plan: dict[str, Any]) -> str:
    return sha256(canonical(plan))


def _private(path: Path, label: str) -> None:
    if path.is_symlink():
        raise ValueError(f"{label} must not be a symlink")
    if stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise ValueError(f"{label} has insecure permissions")


def _run_dir(root: Path, run_id: str) -> Path:
    safe_component(run_id)
    root = root.expanduser()
    if root.is_symlink():
        raise ValueError("workflow root must not be a symlink")
    root.mkdir(parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    path = root / run_id
    if path.is_symlink():
        raise ValueError("workflow run directory must not be a symlink")
    return path


def _events_path(run_dir: Path) -> Path:
    path = run_dir / "events.jsonl"
    if path.is_symlink():
        raise ValueError("workflow event log must not be a symlink")
    return path


def _manifest_path(run_dir: Path) -> Path:
    path = run_dir / "manifest.json"
    if path.is_symlink():
        raise ValueError("workflow manifest must not be a symlink")
    return path


def _read_manifest(run_dir: Path) -> dict[str, Any]:
    if run_dir.is_symlink() or not run_dir.is_dir():
        raise ValueError("workflow run directory is missing or symlinked")
    _private(run_dir, "workflow run directory")
    path = _manifest_path(run_dir)
    if not path.is_file():
        raise ValueError("workflow manifest is missing")
    _private(path, "workflow manifest")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("workflow manifest is invalid") from exc
    if not isinstance(manifest, dict) or manifest.get("schema") != RUN_SCHEMA:
        raise ValueError("invalid workflow manifest")
    if manifest.get("run_id") != run_dir.name:
        raise ValueError("workflow manifest run_id mismatch")
    if not isinstance(manifest.get("plan_hash"), str):
        raise ValueError("workflow manifest plan_hash is missing")
    if not isinstance(manifest.get("steps"), list):
        raise ValueError("workflow manifest steps are invalid")
    seen = set()
    for step in manifest["steps"]:
        if not isinstance(step, dict) or not isinstance(step.get("step_id"), str):
            raise ValueError("workflow manifest step is invalid")
        safe_component(step["step_id"])
        if step["step_id"] in seen:
            raise ValueError("workflow manifest contains duplicate step ids")
        seen.add(step["step_id"])
    return manifest


def _locked(path: Path):
    class Lock:
        def __enter__(self):
            self.handle = path.open("a+", encoding="utf-8")
            if fcntl is not None:
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX)
            return self.handle

        def __exit__(self, *_):
            if fcntl is not None:
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
            self.handle.close()

    return Lock()


def _read_events(run_dir: Path) -> list[dict[str, Any]]:
    path = _events_path(run_dir)
    if not path.is_file():
        raise ValueError("workflow event log is missing")
    _private(path, "workflow event log")
    raw = path.read_bytes()
    if not raw or not raw.endswith(b"\n"):
        raise ValueError("workflow event log is truncated")
    events = []
    previous_hash = None
    try:
        lines = raw.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError("workflow event log is invalid") from exc
    for expected_seq, line in enumerate(lines, 1):
        if not line:
            raise ValueError("workflow event log contains an empty line")
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError("workflow event log contains a truncated event") from exc
        if not isinstance(event, dict) or event.get("schema") != EVENT_SCHEMA:
            raise ValueError("invalid workflow event")
        if event.get("run_id") != run_dir.name or not isinstance(event.get("data"), dict):
            raise ValueError("invalid workflow event")
        if event.get("seq") != expected_seq or event.get("previous_event_hash") != previous_hash:
            raise ValueError("workflow event chain is discontinuous")
        stored_hash = event.get("event_hash")
        unsigned_event = dict(event)
        unsigned_event.pop("event_hash", None)
        if not isinstance(stored_hash, str) or sha256(canonical(unsigned_event)) != stored_hash:
            raise ValueError("workflow event hash mismatch")
        event["event_hash"] = stored_hash
        previous_hash = stored_hash
        events.append(event)
    return events


def append_event(run_dir: Path, event_type: str, data: dict[str, Any]) -> dict[str, Any]:
    path = _events_path(run_dir)
    with _locked(path) as handle:
        handle.seek(0)
        existing = _read_events(run_dir) if path.stat().st_size else []
        previous = existing[-1]["event_hash"] if existing else None
        event = {
            "schema": EVENT_SCHEMA,
            "run_id": run_dir.name,
            "seq": len(existing) + 1,
            "event_type": event_type,
            "previous_event_hash": previous,
            "data": data,
        }
        event["event_hash"] = sha256(canonical(event))
        handle.seek(0, os.SEEK_END)
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
        os.chmod(path, 0o600)
        return event


def create_run(root: Path, run_id: str, plan: dict[str, Any]) -> Path:
    if not isinstance(plan, dict):
        raise ValueError("workflow plan must be an object")
    run_dir = _run_dir(root, run_id)
    if run_dir.exists():
        raise ValueError("workflow run already exists")
    steps = _normalise_steps(plan)
    run_dir.mkdir(mode=0o700)
    manifest = {
        "schema": RUN_SCHEMA,
        "run_id": run_id,
        "plan_hash": plan_hash(plan),
        "archetype": plan.get("archetype"),
        "execution_mode": plan.get("execution_mode", "single_thread"),
        "steps": steps,
    }
    manifest_path = _manifest_path(run_dir)
    manifest_path.write_bytes(canonical(manifest) + b"\n")
    os.chmod(manifest_path, 0o600)
    append_event(run_dir, "run_created", {"plan_hash": manifest["plan_hash"]})
    return run_dir


def replay(run_dir: Path) -> dict[str, Any]:
    manifest = _read_manifest(run_dir)
    events = _read_events(run_dir)
    if not events or events[0]["event_type"] != "run_created":
        raise ValueError("workflow event log must start with run_created")
    if events[0]["data"].get("plan_hash") != manifest["plan_hash"]:
        raise ValueError("workflow creation plan hash mismatch")
    step_definitions = {step["step_id"]: step for step in manifest["steps"]}
    if len(step_definitions) != len(manifest["steps"]):
        raise ValueError("workflow manifest contains duplicate step ids")
    state = {"run_id": manifest["run_id"], "plan_hash": manifest["plan_hash"],
             "status": "PENDING", "steps": {}, "events": len(events)}
    for index, event in enumerate(events):
        event_type, data = event["event_type"], event["data"]
        if event_type == "run_created":
            if index != 0:
                raise ValueError("duplicate run_created event")
            state["status"] = "PENDING"
            continue
        if state["status"] in TERMINAL_STATES:
            raise ValueError("workflow event follows a terminal state")
        if event_type not in STEP_EVENT_TYPES | {"run_cancelled", "plan_stale_detected", "run_completed"}:
            raise ValueError("unknown workflow event")
        if event_type in STEP_EVENT_TYPES:
            step_id = data.get("step_id")
            if step_id not in step_definitions:
                raise ValueError("workflow event references an unknown step")
            if data.get("plan_hash") != manifest["plan_hash"]:
                raise ValueError("workflow event plan hash mismatch")
        if event_type == "step_claimed":
            if not data.get("attempt_id"):
                raise ValueError("step claim is missing attempt_id")
            previous = state["steps"].get(data["step_id"])
            if previous and previous["status"] == "RUNNING":
                raise ValueError("workflow log contains an orphaned running attempt")
            if previous and previous["status"] in {"COMPLETED", "BLOCKED"}:
                raise ValueError("workflow log claims a terminal step")
            state["status"] = "RUNNING"
            state["steps"][data["step_id"]] = {"status": "RUNNING", **data}
        elif event_type == "step_completed":
            previous = state["steps"].get(data["step_id"])
            _require_active_attempt(previous, data)
            state["steps"][data["step_id"]] = {"status": "COMPLETED", **data}
        elif event_type in {"step_failed", "step_blocked"}:
            previous = state["steps"].get(data["step_id"])
            _require_active_attempt(previous, data)
            step_status = "FAILED" if event_type == "step_failed" else "BLOCKED"
            state["status"] = step_status
            state["steps"][data["step_id"]] = {"status": step_status, **data}
        elif event_type == "run_cancelled":
            if not data.get("reason") or data.get("plan_hash") != manifest["plan_hash"]:
                raise ValueError("invalid cancellation event")
            state["status"] = "CANCELLED"
            state["cancel_reason"] = data["reason"]
        elif event_type == "plan_stale_detected":
            if data.get("manifest_plan_hash") != manifest["plan_hash"]:
                raise ValueError("stale-plan event hash mismatch")
            if not data.get("current_plan_hash") or data["current_plan_hash"] == manifest["plan_hash"]:
                raise ValueError("invalid stale-plan event")
            state["status"] = "STALE_PLAN"
        elif event_type == "run_completed":
            if data.get("plan_hash") != manifest["plan_hash"]:
                raise ValueError("workflow completion plan hash mismatch")
            if any(state["steps"].get(step_id, {}).get("status") != "COMPLETED"
                   for step_id in step_definitions):
                raise ValueError("workflow completed before all steps completed")
            state["status"] = "COMPLETED"
    return state


def _normalise_steps(plan: dict[str, Any]) -> list[dict[str, Any]]:
    raw_steps = plan.get("steps", [])
    if not isinstance(raw_steps, list):
        raise ValueError("workflow plan steps must be a list")
    steps = []
    seen = set()
    for index, raw_step in enumerate(raw_steps, 1):
        if not isinstance(raw_step, dict):
            raise ValueError("workflow plan step must be an object")
        step = dict(raw_step)
        step_id = step.get("step_id") or step.get("id") or f"step-{index}"
        safe_component(step_id)
        if step_id in seen:
            raise ValueError("workflow plan contains duplicate step ids")
        seen.add(step_id)
        step["step_id"] = step_id
        steps.append(step)
    return steps


def _require_active_attempt(previous: dict[str, Any] | None, data: dict[str, Any]) -> None:
    if not previous or previous.get("status") != "RUNNING":
        raise ValueError("orphan step completion or transition")
    if data.get("attempt_id") != previous.get("attempt_id"):
        raise ValueError("orphan step attempt")


def _check_current_plan(run_dir: Path, state: dict[str, Any], current_plan: dict[str, Any] | None) -> dict[str, Any]:
    if current_plan is None:
        return state
    if not isinstance(current_plan, dict):
        raise ValueError("workflow plan must be an object")
    current_hash = plan_hash(current_plan)
    if current_hash != state["plan_hash"]:
        if state["status"] != "STALE_PLAN":
            append_event(run_dir, "plan_stale_detected", {
                "manifest_plan_hash": state["plan_hash"],
                "current_plan_hash": current_hash,
            })
        return replay(run_dir)
    if state["status"] == "STALE_PLAN":
        raise ValueError("stale plan cannot be resumed")
    return state


def claim_next(run_dir: Path, current_plan: dict[str, Any] | None = None,
               worker_id: str | None = None) -> dict[str, Any]:
    state = _check_current_plan(run_dir, replay(run_dir), current_plan)
    if state["status"] == "STALE_PLAN":
        if current_plan is not None and plan_hash(current_plan) != state["plan_hash"]:
            return state
        raise ValueError("stale plan cannot be resumed")
    if state["status"] == "CANCELLED":
        return state
    if state["status"] == "COMPLETED":
        return state
    if any(step.get("status") == "RUNNING" for step in state["steps"].values()):
        raise ValueError("orphaned running attempt")
    manifest = _read_manifest(run_dir)
    for step in manifest["steps"]:
        previous = state["steps"].get(step["step_id"])
        status = previous.get("status") if previous else "PENDING"
        if status == "COMPLETED":
            continue
        if status == "BLOCKED":
            raise ValueError("workflow is blocked")
        attempt_id = uuid4().hex
        data = {
            "step_id": step["step_id"],
            "attempt_id": attempt_id,
            "attempt_number": (previous.get("attempt_number", 0) + 1) if previous else 1,
            "plan_hash": state["plan_hash"],
        }
        if worker_id:
            data["worker_id"] = worker_id
        return append_event(run_dir, "step_claimed", data)
    append_event(run_dir, "run_completed", {"plan_hash": state["plan_hash"]})
    return replay(run_dir)


def complete_step(run_dir: Path, step_id: str, envelope_id: str, envelope_hash: str,
                  attempt_id: str | None = None) -> dict[str, Any]:
    state = replay(run_dir)
    previous = state["steps"].get(step_id)
    if previous and previous.get("status") == "COMPLETED":
        if previous.get("envelope_id") != envelope_id or previous.get("envelope_hash") != envelope_hash:
            raise ValueError("conflicting duplicate step completion")
        return previous
    if not step_id or not envelope_id or not envelope_hash:
        raise ValueError("step completion needs step_id, envelope_id and envelope_hash")
    if state["status"] in {"CANCELLED", "STALE_PLAN"}:
        raise ValueError("workflow cannot accept a step completion")
    if previous and previous.get("status") == "RUNNING":
        if not attempt_id:
            raise ValueError("orphan step attempt")
        if attempt_id != previous.get("attempt_id"):
            raise ValueError("orphan step attempt")
    else:
        raise ValueError("orphan step completion")
    event = append_event(run_dir, "step_completed", {
        "step_id": step_id, "attempt_id": attempt_id, "plan_hash": state["plan_hash"],
        "envelope_id": envelope_id, "envelope_hash": envelope_hash,
    })
    if all(step.get("status") == "COMPLETED" for step in replay(run_dir)["steps"].values()) and \
            len(replay(run_dir)["steps"]) == len(_read_manifest(run_dir)["steps"]):
        append_event(run_dir, "run_completed", {"plan_hash": state["plan_hash"]})
    return event


def _transition_step(run_dir: Path, step_id: str, event_type: str, reason: str,
                     attempt_id: str | None) -> dict[str, Any]:
    if not reason or not attempt_id:
        raise ValueError("step transition needs reason and attempt_id")
    state = replay(run_dir)
    previous = state["steps"].get(step_id)
    target_status = "FAILED" if event_type == "step_failed" else "BLOCKED"
    if state["status"] in {"CANCELLED", "STALE_PLAN", "COMPLETED"}:
        raise ValueError("workflow cannot accept a step transition")
    if previous and previous.get("status") == target_status:
        if previous.get("reason") == reason and previous.get("attempt_id") == attempt_id:
            return previous
        raise ValueError("conflicting duplicate step transition")
    if previous and previous.get("status") == "COMPLETED":
        raise ValueError("completed step cannot be transitioned")
    _require_active_attempt(previous, {"attempt_id": attempt_id or (previous or {}).get("attempt_id")})
    data = {
        "step_id": step_id,
        "attempt_id": attempt_id or previous["attempt_id"],
        "plan_hash": state["plan_hash"],
        "reason": reason,
    }
    return append_event(run_dir, event_type, data)


def fail_step(run_dir: Path, step_id: str, reason: str, attempt_id: str | None = None) -> dict[str, Any]:
    return _transition_step(run_dir, step_id, "step_failed", reason, attempt_id)


def block_step(run_dir: Path, step_id: str, reason: str, attempt_id: str | None = None) -> dict[str, Any]:
    return _transition_step(run_dir, step_id, "step_blocked", reason, attempt_id)


def cancel_run(run_dir: Path, reason: str = "cancelled by operator") -> dict[str, Any]:
    if not reason:
        raise ValueError("cancel needs a reason")
    state = replay(run_dir)
    if state["status"] == "CANCELLED":
        if state.get("cancel_reason") == reason:
            return state
        raise ValueError("conflicting duplicate cancellation")
    if state["status"] == "COMPLETED":
        raise ValueError("completed workflow cannot be cancelled")
    if state["status"] == "STALE_PLAN":
        raise ValueError("stale plan cannot be cancelled")
    return append_event(run_dir, "run_cancelled", {
        "plan_hash": state["plan_hash"], "reason": reason,
    })


def resume(run_dir: Path, current_plan: dict[str, Any] | None = None,
           worker_id: str | None = None) -> dict[str, Any]:
    return claim_next(run_dir, current_plan, worker_id)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("--root", type=Path, required=True)
    create.add_argument("--run-id", required=True)
    create.add_argument("--plan-json", type=Path, required=True)
    status = sub.add_parser("status")
    status.add_argument("run_dir", type=Path)
    claim = sub.add_parser("claim-next")
    claim.add_argument("run_dir", type=Path)
    claim.add_argument("--plan-json", type=Path)
    claim.add_argument("--worker-id")
    resume_parser = sub.add_parser("resume")
    resume_parser.add_argument("run_dir", type=Path)
    resume_parser.add_argument("--plan-json", type=Path)
    resume_parser.add_argument("--worker-id")
    complete = sub.add_parser("complete-step")
    complete.add_argument("run_dir", type=Path)
    complete.add_argument("--step-id", required=True)
    complete.add_argument("--envelope-id", required=True)
    complete.add_argument("--envelope-hash", required=True)
    complete.add_argument("--attempt-id", required=True)
    fail = sub.add_parser("fail-step")
    fail.add_argument("run_dir", type=Path)
    fail.add_argument("--step-id", required=True)
    fail.add_argument("--reason", required=True)
    fail.add_argument("--attempt-id", required=True)
    block = sub.add_parser("block-step")
    block.add_argument("run_dir", type=Path)
    block.add_argument("--step-id", required=True)
    block.add_argument("--reason", required=True)
    block.add_argument("--attempt-id", required=True)
    cancel = sub.add_parser("cancel")
    cancel.add_argument("run_dir", type=Path)
    cancel.add_argument("--reason", default="cancelled by operator")
    args = parser.parse_args(argv)
    try:
        current_plan = (json.loads(args.plan_json.read_text(encoding="utf-8"))
                        if getattr(args, "plan_json", None) else None)
        if args.command == "create":
            print(create_run(args.root, args.run_id, json.loads(args.plan_json.read_text(encoding="utf-8"))))
        elif args.command == "status":
            print(json.dumps(replay(args.run_dir), indent=2, sort_keys=True))
        elif args.command in {"claim-next", "resume"}:
            print(json.dumps(claim_next(args.run_dir, current_plan, args.worker_id)))
        elif args.command == "complete-step":
            print(json.dumps(complete_step(args.run_dir, args.step_id, args.envelope_id,
                                            args.envelope_hash, args.attempt_id)))
        elif args.command == "fail-step":
            print(json.dumps(fail_step(args.run_dir, args.step_id, args.reason, args.attempt_id)))
        elif args.command == "block-step":
            print(json.dumps(block_step(args.run_dir, args.step_id, args.reason, args.attempt_id)))
        else:
            print(json.dumps(cancel_run(args.run_dir, args.reason)))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
