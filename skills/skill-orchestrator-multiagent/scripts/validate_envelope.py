#!/usr/bin/env python3
"""Validate CW-AIP envelope JSON between multiagent workflow steps."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None  # type: ignore

ROOT = Path(__file__).resolve().parents[3]
SCHEMA = ROOT / "protocol" / "schemas" / "envelope.core.schema.json"

REQUIRED_BY_TYPE: dict[str, list[str]] = {
    "EvidenceEnvelope": ["payload"],
    "DecisionHandoff": ["payload"],
    "FindingEnvelope": ["payload"],
    "SpecialistHandoff": ["payload"],
    "ArtifactEnvelope": ["payload"],
    "SnapshotMetadata": ["payload"],
}


def load_envelope(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("envelope must be a JSON object")
    return data


def validate_envelope(data: dict, expected_type: str | None = None) -> list[str]:
    errors: list[str] = []
    if expected_type and data.get("type") != expected_type:
        errors.append(f"type: expected {expected_type!r}, got {data.get('type')!r}")
    if jsonschema and SCHEMA.is_file():
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        try:
            jsonschema.validate(data, schema)
        except jsonschema.ValidationError as exc:
            errors.append(f"schema: {exc.message}")
    else:
        for key in ("id", "type", "producer", "protocol_version", "subject", "as_of"):
            if key not in data:
                errors.append(f"missing required field: {key}")
        if data.get("protocol_version") != "1.0":
            errors.append("protocol_version must be '1.0'")
    env_type = data.get("type")
    if isinstance(env_type, str) and env_type in REQUIRED_BY_TYPE:
        if "payload" not in data or not isinstance(data.get("payload"), dict):
            errors.append(f"{env_type} requires object payload")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate CW-AIP envelope JSON")
    parser.add_argument("envelope_json", help="Path to envelope JSON file")
    parser.add_argument("--expect-type", default="", help="Expected envelope type")
    args = parser.parse_args()

    path = Path(args.envelope_json)
    try:
        data = load_envelope(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    errors = validate_envelope(data, expected_type=args.expect_type or None)
    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        return 1

    print(f"OK: envelope {data.get('id')} type={data.get('type')} producer={data.get('producer')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
