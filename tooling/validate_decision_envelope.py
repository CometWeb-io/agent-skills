#!/usr/bin/env python3
"""Validate CW-AIP v2 DecisionEnvelope payloads."""
from __future__ import annotations

import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "protocol" / "cw-aip-v2" / "decision.schema.json"


def fail(message: str) -> None:
    raise ValueError(message)


def validate_schema(data: dict[str, Any]) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        if data.get("schema") != "cometweb.decision/v2":
            fail("schema must be cometweb.decision/v2")
        for key in (
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
        ):
            if key not in data:
                fail(f"missing {key}")
        return
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        path = ".".join(str(p) for p in first.path) or "<root>"
        fail(f"schema:{path}: {first.message}")


def validate_semantics(data: dict[str, Any]) -> None:
    if data.get("verdict") == "GO":
        for gate in data.get("gates") or []:
            if gate.get("status") in {"BLOCK", "COUNSEL_REQUIRED"}:
                fail(f"GO blocked by gate {gate.get('gate_id')} status={gate.get('status')}")
        if data.get("blockers"):
            fail("GO cannot have blockers")
    if data.get("human_approval") == "required" and data.get("verdict") == "GO":
        fail("GO requires human_approval before authorization semantics")


def validate(data: dict[str, Any]) -> None:
    if not isinstance(data, dict):
        fail("payload must be an object")
    validate_schema(data)
    validate_semantics(data)


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: validate_decision_envelope.py <file.json>", file=sys.stderr)
        raise SystemExit(2)
    data = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    payload = data.get("payload") if data.get("type") == "DecisionEnvelope" and "payload" in data else data
    validate(payload)
    print("OK: cometweb.decision/v2")


if __name__ == "__main__":
    main()
