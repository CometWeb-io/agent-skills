#!/usr/bin/env python3
"""Validate CW-AIP v2 EvidenceEnvelope payloads."""
from __future__ import annotations

import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "protocol" / "cw-aip-v2" / "evidence.schema.json"


def fail(message: str) -> None:
    raise ValueError(message)


def validate_schema(data: dict[str, Any]) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        if data.get("schema") != "cometweb.evidence/v2":
            fail("schema must be cometweb.evidence/v2")
        for key in (
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
