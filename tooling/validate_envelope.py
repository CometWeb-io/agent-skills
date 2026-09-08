#!/usr/bin/env python3
"""Validate a full CW-AIP v2 envelope: core + typed payload + hash (+ optional --final)."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
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
HASH_RE = re.compile(r"^(sha256:)?[a-fA-F0-9]{64}$|^pending$")
CORE_REQUIRED = (
    "id",
    "type",
    "producer",
    "producer_version",
    "protocol_version",
    "subject",
    "generated_at",
    "as_of",
    "sensitivity",
    "dependencies",
    "payload",
    "payload_hash",
)


def fail(message: str) -> None:
    raise ValueError(message)


def payload_hash(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def normalize_hash(value: str) -> str:
    if value == "pending":
        return value
    bare = value.removeprefix("sha256:")
    return f"sha256:{bare.lower()}"


def validate_jsonschema(schema_path: pathlib.Path, data: dict[str, Any], label: str) -> bool:
    """Return True if jsonschema ran; False if library missing (caller must fallback)."""
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return False
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        path = ".".join(str(p) for p in first.path) or "<root>"
        fail(f"{label}:{path}: {first.message}")
    return True


def validate_core_fallback(data: dict[str, Any]) -> None:
    for key in CORE_REQUIRED:
        if key not in data:
            fail(f"core: missing {key}")
    if not isinstance(data.get("id"), str) or not data["id"]:
        fail("core:id must be non-empty string")
    if data.get("protocol_version") != "2.0":
        fail("core:protocol_version must be '2.0'")
    if not isinstance(data.get("producer"), str) or not data["producer"]:
        fail("core:producer must be non-empty string")
    if not isinstance(data.get("producer_version"), str) or not data["producer_version"]:
        fail("core:producer_version must be non-empty string")
    if data.get("sensitivity") not in {"public", "internal", "confidential", "restricted"}:
        fail("core: invalid sensitivity")
    if not isinstance(data.get("dependencies"), list):
        fail("core:dependencies must be an array")
    digest = data.get("payload_hash")
    if not isinstance(digest, str) or not HASH_RE.match(digest):
        fail("core:payload_hash must be sha256 hex or 'pending'")


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
    if envelope_type == "FindingEnvelope":
        if payload.get("schema") != "cometweb.finding/v2":
            fail("finding:schema must be cometweb.finding/v2")
        if not payload.get("finding_id") or not payload.get("title"):
            fail("finding: finding_id and title required")
        if not isinstance(payload.get("evidence_refs"), list):
            fail("finding:evidence_refs must be a list")
        return
    if envelope_type == "RoadmapEnvelope":
        if payload.get("schema") != "cometweb.roadmap/v2":
            fail("roadmap:schema must be cometweb.roadmap/v2")
        if not isinstance(payload.get("items"), list):
            fail("roadmap:items must be a list")
        return
    if envelope_type == "ReleaseEnvelope":
        if payload.get("schema") != "cometweb.release/v2":
            fail("release:schema must be cometweb.release/v2")
        if payload.get("verdict") not in {"GO", "NO_GO", "DEFER", "GO_WITH_CONTROLS"}:
            fail("release:verdict must be GO|NO_GO|DEFER|GO_WITH_CONTROLS")
        return


def validate_envelope(data: dict[str, Any], *, final: bool = False) -> None:
    if not isinstance(data, dict):
        fail("envelope must be an object")
    if not validate_jsonschema(CORE, data, "core"):
        validate_core_fallback(data)

    envelope_type = data.get("type")
    if envelope_type not in PAYLOAD_SCHEMAS:
        fail(f"unsupported or missing type: {envelope_type!r}")
    payload = data.get("payload")
    if not isinstance(payload, dict):
        fail("payload must be an object")
    if not validate_jsonschema(PAYLOAD_SCHEMAS[envelope_type], payload, "payload"):
        # Minimal fallback: require schema field when present on typed payloads
        if "schema" in payload and not isinstance(payload["schema"], str):
            fail("payload:schema must be a string")
    semantic_payload(envelope_type, payload)

    digest = data.get("payload_hash")
    if not isinstance(digest, str):
        fail("payload_hash must be a string")
    if final and digest == "pending":
        fail("--final forbids payload_hash=pending")
    if digest != "pending":
        if not HASH_RE.match(digest) or digest == "pending":
            fail(f"invalid payload_hash: {digest!r}")
        expected = normalize_hash(payload_hash(payload))
        got = normalize_hash(digest)
        if got != expected:
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
