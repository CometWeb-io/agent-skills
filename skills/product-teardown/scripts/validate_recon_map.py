#!/usr/bin/env python3
"""Validate a clean-room reconstruction map without judging factual truth."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "cometweb.reconstruction-map/v1"
CLAIM_STATES = {"OBSERVED", "INFERRED", "UNKNOWN"}
PRIORITIES = {"must", "should", "could"}
STATUSES = {"done", "partial", "missing", "skip"}
TRANSFER_MODES = {"INSPIRE", "REIMPLEMENT", "INTEGRATE", "REUSE_CODE", "REUSE_ASSET"}
ID_PATTERN = re.compile(r"[A-Z][A-Z0-9-]{1,31}")


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any, *, required: bool = False) -> bool:
    return isinstance(value, list) and (bool(value) or not required) and all(_nonempty(item) for item in value)


def _confidence(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= 1


def _unique_ids(rows: list[Any], path: str, errors: list[str]) -> set[str]:
    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"{path}[{index}] must be an object")
            continue
        identifier = row.get("id")
        if not isinstance(identifier, str) or ID_PATTERN.fullmatch(identifier) is None:
            errors.append(f"{path}[{index}].id is invalid")
        elif identifier in seen:
            errors.append(f"{path} contains duplicate id: {identifier}")
        else:
            seen.add(identifier)
    return seen


def validate(payload: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["root must be a JSON object"]

    required = {
        "schema_version",
        "source",
        "destination",
        "boundaries",
        "evidence",
        "screens",
        "flows",
        "features",
        "unknowns",
    }
    missing = sorted(required - set(payload))
    if missing:
        errors.append(f"missing root fields: {', '.join(missing)}")
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be '{SCHEMA_VERSION}'")

    for name in ("source", "destination"):
        record = payload.get(name)
        if not isinstance(record, dict):
            errors.append(f"{name} must be an object")
            continue
        for field in ("name", "kind", "ref", "version", "observed_at"):
            if not _nonempty(record.get(field)):
                errors.append(f"{name}.{field} is required")

    boundaries = payload.get("boundaries")
    if not isinstance(boundaries, dict):
        errors.append("boundaries must be an object")
    else:
        for field in ("allowed", "prohibited"):
            if not _string_list(boundaries.get(field), required=True):
                errors.append(f"boundaries.{field} must be a non-empty string array")
        transfer_mode = boundaries.get("default_transfer_mode")
        if transfer_mode not in TRANSFER_MODES:
            errors.append("boundaries.default_transfer_mode is invalid")
        prohibited = {item.casefold().replace("_", " ") for item in boundaries.get("prohibited", [])}
        required_prohibitions = {"private endpoints", "credentials", "proprietary data"}
        if not required_prohibitions <= prohibited:
            errors.append("boundaries.prohibited must name private endpoints, credentials, and proprietary data")

    evidence = payload.get("evidence")
    evidence_by_id: dict[str, dict[str, Any]] = {}
    if not isinstance(evidence, list) or not evidence:
        errors.append("evidence must be a non-empty array")
        evidence = []
    for index, row in enumerate(evidence):
        path = f"evidence[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{path} must be an object")
            continue
        identifier = row.get("id")
        if not isinstance(identifier, str) or ID_PATTERN.fullmatch(identifier) is None:
            errors.append(f"{path}.id is invalid")
        elif identifier in evidence_by_id:
            errors.append(f"duplicate evidence id: {identifier}")
        else:
            evidence_by_id[identifier] = row
        for field in ("subject", "source", "locator", "note"):
            if not _nonempty(row.get(field)):
                errors.append(f"{path}.{field} is required")
        if row.get("subject") not in {"source", "destination"}:
            errors.append(f"{path}.subject must be source or destination")
        if row.get("claim_state") not in CLAIM_STATES:
            errors.append(f"{path}.claim_state is invalid")
        if not _confidence(row.get("confidence")):
            errors.append(f"{path}.confidence must be in [0,1]")

    screens = payload.get("screens")
    if not isinstance(screens, list) or not screens:
        errors.append("screens must be a non-empty array")
        screens = []
    screen_ids = _unique_ids(screens, "screens", errors)
    for index, row in enumerate(screens):
        if not isinstance(row, dict):
            continue
        path = f"screens[{index}]"
        for field in ("name", "states"):
            if field == "states":
                if not _string_list(row.get(field), required=True):
                    errors.append(f"{path}.states must be a non-empty string array")
            elif not _nonempty(row.get(field)):
                errors.append(f"{path}.{field} is required")
        refs = row.get("evidence_ids")
        if not _string_list(refs, required=True):
            errors.append(f"{path}.evidence_ids must be a non-empty string array")
        else:
            errors.extend(f"{path}.evidence_ids references unknown evidence: {ref}"
                          for ref in refs if ref not in evidence_by_id)

    flows = payload.get("flows")
    if not isinstance(flows, list) or not flows:
        errors.append("flows must be a non-empty array")
        flows = []
    _unique_ids(flows, "flows", errors)
    for index, row in enumerate(flows):
        if not isinstance(row, dict):
            continue
        path = f"flows[{index}]"
        if not _nonempty(row.get("name")):
            errors.append(f"{path}.name is required")
        if not _string_list(row.get("steps"), required=True):
            errors.append(f"{path}.steps must be a non-empty string array")
        refs = row.get("evidence_ids")
        if not _string_list(refs, required=True):
            errors.append(f"{path}.evidence_ids must be a non-empty string array")
        else:
            errors.extend(f"{path}.evidence_ids references unknown evidence: {ref}"
                          for ref in refs if ref not in evidence_by_id)

    features = payload.get("features")
    if not isinstance(features, list) or not features:
        errors.append("features must be a non-empty array")
        features = []
    _unique_ids(features, "features", errors)
    for index, row in enumerate(features):
        if not isinstance(row, dict):
            continue
        path = f"features[{index}]"
        if row.get("priority") not in PRIORITIES:
            errors.append(f"{path}.priority is invalid")
        status = row.get("status")
        if status not in STATUSES:
            errors.append(f"{path}.status is invalid")
        if not _nonempty(row.get("name")):
            errors.append(f"{path}.name is required")
        source_refs = row.get("source_evidence_ids")
        target_refs = row.get("target_evidence_ids")
        if not _string_list(source_refs, required=True):
            errors.append(f"{path}.source_evidence_ids must be a non-empty string array")
        else:
            errors.extend(f"{path}.source_evidence_ids references unknown evidence: {ref}"
                          for ref in source_refs if ref not in evidence_by_id)
            errors.extend(
                f"{path}.source_evidence_ids must reference source evidence: {ref}"
                for ref in source_refs
                if ref in evidence_by_id and evidence_by_id[ref].get("subject") != "source"
            )
        if not _string_list(target_refs):
            errors.append(f"{path}.target_evidence_ids must be a string array")
        else:
            errors.extend(f"{path}.target_evidence_ids references unknown evidence: {ref}"
                          for ref in target_refs if ref not in evidence_by_id)
            errors.extend(
                f"{path}.target_evidence_ids must reference destination evidence: {ref}"
                for ref in target_refs
                if ref in evidence_by_id and evidence_by_id[ref].get("subject") != "destination"
            )
        if status == "skip" and not _nonempty(row.get("scope_reason")):
            errors.append(f"{path}.scope_reason is required for skip")
        if status in {"done", "partial"} and not target_refs:
            errors.append(f"{path}.target_evidence_ids is required for {status}")

    unknowns = payload.get("unknowns")
    if not _string_list(unknowns, required=True):
        errors.append("unknowns must be a non-empty string array")

    # Keep the variables in the validator's local contract so malformed
    # screen/flow references cannot be accidentally ignored in future changes.
    if screen_ids and any(not identifier.startswith("S") for identifier in screen_ids):
        errors.append("screen ids must start with S")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", help="map JSON file; stdin if omitted")
    args = parser.parse_args()
    try:
        text = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
        payload = json.loads(text)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INVALID: {exc}")
        return 2
    errors = validate(payload)
    if errors:
        print("INVALID")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("VALID")
    print(f"evidence={len(payload['evidence'])} features={len(payload['features'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
