#!/usr/bin/env python3
"""Validate structural and epistemic invariants for Content Roaster v6 reports."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA = "cometweb.content-roaster/v6"
MODES = {"QUICK", "FULL", "RED_TEAM", "DELTA"}
TONES = {"SURGICAL", "DRY", "BRUTAL"}
LENSES = {"GENERAL", "POSITIONING", "CONVERSION", "EDITORIAL", "TRUST", "OFFER", "TECHNICAL_DOCUMENTATION"}
PROFILES = {"GENERAL", "LANDING_PAGE", "PRODUCT_PAGE", "PRICING", "OFFER", "EMAIL", "ARTICLE", "CASE_STUDY", "SALES_DECK", "LONGFORM", "DOCUMENTATION"}
OUTCOMES = {"MATERIAL_FINDINGS", "NO_MATERIAL_FINDINGS", "INSUFFICIENT_EVIDENCE"}
DECISION_COST = {"LOW", "MEDIUM", "HIGH", "UNKNOWN"}
DECISION_IMPACT = {"DISCOVERY", "COMPREHENSION", "TRUST", "DECISION", "ACTION"}
COVERAGE = {"PARTIAL", "SUBSTANTIAL", "COMPLETE"}
SCOPE = {"FULL_ARTIFACT", "EXCERPT", "SAMPLED", "ARTIFACT_SET", "MIXED"}
GATE_STATUS = {"PASS", "WARN", "BLOCKED"}
GATE_KEYS = {"scope", "contract", "source_integrity", "evidence", "challenge", "assurance", "severity", "repair", "boundary"}
SEVERITIES = {"BLOCKER", "MAJOR", "MINOR"}
SEVERITY_RANK = {"MINOR": 1, "MAJOR": 2, "BLOCKER": 3}
STATES = {"OBSERVED", "MISSING", "INFERRED", "VERIFY_EXTERNAL"}
EVIDENCE_STRENGTH = {"STRONG", "MODERATE", "WEAK"}
SCOPE_SENSITIVITY = {"LOW", "MEDIUM", "HIGH"}
ANCHORS = {"quote", "section", "claim", "metric", "cta", "missing_element"}
CATEGORIES = {"audience", "positioning", "promise", "differentiation", "claim_evidence", "logic", "hierarchy", "specificity", "credibility", "objection", "cta", "redundancy", "readability", "voice", "offer", "technical_documentation"}
CLAIM_TYPES = {"FACTUAL", "QUANTITATIVE", "COMPARATIVE", "OUTCOME", "MECHANISM", "GUARANTEE", "SUBJECTIVE"}
DECISION_ROLES = {"PRIMARY", "SUPPORTING"}
PROOF = {"PRESENT", "WEAK", "ABSENT", "EXTERNAL_REQUIRED"}
BURDEN = {"LOW", "MEDIUM", "HIGH", "VERY_HIGH"}
DEBT_TYPES = {"ABSENT_PROOF", "WEAK_PROOF", "MISMATCHED_PROOF", "EXTERNAL_VERIFICATION", "OVERCLAIM"}
DEBT_STATUS = {"OPEN", "PARTIAL", "CLOSED", "NOT_APPLICABLE"}
OBJECTION_STATUS = {"ANSWERED", "PARTIAL", "UNANSWERED", "NOT_APPLICABLE"}
REPAIR = {"COPY", "SECTION", "STRUCTURE", "PROOF", "OFFER", "UX", "EXTERNAL_VERIFICATION"}
VERIFY = {"MANUAL_INSPECTION", "READER_TEST", "ANALYTICS", "EXPERIMENT", "SOURCE_CHECK", "AUTOMATED_CHECK"}
CONF = {"high", "medium", "low"}
FALSIFIER = {"SURVIVES", "UNRESOLVED", "DOWNGRADED", "WITHDRAWN"}
RESOLUTION = {"RESOLVED", "PARTIAL", "OPEN", "REGRESSED", "NOT_ASSESSABLE"}
RESOLUTION_VERIFICATION = {"PASSED", "PARTIAL", "FAILED", "NOT_RUN"}
RESOLUTION_CHANGE_BASIS = {"ARTIFACT_CHANGED", "SCOPE_CHANGED", "JUDGMENT_CORRECTED", "MIXED", "UNKNOWN"}
MATERIAL_CENTRALITY = {"CENTRAL", "SUPPORTING", "LOCAL"}
MATERIAL_CONSEQUENCE = {"HIGH", "MEDIUM", "LOW"}
MATERIAL_REVERSIBILITY = {"EASY", "MODERATE", "HARD", "UNKNOWN"}
SOURCE_KIND = {"PAGE", "DOCUMENT", "EMAIL", "DECK", "ANALYTICS", "RESEARCH", "SCREENSHOT_TRANSCRIPTION", "OTHER"}
SOURCE_ROLE = {"PRIMARY", "SUPPORTING", "CONTEXT"}
VERSION_STATE = {"PINNED", "MOVING", "UNKNOWN"}

DIAGNOSIS_CLASS = {"COPY", "PROOF", "POSITIONING", "OFFER", "PRODUCT", "AUDIENCE", "STRUCTURE", "UX", "MIXED"}
REPAIR_OWNER = {"CONTENT", "EVIDENCE", "PRODUCT", "OFFER", "UX", "MIXED"}

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
PERSONAL_ATTACK = re.compile(r"\b(?:author|writer|copywriter|you|your team)\b.{0,40}\b(?:stupid|idiot|moron|lazy|incompetent|clueless|fraud)\b", re.I)


def _text(v: Any) -> bool:
    return isinstance(v, str) and bool(v.strip())


def _list(v: Any) -> bool:
    return isinstance(v, list)


def _slist(v: Any, nonempty: bool = False) -> bool:
    return isinstance(v, list) and (bool(v) or not nonempty) and all(_text(x) for x in v)


def _anchor(obj: Any, allowed: set[str], prefix: str, errors: list[str], source_ids: set[str]) -> str | None:
    if not isinstance(obj, dict):
        errors.append(f"{prefix} must be an object")
        return None
    at = obj.get("type")
    if at not in allowed:
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


def _source_manifest(value: Any, errors: list[str]) -> set[str]:
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
    blocked = any(value.get(key) == "BLOCKED" for key in GATE_KEYS)
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



def _diagnosis_ledger(value: Any, claim_ids: set[str], evidence_ids: set[str], errors: list[str]) -> set[str]:
    if not isinstance(value, list):
        errors.append("diagnosis_ledger must be a list")
        return set()
    ids: set[str] = set()
    for i, row in enumerate(value):
        p = f"diagnosis_ledger[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{p} must be an object")
            continue
        did = row.get("id")
        if not _text(did): errors.append(f"{p}.id is required")
        elif did in ids: errors.append(f"{p}.id must be unique")
        else: ids.add(did)
        refs = row.get("claim_refs")
        if not isinstance(refs, list) or not refs: errors.append(f"{p}.claim_refs must be a non-empty list"); refs=[]
        for ref in refs:
            if ref not in claim_ids: errors.append(f"{p}.claim_refs contains unknown claim id {ref!r}")
        ev = row.get("evidence_refs")
        if not isinstance(ev, list) or not ev: errors.append(f"{p}.evidence_refs must be a non-empty list"); ev=[]
        for ref in ev:
            if ref not in evidence_ids: errors.append(f"{p}.evidence_refs contains unknown evidence id {ref!r}")
        if row.get("diagnosis_class") not in DIAGNOSIS_CLASS: errors.append(f"{p}.diagnosis_class is invalid")
        if row.get("repair_owner") not in REPAIR_OWNER: errors.append(f"{p}.repair_owner is invalid")
        if not _text(row.get("summary")): errors.append(f"{p}.summary is required")
    return ids


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
    source_ids = _source_manifest(report.get("source_manifest"), errors)
    _review_plan(report.get("review_plan"), errors)
    assurance = _assurance(report.get("assurance"), errors, source_ids)
    evidence_rows = _evidence_register(report.get("evidence_register"), source_ids, errors)
    unresolved_conflicts = _evidence_conflicts(report.get("evidence_conflicts"), set(evidence_rows), errors)
    if not _slist(report.get("limitations")):
        errors.append("limitations must be a string list")


    mode = report.get("mode")
    if mode not in MODES:
        errors.append("mode is invalid")
    if report.get("tone") not in TONES:
        errors.append("tone is invalid")
    if report.get("lens") not in LENSES:
        errors.append("lens is invalid")
    if report.get("review_profile") not in PROFILES:
        errors.append("review_profile is invalid")
    if mode == "DELTA":
        comparison = report.get("comparison")
        if not isinstance(comparison, dict) or not _text(comparison.get("base_artifact")) or not _text(comparison.get("head_artifact")):
            errors.append("DELTA mode requires comparison.base_artifact and comparison.head_artifact")

    contract = report.get("review_contract")
    if not isinstance(contract, dict):
        errors.append("review_contract must be an object")
    else:
        for key in ("audience", "desired_action", "decision_stage"):
            if not _text(contract.get(key)):
                errors.append(f"review_contract.{key} is required; use 'unknown' when truly unknown")
        if contract.get("decision_cost") not in DECISION_COST:
            errors.append("review_contract.decision_cost is invalid")
        for key in ("known_constraints", "unknowns"):
            if not _list(contract.get(key)):
                errors.append(f"review_contract.{key} must be a list")

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


    chain = report.get("message_chain")
    if not isinstance(chain, dict):
        errors.append("message_chain must be an object")
    else:
        for key in ("problem", "promise", "mechanism", "proof", "objection_handling", "action"):
            if not _text(chain.get(key)):
                errors.append(f"message_chain.{key} is required; use 'unknown' when unresolved")

    if not _text(report.get("central_promise")):
        errors.append("central_promise must be a non-empty string")

    claims = report.get("claim_map")
    if not isinstance(claims, list) or not claims:
        errors.append("claim_map must be a non-empty list")
        claims = []
    claim_ids: set[str] = set()
    primary_ids: set[str] = set()
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
        if claim.get("decision_role") == "PRIMARY" and _text(cid):
            primary_ids.add(cid)
        if not _text(claim.get("claim")):
            errors.append(f"{p}.claim is required")
        ctype = claim.get("claim_type")
        if ctype not in CLAIM_TYPES:
            errors.append(f"{p}.claim_type is invalid")
        if claim.get("decision_role") not in DECISION_ROLES:
            errors.append(f"{p}.decision_role is invalid")
        if claim.get("proof_status") not in PROOF:
            errors.append(f"{p}.proof_status is invalid")
        burden = claim.get("proof_burden")
        if burden not in BURDEN:
            errors.append(f"{p}.proof_burden is invalid")
        if ctype == "GUARANTEE" and burden != "VERY_HIGH":
            errors.append(f"{p}: GUARANTEE requires VERY_HIGH proof_burden")
        if ctype in {"QUANTITATIVE", "COMPARATIVE", "OUTCOME"} and burden == "LOW":
            errors.append(f"{p}: {ctype} claim cannot use LOW proof_burden")
        _anchor(claim.get("anchor"), ANCHORS - {"missing_element"}, f"{p}.anchor", errors, source_ids)

    if claims and not primary_ids:
        errors.append("claim_map requires at least one PRIMARY claim")

    diagnosis_ids = _diagnosis_ledger(report.get("diagnosis_ledger"), claim_ids, set(evidence_rows), errors)

    debt = report.get("proof_debt_ledger")
    if not isinstance(debt, list):
        errors.append("proof_debt_ledger must be a list")
        debt = []
    debt_ids: set[str] = set()
    debt_claim_refs: set[str] = set()
    for i, row in enumerate(debt):
        p = f"proof_debt_ledger[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{p} must be an object")
            continue
        did = row.get("id")
        if not _text(did):
            errors.append(f"{p}.id is required")
        elif did in debt_ids:
            errors.append(f"{p}.id must be unique")
        else:
            debt_ids.add(did)
        claim_ref = row.get("claim_ref")
        if claim_ref not in claim_ids:
            errors.append(f"{p}.claim_ref references unknown claim")
        else:
            debt_claim_refs.add(claim_ref)
        if row.get("debt_type") not in DEBT_TYPES:
            errors.append(f"{p}.debt_type is invalid")
        if row.get("status") not in DEBT_STATUS:
            errors.append(f"{p}.status is invalid")
        for key in ("required_evidence", "why_it_matters"):
            if not _text(row.get(key)):
                errors.append(f"{p}.{key} is required")

    for claim in claims:
        if not isinstance(claim, dict):
            continue
        cid = claim.get("id")
        if claim.get("decision_role") == "PRIMARY" and claim.get("proof_burden") in {"HIGH", "VERY_HIGH"} and claim.get("proof_status") != "PRESENT":
            if cid not in debt_claim_refs:
                errors.append(f"claim_map[{cid!r}] requires proof_debt_ledger entry for unresolved high-burden PRIMARY proof")

    objections = report.get("objection_ledger")
    if not isinstance(objections, list):
        errors.append("objection_ledger must be a list")
        objections = []
    objection_ids: set[str] = set()
    for i, obj in enumerate(objections):
        p = f"objection_ledger[{i}]"
        if not isinstance(obj, dict):
            errors.append(f"{p} must be an object")
            continue
        oid = obj.get("id")
        if not _text(oid):
            errors.append(f"{p}.id is required")
        elif oid in objection_ids:
            errors.append(f"{p}.id must be unique")
        else:
            objection_ids.add(oid)
        for key in ("objection", "relevance"):
            if not _text(obj.get(key)):
                errors.append(f"{p}.{key} is required")
        if obj.get("status") not in OBJECTION_STATUS:
            errors.append(f"{p}.status is invalid")

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
    finding_ids: set[str] = set()
    finding_keys: set[str] = set()
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
        elif fid in finding_ids:
            errors.append(f"{p}.id must be unique")
        else:
            finding_ids.add(fid)
        if not _text(key):
            errors.append(f"{p}.finding_key is required")
        elif key in finding_keys:
            errors.append(f"{p}.finding_key must be unique")
        else:
            finding_keys.add(key)
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
        diagnosis_ref = finding.get("diagnosis_ref")
        if diagnosis_ref not in diagnosis_ids:
            errors.append(f"{p}.diagnosis_ref must reference diagnosis_ledger")
        state = finding.get("evidence_state")
        strength = finding.get("evidence_strength")
        scope_sensitivity = finding.get("scope_sensitivity")
        confidence = finding.get("confidence")
        if severity not in SEVERITIES:
            errors.append(f"{p}.severity is invalid")
        if finding.get("category") not in CATEGORIES:
            errors.append(f"{p}.category is invalid")
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

        at = _anchor(finding.get("anchor"), ANCHORS, f"{p}.anchor", errors, source_ids)
        if state == "MISSING":
            if at != "missing_element":
                errors.append(f"{p}: MISSING requires missing_element anchor")
            if not _text(finding.get("omission_basis")):
                errors.append(f"{p}.omission_basis is required for MISSING")
        if state == "INFERRED" and not _text(finding.get("inference_basis")):
            errors.append(f"{p}.inference_basis is required for INFERRED")

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
        if finding.get("decision_impact") not in DECISION_IMPACT:
            errors.append(f"{p}.decision_impact is invalid")
        materiality = _materiality(finding.get("materiality"), f"{p}.materiality", errors)
        for key_name in ("observation", "failure_mode", "why_it_matters", "repair"):
            if not _text(finding.get(key_name)):
                errors.append(f"{p}.{key_name} is required")
        if finding.get("repair_class") not in REPAIR:
            errors.append(f"{p}.repair_class is invalid")
        _verification(finding.get("verification"), f"{p}.verification", errors)

        falsifier_result = None
        falsifier_obj = finding.get("falsifier_check")
        if severity in {"BLOCKER", "MAJOR"} or falsifier_obj is not None:
            falsifier_result = _falsifier(falsifier_obj, f"{p}.falsifier_check", errors)
            if falsifier_result == "WITHDRAWN":
                errors.append(f"{p}: withdrawn finding must not remain in findings")
            if falsifier_result == "UNRESOLVED" and confidence == "high":
                errors.append(f"{p}: unresolved falsifier cannot have high confidence")
            if falsifier_result == "DOWNGRADED":
                prior = finding.get("falsifier_check", {}).get("downgraded_from")
                if prior not in SEVERITY_RANK or severity not in SEVERITY_RANK or SEVERITY_RANK[prior] <= SEVERITY_RANK[severity]:
                    errors.append(f"{p}: DOWNGRADED requires falsifier_check.downgraded_from above final severity")

        if severity == "BLOCKER":
            if not any(ref in primary_ids for ref in refs):
                errors.append(f"{p}: BLOCKER requires at least one PRIMARY claim_ref")
            if finding.get("decision_impact") not in {"TRUST", "DECISION", "ACTION"}:
                errors.append(f"{p}: BLOCKER decision_impact must be TRUST, DECISION, or ACTION")
            if materiality.get("centrality") != "CENTRAL":
                errors.append(f"{p}: BLOCKER requires materiality.centrality=CENTRAL")
            if materiality.get("consequence") != "HIGH":
                errors.append(f"{p}: BLOCKER requires materiality.consequence=HIGH")
            if confidence == "low":
                errors.append(f"{p}: BLOCKER cannot have low confidence")
            if strength == "WEAK":
                errors.append(f"{p}: BLOCKER cannot use WEAK evidence_strength")
            if scope_sensitivity == "HIGH":
                errors.append(f"{p}: BLOCKER cannot use HIGH scope_sensitivity")

        combined = " ".join(str(finding.get(k, "")) for k in ("observation", "failure_mode", "roast_line", "why_it_matters", "repair"))
        if PERSONAL_ATTACK.search(combined):
            errors.append(f"{p} contains a personal attack on an author/writer")

    _outcome_basis(report.get("outcome_basis"), outcome, finding_ids, errors)

    first = report.get("first_attack_id")
    ranks = [SEVERITY_RANK.get(f.get("severity"), 0) for f in findings if isinstance(f, dict)]
    if ranks and ranks != sorted(ranks, reverse=True):
        errors.append("findings must be ordered by severity descending")
    if findings and first in finding_ids:
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
        if first not in finding_ids:
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
    if mode == "DELTA" and "resolution_ledger" not in report:
        errors.append("DELTA mode requires resolution_ledger")

    queue = report.get("verification_queue")
    if not isinstance(queue, list):
        errors.append("verification_queue must be a list")
    else:
        for i, row in enumerate(queue):
            p = f"verification_queue[{i}]"
            if not isinstance(row, dict):
                errors.append(f"{p} must be an object")
                continue
            for key in ("id", "question", "evidence_needed", "why_it_matters"):
                if not _text(row.get(key)):
                    errors.append(f"{p}.{key} is required")

    if not isinstance(report.get("preserve"), list):
        errors.append("preserve must be a list")
    if not _text(report.get("core_fix")):
        errors.append("core_fix must be a non-empty string")
    return errors


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args in (['--help'], ['-h']):
        print("usage: validate_roast.py report.json")
        return 0
    if len(args) != 1:
        print("usage: validate_roast.py report.json", file=sys.stderr)
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
    print("OK: content roast report v6")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
