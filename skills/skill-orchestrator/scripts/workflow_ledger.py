#!/usr/bin/env python3
"""Append-only, hash-chained local workflow run ledger."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows uses single-writer fixtures.
    fcntl = None

RUN_SCHEMA = "cometweb.workflow-run/v1"
EVENT_SCHEMA = "cometweb.workflow-event/v1"
RUN_STATES = {"PENDING", "RUNNING", "BLOCKED", "FAILED", "CANCELLED", "COMPLETED", "STALE_PLAN"}


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
    events = []
    previous_hash = None
    for expected_seq, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line:
            raise ValueError("workflow event log contains an empty line")
        event = json.loads(line)
        if not isinstance(event, dict) or event.get("schema") != EVENT_SCHEMA:
            raise ValueError("invalid workflow event")
        if event.get("seq") != expected_seq or event.get("previous_event_hash") != previous_hash:
            raise ValueError("workflow event chain is discontinuous")
        stored_hash = event.pop("event_hash", None)
        if not isinstance(stored_hash, str) or sha256(canonical(event)) != stored_hash:
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
    run_dir = _run_dir(root, run_id)
    if run_dir.exists():
        raise ValueError("workflow run already exists")
    run_dir.mkdir(mode=0o700)
    manifest = {
        "schema": RUN_SCHEMA,
        "run_id": run_id,
        "plan_hash": plan_hash(plan),
        "archetype": plan.get("archetype"),
        "execution_mode": plan.get("execution_mode", "single_thread"),
        "steps": plan.get("steps", []),
    }
    (run_dir / "manifest.json").write_bytes(canonical(manifest) + b"\n")
    os.chmod(run_dir / "manifest.json", 0o600)
    append_event(run_dir, "run_created", {"plan_hash": manifest["plan_hash"]})
    return run_dir


def replay(run_dir: Path) -> dict[str, Any]:
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    events = _read_events(run_dir)
    state = {"run_id": manifest["run_id"], "status": "PENDING", "steps": {}, "events": len(events)}
    for event in events:
        event_type, data = event["event_type"], event["data"]
        if event_type == "run_created":
            state["status"] = "PENDING"
        elif event_type == "step_claimed":
            state["status"] = "RUNNING"
            state["steps"][data["step_id"]] = {"status": "RUNNING", **data}
        elif event_type == "step_completed":
            state["steps"][data["step_id"]] = {"status": "COMPLETED", **data}
        elif event_type in {"step_failed", "step_blocked"}:
            state["status"] = "FAILED" if event_type == "step_failed" else "BLOCKED"
            state["steps"][data["step_id"]] = {"status": state["status"], **data}
        elif event_type == "cancel_requested" or event_type == "run_cancelled":
            state["status"] = "CANCELLED"
        elif event_type == "plan_stale_detected":
            state["status"] = "STALE_PLAN"
        elif event_type == "run_completed":
            state["status"] = "COMPLETED"
    return state


def complete_step(run_dir: Path, step_id: str, envelope_id: str, envelope_hash: str) -> dict[str, Any]:
    state = replay(run_dir)
    previous = state["steps"].get(step_id)
    if previous and previous.get("status") == "COMPLETED":
        if previous.get("envelope_hash") != envelope_hash:
            raise ValueError("conflicting duplicate step completion")
        return previous
    if not step_id or not envelope_id or not envelope_hash:
        raise ValueError("step completion needs step_id, envelope_id and envelope_hash")
    return append_event(run_dir, "step_completed", {
        "step_id": step_id, "envelope_id": envelope_id, "envelope_hash": envelope_hash,
    })


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("--root", type=Path, required=True)
    create.add_argument("--run-id", required=True)
    create.add_argument("--plan-json", type=Path, required=True)
    status = sub.add_parser("status")
    status.add_argument("run_dir", type=Path)
    complete = sub.add_parser("complete-step")
    complete.add_argument("run_dir", type=Path)
    complete.add_argument("--step-id", required=True)
    complete.add_argument("--envelope-id", required=True)
    complete.add_argument("--envelope-hash", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            print(create_run(args.root, args.run_id, json.loads(args.plan_json.read_text(encoding="utf-8"))))
        elif args.command == "status":
            print(json.dumps(replay(args.run_dir), indent=2, sort_keys=True))
        else:
            print(json.dumps(complete_step(args.run_dir, args.step_id, args.envelope_id, args.envelope_hash)))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
