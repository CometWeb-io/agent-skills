#!/usr/bin/env python3
"""Validate a full CW-AIP v2 envelope: core + typed payload + hash (+ optional --final)."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORE = ROOT / "protocol" / "cw-aip-v2" / "core.schema.json"
PAYLOAD_SCHEMAS = {
    "ContextEnvelope": ROOT / "protocol" / "cw-aip-v2" / "context.schema.json",
    "EvidenceEnvelope": ROOT / "protocol" / "cw-aip-v2" / "evidence.schema.json",
    "DecisionEnvelope": ROOT / "protocol" / "cw-aip-v2" / "decision.schema.json",
    "FindingEnvelope": ROOT / "protocol" / "cw-aip-v2" / "finding.schema.json",
    "RoadmapEnvelope": ROOT / "protocol" / "cw-aip-v2" / "roadmap.schema.json",
    "ReleaseEnvelope": ROOT / "protocol" / "cw-aip-v2" / "release.schema.json",
}


def fail(message: str) -> None:
    raise ValueError(message)


def payload_hash(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def validate_jsonschema(schema_path: pathlib.Path, data: dict[str, Any], label: str) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        path = ".".join(str(p) for p in first.path) or "<root>"
        fail(f"{label}:{path}: {first.message}")


def semantic_payload(envelope_type: str, payload: dict[str, Any]) -> None:
    tooling = str(ROOT / "tooling")
    if tooling not in sys.path:
        sys.path.insert(0, tooling)
    context_scripts = str(ROOT / "skills" / "cometweb-context" / "scripts")
    if context_scripts not in sys.path:
        sys.path.insert(0, context_scripts)

    if envelope_type == "ContextEnvelope":
        from validate_context_envelope import validate as validate_context

        validate_context(payload)
        return
    if envelope_type == "EvidenceEnvelope":
        from validate_evidence_envelope import validate as validate_evidence

        validate_evidence(payload)
        return
    if envelope_type == "DecisionEnvelope":
        from validate_decision_envelope import validate as validate_decision

        validate_decision(payload)
        return


def validate_envelope(data: dict[str, Any], *, final: bool = False) -> None:
    if not isinstance(data, dict):
        fail("envelope must be an object")
    validate_jsonschema(CORE, data, "core")
    envelope_type = data.get("type")
    if envelope_type not in PAYLOAD_SCHEMAS:
        fail(f"unsupported or missing type: {envelope_type!r}")
    payload = data.get("payload")
    if not isinstance(payload, dict):
        fail("payload must be an object")
    validate_jsonschema(PAYLOAD_SCHEMAS[envelope_type], payload, "payload")
    semantic_payload(envelope_type, payload)

    digest = data.get("payload_hash")
    if final and digest == "pending":
        fail("--final forbids payload_hash=pending")
    if digest and digest != "pending":
        expected = payload_hash(payload)
        bare = expected.removeprefix("sha256:")
        if digest not in {expected, bare, f"sha256:{digest}"}:
            fail(f"payload_hash mismatch: got {digest}, expected {expected}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument(
        "--final",
        action="store_true",
        help="Reject draft markers (payload_hash=pending)",
    )
    parser.add_argument(
        "--print-hash",
        action="store_true",
        help="Print canonical payload hash for the file's payload",
    )
    args = parser.parse_args()
    data = json.loads(pathlib.Path(args.file).read_text(encoding="utf-8"))
    if args.print_hash:
        payload = data.get("payload") if isinstance(data.get("payload"), dict) else data
        print(payload_hash(payload))
        return
    validate_envelope(data, final=args.final)
    print(f"OK: CW-AIP v2 envelope ({data.get('type')})")


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
