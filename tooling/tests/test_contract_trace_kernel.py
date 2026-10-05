from __future__ import annotations

import json
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills/web-app-auditor/scripts/contract_trace_kernel.py"
SPEC = importlib.util.spec_from_file_location("contract_trace_kernel", SCRIPT)
assert SPEC and SPEC.loader
contract_trace_kernel = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contract_trace_kernel)


def trace() -> dict:
    return {
        "schema": "cometweb.contract-trace/v1",
        "revision": "a" * 40,
        "build": "build-1",
        "environment": "staging",
        "journey_id": "save",
        "claim": "bounded",
        "nodes": [
            {"id": "ui", "kind": "ui"},
            {"id": "api", "kind": "api"},
            {"id": "job", "kind": "job"},
            {"id": "durable", "kind": "durable"},
        ],
        "evidence": [
            {"id": "E1", "channel": "browser", "locator": "browser-run-1"},
            {"id": "E2", "channel": "joined", "locator": "joined-run-1"},
        ],
        "edges": [
            {"id": "ui-api", "from": "ui", "to": "api", "kind": "request", "state": "pass", "evidence_ids": ["E1"]},
            {"id": "api-job", "from": "api", "to": "job", "kind": "job", "state": "pass", "evidence_ids": ["E2"]},
            {"id": "job-durable", "from": "job", "to": "durable", "kind": "durable", "state": "pass", "evidence_ids": ["E2"]},
        ],
        "scenarios": [
            {"id": "happy", "kind": "happy", "status": "pass", "evidence_ids": ["E2"]},
            {"id": "null", "kind": "null_partial", "status": "pass", "evidence_ids": ["E2"]},
            {"id": "retry", "kind": "retry_duplicate", "status": "pass", "evidence_ids": ["E2"]},
            {"id": "tenant", "kind": "wrong_tenant", "status": "pass", "evidence_ids": ["E2"]},
            {"id": "rollback", "kind": "rollback", "status": "pass", "evidence_ids": ["E2"]},
        ],
    }


def test_valid_bounded_trace():
    assert contract_trace_kernel.validate(trace()) == []


def test_browser_evidence_cannot_prove_backend_edge():
    payload = trace()
    payload["edges"][1]["evidence_ids"] = ["E1"]
    assert any("browser-evidence" in error for error in contract_trace_kernel.validate(payload))


def test_browser_evidence_cannot_prove_service_edge():
    payload = trace()
    payload["nodes"].append({"id": "service", "kind": "service"})
    payload["edges"].append(
        {
            "id": "api-service",
            "from": "api",
            "to": "service",
            "kind": "request",
            "state": "pass",
            "evidence_ids": ["E1"],
        }
    )
    assert any("browser-evidence" in error for error in contract_trace_kernel.validate(payload))


@pytest.mark.parametrize("mutation", [
    lambda payload: payload["scenarios"].pop(),
    lambda payload: payload["scenarios"][0].update(status="unknown"),
    lambda payload: payload["edges"][0].update(to="missing"),
])
def test_invalid_trace_is_not_authorizing(mutation):
    payload = trace()
    mutation(payload)
    assert contract_trace_kernel.validate(payload)


def test_cli_returns_json_error(tmp_path: Path):
    path = tmp_path / "trace.json"
    path.write_text(json.dumps({"schema": "wrong"}), encoding="utf-8")
    proc = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)
    assert proc.returncode == 1
    assert json.loads(proc.stdout)["status"] == "INVALID"


@pytest.mark.parametrize(
    "path,bad_value",
    [
        (("claim",), []),
        (("nodes", 0, "id"), []),
        (("evidence", 0, "channel"), []),
        (("edges", 0, "state"), []),
        (("scenarios", 0, "kind"), []),
    ],
)
def test_malformed_nested_values_fail_closed(path: tuple[object, ...], bad_value: object):
    payload = trace()
    target = payload
    for key in path[:-1]:
        target = target[key]  # type: ignore[index]
    target[path[-1]] = bad_value  # type: ignore[index]
    errors = contract_trace_kernel.validate(payload)
    assert errors
    assert all(isinstance(error, str) for error in errors)


def test_duplicate_scenario_kind_is_invalid():
    payload = trace()
    payload["scenarios"].append(
        {"id": "happy-2", "kind": "happy", "status": "pass", "evidence_ids": ["E2"]}
    )
    assert any("kind:duplicate" in error for error in contract_trace_kernel.validate(payload))
