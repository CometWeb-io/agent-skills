#!/usr/bin/env python3
"""Validate and score a destination feature matrix without optimistic defaults."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

PRIORITY_WEIGHTS = {"must": 3, "should": 2, "could": 1}
STATUS_CREDIT = {"done": 1.0, "partial": 0.5, "missing": 0.0}
STATUSES = set(STATUS_CREDIT) | {"skip"}
EVIDENCE_SUBJECTS = {"source", "destination"}


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and all(_nonempty(item) for item in value)


def _split_refs(value: str | None) -> list[str]:
    return [item.strip() for item in (value or "").split(";") if item.strip()]


def load_matrix(path: Path, evidence_path: Path | None = None) -> dict[str, Any]:
    if path.suffix.casefold() == ".csv":
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        evidence_file = evidence_path or path.with_name(f"{path.stem}.evidence.json")
        evidence = json.loads(evidence_file.read_text(encoding="utf-8")) if evidence_file.is_file() else []
        return {
            "schema_version": "cometweb.feature-matrix/v1",
            "evidence": evidence,
            "features": [
                {
                    "id": row.get("id", ""),
                    "name": row.get("name", ""),
                    "priority": row.get("priority", ""),
                    "status": row.get("status", ""),
                    "source_evidence_ids": _split_refs(row.get("source_evidence_ids")),
                    "target_evidence_ids": _split_refs(row.get("target_evidence_ids")),
                    "scope_reason": row.get("scope_reason", ""),
                }
                for row in rows
            ],
        }
    return json.loads(path.read_text(encoding="utf-8"))


def validate(payload: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["root must be an object"]
    if payload.get("schema_version") != "cometweb.feature-matrix/v1":
        errors.append("schema_version must be 'cometweb.feature-matrix/v1'")
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
        if not _nonempty(identifier):
            errors.append(f"{path}.id is required")
        elif identifier in evidence_by_id:
            errors.append(f"duplicate evidence id: {identifier}")
        else:
            evidence_by_id[identifier] = row
        if row.get("subject") not in EVIDENCE_SUBJECTS:
            errors.append(f"{path}.subject must be source or destination")
        for field in ("source", "locator"):
            if not _nonempty(row.get(field)):
                errors.append(f"{path}.{field} is required")
    features = payload.get("features")
    if not isinstance(features, list) or not features:
        return [*errors, "features must be a non-empty array"]

    seen: set[str] = set()
    for index, feature in enumerate(features):
        path = f"features[{index}]"
        if not isinstance(feature, dict):
            errors.append(f"{path} must be an object")
            continue
        identifier = feature.get("id")
        if not _nonempty(identifier):
            errors.append(f"{path}.id is required")
        elif identifier in seen:
            errors.append(f"duplicate feature id: {identifier}")
        else:
            seen.add(identifier)
        if not _nonempty(feature.get("name")):
            errors.append(f"{path}.name is required")
        if feature.get("priority") not in PRIORITY_WEIGHTS:
            errors.append(f"{path}.priority must be one of {sorted(PRIORITY_WEIGHTS)}")
        status = feature.get("status")
        if status not in STATUSES:
            errors.append(f"{path}.status must be one of {sorted(STATUSES)}")
        for field in ("source_evidence_ids", "target_evidence_ids"):
            if not _string_list(feature.get(field)):
                errors.append(f"{path}.{field} must be a string array")
        if not feature.get("source_evidence_ids"):
            errors.append(f"{path}.source_evidence_ids must not be empty")
        source_references = feature.get("source_evidence_ids")
        target_references = feature.get("target_evidence_ids")
        for reference in source_references if isinstance(source_references, list) else []:
            evidence_row = evidence_by_id.get(reference)
            if evidence_row is None:
                errors.append(f"{path}.source_evidence_ids references unknown evidence: {reference}")
            elif evidence_row.get("subject") != "source":
                errors.append(f"{path}.source_evidence_ids must reference source evidence: {reference}")
        for reference in target_references if isinstance(target_references, list) else []:
            evidence_row = evidence_by_id.get(reference)
            if evidence_row is None:
                errors.append(f"{path}.target_evidence_ids references unknown evidence: {reference}")
            elif evidence_row.get("subject") != "destination":
                errors.append(f"{path}.target_evidence_ids must reference destination evidence: {reference}")
        if status in {"done", "partial"} and not feature.get("target_evidence_ids"):
            errors.append(f"{path}.target_evidence_ids is required for {status}")
        if status == "skip" and not _nonempty(feature.get("scope_reason")):
            errors.append(f"{path}.scope_reason is required for skip")
    return errors


def score_matrix(payload: dict[str, Any]) -> dict[str, Any]:
    errors = validate(payload)
    if errors:
        raise ValueError("; ".join(errors))
    included = [feature for feature in payload["features"] if feature["status"] != "skip"]
    denominator = sum(PRIORITY_WEIGHTS[feature["priority"]] for feature in included)
    numerator = sum(
        PRIORITY_WEIGHTS[feature["priority"]] * STATUS_CREDIT[feature["status"]]
        for feature in included
    )
    missing_work = sorted(
        (feature for feature in included if feature["status"] in {"missing", "partial"}),
        key=lambda feature: (-PRIORITY_WEIGHTS[feature["priority"]], feature["id"]),
    )
    return {
        "schema_version": "cometweb.feature-matrix-score/v1",
        "feature_count": len(payload["features"]),
        "included_count": len(included),
        "skipped_count": len(payload["features"]) - len(included),
        "weighted_numerator": numerator,
        "weighted_denominator": denominator,
        "score": round(numerator / denominator, 6) if denominator else None,
        "missing_work": [
            {"id": feature["id"], "name": feature["name"], "priority": feature["priority"],
             "status": feature["status"]}
            for feature in missing_work
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--evidence", type=Path, help="sidecar evidence JSON for CSV matrices")
    args = parser.parse_args()
    try:
        result = score_matrix(load_matrix(args.input, args.evidence))
    except (OSError, ValueError, json.JSONDecodeError, csv.Error) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
