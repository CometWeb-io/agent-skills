"""Roadmap payload validation."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .constants import (
    CAPABILITY_STATES,
    EFFORT_FACTORS,
    GATE_STATUSES,
    GATE_TYPES,
    ITEM_KINDS,
    KERNEL_VERSION,
    SCHEMA_VERSION,
    TARGET_APPLICABILITY,
    TARGET_PROFILES,
    VALID_LANES,
)
from .delta import (
    _snapshot_consistency_errors,
    assessment_contract_sha256,
    snapshot_report,
)
from .evidence import evidence_report
from .graph import graph_report
from .inventory import coverage_report, file_coverage_report
from .util import (
    by_id,
    normalized,
    normalized_lower,
    normalized_upper,
    require_probability_like,
)


def validate_target_contract(target: Any) -> Tuple[List[str], List[str], set[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    ids: set[str] = set()
    if not isinstance(target, dict):
        return ["target_contract must be an object"], warnings, ids
    profile = normalized_upper(target.get("target_profile", ""))
    if profile not in TARGET_PROFILES:
        errors.append(f"target_contract.target_profile must be one of: {', '.join(sorted(TARGET_PROFILES))}")
    requirements = target.get("requirements", [])
    if not isinstance(requirements, list):
        errors.append("target_contract.requirements must be a list")
        return errors, warnings, ids
    for index, row in enumerate(requirements):
        if not isinstance(row, dict):
            errors.append(f"target requirement[{index}] must be an object")
            continue
        req_id = normalized(row.get("id", ""))
        if not req_id:
            errors.append(f"target requirement[{index}] missing id")
            continue
        if req_id in ids:
            errors.append(f"duplicate target requirement id: {req_id}")
        ids.add(req_id)
        applicability = normalized_upper(row.get("applicability", "APPLIES"))
        if applicability not in TARGET_APPLICABILITY:
            errors.append(f"{req_id}: invalid applicability {applicability}")
        if applicability == "NOT_APPLICABLE" and not normalized(row.get("reason", "")):
            warnings.append(f"{req_id}: NOT_APPLICABLE should include reason")
        if not normalized(row.get("requirement", "")):
            errors.append(f"{req_id}: missing requirement text")
    return errors, warnings, ids


def validate_acceptance(item_id: str, criteria: Any) -> List[str]:
    errors: List[str] = []
    if not isinstance(criteria, list) or not criteria:
        return [f"{item_id}: acceptance_criteria must be a non-empty list"]
    for index, criterion in enumerate(criteria):
        if not isinstance(criterion, dict):
            errors.append(f"{item_id}: acceptance_criteria[{index}] must be an object with criterion/verify_with/proof")
            continue
        for field in ("criterion", "verify_with", "proof"):
            if not normalized(criterion.get(field, "")):
                errors.append(f"{item_id}: acceptance_criteria[{index}] missing {field}")
    return errors


def validate_roadmap(payload: Dict[str, Any], *, expected_scope_sha256: str | None = None) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("roadmap payload must be an object")
    errors: List[str] = []
    warnings: List[str] = []

    schema_version = normalized(payload.get("schema_version", ""))
    if schema_version != SCHEMA_VERSION:
        warnings.append(f"schema_version is {schema_version or '<missing>'}; expected {SCHEMA_VERSION}")

    assessment = payload.get("assessment", {})
    if not isinstance(assessment, dict):
        errors.append("assessment must be an object")
    elif not normalized(assessment.get("mode", "")):
        warnings.append("assessment.mode missing")

    if isinstance(assessment, dict) and "mode" in assessment and (not isinstance(assessment["mode"], str) or normalized_upper(assessment["mode"]) not in {"STANDARD", "EXHAUSTIVE", "DELTA", "FOCUSED"}):
        errors.append("assessment.mode is unknown")
    contract_hash = assessment_contract_sha256(payload) if isinstance(assessment, dict) else None
    if expected_scope_sha256 is not None and expected_scope_sha256 != contract_hash:
        errors.append("assessment contract differs from independently supplied scope fingerprint")
    errors.extend(_snapshot_consistency_errors(payload))
    file_coverage = file_coverage_report(payload)
    errors.extend(file_coverage["errors"])
    if file_coverage["status"] == "ACCOUNTED_WITH_EXCLUSIONS":
        warnings.append("file accounting includes explicit exclusions; not every file was inspected")

    target_errors, target_warnings, target_ids = validate_target_contract(payload.get("target_contract", {}))
    errors.extend(target_errors)
    warnings.extend(target_warnings)
    target = payload.get("target_contract")
    target_requirements = by_id(target.get("requirements", []) if isinstance(target, dict) else [], "id")

    coverage = coverage_report(payload.get("coverage", []))
    errors.extend(coverage.get("errors", []))
    if isinstance(assessment, dict) and normalized_upper(assessment.get("mode", "")) == "EXHAUSTIVE" and file_coverage["errors"]:
        coverage["domain_scope_claim"] = coverage["scope_claim"]
        coverage["scope_claim"] = "EXHAUSTIVE_NOT_PROVEN"
    if coverage["scope_claim"] == "WHOLE_PROJECT_SCOPE_NOT_DEFENSIBLE":
        warnings.append("coverage is too weak for an unqualified whole-project roadmap claim")
    elif coverage["scope_claim"] == "WHOLE_PROJECT_SCOPE_QUALIFIED":
        warnings.append("whole-project roadmap is qualified by incomplete coverage")

    claims = payload.get("claims", [])
    if not isinstance(claims, list):
        errors.append("claims must be a list")
        claims = []
    claim_ids: set[str] = set()
    claim_reports: Dict[str, Dict[str, Any]] = {}
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            errors.append(f"claims[{index}] must be an object")
            continue
        claim_id = normalized(claim.get("claim_id", ""))
        if not claim_id:
            errors.append(f"claims[{index}] missing claim_id")
            continue
        if claim_id in claim_ids:
            errors.append(f"duplicate claim id: {claim_id}")
            continue
        claim_ids.add(claim_id)
        if not normalized(claim.get("text", "")):
            warnings.append(f"{claim_id}: missing claim text")
        try:
            report = evidence_report(claim)
            claim_reports[claim_id] = report
            for warning in report["warnings"]:
                warnings.append(f"{claim_id}: {warning}")
        except ValueError as exc:
            errors.append(f"{claim_id}: {exc}")

    capabilities = payload.get("capabilities", [])
    if not isinstance(capabilities, list):
        errors.append("capabilities must be a list")
        capabilities = []
    capability_ids: set[str] = set()
    for index, capability in enumerate(capabilities):
        if not isinstance(capability, dict):
            errors.append(f"capabilities[{index}] must be an object")
            continue
        cap_id = normalized(capability.get("capability_id", ""))
        if not cap_id:
            errors.append(f"capabilities[{index}] missing capability_id")
            continue
        if cap_id in capability_ids:
            errors.append(f"duplicate capability id: {cap_id}")
        capability_ids.add(cap_id)
        state = normalized_upper(capability.get("state", ""))
        if state not in CAPABILITY_STATES:
            errors.append(f"{cap_id}: invalid capability state {state}")
        cap_claim_refs = capability.get("claim_refs", []) or []
        if not isinstance(cap_claim_refs, list):
            errors.append(f"{cap_id}: claim_refs must be a list")
            cap_claim_refs = []
        else:
            missing_refs = sorted({normalized(ref) for ref in cap_claim_refs if normalized(ref) not in claim_ids})
            if missing_refs:
                errors.append(f"{cap_id}: unknown claim refs {missing_refs}")
        cap_target_refs = capability.get("target_requirement_refs", []) or []
        if not isinstance(cap_target_refs, list):
            errors.append(f"{cap_id}: target_requirement_refs must be a list")
        else:
            missing_targets = sorted({normalized(ref) for ref in cap_target_refs if normalized(ref) not in target_ids})
            if missing_targets:
                errors.append(f"{cap_id}: unknown target requirement refs {missing_targets}")
        if state == "NOT_APPLICABLE" and not normalized(capability.get("not_applicable_reason", "")):
            errors.append(f"{cap_id}: NOT_APPLICABLE requires not_applicable_reason")
        if state == "MISSING":
            linked = [claim_reports.get(normalized(ref)) for ref in cap_claim_refs]
            if not any(report and report.get("claim_type") == "absence" and report.get("verification_requirements_met") for report in linked):
                errors.append(f"{cap_id}: MISSING requires a linked verified absence claim")

    items = payload.get("items", [])
    if not isinstance(items, list):
        errors.append("items must be a list")
        items = []
    required_item_fields = ["id", "title", "kind", "outcome", "acceptance_criteria", "effort", "depends_on"]
    item_ids: set[str] = set()

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"items[{index}] must be an object")
            continue
        item_id = normalized(item.get("id", f"index-{index}"))
        if item_id in item_ids:
            errors.append(f"duplicate roadmap item id: {item_id}")
        item_ids.add(item_id)
        for field in required_item_fields:
            if field not in item:
                errors.append(f"{item_id}: missing {field}")
        kind = normalized_upper(item.get("kind", ""))
        if kind not in ITEM_KINDS:
            errors.append(f"{item_id}: invalid kind {kind}")
        effort = normalized_upper(item.get("effort", ""))
        if effort not in EFFORT_FACTORS:
            errors.append(f"{item_id}: invalid effort {effort}")
        elif effort == "XL" and not normalized(item.get("decomposition_note", "")):
            errors.append(f"{item_id}: XL item requires decomposition_note")
        errors.extend(validate_acceptance(item_id, item.get("acceptance_criteria")))

        claim_refs = item.get("problem_claim_refs", []) or []
        target_refs = item.get("target_requirement_refs", []) or []
        capability_refs = item.get("capability_refs", []) or []
        if not isinstance(claim_refs, list):
            errors.append(f"{item_id}: problem_claim_refs must be a list")
            claim_refs = []
        if not isinstance(target_refs, list):
            errors.append(f"{item_id}: target_requirement_refs must be a list")
            target_refs = []
        if not isinstance(capability_refs, list):
            errors.append(f"{item_id}: capability_refs must be a list")
            capability_refs = []
        if not claim_refs and not target_refs:
            errors.append(f"{item_id}: requires problem_claim_refs or target_requirement_refs")

        unknown_claims = sorted({normalized(ref) for ref in claim_refs if normalized(ref) not in claim_ids})
        unknown_targets = sorted({normalized(ref) for ref in target_refs if normalized(ref) not in target_ids})
        unknown_caps = sorted({normalized(ref) for ref in capability_refs if normalized(ref) not in capability_ids})
        if unknown_claims:
            errors.append(f"{item_id}: unknown claim refs {unknown_claims}")
        if unknown_targets:
            errors.append(f"{item_id}: unknown target requirement refs {unknown_targets}")
        if unknown_caps:
            errors.append(f"{item_id}: unknown capability refs {unknown_caps}")

        lane = normalized_upper(item.get("lane", "")) if item.get("lane") is not None else None
        if lane and lane not in VALID_LANES:
            errors.append(f"{item_id}: invalid lane {lane}")

        confidence = item.get("evidence_confidence")
        if confidence is None:
            warnings.append(f"{item_id}: missing evidence_confidence")
            confidence_value = 0.0
        else:
            try:
                confidence_value = require_probability_like(confidence, f"{item_id}.evidence_confidence")
            except ValueError as exc:
                errors.append(str(exc))
                confidence_value = 0.0

        gate_raw = item.get("mandatory_gate")
        gate = normalized_lower(gate_raw) if gate_raw not in (None, "", "none") else None
        gate_status = normalized_upper(item.get("gate_status", "UNVERIFIED" if gate else "NOT_REQUIRED"))
        if gate is not None and gate not in GATE_TYPES:
            errors.append(f"{item_id}: invalid mandatory_gate {gate}")
        if gate_status not in GATE_STATUSES:
            errors.append(f"{item_id}: invalid gate_status {gate_status}")
        if gate and gate_status in {"CLEAR", "CLEAR_WITH_CONTROLS", "BLOCK"} and not normalized(item.get("gate_basis", "")):
            errors.append(f"{item_id}: resolved mandatory gate requires gate_basis")
        if gate and gate_status == "UNVERIFIED" and lane and lane != "VERIFY_NOW":
            errors.append(f"{item_id}: unverified mandatory gate must use VERIFY_NOW lane")
        if lane == "BLOCKER":
            if gate:
                if gate_status != "BLOCK":
                    errors.append(f"{item_id}: BLOCKER with mandatory gate requires gate_status BLOCK")
            else:
                mandatory_targets = [
                    target_requirements.get(normalized(ref)) for ref in target_refs
                    if normalized(ref) in target_requirements
                ]
                has_mandatory_target = any(
                    target and target.get("mandatory")
                    and normalized_upper(target.get("applicability", "APPLIES")) == "APPLIES"
                    for target in mandatory_targets
                )
                if not (bool(item.get("target_blocker")) and confidence_value >= 0.70 and has_mandatory_target):
                    errors.append(f"{item_id}: non-gate BLOCKER requires target_blocker=true, evidence_confidence >= 0.70, and a linked mandatory target requirement")

        linked_reports = [claim_reports.get(normalized(ref)) for ref in claim_refs if normalized(ref) in claim_reports]
        if lane == "BLOCKER" and not gate:
            if any(report and report.get("status") in {"CONTESTED", "STALE_EVIDENCE", "UNSUPPORTED", "HYPOTHESIS", "INSUFFICIENT_VERIFICATION"} for report in linked_reports):
                errors.append(f"{item_id}: non-gate BLOCKER depends on unresolved/insufficient claim evidence")
        if lane in {"NOW", "BLOCKER"}:
            stale_current = [report.get("claim_id") for report in linked_reports if report and report.get("current_sensitive") and report.get("status") == "STALE_EVIDENCE"]
            if stale_current:
                errors.append(f"{item_id}: current-priority item depends on stale current-sensitive claims {stale_current}")

        linked_confidences = [report["heuristic_confidence"] for report in linked_reports if report]
        if linked_confidences and confidence_value > max(linked_confidences) + 0.15:
            warnings.append(f"{item_id}: evidence_confidence materially exceeds linked claim confidence")
        if kind == "VALIDATE" and lane and lane not in {"VALIDATE", "NEXT", "LATER"}:
            warnings.append(f"{item_id}: VALIDATE item in {lane} lane; ensure urgency is intentional")
        if kind == "VERIFY" and lane == "PARK" and (gate or item.get("target_blocker")):
            errors.append(f"{item_id}: binding verification cannot be PARK")
        if not normalized(item.get("why_now", "")):
            warnings.append(f"{item_id}: missing why_now")
        if not normalized(item.get("non_goal", "")):
            warnings.append(f"{item_id}: missing non_goal; scope creep risk")
        if kind in {"BUILD", "FIX", "HARDEN", "INSTRUMENT", "MIGRATE"} and not normalized(item.get("success_signal", "")):
            warnings.append(f"{item_id}: missing success_signal")

    try:
        graph = graph_report(items)
    except ValueError:
        errors.append("invalid dependency graph records")
        graph = {"valid": False, "duplicate_ids": [], "missing_dependencies": {}, "cycle_nodes": [],
                 "topological_order": [], "waves": [], "dependency_leverage": [],
                 "critical_chain_by_hard_dependency_count": []}
    if graph["duplicate_ids"]:
        errors.append(f"duplicate item ids: {graph['duplicate_ids']}")
    if graph["missing_dependencies"]:
        errors.append(f"missing dependencies: {graph['missing_dependencies']}")
    if graph["cycle_nodes"]:
        errors.append(f"dependency cycle: {graph['cycle_nodes']}")

    linked_target_ids: set[str] = set()
    for capability in capabilities:
        if isinstance(capability, dict):
            linked_target_ids.update(normalized(ref) for ref in (capability.get("target_requirement_refs") or []))
    for item in items:
        if isinstance(item, dict):
            linked_target_ids.update(normalized(ref) for ref in (item.get("target_requirement_refs") or []))
    for target_id, requirement in target_requirements.items():
        if requirement.get("mandatory") and normalized_upper(requirement.get("applicability", "APPLIES")) == "APPLIES" and target_id not in linked_target_ids:
            warnings.append(f"mandatory target requirement {target_id} is not linked to any capability or roadmap item")

    snapshot = snapshot_report(payload)
    return {
        "valid": not errors,
        "kernel_version": KERNEL_VERSION,
        "assessment_contract_sha256": contract_hash,
        "file_coverage": file_coverage,
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "coverage": coverage,
        "claim_reports": claim_reports,
        "graph": graph,
        "snapshot": snapshot,
    }

