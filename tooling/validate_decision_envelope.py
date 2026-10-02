#!/usr/bin/env python3
"""Validate CW-AIP v2 DecisionEnvelope payloads."""
from __future__ import annotations

import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "protocol" / "cw-aip-v2" / "decision.schema.json"
REQUIRED = {
    "schema",
    "decision_question",
    "profile",
    "as_of",
    "verdict",
    "option",
    "gates",
    "blockers",
    "controls",
    "evidence_deps",
    "snapshot_hash",
}
ALLOWED = REQUIRED | {"validity", "human_approval"}


def fail(message: str) -> None:
    raise ValueError(message)


def string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        fail(f"{label} must be an array of strings")
    return value


def validate_fallback(data: dict[str, Any]) -> None:
    missing = sorted(REQUIRED - set(data))
    if missing:
        fail(f"missing {missing[0]}")
    unexpected = sorted(set(data) - ALLOWED)
    if unexpected:
        fail(f"unexpected properties: {', '.join(unexpected)}")
    if data.get("schema") != "cometweb.decision/v2":
        fail("schema must be cometweb.decision/v2")
    for key in ("decision_question", "as_of", "snapshot_hash"):
        if not isinstance(data.get(key), str) or not data[key]:
            fail(f"{key} must be a non-empty string")
    if not isinstance(data.get("option"), str):
        fail("option must be a string")
    if data.get("profile") not in {"LIGHT", "STANDARD", "DEEP", "FAST"}:
        fail("profile must be LIGHT|STANDARD|DEEP|FAST")
    if data.get("verdict") not in {"GO", "NO_GO", "TEST", "DEFER"}:
        fail("verdict must be GO|NO_GO|TEST|DEFER")
    gates = data.get("gates")
    if not isinstance(gates, list) or not all(isinstance(item, dict) for item in gates):
        fail("gates must be an array of objects")
    for gate in gates:
        if not isinstance(gate.get("gate_id"), str):
            fail("gates.gate_id must be a string")
        if gate.get("status") not in {
            "NOT_REQUIRED",
            "CLEAR",
            "CLEAR_WITH_CONTROLS",
            "COUNSEL_REQUIRED",
            "BLOCK",
        }:
            fail("gates.status is invalid")
    for key in ("blockers", "controls", "evidence_deps"):
        string_list(data.get(key), key)
    if "validity" in data and data["validity"] not in {"VALID", "WATCH", "STALE", "REOPEN", "SUPERSEDED"}:
        fail("validity is invalid")
    if "human_approval" in data and data["human_approval"] not in {
        "not_required",
        "required",
        "granted",
        "denied",
        "pending",
    }:
        fail("human_approval is invalid")


def validate_schema(data: dict[str, Any]) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        validate_fallback(data)
        return
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        path = ".".join(str(p) for p in first.path) or "<root>"
        fail(f"schema:{path}: {first.message}")
    validate_fallback(data)


# A GO is only coherent when approval is not needed or has been given; a
# required, pending or denied approval cannot sit next to an authorizing verdict.
GO_COMPATIBLE_APPROVAL = {None, "not_required", "granted"}


def validate_semantics(data: dict[str, Any]) -> None:
    seen_gates: set[str] = set()
    for gate in data.get("gates") or []:
        gate_id = gate.get("gate_id")
        if gate_id in seen_gates:
            # Two rows for one gate let a CLEAR copy mask a BLOCK in consumers
            # that index gates by ID.
            fail(f"duplicate gate_id: {gate_id}")
        seen_gates.add(gate_id)
    if data.get("verdict") == "GO":
        for gate in data.get("gates") or []:
            if gate.get("status") in {"BLOCK", "COUNSEL_REQUIRED"}:
                fail(f"GO blocked by gate {gate.get('gate_id')} status={gate.get('status')}")
        if data.get("blockers"):
            fail("GO cannot have blockers")
        approval = data.get("human_approval")
        if approval not in GO_COMPATIBLE_APPROVAL:
            fail(f"GO is incompatible with human_approval={approval}; use DEFER until approval is granted")


def validate(data: dict[str, Any]) -> None:
    if not isinstance(data, dict):
        fail("payload must be an object")
    validate_schema(data)
    validate_semantics(data)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    usage = "usage: validate_decision_envelope.py <file.json>"
    if args in (["-h"], ["--help"]):
        print(usage)
        print("Validate a cometweb.decision/v2 payload, bare or wrapped in a CW-AIP envelope.")
        return 0
    if len(args) != 1:
        print(usage, file=sys.stderr)
        return 2
    try:
        data = json.loads(pathlib.Path(args[0]).read_text(encoding="utf-8"))
        wrapped = isinstance(data, dict) and data.get("type") == "DecisionEnvelope" and "payload" in data
        validate(data["payload"] if wrapped else data)
    except OSError as exc:
        print(f"FAIL: cannot read {args[0]}: {exc.strerror or exc}", file=sys.stderr)
        return 1
    except ValueError as exc:  # includes JSONDecodeError and UnicodeDecodeError
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("OK: cometweb.decision/v2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
