#!/usr/bin/env python3
"""Validate structural and epistemic invariants for Science Roaster v6 reports."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA = "cometweb.science-roaster/v6"
MODES = {"QUICK", "FULL", "REVIEWER_2", "REVISION"}
EVIDENCE_MODES = {"SOURCE_BOUND", "VERIFY_EXTERNAL"}
PROFILES = {"EXPERIMENTAL", "OBSERVATIONAL", "PREDICTIVE", "VALIDATION", "METHODS", "COMPUTATIONAL", "REVIEW", "PROTOCOL", "MIXED"}
OUTCOMES = {"MATERIAL_FINDINGS", "NO_MATERIAL_FINDINGS", "INSUFFICIENT_EVIDENCE"}
COVERAGE = {"PARTIAL", "SUBSTANTIAL", "COMPLETE"}
SCOPE = {"FULL_ARTIFACT", "EXCERPT", "SAMPLED", "ARTIFACT_SET", "MIXED"}
GATE_STATUS = {"PASS", "WARN", "BLOCKED"}
GATE_KEYS = {"scope", "contract", "source_integrity", "evidence", "challenge", "assurance", "severity", "repair", "boundary"}
SEVERITIES = {"FATAL", "MAJOR", "MINOR"}
SEVERITY_RANK = {"MINOR": 1, "MAJOR": 2, "FATAL": 3}
STATES = {"OBSERVED", "NOT_REPORTED", "INFERRED", "EXTERNAL_VERIFIED"}
EVIDENCE_STRENGTH = {"STRONG", "MODERATE", "WEAK"}
SCOPE_SENSITIVITY = {"LOW", "MEDIUM", "HIGH"}
ANCHORS = {"quote", "metric", "table", "figure", "section", "citation", "missing_report", "external_source"}
CATEGORIES = {"research_question", "novelty", "design", "controls", "sampling", "missingness", "measurement", "construct_validity", "calibration", "statistics", "multiplicity", "power_precision", "causal_inference", "model_validation", "leakage", "holdout", "external_validity", "reproducibility", "figures_tables", "reporting", "ethics_governance", "conflict_of_interest"}
VALIDITY_DOMAINS = {"CONSTRUCT", "INTERNAL", "STATISTICAL", "EXTERNAL", "REPRODUCIBILITY", "REPORTING"}
INFERENTIAL_TYPES = {"DESCRIPTIVE", "ASSOCIATIONAL", "PREDICTIVE", "CAUSAL", "MECHANISTIC", "TRANSPORT"}
EVIDENCE_ROLES = {"PRIMARY", "SECONDARY", "EXPLORATORY", "POST_HOC", "BACKGROUND"}
SUPPORT_STATUS = {"SUPPORTED", "OVERSTATED", "UNRESOLVED", "CONTRADICTED"}
ALT_STATUS = {"ADDRESSED", "PARTIAL", "UNADDRESSED", "UNKNOWN", "NOT_APPLICABLE"}
ROBUSTNESS_STATUS = {"ROBUST", "SENSITIVE", "NOT_RUN", "NOT_APPLICABLE", "UNKNOWN"}
REFERENCE_STATUS = {"VALIDATED", "CALIBRATED", "OPERATIONAL_CALIBRATED", "OPERATIONAL_UNCALIBRATED", "UNKNOWN", "NOT_APPLICABLE"}
ALIGNMENT = {"ALIGNED", "PARTIAL", "UNRESOLVED", "NOT_APPLICABLE"}
VALIDITY_STATUS = {"SUPPORTED", "PARTIAL", "UNRESOLVED", "THREATENED", "NOT_APPLICABLE"}
INTEGRITY_AREAS = {"DEPENDENCE", "MISSINGNESS", "MULTIPLICITY", "EXCLUSIONS_STOPPING", "HOLDOUT", "LEAKAGE", "PREREGISTRATION", "POWER_PRECISION", "OTHER"}
INTEGRITY_STATUS = {"ADEQUATE", "PARTIAL", "UNRESOLVED", "PROBLEM", "NOT_APPLICABLE"}
REPAIR_LEVEL = {"REPORTING_ONLY", "REANALYSIS", "NEW_DATA", "REDESIGN"}
VERIFY = {"MANUAL_INSPECTION", "REANALYSIS", "CALIBRATION", "REPLICATION", "SENSITIVITY_ANALYSIS", "SOURCE_CHECK", "CODE_RERUN", "DATA_AUDIT", "PROTOCOL_CHECK"}
CONF = {"high", "medium", "low"}
FALSIFIER = {"SURVIVES", "UNRESOLVED", "DOWNGRADED", "WITHDRAWN"}
RESOLUTION = {"RESOLVED", "PARTIAL", "OPEN", "REGRESSED", "NOT_ASSESSABLE"}
RESOLUTION_VERIFICATION = {"PASSED", "PARTIAL", "FAILED", "NOT_RUN"}
RESOLUTION_CHANGE_BASIS = {"ARTIFACT_CHANGED", "SCOPE_CHANGED", "JUDGMENT_CORRECTED", "MIXED", "UNKNOWN"}
CLAIM_SURVIVAL = {"SURVIVES_AS_STATED", "SURVIVES_NARROWED", "UNRESOLVED", "CONTRADICTED"}
MATERIAL_CENTRALITY = {"CENTRAL", "SUPPORTING", "LOCAL"}
MATERIAL_CONSEQUENCE = {"HIGH", "MEDIUM", "LOW"}
MATERIAL_REVERSIBILITY = {"EASY", "MODERATE", "HARD", "UNKNOWN"}
SOURCE_KIND = {"MANUSCRIPT", "SUPPLEMENT", "PROTOCOL", "PREREGISTRATION", "DATA", "CODE", "REVIEWER_RESPONSE", "LITERATURE", "OTHER"}
SOURCE_ROLE = {"PRIMARY", "SUPPORTING", "CONTEXT"}
VERSION_STATE = {"PINNED", "MOVING", "UNKNOWN"}

MULTIPLICITY_STATUS = {"CONTROLLED", "DECLARED", "UNCONTROLLED", "NOT_APPLICABLE", "NOT_REPORTED"}
IDENTIFICATION_STATUS = {"IDENTIFIED", "ASSUMPTION_DEPENDENT", "DESCRIPTIVE_ONLY", "NOT_APPLICABLE", "NOT_REPORTED"}
DATA_SPLIT_STATUS = {"LOCKED", "REUSED", "NOT_APPLICABLE", "NOT_REPORTED"}

TRUST_CLASS = {"USER_SUPPLIED", "SYSTEM_OF_RECORD", "EXTERNAL_REFERENCE", "TOOL_RESULT", "GENERATED", "UNKNOWN"}
ASSURANCE_MODES = {"SINGLE_REVIEW", "SECOND_PASS", "BLIND_DUAL_REVIEW"}
INDEPENDENCE = {"NONE", "SAME_CONTEXT", "SEPARATE_CONTEXT"}
SECOND_PASS_STATUS = {"NOT_RUN", "COMPLETED", "UNAVAILABLE"}
EVIDENCE_KINDS = {"OBSERVATION", "COUNTEREVIDENCE", "CONTEXT", "ABSENCE_PROOF", "VERIFICATION"}
CONFLICT_DISPOSITION = {"RESOLVED", "UNRESOLVED", "OUT_OF_SCOPE"}
CONF_DIRECTNESS = {"HIGH", "MEDIUM", "LOW"}
CONF_SCOPE_SUPPORT = {"HIGH", "MEDIUM", "LOW"}
COUNTEREVIDENCE_STATUS = {"ADDRESSED", "PARTIAL", "UNKNOWN"}
RESIDUAL_RISK = {"LOW", "MEDIUM", "HIGH", "UNKNOWN"}
PERSONAL_ATTACK = re.compile(r"\b(?:author|researcher|scientist|you|your coauthors?|your team)\b.{0,40}\b(?:stupid|idiot|moron|lazy|incompetent|clueless|fraud)\b", re.I)


def _text(v: Any) -> bool:
    return isinstance(v, str) and bool(v.strip())


def _list(v: Any) -> bool:
    return isinstance(v, list)


def _slist(v: Any, nonempty: bool = False) -> bool:
    return isinstance(v, list) and (bool(v) or not nonempty) and all(_text(x) for x in v)


def _anchor(obj: Any, prefix: str, errors: list[str], source_ids: set[str]) -> str | None:
    if not isinstance(obj, dict):
        errors.append(f"{prefix} must be an object")
        return None
    at = obj.get("type")
    if at not in ANCHORS:
        errors.append(f"{prefix}.type is invalid")
    if not _text(obj.get("value")):
        errors.append(f"{prefix}.value is required")
    source_id = obj.get("source_id")
    if source_id not in source_ids:
        errors.append(f"{prefix}.source_id must reference source_manifest")
    return at


def _verification(obj: Any, prefix: str, errors: list[str]) -> None:
    if not isinstance(obj, dict):
        errors.append(f"{prefix} must be an object")
        return
    if obj.get("type") not in VERIFY:
        errors.append(f"{prefix}.type is invalid")
    for key in ("method", "success_condition", "failure_signal"):
        if not _text(obj.get(key)):
            errors.append(f"{prefix}.{key} is required")


def _materiality(obj: Any, prefix: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(obj, dict):
        errors.append(f"{prefix} must be an object")
        return {}
    if obj.get("centrality") not in MATERIAL_CENTRALITY:
        errors.append(f"{prefix}.centrality is invalid")
    if obj.get("consequence") not in MATERIAL_CONSEQUENCE:
        errors.append(f"{prefix}.consequence is invalid")
    if obj.get("reversibility") not in MATERIAL_REVERSIBILITY:
        errors.append(f"{prefix}.reversibility is invalid")
    return obj


def _source_manifest(value: Any, evidence_mode: Any, errors: list[str]) -> set[str]:
    if not isinstance(value, list) or not value:
        errors.append("source_manifest must be a non-empty list")
        return set()
    ids: set[str] = set()
    primary_count = 0
    for i, row in enumerate(value):
        p = f"source_manifest[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{p} must be an object")
            continue
        sid = row.get("id")
        if not _text(sid):
            errors.append(f"{p}.id is required")
        elif sid in ids:
            errors.append(f"{p}.id must be unique")
        else:
            ids.add(sid)
        if row.get("kind") not in SOURCE_KIND:
            errors.append(f"{p}.kind is invalid")
        if not _text(row.get("locator")):
            errors.append(f"{p}.locator is required")
        if row.get("role") not in SOURCE_ROLE:
            errors.append(f"{p}.role is invalid")
        elif row.get("role") == "PRIMARY":
            primary_count += 1
        if row.get("version_state") not in VERSION_STATE:
            errors.append(f"{p}.version_state is invalid")
        if row.get("kind") == "LITERATURE" and evidence_mode == "SOURCE_BOUND" and row.get("role") == "PRIMARY":
            errors.append(f"{p}: external literature cannot silently become PRIMARY evidence in SOURCE_BOUND mode")
        if row.get("instruction_boundary") != "TREAT_AS_DATA":
            errors.append(f"{p}.instruction_boundary must equal TREAT_AS_DATA")
        if row.get("trust_class") not in TRUST_CLASS:
            errors.append(f"{p}.trust_class is invalid")
        sha = row.get("sha256")
        if sha is not None and (not isinstance(sha, str) or re.fullmatch(r"[0-9a-fA-F]{64}", sha) is None):
            errors.append(f"{p}.sha256 must be a 64-character hex string when present")
    if primary_count == 0:
        errors.append("source_manifest requires at least one PRIMARY source")
    return ids


def _quality_gates(value: Any, outcome: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("quality_gates must be an object")
        return
    missing = GATE_KEYS - set(value)
    extra = set(value) - GATE_KEYS
    if missing:
        errors.append(f"quality_gates missing keys: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"quality_gates has unknown keys: {', '.join(sorted(extra))}")
    for key in GATE_KEYS:
        if value.get(key) not in GATE_STATUS:
            errors.append(f"quality_gates.{key} is invalid")
    blocked = any(value.get(k) == "BLOCKED" for k in GATE_KEYS)
    if blocked and outcome != "INSUFFICIENT_EVIDENCE":
        errors.append("BLOCKED quality gate requires review_outcome=INSUFFICIENT_EVIDENCE")
    if outcome == "INSUFFICIENT_EVIDENCE" and not blocked:
        errors.append("INSUFFICIENT_EVIDENCE requires at least one BLOCKED quality gate")


def _falsifier(obj: Any, prefix: str, errors: list[str]) -> str | None:
    if not isinstance(obj, dict):
        errors.append(f"{prefix} must be an object")
        return None
    if not _text(obj.get("challenge")):
        errors.append(f"{prefix}.challenge is required")
    if not _slist(obj.get("searched_for"), True):
        errors.append(f"{prefix}.searched_for must be a non-empty string list")
    if not _slist(obj.get("counterevidence")):
        errors.append(f"{prefix}.counterevidence must be a string list")
    if not _slist(obj.get("alternative_explanations"), True):
        errors.append(f"{prefix}.alternative_explanations must be a non-empty string list")
    result = obj.get("result")
    if result not in FALSIFIER:
        errors.append(f"{prefix}.result is invalid")
    if not _text(obj.get("notes")):
        errors.append(f"{prefix}.notes is required")
    return result



def _review_plan(value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("review_plan must be an object")
        return
    if not _text(value.get("objective")):
        errors.append("review_plan.objective is required")
    for key in ("must_inspect", "attack_surfaces", "stop_conditions"):
        if not _slist(value.get(key), True):
            errors.append(f"review_plan.{key} must be a non-empty string list")
    if not _text(value.get("sampling_strategy")):
        errors.append("review_plan.sampling_strategy is required")
    if not _slist(value.get("escalation_conditions")):
        errors.append("review_plan.escalation_conditions must be a string list")


def _assurance(value: Any, errors: list[str], source_ids: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append("assurance must be an object")
        return {}
    mode = value.get("mode")
    independence = value.get("independence")
    status = value.get("second_pass_status")
    if mode not in ASSURANCE_MODES:
        errors.append("assurance.mode is invalid")
    if independence not in INDEPENDENCE:
        errors.append("assurance.independence is invalid")
    if status not in SECOND_PASS_STATUS:
        errors.append("assurance.second_pass_status is invalid")
    if not _slist(value.get("disagreement_summary")):
        errors.append("assurance.disagreement_summary must be a string list")
    if not _slist(value.get("limitations")):
        errors.append("assurance.limitations must be a string list")

    passes = value.get("pass_records")
    if not isinstance(passes, list) or not passes:
        errors.append("assurance.pass_records must be a non-empty list")
        passes = []
    pass_ids: set[str] = set()
    completed_primary = 0
    completed_secondary = 0
    unavailable_secondary = 0
    reviewer_contexts: list[str] = []
    blind_completed = 0
    for i, row in enumerate(passes):
        p = f"assurance.pass_records[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{p} must be an object")
            continue
        pid = row.get("pass_id")
        if not _text(pid):
            errors.append(f"{p}.pass_id is required")
        elif pid in pass_ids:
            errors.append(f"{p}.pass_id must be unique")
        else:
            pass_ids.add(pid)
        role = row.get("role")
        if role not in {"PRIMARY", "SECONDARY", "ARBITER"}:
            errors.append(f"{p}.role is invalid")
        pstatus = row.get("status")
        if pstatus not in {"COMPLETED", "UNAVAILABLE", "FAILED"}:
            errors.append(f"{p}.status is invalid")
        if not _text(row.get("context_ref")):
            errors.append(f"{p}.context_ref is required")
        if not isinstance(row.get("blind_to_prior_findings"), bool):
            errors.append(f"{p}.blind_to_prior_findings must be boolean")
        refs = row.get("source_refs")
        if not isinstance(refs, list) or not refs or not all(_text(x) for x in refs):
            errors.append(f"{p}.source_refs must be a non-empty string list")
            refs = []
        for ref in refs:
            if ref not in source_ids:
                errors.append(f"{p}.source_refs contains unknown source id {ref!r}")
        if pstatus == "COMPLETED" and role in {"PRIMARY", "SECONDARY"}:
            reviewer_contexts.append(str(row.get("context_ref", "")))
            blind_completed += int(row.get("blind_to_prior_findings") is True)
        if pstatus == "COMPLETED" and role == "PRIMARY":
            completed_primary += 1
        if pstatus == "COMPLETED" and role == "SECONDARY":
            completed_secondary += 1
        if pstatus == "UNAVAILABLE" and role == "SECONDARY":
            unavailable_secondary += 1

    if mode == "SINGLE_REVIEW":
        if independence != "NONE" or status != "NOT_RUN":
            errors.append("SINGLE_REVIEW requires independence=NONE and second_pass_status=NOT_RUN")
        if completed_primary != 1 or completed_secondary != 0:
            errors.append("SINGLE_REVIEW requires exactly one completed PRIMARY pass and no completed SECONDARY pass")
    elif mode == "SECOND_PASS":
        if status not in {"COMPLETED", "UNAVAILABLE"}:
            errors.append("SECOND_PASS requires COMPLETED or UNAVAILABLE second_pass_status")
        if completed_primary < 1:
            errors.append("SECOND_PASS requires a completed PRIMARY pass")
        if status == "COMPLETED":
            if independence not in {"SAME_CONTEXT", "SEPARATE_CONTEXT"}:
                errors.append("completed SECOND_PASS requires SAME_CONTEXT or SEPARATE_CONTEXT independence")
            if completed_secondary < 1:
                errors.append("completed SECOND_PASS requires a completed SECONDARY pass record")
            if independence == "SEPARATE_CONTEXT" and len(set(reviewer_contexts)) < 2:
                errors.append("SEPARATE_CONTEXT SECOND_PASS requires distinct reviewer context_ref values")
        if status == "UNAVAILABLE":
            if independence != "NONE":
                errors.append("unavailable SECOND_PASS requires independence=NONE")
            if unavailable_secondary < 1:
                errors.append("unavailable SECOND_PASS requires an UNAVAILABLE SECONDARY pass record")
            if not value.get("limitations"):
                errors.append("unavailable SECOND_PASS requires an assurance limitation")
    elif mode == "BLIND_DUAL_REVIEW":
        if independence != "SEPARATE_CONTEXT" or status != "COMPLETED":
            errors.append("BLIND_DUAL_REVIEW requires SEPARATE_CONTEXT and COMPLETED second pass")
        if completed_primary < 1 or completed_secondary < 1:
            errors.append("BLIND_DUAL_REVIEW requires completed PRIMARY and SECONDARY reviewer passes")
        if len(set(reviewer_contexts)) < 2:
            errors.append("BLIND_DUAL_REVIEW requires distinct reviewer context_ref values")
        if blind_completed < 2:
            errors.append("BLIND_DUAL_REVIEW requires both reviewer passes blind_to_prior_findings=true")
    return value


def _outcome_basis(value: Any, outcome: Any, finding_ids: set[str], errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("outcome_basis must be an object")
        return
    surviving = value.get("surviving_finding_ids")
    if not isinstance(surviving, list) or not all(_text(x) for x in surviving):
        errors.append("outcome_basis.surviving_finding_ids must be a string list")
        surviving = []
    if len(set(surviving)) != len(surviving):
        errors.append("outcome_basis.surviving_finding_ids must not contain duplicates")
    for key in ("withdrawn_candidate_count", "unresolved_candidate_count"):
        n = value.get(key)
        if not isinstance(n, int) or isinstance(n, bool) or n < 0:
            errors.append(f"outcome_basis.{key} must be a non-negative integer")
    if not _text(value.get("reason")):
        errors.append("outcome_basis.reason is required")
    if outcome == "MATERIAL_FINDINGS" and set(surviving) != finding_ids:
        errors.append("MATERIAL_FINDINGS requires outcome_basis.surviving_finding_ids to match findings")
    if outcome in {"NO_MATERIAL_FINDINGS", "INSUFFICIENT_EVIDENCE"} and surviving:
        errors.append(f"{outcome} requires empty outcome_basis.surviving_finding_ids")
    if outcome == "NO_MATERIAL_FINDINGS" and value.get("unresolved_candidate_count") not in {0, None}:
        errors.append("NO_MATERIAL_FINDINGS requires unresolved_candidate_count=0")


def _evidence_register(value: Any, source_ids: set[str], errors: list[str]) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list) or not value:
        errors.append("evidence_register must be a non-empty list")
        return {}
    rows: dict[str, dict[str, Any]] = {}
    for i, row in enumerate(value):
        p = f"evidence_register[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{p} must be an object")
            continue
        eid = row.get("id")
        if not _text(eid):
            errors.append(f"{p}.id is required")
        elif eid in rows:
            errors.append(f"{p}.id must be unique")
        else:
            rows[eid] = row
        if row.get("source_id") not in source_ids:
            errors.append(f"{p}.source_id must reference source_manifest")
        if row.get("kind") not in EVIDENCE_KINDS:
            errors.append(f"{p}.kind is invalid")
        if not _text(row.get("locator")):
            errors.append(f"{p}.locator is required")
        if not _text(row.get("summary")):
            errors.append(f"{p}.summary is required")
        if row.get("strength") not in EVIDENCE_STRENGTH:
            errors.append(f"{p}.strength is invalid")
        if not _slist(row.get("limitations")):
            errors.append(f"{p}.limitations must be a string list")
    return rows


def _evidence_conflicts(value: Any, evidence_ids: set[str], errors: list[str]) -> bool:
    if not isinstance(value, list):
        errors.append("evidence_conflicts must be a list")
        return False
    ids: set[str] = set()
    unresolved = False
    for i, row in enumerate(value):
        p = f"evidence_conflicts[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{p} must be an object")
            continue
        cid = row.get("id")
        if not _text(cid):
            errors.append(f"{p}.id is required")
        elif cid in ids:
            errors.append(f"{p}.id must be unique")
        else:
            ids.add(cid)
        refs = row.get("evidence_refs")
        if not isinstance(refs, list) or len(refs) < 2 or not all(_text(x) for x in refs):
            errors.append(f"{p}.evidence_refs must contain at least two evidence ids")
            refs = []
        for ref in refs:
            if ref not in evidence_ids:
                errors.append(f"{p}.evidence_refs contains unknown evidence id {ref!r}")
        if not _text(row.get("conflict")):
            errors.append(f"{p}.conflict is required")
        disposition = row.get("disposition")
        if disposition not in CONFLICT_DISPOSITION:
            errors.append(f"{p}.disposition is invalid")
        if disposition == "UNRESOLVED":
            unresolved = True
        if not _text(row.get("residual_uncertainty")):
            errors.append(f"{p}.residual_uncertainty is required")
    return unresolved


def _finding_evidence_refs(value: Any, prefix: str, evidence_rows: dict[str, dict[str, Any]], anchor_source: Any, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or not value or not all(_text(x) for x in value):
        errors.append(f"{prefix}.evidence_refs must be a non-empty string list")
        return []
    for ref in value:
        if ref not in evidence_rows:
            errors.append(f"{prefix}.evidence_refs contains unknown evidence id {ref!r}")
    if anchor_source in {row.get("source_id") for ref, row in evidence_rows.items() if ref in value}:
        pass
    else:
        errors.append(f"{prefix}.evidence_refs must include evidence from the anchor source")
    return value


def _confidence_basis(value: Any, prefix: str, report_assurance: dict[str, Any], confidence: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{prefix}.confidence_basis must be an object")
        return
    directness = value.get("directness")
    scope_support = value.get("scope_support")
    counter = value.get("counterevidence_status")
    independence = value.get("independence")
    if directness not in CONF_DIRECTNESS:
        errors.append(f"{prefix}.confidence_basis.directness is invalid")
    if scope_support not in CONF_SCOPE_SUPPORT:
        errors.append(f"{prefix}.confidence_basis.scope_support is invalid")
    if counter not in COUNTEREVIDENCE_STATUS:
        errors.append(f"{prefix}.confidence_basis.counterevidence_status is invalid")
    if independence not in INDEPENDENCE:
        errors.append(f"{prefix}.confidence_basis.independence is invalid")
    if report_assurance and independence != report_assurance.get("independence"):
        errors.append(f"{prefix}.confidence_basis.independence must match report assurance")
    if not _text(value.get("rationale")):
        errors.append(f"{prefix}.confidence_basis.rationale is required")
    if confidence == "high" and (directness == "LOW" or scope_support == "LOW" or counter == "UNKNOWN"):
        errors.append(f"{prefix}: high confidence requires non-low directness/scope support and addressed counterevidence")


def _residual_risk(value: Any, prefix: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{prefix}.residual_risk must be an object")
        return
    if value.get("after_repair") not in RESIDUAL_RISK:
        errors.append(f"{prefix}.residual_risk.after_repair is invalid")
    if not _text(value.get("closure_dependency")):
        errors.append(f"{prefix}.residual_risk.closure_dependency is required")



def _inferential_claim_ledger(value: Any, central_claim_ids: set[str], evidence_ids: set[str], errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append("inferential_claim_ledger must be a non-empty list")
        return
    seen: set[str] = set()
    for i, row in enumerate(value):
        p = f"inferential_claim_ledger[{i}]"
        if not isinstance(row, dict): errors.append(f"{p} must be an object"); continue
        ref = row.get("claim_ref")
        if ref not in central_claim_ids: errors.append(f"{p}.claim_ref must reference a central claim")
        elif ref in seen: errors.append(f"{p}.claim_ref must be unique")
        else: seen.add(ref)
        for key in ("estimand", "independent_unit", "analysis_population", "uncertainty_basis"):
            if not _text(row.get(key)): errors.append(f"{p}.{key} is required; use NOT_REPORTED when unresolved")
        if row.get("multiplicity_status") not in MULTIPLICITY_STATUS: errors.append(f"{p}.multiplicity_status is invalid")
        if row.get("identification_status") not in IDENTIFICATION_STATUS: errors.append(f"{p}.identification_status is invalid")
        if row.get("data_split_status") not in DATA_SPLIT_STATUS: errors.append(f"{p}.data_split_status is invalid")
        refs=row.get("evidence_refs")
        if not isinstance(refs,list) or not refs: errors.append(f"{p}.evidence_refs must be a non-empty list"); refs=[]
        for eid in refs:
            if eid not in evidence_ids: errors.append(f"{p}.evidence_refs contains unknown evidence id {eid!r}")
    missing = central_claim_ids - seen
    if missing: errors.append(f"inferential_claim_ledger missing central claims: {', '.join(sorted(missing))}")


def validate(report: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(report, dict):
        return ["report must be an object"]

    if report.get("schema") != SCHEMA:
        errors.append(f"schema must equal {SCHEMA}")
    if not _text(report.get("artifact")):
        errors.append("artifact must be a non-empty string")
    outcome = report.get("review_outcome")
    if outcome not in OUTCOMES:
        errors.append("review_outcome is invalid")
    mode = report.get("mode")
    evidence_mode = report.get("evidence_mode")
    if mode not in MODES:
        errors.append("mode is invalid")
    if evidence_mode not in EVIDENCE_MODES:
        errors.append("evidence_mode is invalid")
    if report.get("study_profile") not in PROFILES:
        errors.append("study_profile is invalid")
    source_ids = _source_manifest(report.get("source_manifest"), evidence_mode, errors)
    _review_plan(report.get("review_plan"), errors)
    assurance = _assurance(report.get("assurance"), errors, source_ids)
    evidence_rows = _evidence_register(report.get("evidence_register"), source_ids, errors)
    unresolved_conflicts = _evidence_conflicts(report.get("evidence_conflicts"), set(evidence_rows), errors)
    if not _slist(report.get("limitations")):
        errors.append("limitations must be a string list")


    if mode == "REVISION":
        comparison = report.get("comparison")
        if not isinstance(comparison, dict) or not _text(comparison.get("base_artifact")) or not _text(comparison.get("head_artifact")):
            errors.append("REVISION mode requires comparison.base_artifact and comparison.head_artifact")

    contract = report.get("study_contract")
    if not isinstance(contract, dict):
        errors.append("study_contract must be an object")
    else:
        required_text = (
            "research_question", "target_construct", "population", "analysis_population", "unit_of_analysis", "reference",
            "reference_status", "estimand", "primary_endpoint", "evidence_status", "preregistration_status", "novelty_claim",
            "missingness_strategy", "multiplicity_strategy", "dependence_structure",
        )
        for key in required_text:
            if not _text(contract.get(key)):
                errors.append(f"study_contract.{key} is required; use 'NOT_REPORTED' when appropriate")
        if contract.get("reference_status") not in REFERENCE_STATUS:
            errors.append("study_contract.reference_status is invalid")

    coverage = report.get("coverage")
    if not isinstance(coverage, dict):
        errors.append("coverage must be an object")
    else:
        if coverage.get("level") not in COVERAGE:
            errors.append("coverage.level is invalid")
        if coverage.get("scope_basis") not in SCOPE:
            errors.append("coverage.scope_basis is invalid")
        if coverage.get("coverage_confidence") not in CONF:
            errors.append("coverage.coverage_confidence is invalid")
        if not _text(coverage.get("sampling_strategy")):
            errors.append("coverage.sampling_strategy is required")
        for key in ("inspected", "not_inspected", "limitations"):
            if not _list(coverage.get(key)):
                errors.append(f"coverage.{key} must be a list")

    _quality_gates(report.get("quality_gates"), outcome, errors)
    gates = report.get("quality_gates") if isinstance(report.get("quality_gates"), dict) else {}
    if unresolved_conflicts and gates.get("evidence") == "PASS":
        errors.append("unresolved evidence_conflicts require quality_gates.evidence=WARN or BLOCKED")
    if assurance.get("mode") == "SECOND_PASS" and assurance.get("second_pass_status") == "UNAVAILABLE" and gates.get("assurance") == "PASS":
        errors.append("unavailable SECOND_PASS requires quality_gates.assurance=WARN or BLOCKED")


    measurement = report.get("measurement_chain")
    if not isinstance(measurement, dict):
        errors.append("measurement_chain must be an object")
    else:
        for key in ("construct", "operationalization", "reference", "transformation", "endpoint"):
            if not _text(measurement.get(key)):
                errors.append(f"measurement_chain.{key} is required; use 'NOT_APPLICABLE' when appropriate")
        if measurement.get("alignment_status") not in ALIGNMENT:
            errors.append("measurement_chain.alignment_status is invalid")

    claims = report.get("claim_map")
    if not isinstance(claims, list) or not claims:
        errors.append("claim_map must be a non-empty list")
        claims = []
    claim_ids: set[str] = set()
    central_ids: set[str] = set()
    for i, claim in enumerate(claims):
        p = f"claim_map[{i}]"
        if not isinstance(claim, dict):
            errors.append(f"{p} must be an object")
            continue
        cid = claim.get("id")
        if not _text(cid):
            errors.append(f"{p}.id is required")
        elif cid in claim_ids:
            errors.append(f"{p}.id must be unique")
        else:
            claim_ids.add(cid)
        if claim.get("central") is True and _text(cid):
            central_ids.add(cid)
        if not isinstance(claim.get("central"), bool):
            errors.append(f"{p}.central must be boolean")
        if not _text(claim.get("claim")):
            errors.append(f"{p}.claim is required")
        if claim.get("inferential_type") not in INFERENTIAL_TYPES:
            errors.append(f"{p}.inferential_type is invalid")
        if claim.get("evidence_role") not in EVIDENCE_ROLES:
            errors.append(f"{p}.evidence_role is invalid")
        for key in ("population_scope", "endpoint_scope", "analysis_set"):
            if not _text(claim.get(key)):
                errors.append(f"{p}.{key} is required")
        _anchor(claim.get("anchor"), f"{p}.anchor", errors, source_ids)
        if claim.get("support_status") not in SUPPORT_STATUS:
            errors.append(f"{p}.support_status is invalid")

    if claims and not central_ids:
        errors.append("claim_map requires at least one central claim")

    _inferential_claim_ledger(report.get("inferential_claim_ledger"), central_ids, set(evidence_rows), errors)

    validity = report.get("validity_ledger")
    if not isinstance(validity, list):
        errors.append("validity_ledger must be a list")
        validity = []
    seen_validity: set[str] = set()
    for i, row in enumerate(validity):
        p = f"validity_ledger[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{p} must be an object")
            continue
        domain = row.get("domain")
        if domain not in VALIDITY_DOMAINS:
            errors.append(f"{p}.domain is invalid")
        elif domain in seen_validity:
            errors.append(f"{p}.domain must be unique")
        else:
            seen_validity.add(domain)
        if row.get("status") not in VALIDITY_STATUS:
            errors.append(f"{p}.status is invalid")
        if not _text(row.get("basis")):
            errors.append(f"{p}.basis is required")

    integrity = report.get("analysis_integrity_ledger")
    if not isinstance(integrity, list):
        errors.append("analysis_integrity_ledger must be a list")
        integrity = []
    for i, row in enumerate(integrity):
        p = f"analysis_integrity_ledger[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{p} must be an object")
            continue
        if row.get("area") not in INTEGRITY_AREAS:
            errors.append(f"{p}.area is invalid")
        if row.get("status") not in INTEGRITY_STATUS:
            errors.append(f"{p}.status is invalid")
        if not _text(row.get("basis")):
            errors.append(f"{p}.basis is required")

    alternatives = report.get("alternative_explanations")
    if not isinstance(alternatives, list):
        errors.append("alternative_explanations must be a list")
        alternatives = []
    alt_ids: set[str] = set()
    for i, row in enumerate(alternatives):
        p = f"alternative_explanations[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{p} must be an object")
            continue
        aid = row.get("id")
        if not _text(aid):
            errors.append(f"{p}.id is required")
        elif aid in alt_ids:
            errors.append(f"{p}.id must be unique")
        else:
            alt_ids.add(aid)
        refs = row.get("claim_refs")
        if not isinstance(refs, list) or not refs:
            errors.append(f"{p}.claim_refs must be a non-empty list")
        else:
            for ref in refs:
                if ref not in claim_ids:
                    errors.append(f"{p}.claim_refs contains unknown claim id {ref!r}")
        if not _text(row.get("explanation")):
            errors.append(f"{p}.explanation is required")
        if not isinstance(row.get("addressed_by"), list):
            errors.append(f"{p}.addressed_by must be a list")
        if row.get("status") not in ALT_STATUS:
            errors.append(f"{p}.status is invalid")

    robustness = report.get("robustness_ledger")
    if not isinstance(robustness, list):
        errors.append("robustness_ledger must be a list")
        robustness = []
    for i, row in enumerate(robustness):
        p = f"robustness_ledger[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{p} must be an object")
            continue
        if row.get("claim_ref") not in claim_ids:
            errors.append(f"{p}.claim_ref references unknown claim")
        if not _text(row.get("check")):
            errors.append(f"{p}.check is required")
        if row.get("status") not in ROBUSTNESS_STATUS:
            errors.append(f"{p}.status is invalid")
        if not _text(row.get("evidence")):
            errors.append(f"{p}.evidence is required")

    roots = report.get("root_causes", [])
    if not isinstance(roots, list):
        errors.append("root_causes must be a list")
        roots = []
    root_ids: set[str] = set()
    for i, root in enumerate(roots):
        p = f"root_causes[{i}]"
        if not isinstance(root, dict):
            errors.append(f"{p} must be an object")
            continue
        rid = root.get("id")
        if not _text(rid):
            errors.append(f"{p}.id is required")
        elif rid in root_ids:
            errors.append(f"{p}.id must be unique")
        else:
            root_ids.add(rid)
        for key in ("label", "summary"):
            if not _text(root.get(key)):
                errors.append(f"{p}.{key} is required")
        refs = root.get("claim_refs", [])
        if not isinstance(refs, list):
            errors.append(f"{p}.claim_refs must be a list")
        else:
            for ref in refs:
                if ref not in claim_ids:
                    errors.append(f"{p}.claim_refs contains unknown claim id {ref!r}")

    no_material = report.get("no_material_findings")
    if not isinstance(no_material, bool):
        errors.append("no_material_findings must be boolean")

    findings = report.get("findings")
    if not isinstance(findings, list):
        errors.append("findings must be a list")
        findings = []
    ids: set[str] = set()
    keys: set[str] = set()
    identity_owner: dict[str, str] = {}
    for i, finding in enumerate(findings):
        p = f"findings[{i}]"
        if not isinstance(finding, dict):
            errors.append(f"{p} must be an object")
            continue
        fid = finding.get("id")
        key = finding.get("finding_key")
        if not _text(fid):
            errors.append(f"{p}.id is required")
        elif fid in ids:
            errors.append(f"{p}.id must be unique")
        else:
            ids.add(fid)
        if not _text(key):
            errors.append(f"{p}.finding_key is required")
        elif key in keys:
            errors.append(f"{p}.finding_key must be unique")
        else:
            keys.add(key)
        aliases = finding.get("finding_aliases")
        if not _slist(aliases):
            errors.append(f"{p}.finding_aliases must be a string list")
            aliases = []
        elif len(set(aliases)) != len(aliases):
            errors.append(f"{p}.finding_aliases must not contain duplicates")
        if _text(key):
            if key in aliases:
                errors.append(f"{p}.finding_aliases must not repeat finding_key")
            for token in [key, *aliases]:
                owner = identity_owner.get(token)
                if owner is not None and owner != str(fid):
                    errors.append(f"{p}: finding identity token {token!r} is already owned by {owner!r}")
                else:
                    identity_owner[token] = str(fid)

        severity = finding.get("severity")
        anchor_source = finding.get("anchor", {}).get("source_id") if isinstance(finding.get("anchor"), dict) else None
        _finding_evidence_refs(finding.get("evidence_refs"), p, evidence_rows, anchor_source, errors)
        _confidence_basis(finding.get("confidence_basis"), p, assurance, finding.get("confidence"), errors)
        _residual_risk(finding.get("residual_risk"), p, errors)
        state = finding.get("evidence_state")
        strength = finding.get("evidence_strength")
        scope_sensitivity = finding.get("scope_sensitivity")
        confidence = finding.get("confidence")
        if severity not in SEVERITIES:
            errors.append(f"{p}.severity is invalid")
        if finding.get("category") not in CATEGORIES:
            errors.append(f"{p}.category is invalid")
        if finding.get("validity_domain") not in VALIDITY_DOMAINS:
            errors.append(f"{p}.validity_domain is invalid")
        if state not in STATES:
            errors.append(f"{p}.evidence_state is invalid")
        if strength not in EVIDENCE_STRENGTH:
            errors.append(f"{p}.evidence_strength is invalid")
        if scope_sensitivity not in SCOPE_SENSITIVITY:
            errors.append(f"{p}.scope_sensitivity is invalid")
        if confidence not in CONF:
            errors.append(f"{p}.confidence is invalid")
        if scope_sensitivity == "HIGH" and confidence == "high":
            errors.append(f"{p}: HIGH scope_sensitivity cannot have high confidence")
        if strength == "WEAK" and confidence == "high":
            errors.append(f"{p}: WEAK evidence cannot have high confidence")

        at = _anchor(finding.get("anchor"), f"{p}.anchor", errors, source_ids)
        if state == "NOT_REPORTED":
            if at != "missing_report":
                errors.append(f"{p}: NOT_REPORTED requires missing_report anchor")
            if not _text(finding.get("what_cannot_be_assessed")):
                errors.append(f"{p}.what_cannot_be_assessed is required for NOT_REPORTED")
        if state == "INFERRED" and not _text(finding.get("inference_basis")):
            errors.append(f"{p}.inference_basis is required for INFERRED")
        if state == "EXTERNAL_VERIFIED":
            if evidence_mode != "VERIFY_EXTERNAL":
                errors.append(f"{p}: EXTERNAL_VERIFIED is invalid in SOURCE_BOUND mode")
            if at != "external_source":
                errors.append(f"{p}: EXTERNAL_VERIFIED requires external_source anchor")

        refs = finding.get("claim_refs")
        if not isinstance(refs, list):
            errors.append(f"{p}.claim_refs must be a list")
            refs = []
        for ref in refs:
            if ref not in claim_ids:
                errors.append(f"{p}.claim_refs contains unknown claim id {ref!r}")
        root_id = finding.get("root_cause_id")
        if root_id is not None and root_id not in root_ids:
            errors.append(f"{p}.root_cause_id references unknown root cause")

        materiality = _materiality(finding.get("materiality"), f"{p}.materiality", errors)
        for key_name in ("observation", "scientific_risk", "repair"):
            if not _text(finding.get(key_name)):
                errors.append(f"{p}.{key_name} is required")
        if finding.get("repair_level") not in REPAIR_LEVEL:
            errors.append(f"{p}.repair_level is invalid")
        _verification(finding.get("verification"), f"{p}.verification", errors)

        falsifier_obj = finding.get("falsifier_check")
        if severity in {"FATAL", "MAJOR"} or falsifier_obj is not None:
            result = _falsifier(falsifier_obj, f"{p}.falsifier_check", errors)
            if result == "WITHDRAWN":
                errors.append(f"{p}: withdrawn finding must not remain in findings")
            if result == "UNRESOLVED" and confidence == "high":
                errors.append(f"{p}: unresolved falsifier cannot have high confidence")
            if result == "DOWNGRADED":
                prior = finding.get("falsifier_check", {}).get("downgraded_from")
                if prior not in SEVERITY_RANK or severity not in SEVERITY_RANK or SEVERITY_RANK[prior] <= SEVERITY_RANK[severity]:
                    errors.append(f"{p}: DOWNGRADED requires falsifier_check.downgraded_from above final severity")

        if severity == "FATAL":
            if not any(ref in central_ids for ref in refs):
                errors.append(f"{p}: FATAL requires at least one central claim_ref")
            if not _text(finding.get("central_claim_impact")):
                errors.append(f"{p}.central_claim_impact is required for FATAL")
            if finding.get("repair_level") == "REPORTING_ONLY":
                errors.append(f"{p}: FATAL cannot be REPORTING_ONLY")
            if state == "NOT_REPORTED":
                errors.append(f"{p}: FATAL cannot be based only on NOT_REPORTED")
            if confidence == "low":
                errors.append(f"{p}: FATAL cannot have low confidence")
            if strength == "WEAK":
                errors.append(f"{p}: FATAL cannot use WEAK evidence_strength")
            if scope_sensitivity == "HIGH":
                errors.append(f"{p}: FATAL cannot use HIGH scope_sensitivity")
            if materiality.get("centrality") != "CENTRAL":
                errors.append(f"{p}: FATAL requires materiality.centrality=CENTRAL")
            if materiality.get("consequence") != "HIGH":
                errors.append(f"{p}: FATAL requires materiality.consequence=HIGH")

        combined = " ".join(str(finding.get(k, "")) for k in ("observation", "scientific_risk", "reviewer_attack", "repair", "central_claim_impact"))
        if PERSONAL_ATTACK.search(combined):
            errors.append(f"{p} contains a personal attack on an author/researcher")

    _outcome_basis(report.get("outcome_basis"), outcome, ids, errors)

    first = report.get("first_attack_id")
    ranks = [SEVERITY_RANK.get(f.get("severity"), 0) for f in findings if isinstance(f, dict)]
    if ranks and ranks != sorted(ranks, reverse=True):
        errors.append("findings must be ordered by severity descending")
    if findings and first in ids:
        first_row = next((f for f in findings if isinstance(f, dict) and f.get("id") == first), None)
        if first_row is not None and SEVERITY_RANK.get(first_row.get("severity"), 0) < max(ranks or [0]):
            errors.append("first_attack_id must reference a highest-severity finding")
    if not findings and roots:
        errors.append("root_causes must be empty when findings are empty")
    if findings:
        if outcome != "MATERIAL_FINDINGS":
            errors.append("non-empty findings require review_outcome=MATERIAL_FINDINGS")
        if no_material is not False:
            errors.append("no_material_findings must be false when findings exist")
        if first not in ids:
            errors.append("first_attack_id must reference an existing finding")
    else:
        if first is not None:
            errors.append("first_attack_id must be null when findings are empty")
        if outcome == "NO_MATERIAL_FINDINGS" and no_material is not True:
            errors.append("NO_MATERIAL_FINDINGS requires no_material_findings=true")
        if outcome == "INSUFFICIENT_EVIDENCE" and no_material is not False:
            errors.append("INSUFFICIENT_EVIDENCE requires no_material_findings=false")
        if outcome == "MATERIAL_FINDINGS":
            errors.append("MATERIAL_FINDINGS requires at least one finding")

    ledger = report.get("resolution_ledger", [])
    if not isinstance(ledger, list):
        errors.append("resolution_ledger must be a list")
        ledger = []
    for i, row in enumerate(ledger):
        p = f"resolution_ledger[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{p} must be an object")
            continue
        if not _text(row.get("finding_key")):
            errors.append(f"{p}.finding_key is required")
        status = row.get("status")
        if status not in RESOLUTION:
            errors.append(f"{p}.status is invalid")
        if not _text(row.get("evidence")):
            errors.append(f"{p}.evidence is required")
        verification_status = row.get("verification_status")
        if verification_status not in RESOLUTION_VERIFICATION:
            errors.append(f"{p}.verification_status is invalid")
        if row.get("change_basis") not in RESOLUTION_CHANGE_BASIS:
            errors.append(f"{p}.change_basis is invalid")
        if status == "RESOLVED" and verification_status != "PASSED":
            errors.append(f"{p}: RESOLVED requires verification_status=PASSED")
        if status == "NOT_ASSESSABLE" and verification_status != "NOT_RUN":
            errors.append(f"{p}: NOT_ASSESSABLE requires verification_status=NOT_RUN")
    if mode == "REVISION" and "resolution_ledger" not in report:
        errors.append("REVISION mode requires resolution_ledger")

    queue = report.get("external_verification_queue")
    if not isinstance(queue, list):
        errors.append("external_verification_queue must be a list")
    else:
        for i, row in enumerate(queue):
            p = f"external_verification_queue[{i}]"
            if not isinstance(row, dict):
                errors.append(f"{p} must be an object")
                continue
            for key in ("id", "question", "evidence_needed", "why_it_matters"):
                if not _text(row.get(key)):
                    errors.append(f"{p}.{key} is required")

    survival = report.get("claim_survival")
    if not isinstance(survival, list):
        errors.append("claim_survival must be a list")
        survival = []
    seen_survival: set[str] = set()
    for i, row in enumerate(survival):
        p = f"claim_survival[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{p} must be an object")
            continue
        ref = row.get("claim_ref")
        if ref not in claim_ids:
            errors.append(f"{p}.claim_ref references unknown claim")
        elif ref in seen_survival:
            errors.append(f"{p}.claim_ref must be unique")
        else:
            seen_survival.add(ref)
        if row.get("status") not in CLAIM_SURVIVAL:
            errors.append(f"{p}.status is invalid")
        if not _text(row.get("reason")):
            errors.append(f"{p}.reason is required")
    for ref in central_ids:
        if ref not in seen_survival:
            errors.append(f"claim_survival must include central claim {ref!r}")

    if not isinstance(report.get("survives"), list):
        errors.append("survives must be a list")
    if not _text(report.get("minimal_surviving_claim")):
        errors.append("minimal_surviving_claim must be a non-empty string")
    if not _text(report.get("core_fix")):
        errors.append("core_fix must be a non-empty string")
    return errors


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args in (['--help'], ['-h']):
        print("usage: validate_review.py report.json")
        return 0
    if len(args) != 1:
        print("usage: validate_review.py report.json", file=sys.stderr)
        return 2
    try:
        report = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    errors = validate(report)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("OK: science roast report v6")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
