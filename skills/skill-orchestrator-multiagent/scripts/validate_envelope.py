#!/usr/bin/env python3
"""Validate CW-AIP envelope JSON between multiagent workflow steps.

Accepts both protocol versions, dispatching on ``protocol_version``:

- ``1.0`` — checked against the bundled v1 core schema.
- ``2.0`` — checked against the bundled v2 core schema, and the canonical
  ``payload_hash`` is recomputed unless it is the draft marker ``pending``.

Typed payload semantics (evidence graph, decision gates) stay with the producing
skill; this gate checks the envelope shape a parent needs before step N+1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None  # type: ignore

REFERENCES = Path(__file__).resolve().parents[1] / "references"
SCHEMA = REFERENCES / "envelope.core.schema.json"
SCHEMA_V2 = REFERENCES / "cw-aip-v2.core.schema.json"
SCHEMAS = {"1.0": SCHEMA, "2.0": SCHEMA_V2}

REQUIRED_BY_TYPE: dict[str, list[str]] = {
    "EvidenceEnvelope": ["payload"],
    "DecisionHandoff": ["payload"],
    "FindingEnvelope": ["payload"],
    "SpecialistHandoff": ["payload"],
    "ArtifactEnvelope": ["payload"],
    "SnapshotMetadata": ["payload"],
}

# The planner names v1 kinds. A v2 producer answers a v1 DecisionHandoff step
# with the typed v2 kind for its domain, so --expect-type accepts that kind too.
V2_EQUIVALENTS: dict[str, frozenset[str]] = {
    "DecisionHandoff": frozenset({"DecisionEnvelope", "ReleaseEnvelope"}),
}


def load_envelope(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("envelope must be a JSON object")
    return data


def payload_hash(payload: dict[str, Any]) -> str:
    """Canonical CW-AIP v2 payload hash (see protocol/cw-aip-v2/README.md)."""
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def type_matches(expected: str, actual: object, version: object) -> bool:
    if actual == expected:
        return True
    return version == "2.0" and actual in V2_EQUIVALENTS.get(expected, frozenset())


def check_payload_hash(data: dict, final: bool) -> list[str]:
    digest = data.get("payload_hash")
    payload = data.get("payload")
    if not isinstance(digest, str) or not isinstance(payload, dict):
        return []  # already reported by the schema
    if digest == "pending":
        return ["payload_hash: 'pending' is a draft marker and is rejected by --final"] if final else []
    try:
        expected = payload_hash(payload)
    except ValueError as exc:
        return [f"payload_hash: payload is not canonical JSON: {exc}"]
    if "sha256:" + digest.removeprefix("sha256:").lower() != expected:
        return [f"payload_hash mismatch: got {digest}, expected {expected}"]
    return []


def validate_envelope(data: dict, expected_type: str | None = None, *, final: bool = False) -> list[str]:
    errors: list[str] = []
    version = data.get("protocol_version")
    if expected_type and not type_matches(expected_type, data.get("type"), version):
        errors.append(f"type: expected {expected_type!r}, got {data.get('type')!r}")
    schema_path = SCHEMAS.get(version) if isinstance(version, str) else None
    if jsonschema is None:
        errors.append("jsonschema dependency is required for envelope validation")
    elif schema_path is None:
        errors.append(f"schema: unsupported protocol_version {version!r} (expected '1.0' or '2.0')")
    elif not schema_path.is_file():
        errors.append("bundled envelope schema is missing")
    else:
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            jsonschema.Draft202012Validator.check_schema(schema)
            jsonschema.validate(data, schema)
        except (OSError, json.JSONDecodeError, jsonschema.SchemaError) as exc:
            errors.append(f"schema unavailable or invalid: {exc}")
        except jsonschema.ValidationError as exc:
            errors.append(f"schema: {exc.message}")
    env_type = data.get("type")
    if version == "1.0" and isinstance(env_type, str) and env_type in REQUIRED_BY_TYPE:
        if "payload" not in data or not isinstance(data.get("payload"), dict):
            errors.append(f"{env_type} requires object payload")
    if version == "2.0":
        errors.extend(check_payload_hash(data, final))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate CW-AIP v1 or v2 envelope JSON")
    parser.add_argument("envelope_json", help="Path to envelope JSON file")
    parser.add_argument("--expect-type", default="", help="Expected envelope type")
    parser.add_argument("--final", action="store_true", help="Reject a v2 payload_hash of 'pending'")
    args = parser.parse_args()

    path = Path(args.envelope_json)
    try:
        data = load_envelope(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    errors = validate_envelope(data, expected_type=args.expect_type or None, final=args.final)
    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        return 1

    print(
        f"OK: envelope {data.get('id')} type={data.get('type')} producer={data.get('producer')} "
        f"protocol_version={data.get('protocol_version')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
