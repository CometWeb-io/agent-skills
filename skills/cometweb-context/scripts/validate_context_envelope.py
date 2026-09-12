#!/usr/bin/env python3
"""Validator for cometweb.context/v2 envelopes."""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import sys

REQUIRED = [
    "schema", "snapshot_id", "generated_at", "goal", "mode", "profile", "baseline",
    "sources", "facts", "deltas", "conflicts", "gaps", "blocked_public_claims", "handoff",
]
MODES = {"targeted", "standard", "delta", "full"}
PROFILES = {"product", "portfolio", "gtm", "outreach", "brand", "meeting", "weekly", "claim-verification", "custom"}
FRESHNESS = {"fresh", "aging", "stale", "unknown"}
AUTHORITIES = {"system_of_record", "canonical", "primary", "secondary", "fallback"}
ACCESS = {"live", "local", "connector", "cached", "fallback"}
SENSITIVITY = {"public", "internal", "confidential", "restricted"}
SOURCE_TYPES = {"github", "local-repo", "vault", "notion", "crm", "gmail", "calendar", "contacts", "insight", "website", "social", "file", "other"}
BASELINE_STATUS = {"available", "unavailable", "not_requested"}
FP_STATUS = {"loaded", "not_required", "unavailable"}


def fail(message: str) -> None:
    raise ValueError(message)


def require_iso8601(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        fail(f"{field} must be a non-empty ISO-8601 string")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            fail(f"{field} must include a timezone offset")
    except ValueError as exc:
        raise ValueError(f"{field} must be ISO-8601") from exc


def validate(data: dict) -> None:
    if not isinstance(data, dict):
        fail("envelope must be an object")
    missing = [key for key in REQUIRED if key not in data]
    if missing:
        fail(f"missing keys: {', '.join(missing)}")
    if data["schema"] != "cometweb.context/v2":
        fail("schema must be cometweb.context/v2")
    if not isinstance(data["mode"], str) or data["mode"] not in MODES:
        fail(f"invalid mode: {data['mode']}")
    if not isinstance(data["profile"], str) or data["profile"] not in PROFILES:
        fail(f"invalid profile: {data['profile']}")
    require_iso8601(data["generated_at"], "generated_at")
    if not isinstance(data["snapshot_id"], str) or not data["snapshot_id"].strip():
        fail("snapshot_id must be non-empty")
    if not isinstance(data["goal"], str) or not data["goal"].strip():
        fail("goal must be non-empty")

    baseline = data.get("baseline")
    if not isinstance(baseline, dict):
        fail("baseline must be an object")
    baseline_status = baseline.get("status")
    if not isinstance(baseline_status, str) or baseline_status not in BASELINE_STATUS:
        fail("invalid baseline.status")
    if data["mode"] == "delta" and baseline_status not in {"available", "unavailable"}:
        fail("delta mode requires baseline.status available or unavailable")

    if baseline_status == "available" and (not isinstance(baseline.get("ref"), str) or not baseline["ref"].strip()):
        fail("available baseline requires a non-empty ref")
    if data["deltas"] and baseline_status != "available":
        fail("non-empty deltas require an available baseline")

    if not isinstance(data["sources"], list):
        fail("sources must be a list")
    source_ids: set[str] = set()
    for index, source in enumerate(data["sources"]):
        if not isinstance(source, dict):
            fail(f"sources[{index}] must be an object")
        for key in ["source_id", "source_type", "authority", "access", "retrieved_at", "freshness", "sensitivity", "summary", "evidence_ref"]:
            if key not in source:
                fail(f"sources[{index}] missing {key}")
        for field in ("summary", "evidence_ref"):
            if not isinstance(source[field], str) or not source[field].strip():
                fail(f"sources[{index}].{field} must be non-empty")
        sid = source["source_id"]
        if not isinstance(sid, str) or not sid.strip():
            fail(f"sources[{index}] source_id must be non-empty")
        if sid in source_ids:
            fail(f"duplicate source_id: {sid}")
        source_ids.add(sid)
        if not isinstance(source["source_type"], str) or source["source_type"] not in SOURCE_TYPES:
            fail(f"sources[{index}] invalid source_type")
        if not isinstance(source["authority"], str) or source["authority"] not in AUTHORITIES:
            fail(f"sources[{index}] invalid authority")
        if not isinstance(source["access"], str) or source["access"] not in ACCESS:
            fail(f"sources[{index}] invalid access")
        if not isinstance(source["freshness"], str) or source["freshness"] not in FRESHNESS:
            fail(f"sources[{index}] invalid freshness")
        if not isinstance(source["sensitivity"], str) or source["sensitivity"] not in SENSITIVITY:
            fail(f"sources[{index}] invalid sensitivity")
        require_iso8601(source["retrieved_at"], f"sources[{index}].retrieved_at")
        retrieved = dt.datetime.fromisoformat(source["retrieved_at"].replace("Z", "+00:00"))
        generated = dt.datetime.fromisoformat(data["generated_at"].replace("Z", "+00:00"))
        if retrieved > generated:
            fail(f"sources[{index}].retrieved_at cannot be after generated_at")
        if source.get("effective_at"):
            require_iso8601(source["effective_at"], f"sources[{index}].effective_at")

    for source in data["sources"]:
        if source["authority"] == "system_of_record" and source["access"] in {"cached", "fallback"}:
            if not isinstance(data["gaps"], list) or not any(isinstance(g, dict) and g.get("kind") == "authority_gap" for g in data["gaps"]):
                fail("fallback system_of_record requires an explicit authority_gap")

    if not isinstance(data["facts"], list):
        fail("facts must be a list")
    fact_ids: set[str] = set()
    for index, fact in enumerate(data["facts"]):
        if not isinstance(fact, dict):
            fail(f"facts[{index}] must be an object")
        for key in ["fact_id", "statement", "source_ids", "confidence", "sensitivity"]:
            if key not in fact:
                fail(f"facts[{index}] missing {key}")
        if not isinstance(fact["statement"], str) or not fact["statement"].strip():
            fail(f"facts[{index}].statement must be non-empty")
        if fact.get("sensitivity") in ("confidential", "restricted") and len(fact["statement"]) > 800:
            fail(f"facts[{index}] exceeds confidential summary limit")
        fid = fact["fact_id"]
        if not isinstance(fid, str) or not fid.strip():
            fail(f"facts[{index}] fact_id must be non-empty")
        if fid in fact_ids:
            fail(f"duplicate fact_id: {fid}")
        fact_ids.add(fid)
        if not isinstance(fact["source_ids"], list) or not fact["source_ids"]:
            fail(f"facts[{index}] source_ids must be a non-empty list")
        refs = fact["source_ids"]
        if any(not isinstance(sid, str) or not sid.strip() for sid in refs):
            fail(f"facts[{index}].source_ids must contain non-empty strings")
        if len(set(refs)) != len(refs):
            fail(f"facts[{index}].source_ids must be unique")
        unknown = [sid for sid in refs if sid not in source_ids]
        if unknown:
            fail(f"facts[{index}] references unknown source_ids: {', '.join(unknown)}")
        if not isinstance(fact["confidence"], str) or fact["confidence"] not in {"high", "medium", "low"}:
            fail(f"facts[{index}] invalid confidence")
        if not isinstance(fact["sensitivity"], str) or fact["sensitivity"] not in SENSITIVITY:
            fail(f"facts[{index}] invalid sensitivity")

    for key in ["deltas", "conflicts", "gaps", "blocked_public_claims"]:
        if not isinstance(data[key], list):
            fail(f"{key} must be a list")

    handoff = data["handoff"]
    if not isinstance(handoff, dict):
        fail("handoff must be an object")
    for key in ["recommended_next_skill", "dependencies", "constraints"]:
        if key not in handoff:
            fail(f"handoff missing {key}")
    if not isinstance(handoff["dependencies"], list) or not isinstance(handoff["constraints"], list):
        fail("handoff dependencies/constraints must be lists")

    governance = data.get("governance")
    if governance is not None:
        if not isinstance(governance, dict):
            fail("governance must be an object")
        fp = governance.get("first_principles")
        if fp is not None:
            if not isinstance(fp, dict):
                fail("governance.first_principles must be an object")
            if not isinstance(fp.get("status"), str) or fp.get("status") not in FP_STATUS:
                fail("invalid governance.first_principles.status")
            if not isinstance(fp.get("required"), bool):
                fail("governance.first_principles.required must be boolean")
            if fp.get("required") and fp.get("status") == "not_required":
                fail("required First Principles cannot have status not_required")


def _unique_pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _reject_nonfinite(value):
    raise ValueError(f"non-finite JSON number: {value}")


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: validate_context_envelope.py <file.json>", file=sys.stderr)
        raise SystemExit(2)
    path = pathlib.Path(sys.argv[1])
    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_pairs, parse_constant=_reject_nonfinite)
        validate(data)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print("OK: cometweb.context/v2")


if __name__ == "__main__":
    main()
