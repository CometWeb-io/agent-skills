#!/usr/bin/env python3
"""Deterministic ranking aid for Product Teardown v2 pattern candidates.

The score is not evidence and never overrides proof burdens or mandatory gates.
Input may be a pattern object, an array of patterns, or a v2 ledger with patterns[].
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

POSITIVE_WEIGHTS = {
    "problem_fit": 0.14,
    "mechanism_fit": 0.12,
    "source_evidence_strength": 0.10,
    "destination_evidence_strength": 0.12,
    "implementation_feasibility": 0.12,
    "expected_upside": 0.10,
    "reversibility": 0.07,
    "maintenance_fit": 0.07,
    "strategic_fit": 0.08,
    "differentiation": 0.08,
}

PENALTY_WEIGHTS = {
    "dependency_risk": 0.08,
    "complexity_tax": 0.08,
    "opportunity_cost": 0.04,
    "legal_ip_risk": 0.05,
    "security_privacy_risk": 0.05,
    "measurement_risk": 0.03,
}

VALID_GATES = {"clear", "not_required", "review", "block", "unknown"}


def clamp01(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric in [0,1]") from exc
    if not 0.0 <= number <= 1.0:
        raise ValueError(f"{field} must be in [0,1], got {number}")
    return number


def gate_state(pattern: dict[str, Any]) -> str:
    gates = pattern.get("gates") or {}
    values: list[str] = []
    for key in ("legal_ip", "security_privacy"):
        value = str(gates.get(key, "unknown")).lower()
        if value not in VALID_GATES:
            raise ValueError(f"gates.{key} must be one of {sorted(VALID_GATES)}")
        values.append(value)
    if "block" in values:
        return "block"
    if "review" in values or "unknown" in values:
        return "review"
    return "clear"


def has_target_evidence(pattern: dict[str, Any], transfer: dict[str, float]) -> bool:
    refs = pattern.get("target_evidence_ids") or []
    return bool(refs) and transfer["destination_evidence_strength"] >= 0.35


def classify(score: int, pattern: dict[str, Any], transfer: dict[str, float], gate: str) -> str:
    # Source-only discovery cannot be promoted to a target action by a score.
    if not has_target_evidence(pattern, transfer):
        return "CANDIDATE"
    if gate != "clear":
        return "REVIEW_REQUIRED"
    if (
        score >= 76
        and transfer["source_evidence_strength"] >= 0.65
        and transfer["destination_evidence_strength"] >= 0.65
        and transfer["implementation_feasibility"] >= 0.60
        and transfer["strategic_fit"] >= 0.50
    ):
        return "ADOPT"
    if score >= 56 and transfer["reversibility"] >= 0.45:
        return "EXPERIMENT"
    if score >= 40:
        return "BACKLOG"
    return "REJECT"


def score_pattern(pattern: dict[str, Any]) -> dict[str, Any]:
    transfer_raw = pattern.get("transfer") or {}
    required = (*POSITIVE_WEIGHTS, *PENALTY_WEIGHTS)
    missing = [key for key in required if key not in transfer_raw]
    if missing:
        pid = pattern.get("id", "<unknown>")
        raise ValueError(f"pattern {pid} missing transfer fields: {', '.join(missing)}")

    transfer: dict[str, float] = {}
    for key in required:
        transfer[key] = clamp01(transfer_raw[key], f"transfer.{key}")

    positive = sum(POSITIVE_WEIGHTS[key] * transfer[key] for key in POSITIVE_WEIGHTS)
    penalty = sum(PENALTY_WEIGHTS[key] * transfer[key] for key in PENALTY_WEIGHTS)
    raw = max(0.0, min(1.0, positive - penalty))
    score = round(raw * 100)
    gate = gate_state(pattern)
    suggested = classify(score, pattern, transfer, gate)

    result = dict(pattern)
    result["heuristic_score"] = score
    result["gate_state"] = gate
    result["suggested_action"] = suggested
    result["score_components"] = {
        "positive": round(positive, 4),
        "penalty": round(penalty, 4),
        "target_evidence_ceiling_applied": not has_target_evidence(pattern, transfer),
    }
    return result


def normalize(payload: Any) -> tuple[list[dict[str, Any]], bool]:
    if isinstance(payload, dict) and isinstance(payload.get("patterns"), list):
        return payload["patterns"], True
    if isinstance(payload, list):
        return payload, False
    if isinstance(payload, dict):
        return [payload], False
    raise ValueError("input must be a pattern object, array of patterns, or ledger with patterns[]")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", help="JSON file; stdin if omitted")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    try:
        text = open(args.input, "r", encoding="utf-8").read() if args.input else sys.stdin.read()
        payload = json.loads(text)
        patterns, was_ledger = normalize(payload)
        scored = [score_pattern(pattern) for pattern in patterns]
        scored.sort(key=lambda row: (-row["heuristic_score"], str(row.get("id", ""))))
        if was_ledger:
            output = dict(payload)
            output["patterns"] = scored
        else:
            output = scored[0] if isinstance(payload, dict) else scored
        json.dump(output, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
        sys.stdout.write("\n")
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
