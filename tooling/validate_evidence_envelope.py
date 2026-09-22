#!/usr/bin/env python3
"""Validate CW-AIP v2 EvidenceEnvelope payloads."""
from __future__ import annotations

import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "protocol" / "cw-aip-v2" / "evidence.schema.json"
REQUIRED = {
    "schema",
    "research_contract",
    "mode",
    "as_of",
    "material_claims",
    "sources",
    "evidence_edges",
    "gaps",
    "contradictions",
    "readiness",
    "evidence_pack_hash",
}
ALLOWED = REQUIRED | {"handoff"}


def fail(message: str) -> None:
    raise ValueError(message)


def require_object_list(value: object, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        fail(f"{label} must be an array of objects")
    return value


def validate_fallback(data: dict[str, Any]) -> None:
    missing = sorted(REQUIRED - set(data))
    if missing:
        fail(f"missing {missing[0]}")
    unexpected = sorted(set(data) - ALLOWED)
    if unexpected:
        fail(f"unexpected properties: {', '.join(unexpected)}")
    if data.get("schema") != "cometweb.evidence/v2":
        fail("schema must be cometweb.evidence/v2")
    for key in ("research_contract", "as_of", "evidence_pack_hash"):
        if not isinstance(data.get(key), str) or not data[key]:
            fail(f"{key} must be a non-empty string")
    if data.get("mode") not in {"QUICK", "STANDARD", "DEEP"}:
        fail("mode must be QUICK|STANDARD|DEEP")
    if data.get("readiness") not in {"READY", "NOT_READY", "DEFER"}:
        fail("readiness must be READY|NOT_READY|DEFER")

    for claim in require_object_list(data.get("material_claims"), "material_claims"):
        for key in ("claim_id", "text", "status"):
            if not isinstance(claim.get(key), str) or not claim[key]:
                fail(f"material_claims.{key} must be a non-empty string")
        if claim.get("epistemic_kind") not in {"FACT", "INFERENCE"}:
            fail("material_claims.epistemic_kind must be FACT|INFERENCE")
        if claim.get("materiality") not in {"critical", "material", "supporting"}:
            fail("material_claims.materiality must be critical|material|supporting")

    for source in require_object_list(data.get("sources"), "sources"):
        if not isinstance(source.get("source_id"), str) or not source["source_id"]:
            fail("sources.source_id must be a non-empty string")

    for edge in require_object_list(data.get("evidence_edges"), "evidence_edges"):
        for key in ("edge_id", "claim_id", "source_id"):
            if not isinstance(edge.get(key), str):
                fail(f"evidence_edges.{key} must be a string")
        if edge.get("direction") not in {"SUPPORT", "CONTRADICT", "CONTEXT"}:
            fail("evidence_edges.direction must be SUPPORT|CONTRADICT|CONTEXT")
        if edge.get("admission") not in {"ACCEPTED", "CONTEXT_ONLY", "REJECTED"}:
            fail("evidence_edges.admission must be ACCEPTED|CONTEXT_ONLY|REJECTED")

    require_object_list(data.get("gaps"), "gaps")
    require_object_list(data.get("contradictions"), "contradictions")
    handoff = data.get("handoff")
    if handoff is not None:
        if not isinstance(handoff, dict):
            fail("handoff must be an object")
        next_skill = handoff.get("recommended_next_skill")
        if next_skill is not None and not isinstance(next_skill, str):
            fail("handoff.recommended_next_skill must be a string or null")
        constraints = handoff.get("constraints")
        if constraints is not None and (
            not isinstance(constraints, list) or not all(isinstance(item, str) for item in constraints)
        ):
            fail("handoff.constraints must be an array of strings")


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


def validate_semantics(data: dict[str, Any]) -> None:
    source_ids = {s.get("source_id") for s in data.get("sources") or [] if isinstance(s, dict)}
    claim_ids = set()
    for claim in data.get("material_claims") or []:
        cid = claim.get("claim_id")
        if cid in claim_ids:
            fail(f"duplicate claim_id: {cid}")
        claim_ids.add(cid)
        if claim.get("epistemic_kind") == "INFERENCE" and claim.get("status") == "VERIFIED":
            fail(f"{cid}: INFERENCE cannot be VERIFIED")

    for edge in data.get("evidence_edges") or []:
        if edge.get("claim_id") not in claim_ids:
            fail(f"edge {edge.get('edge_id')} unknown claim_id")
        if edge.get("source_id") not in source_ids:
            fail(f"edge {edge.get('edge_id')} unknown source_id")

    if data.get("readiness") == "READY":
        for gap in data.get("gaps") or []:
            if isinstance(gap, dict) and gap.get("blocking"):
                fail("READY cannot have blocking gaps")
        for contradiction in data.get("contradictions") or []:
            if isinstance(contradiction, dict) and contradiction.get("status") == "unresolved":
                if contradiction.get("materiality") in {"critical", "material"}:
                    fail("READY cannot have unresolved material contradictions")


def validate(data: dict[str, Any]) -> None:
    if not isinstance(data, dict):
        fail("payload must be an object")
    validate_schema(data)
    validate_semantics(data)


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: validate_evidence_envelope.py <file.json>", file=sys.stderr)
        raise SystemExit(2)
    data = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    # Accept full CW-AIP core wrapper or bare payload
    payload = data.get("payload") if data.get("type") == "EvidenceEnvelope" and "payload" in data else data
    validate(payload)
    print("OK: cometweb.evidence/v2")


if __name__ == "__main__":
    main()
