"""Adversarial table: no authorizing verdict next to anything unresolved.

Each row mutates a valid v2 Decision or Release payload, re-hashes it, and runs it
through the full validator (with jsonschema and stdlib-only) and through the
multiagent between-step gate. All three must agree: a parent must not hand step
N+1 a GO that ``tooling/validate_envelope.py`` would reject, and a host without
jsonschema must not accept what CI rejects.
"""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
V2 = ROOT / "fixtures" / "cwaip-v2" / "conformance" / "valid"
VALIDATOR = ROOT / "tooling" / "validate_envelope.py"
GATE = ROOT / "skills" / "skill-orchestrator-multiagent" / "scripts" / "validate_envelope.py"

DECISION = "decision-test.json"
RELEASE = "release-go-with-controls.json"

# (id, fixture, payload overrides, expected outcome, stderr marker when rejected)
CASES = [
    # Release: blockers, BLOCK and COUNSEL_REQUIRED gates, any spelling of the status.
    ("release-go-clear", RELEASE, {"verdict": "GO", "controls": []}, "accept", None),
    ("release-gwc-clear", RELEASE, {}, "accept", None),
    ("release-go-blocker", RELEASE, {"verdict": "GO", "blockers": ["x"]}, "reject", "GO cannot have blockers"),
    ("release-go-block-gate", RELEASE,
     {"verdict": "GO", "gates": [{"gate_id": "security", "status": "BLOCK"}]}, "reject", "status=BLOCK"),
    ("release-gwc-block-gate", RELEASE,
     {"gates": [{"gate_id": "qa", "status": "CLEAR"}, {"gate_id": "security", "status": "BLOCK"}]},
     "reject", "GO_WITH_CONTROLS blocked by gate security"),
    ("release-gwc-padded-lowercase-block", RELEASE,
     {"gates": [{"gate_id": "privacy", "status": "  block "}]}, "reject", "blocked by gate privacy"),
    ("release-go-counsel-required", RELEASE,
     {"verdict": "GO", "gates": [{"gate_id": "legal", "status": "counsel_required"}]},
     "reject", "status=counsel_required"),
    ("release-go-block-gate-with-extra-fields", RELEASE,
     {"verdict": "GO", "gates": [{"gate_id": "ops", "status": "BLOCK", "waived": True}]},
     "reject", "status=BLOCK"),
    ("release-no-go-block-gate", RELEASE,
     {"verdict": "NO_GO", "gates": [{"gate_id": "security", "status": "BLOCK"}], "blockers": ["x"]}, "accept", None),
    ("release-defer-counsel-required", RELEASE,
     {"verdict": "DEFER", "gates": [{"gate_id": "legal", "status": "COUNSEL_REQUIRED"}]}, "accept", None),
    # Decision: gates and human approval.
    ("decision-go-clear", DECISION, {"verdict": "GO"}, "accept", None),
    ("decision-go-approval-granted", DECISION, {"verdict": "GO", "human_approval": "granted"}, "accept", None),
    ("decision-go-approval-absent", DECISION, {"verdict": "GO", "human_approval": None}, "accept", None),
    ("decision-go-block-gate", DECISION,
     {"verdict": "GO", "gates": [{"gate_id": "legal", "status": "BLOCK"}]}, "reject", "GO blocked by gate legal"),
    ("decision-go-counsel-required", DECISION,
     {"verdict": "GO", "gates": [{"gate_id": "legal", "status": "COUNSEL_REQUIRED"}]},
     "reject", "GO blocked by gate legal"),
    ("decision-go-blocker", DECISION, {"verdict": "GO", "blockers": ["x"]}, "reject", "GO cannot have blockers"),
    ("decision-go-approval-required", DECISION, {"verdict": "GO", "human_approval": "required"},
     "reject", "human_approval=required"),
    ("decision-go-approval-pending", DECISION, {"verdict": "GO", "human_approval": "pending"},
     "reject", "human_approval=pending"),
    ("decision-go-approval-denied", DECISION, {"verdict": "GO", "human_approval": "denied"},
     "reject", "human_approval=denied"),
    ("decision-defer-approval-pending", DECISION, {"verdict": "DEFER", "human_approval": "pending"}, "accept", None),
    ("decision-test-approval-denied", DECISION, {"verdict": "TEST", "human_approval": "denied"}, "accept", None),
]


def payload_hash(payload: dict) -> str:
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def build(tmp_path: Path, name: str, fixture: str, overrides: dict) -> Path:
    envelope = json.loads((V2 / fixture).read_text(encoding="utf-8"))
    payload = copy.deepcopy(envelope["payload"])
    for key, value in overrides.items():
        if value is None:
            payload.pop(key, None)
        else:
            payload[key] = value
    envelope["payload"] = payload
    envelope["payload_hash"] = payload_hash(payload)
    path = tmp_path / f"{name}.json"
    path.write_text(json.dumps(envelope), encoding="utf-8")
    return path


def run(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, capture_output=True, text=True, timeout=60, cwd=ROOT)


@pytest.mark.parametrize("runner", ["validator-jsonschema", "validator-stdlib", "multiagent-gate"])
@pytest.mark.parametrize("name,fixture,overrides,expect,marker", CASES, ids=[c[0] for c in CASES])
def test_authorizing_verdict_table(
    tmp_path: Path, runner: str, name: str, fixture: str, overrides: dict, expect: str, marker: str | None
) -> None:
    path = build(tmp_path, name, fixture, overrides)
    if runner == "multiagent-gate":
        proc = run([sys.executable, str(GATE), str(path), "--final"])
    else:
        stdlib = ["-S"] if runner == "validator-stdlib" else []
        proc = run([sys.executable, *stdlib, str(VALIDATOR), str(path), "--final"])
    assert "Traceback" not in proc.stderr
    if expect == "accept":
        assert proc.returncode == 0, proc.stderr
    else:
        assert proc.returncode == 1, proc.stdout
        assert marker in proc.stderr, proc.stderr
