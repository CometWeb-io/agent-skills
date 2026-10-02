#!/usr/bin/env python3
"""Validate CW-AIP envelope JSON between multiagent workflow steps.

Accepts both protocol versions, dispatching on ``protocol_version``:

- ``1.0`` — checked against the bundled v1 core schema, or, for a kind with a
  v1 kind schema (``EvidenceEnvelope``, ``DecisionHandoff``), against that kind
  schema, which includes the core.
- ``2.0`` — checked against the bundled v2 core schema, and the canonical
  ``payload_hash`` is recomputed unless it is the draft marker ``pending``.

For both versions an authorizing verdict (``GO``, and for releases
``GO_WITH_CONTROLS``) next to a non-empty ``blockers`` list is rejected. Full v2
payload semantics (evidence graph, decision gates) stay with the producing skill
and ``tooling/validate_envelope.py``; this gate checks what a parent needs before
step N+1.
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
# v1 kinds whose kind schema adds payload rules on top of the core. Each one
# references the core by $id, so the bundled core is registered alongside it.
V1_KIND_SCHEMAS = {
    "EvidenceEnvelope": REFERENCES / "evidence-envelope.schema.json",
    "DecisionHandoff": REFERENCES / "decision-handoff.schema.json",
}
# v2 kinds and the verdicts that authorize action. A blocker next to any of
# them is incoherent; controls bound residual risk but do not clear a blocker.
V2_AUTHORIZING_VERDICTS: dict[str, frozenset[str]] = {
    "DecisionEnvelope": frozenset({"GO"}),
    "ReleaseEnvelope": frozenset({"GO", "GO_WITH_CONTROLS"}),
}

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


def check_authorizing_verdict(data: dict) -> list[str]:
    """v2 Decision/Release: an authorizing verdict cannot carry open blockers.

    The v1 ``DecisionHandoff`` kind schema expresses the same rule in JSON Schema.
    """
    verdicts = V2_AUTHORIZING_VERDICTS.get(data.get("type"))  # type: ignore[arg-type]
    payload = data.get("payload")
    if not verdicts or not isinstance(payload, dict):
        return []
    verdict = payload.get("verdict")
    if verdict in verdicts and isinstance(payload.get("blockers"), list) and payload["blockers"]:
        return [f"payload.blockers: {verdict} cannot have blockers"]
    return []


def load_schema(path: Path) -> dict:
    schema = json.loads(path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    return schema


def build_validator(core_path: Path, kind_path: Path | None) -> "jsonschema.Draft202012Validator":
    core = load_schema(core_path)
    if kind_path is None:
        return jsonschema.Draft202012Validator(core)
    from referencing import Registry, Resource

    registry = Registry().with_resource(core["$id"], Resource.from_contents(core))
    return jsonschema.Draft202012Validator(load_schema(kind_path), registry=registry)


def schema_errors(data: dict, version: object) -> list[str]:
    schema_path = SCHEMAS.get(version) if isinstance(version, str) else None
    if jsonschema is None:
        return ["jsonschema dependency is required for envelope validation"]
    if schema_path is None:
        return [f"schema: unsupported protocol_version {version!r} (expected '1.0' or '2.0')"]
    if not schema_path.is_file():
        return ["bundled envelope schema is missing"]
    env_type = data.get("type")
    kind_path = V1_KIND_SCHEMAS.get(env_type) if version == "1.0" and isinstance(env_type, str) else None
    if kind_path is not None and not kind_path.is_file():
        # Falling back to the core would silently drop the payload rules.
        return [f"bundled kind schema is missing: {kind_path.name}"]
    try:
        validator = build_validator(schema_path, kind_path)
        found = sorted(
            validator.iter_errors(data), key=lambda e: ([str(part) for part in e.absolute_path], e.message)
        )
    except (OSError, json.JSONDecodeError, KeyError, jsonschema.SchemaError) as exc:
        return [f"schema unavailable or invalid: {exc}"]
    except Exception as exc:  # e.g. an unresolvable $ref: fail closed, never pass
        return [f"schema unavailable or invalid: {type(exc).__name__}: {exc}"]
    return [f"schema: {error.json_path}: {error.message}" for error in found]


def validate_envelope(data: dict, expected_type: str | None = None, *, final: bool = False) -> list[str]:
    errors: list[str] = []
    version = data.get("protocol_version")
    if expected_type and not type_matches(expected_type, data.get("type"), version):
        errors.append(f"type: expected {expected_type!r}, got {data.get('type')!r}")
    errors.extend(schema_errors(data, version))
    env_type = data.get("type")
    if version == "1.0" and isinstance(env_type, str) and env_type in REQUIRED_BY_TYPE:
        if "payload" not in data or not isinstance(data.get("payload"), dict):
            errors.append(f"{env_type} requires object payload")
    if version == "2.0":
        errors.extend(check_authorizing_verdict(data))
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
