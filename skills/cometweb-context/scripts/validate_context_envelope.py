#!/usr/bin/env python3
"""JSON Schema + semantic validator for cometweb.context/v2 envelopes."""

from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "protocol" / "cw-aip-v2" / "context.schema.json"

PROFILES = {
    "product",
    "gtm",
    "outreach",
    "brand",
    "meeting",
    "weekly",
    "claim-verification",
    "custom",
}
AUTHORITIES = {"system_of_record", "canonical", "primary", "secondary", "fallback"}
ACCESS = {"live", "local", "connector", "cached", "fallback"}
SENSITIVITY = {"public", "internal", "confidential", "restricted"}
FRESHNESS = {"fresh", "aging", "stale", "unknown"}
MODES = {"targeted", "standard", "delta", "full"}


def fail(message: str) -> None:
    raise ValueError(message)


def _is_iso_datetime(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_schema(data: dict[str, Any]) -> None:
    try:
        import jsonschema
        from jsonschema import Draft202012Validator
    except ImportError:
        # Fallback structural checks if jsonschema is not installed
        _validate_structural_fallback(data)
        return

    schema = _load_schema()
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        path = ".".join(str(p) for p in first.path) or "<root>"
        fail(f"schema:{path}: {first.message}")


def _validate_structural_fallback(data: dict[str, Any]) -> None:
    required = [
        "schema",
        "snapshot_id",
        "generated_at",
        "goal",
        "mode",
        "profile",
        "baseline",
        "sources",
        "facts",
        "deltas",
        "conflicts",
        "gaps",
        "blocked_public_claims",
        "handoff",
    ]
    missing = [key for key in required if key not in data]
    if missing:
        fail(f"missing keys: {', '.join(missing)}")
    if data.get("schema") != "cometweb.context/v2":
        fail("schema must be cometweb.context/v2")
    if data.get("mode") not in MODES:
        fail(f"invalid mode: {data.get('mode')}")
    if data.get("profile") not in PROFILES:
        fail(f"invalid profile: {data.get('profile')}")
    if not isinstance(data.get("sources"), list):
        fail("sources must be a list")
    if not isinstance(data.get("facts"), list):
        fail("facts must be a list")


def validate_semantics(data: dict[str, Any]) -> None:
    if not _is_iso_datetime(data.get("generated_at")):
        fail("generated_at must be ISO-8601 datetime")

    baseline = data.get("baseline") or {}
    baseline_status = baseline.get("status")
    if data.get("mode") == "delta" and baseline_status not in {"available", "unavailable"}:
        fail("delta mode requires baseline.status available or unavailable")
    if baseline_status != "available" and data.get("deltas"):
        fail("deltas must be [] when baseline is not available")

    sources = data.get("sources") or []
    source_ids: list[str] = []
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            fail(f"sources[{index}] must be an object")
        sid = source.get("source_id")
        if not isinstance(sid, str) or not sid:
            fail(f"sources[{index}] missing source_id")
        if sid in source_ids:
            fail(f"duplicate source_id: {sid}")
        source_ids.append(sid)
        if source.get("authority") not in AUTHORITIES:
            fail(f"sources[{index}] invalid authority")
        if source.get("access") not in ACCESS:
            fail(f"sources[{index}] invalid access")
        if source.get("freshness") not in FRESHNESS:
            fail(f"sources[{index}] invalid freshness")
        if source.get("sensitivity") not in SENSITIVITY:
            fail(f"sources[{index}] invalid sensitivity")
        if not _is_iso_datetime(source.get("retrieved_at")):
            fail(f"sources[{index}] retrieved_at must be ISO-8601")
        effective = source.get("effective_at")
        if effective is not None and not _is_iso_datetime(effective):
            fail(f"sources[{index}] effective_at must be ISO-8601 or null")

    known = set(source_ids)
    fact_ids: set[str] = set()
    for index, fact in enumerate(data.get("facts") or []):
        if not isinstance(fact, dict):
            fail(f"facts[{index}] must be an object")
        fid = fact.get("fact_id")
        if not isinstance(fid, str) or not fid:
            fail(f"facts[{index}] missing fact_id")
        if fid in fact_ids:
            fail(f"duplicate fact_id: {fid}")
        fact_ids.add(fid)
        if not isinstance(fact.get("statement"), str):
            fail(f"facts[{index}] statement must be a string")
        source_refs = fact.get("source_ids")
        if not isinstance(source_refs, list) or not source_refs:
            fail(f"facts[{index}] source_ids must be a non-empty list")
        for ref in source_refs:
            if ref not in known:
                fail(f"facts[{index}] unknown source_id: {ref}")
        if fact.get("confidence") not in {"high", "medium", "low"}:
            fail(f"facts[{index}] invalid confidence")
        if fact.get("sensitivity") not in SENSITIVITY:
            fail(f"facts[{index}] invalid sensitivity")

    for index, conflict in enumerate(data.get("conflicts") or []):
        if not isinstance(conflict, dict):
            fail(f"conflicts[{index}] must be an object")
        status = conflict.get("status")
        if status == "resolved" and not conflict.get("basis"):
            fail(f"conflicts[{index}] resolved conflict requires basis")

    for index, gap in enumerate(data.get("gaps") or []):
        if not isinstance(gap, dict):
            fail(f"gaps[{index}] must be an object")
        if gap.get("kind") == "authority_gap" and not gap.get("missing_authority"):
            fail(f"gaps[{index}] authority_gap requires missing_authority")

    for index, blocked in enumerate(data.get("blocked_public_claims") or []):
        if not isinstance(blocked, dict):
            fail(f"blocked_public_claims[{index}] must be an object")
        if not blocked.get("reason"):
            fail(f"blocked_public_claims[{index}] requires reason")

    handoff = data.get("handoff") or {}
    if not isinstance(handoff, dict):
        fail("handoff must be an object")
    for key in ("dependencies", "constraints"):
        if key in handoff and not isinstance(handoff[key], list):
            fail(f"handoff.{key} must be a list")


def validate(data: dict[str, Any]) -> None:
    if not isinstance(data, dict):
        fail("envelope must be an object")
    validate_schema(data)
    validate_semantics(data)


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: validate_context_envelope.py <file.json>", file=sys.stderr)
        raise SystemExit(2)
    path = pathlib.Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))
    validate(data)
    print("OK: cometweb.context/v2")


if __name__ == "__main__":
    main()
