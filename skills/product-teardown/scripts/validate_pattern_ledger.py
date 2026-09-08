#!/usr/bin/env python3
"""Validate Product Teardown v2 machine-readable ledgers.

Checks structure plus decision-critical cross-field invariants. It does not
validate the factual truth of evidence or recommendations.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

SCHEMA_VERSION = "2.0"
SHAPES = {"SOURCE_ONLY", "SOURCE_TO_TARGET", "MULTI_SOURCE_TO_TARGET"}
MODES = {"SNAPSHOT", "STANDARD", "DEEP"}
CLAIM_STATES = {"OBSERVED", "INFERRED", "HYPOTHESIS", "UNKNOWN"}
SOURCE_LANES = {"source_behavior", "source_implementation", "source_rationale", "source_outcome"}
DESTINATION_LANES = {
    "destination_problem",
    "destination_existing_capability",
    "destination_constraint",
    "destination_baseline",
}
VERDICTS = {"CANDIDATE", "ADOPT", "EXPERIMENT", "BACKLOG", "REJECT", "REVIEW_REQUIRED"}
GATES = {"clear", "not_required", "review", "block", "unknown"}
TRANSFER_MODES = {"INSPIRE", "REIMPLEMENT", "INTEGRATE", "REUSE_CODE", "REUSE_ASSET"}
CATEGORIES = {
    "jtbd_workflow",
    "information_architecture",
    "interaction",
    "activation_onboarding",
    "collaboration_permissions",
    "monetization",
    "data_domain_model",
    "architecture",
    "developer_experience",
    "reliability_operations",
    "trust_safety",
    "growth_distribution",
}
REQUIRED_TRANSFER = {
    "problem_fit",
    "mechanism_fit",
    "source_evidence_strength",
    "destination_evidence_strength",
    "implementation_feasibility",
    "expected_upside",
    "reversibility",
    "maintenance_fit",
    "strategic_fit",
    "differentiation",
    "dependency_risk",
    "complexity_tax",
    "opportunity_cost",
    "legal_ip_risk",
    "security_privacy_risk",
    "measurement_risk",
}
CONFIDENCE_FIELDS = {"source", "mechanism", "destination", "execution", "overall"}
INTERACTION_FIELDS = {"requires", "enables", "conflicts_with", "substitutes_for", "bundles_with"}
EXPERIMENT_FIELDS = {
    "hypothesis",
    "test_type",
    "primary_metric",
    "guardrail",
    "baseline",
    "success_rule",
    "timebox_or_sample",
    "kill_criteria",
    "changes_verdict",
}


def num01(value: Any) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return 0.0 <= number <= 1.0


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def nonempty_string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(nonempty_string(item) for item in value)


def string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def gate_is_clear(value: Any) -> bool:
    return str(value).lower() in {"clear", "not_required"}


def validate(payload: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["root must be a JSON object"]

    if str(payload.get("schema_version")) != SCHEMA_VERSION:
        errors.append(f"schema_version must be '{SCHEMA_VERSION}'")

    shape = payload.get("shape")
    if shape not in SHAPES:
        errors.append(f"shape must be one of {sorted(SHAPES)}")

    if payload.get("mode") not in MODES:
        errors.append(f"mode must be one of {sorted(MODES)}")

    source_targets = payload.get("source_targets")
    source_ids: set[str] = set()
    if not isinstance(source_targets, list) or not source_targets:
        errors.append("source_targets must be a non-empty array")
        source_targets = []
    for i, item in enumerate(source_targets):
        p = f"source_targets[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{p} must be an object")
            continue
        sid = item.get("id")
        if not nonempty_string(sid):
            errors.append(f"{p}.id is required")
        elif sid in source_ids:
            errors.append(f"duplicate source target id: {sid}")
        else:
            source_ids.add(sid)
        for key in ("name", "kind"):
            if not nonempty_string(item.get(key)):
                errors.append(f"{p}.{key} is required")

    destination = payload.get("destination")
    if shape in {"SOURCE_TO_TARGET", "MULTI_SOURCE_TO_TARGET"}:
        if not isinstance(destination, dict):
            errors.append(f"destination must be an object for shape {shape}")
        else:
            for key in ("name", "kind"):
                if not nonempty_string(destination.get(key)):
                    errors.append(f"destination.{key} is required")

    evidence = payload.get("evidence")
    if not isinstance(evidence, list):
        errors.append("evidence must be an array")
        evidence = []

    evidence_by_id: dict[str, dict[str, Any]] = {}
    for i, item in enumerate(evidence):
        p = f"evidence[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{p} must be an object")
            continue
        eid = item.get("evidence_id")
        if not nonempty_string(eid):
            errors.append(f"{p}.evidence_id is required")
        elif eid in evidence_by_id:
            errors.append(f"duplicate evidence_id: {eid}")
        else:
            evidence_by_id[eid] = item

        subject = item.get("subject")
        if subject not in {"source", "destination"}:
            errors.append(f"{p}.subject must be source or destination")

        target_id = item.get("target_id")
        if subject == "source" and target_id not in source_ids:
            errors.append(f"{p}.target_id must reference a source target id")
        if subject == "destination" and target_id != "DEST":
            errors.append(f"{p}.target_id must be DEST for destination evidence")

        for key in ("source", "locator", "source_type", "note"):
            if not nonempty_string(item.get(key)):
                errors.append(f"{p}.{key} is required")

        lane = item.get("claim_lane")
        if subject == "source" and lane not in SOURCE_LANES:
            errors.append(f"{p}.claim_lane invalid for source evidence")
        if subject == "destination" and lane not in DESTINATION_LANES:
            errors.append(f"{p}.claim_lane invalid for destination evidence")

        if item.get("claim_state") not in CLAIM_STATES:
            errors.append(f"{p}.claim_state invalid")
        if not num01(item.get("confidence")):
            errors.append(f"{p}.confidence must be in [0,1]")

    patterns = payload.get("patterns")
    if not isinstance(patterns, list) or not patterns:
        errors.append("patterns must be a non-empty array")
        patterns = []

    pattern_ids: set[str] = set()
    deferred_interaction_checks: list[tuple[str, str, list[str]]] = []

    for i, item in enumerate(patterns):
        p = f"patterns[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{p} must be an object")
            continue

        pid = item.get("id")
        if not nonempty_string(pid):
            errors.append(f"{p}.id is required")
            pid = f"<pattern-{i}>"
        elif pid in pattern_ids:
            errors.append(f"duplicate pattern id: {pid}")
        else:
            pattern_ids.add(pid)

        for key in ("name", "problem", "mechanism", "source_observation", "decision_reason"):
            if not nonempty_string(item.get(key)):
                errors.append(f"{p}.{key} is required")
        if item.get("category") not in CATEGORIES:
            errors.append(f"{p}.category invalid")

        source_refs = item.get("evidence_ids")
        target_refs = item.get("target_evidence_ids")
        if not nonempty_string_list(source_refs):
            errors.append(f"{p}.evidence_ids must be a non-empty array")
            source_refs = []
        if not isinstance(target_refs, list) or not all(nonempty_string(ref) for ref in target_refs):
            errors.append(f"{p}.target_evidence_ids must be an array of strings")
            target_refs = []

        for ref in source_refs:
            evidence_item = evidence_by_id.get(ref)
            if evidence_item is None:
                errors.append(f"{p}.evidence_ids references unknown evidence: {ref}")
            elif evidence_item.get("subject") != "source":
                errors.append(f"{p}.evidence_ids must reference source evidence: {ref}")
        for ref in target_refs:
            evidence_item = evidence_by_id.get(ref)
            if evidence_item is None:
                errors.append(f"{p}.target_evidence_ids references unknown evidence: {ref}")
            elif evidence_item.get("subject") != "destination":
                errors.append(f"{p}.target_evidence_ids must reference destination evidence: {ref}")

        transfer = item.get("transfer")
        if not isinstance(transfer, dict):
            errors.append(f"{p}.transfer must be an object")
            transfer = {}
        missing = sorted(REQUIRED_TRANSFER - set(transfer))
        if missing:
            errors.append(f"{p}.transfer missing: {', '.join(missing)}")
        for key in REQUIRED_TRANSFER & set(transfer):
            if not num01(transfer[key]):
                errors.append(f"{p}.transfer.{key} must be in [0,1]")

        gates = item.get("gates")
        if not isinstance(gates, dict):
            errors.append(f"{p}.gates must be an object")
            gates = {}
        for key in ("legal_ip", "security_privacy"):
            if str(gates.get(key, "")).lower() not in GATES:
                errors.append(f"{p}.gates.{key} invalid")

        implementation = item.get("implementation")
        if not isinstance(implementation, dict):
            errors.append(f"{p}.implementation must be an object")
            implementation = {}
        transfer_mode = implementation.get("transfer_mode")
        if transfer_mode not in TRANSFER_MODES:
            errors.append(f"{p}.implementation.transfer_mode invalid")
        for key in ("target_surfaces", "prerequisites", "steps"):
            if key in implementation and not string_list(implementation.get(key)):
                errors.append(f"{p}.implementation.{key} must be an array of strings")
        for key in ("effort_band", "uncertainty"):
            if key in implementation and not nonempty_string(implementation.get(key)):
                errors.append(f"{p}.implementation.{key} must be a string")
        if transfer_mode in {"REUSE_CODE", "REUSE_ASSET"} and not nonempty_string(implementation.get("provenance_note")):
            errors.append(f"{p}.implementation.provenance_note required for {transfer_mode}")

        interactions = item.get("interactions")
        if not isinstance(interactions, dict):
            errors.append(f"{p}.interactions must be an object")
            interactions = {}
        for key in INTERACTION_FIELDS:
            refs = interactions.get(key)
            if not string_list(refs):
                errors.append(f"{p}.interactions.{key} must be an array of strings")
            else:
                deferred_interaction_checks.append((p, key, refs))

        confidence = item.get("confidence")
        if not isinstance(confidence, dict):
            errors.append(f"{p}.confidence must be an object")
            confidence = {}
        missing_conf = sorted(CONFIDENCE_FIELDS - set(confidence))
        if missing_conf:
            errors.append(f"{p}.confidence missing: {', '.join(missing_conf)}")
        for key in CONFIDENCE_FIELDS & set(confidence):
            if not num01(confidence[key]):
                errors.append(f"{p}.confidence.{key} must be in [0,1]")

        verdict = item.get("verdict")
        if verdict not in VERDICTS:
            errors.append(f"{p}.verdict invalid")
            continue

        source_observed = any(
            evidence_by_id.get(ref, {}).get("claim_state") == "OBSERVED"
            and evidence_by_id.get(ref, {}).get("claim_lane") in {"source_behavior", "source_implementation"}
            for ref in source_refs
        )
        destination_problem = any(
            evidence_by_id.get(ref, {}).get("claim_lane") == "destination_problem"
            and evidence_by_id.get(ref, {}).get("claim_state") == "OBSERVED"
            for ref in target_refs
        )
        gates_clear = gate_is_clear(gates.get("legal_ip")) and gate_is_clear(gates.get("security_privacy"))

        if verdict in {"ADOPT", "EXPERIMENT"}:
            if not isinstance(destination, dict):
                errors.append(f"{p}: {verdict} requires destination context")
            if not destination_problem:
                errors.append(f"{p}: {verdict} requires OBSERVED destination_problem evidence")
            if not source_observed:
                errors.append(f"{p}: {verdict} requires OBSERVED source behavior or implementation evidence")
            if not gates_clear:
                errors.append(f"{p}: {verdict} requires clear/not_required mandatory gates")

        if verdict == "ADOPT":
            threshold_checks = {
                "source_evidence_strength": 0.65,
                "destination_evidence_strength": 0.65,
                "implementation_feasibility": 0.60,
            }
            for key, threshold in threshold_checks.items():
                value = transfer.get(key)
                if not num01(value) or float(value) < threshold:
                    errors.append(f"{p}: ADOPT requires transfer.{key} >= {threshold:.2f}")
            if not nonempty_string_list(implementation.get("steps")):
                errors.append(f"{p}: ADOPT requires non-empty implementation.steps")
            for key in ("success_metric", "rollback", "kill_criteria"):
                if not nonempty_string(implementation.get(key)):
                    errors.append(f"{p}: ADOPT requires implementation.{key}")

        if verdict == "EXPERIMENT":
            experiment = item.get("experiment")
            if not isinstance(experiment, dict):
                errors.append(f"{p}: EXPERIMENT requires experiment object")
            else:
                for key in EXPERIMENT_FIELDS:
                    if not nonempty_string(experiment.get(key)):
                        errors.append(f"{p}.experiment.{key} is required for EXPERIMENT")

        if verdict == "REVIEW_REQUIRED" and gates_clear:
            errors.append(f"{p}: REVIEW_REQUIRED requires a non-clear mandatory gate")

        if verdict == "CANDIDATE" and shape != "SOURCE_ONLY" and target_refs:
            # Allowed as a conservative verdict; no error. The rule exists to avoid forcing promotion.
            pass

    for p, key, refs in deferred_interaction_checks:
        for ref in refs:
            if ref not in pattern_ids:
                errors.append(f"{p}.interactions.{key} references unknown pattern: {ref}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", help="ledger JSON file; stdin if omitted")
    args = parser.parse_args()

    try:
        text = open(args.input, "r", encoding="utf-8").read() if args.input else sys.stdin.read()
        payload = json.loads(text)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INVALID: {exc}")
        return 2

    errors = validate(payload)
    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        return 1

    print("VALID")
    print(f"evidence={len(payload.get('evidence', []))} patterns={len(payload.get('patterns', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
