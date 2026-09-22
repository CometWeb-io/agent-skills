#!/usr/bin/env python3
"""Validate structural and epistemic invariants for Repo Roaster v6 reports."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA = "cometweb.repo-roaster/v6"
MODES = {"QUICK", "FULL", "FORENSIC", "DIFF", "RECHECK"}
PROFILES = {"FULL_REPO", "PR", "SERVICE", "MONOREPO", "LIBRARY", "CLI", "DESKTOP_APP", "MOBILE_APP", "DATA_PIPELINE", "AI_AGENT_SYSTEM", "INFRA", "MIGRATION"}
LENSES = {"GENERAL", "ARCHITECTURE", "CORRECTNESS", "DATA_INTEGRITY", "TESTABILITY", "SECURITY_REVIEW", "PERFORMANCE", "RELIABILITY", "OPERABILITY", "SUPPLY_CHAIN", "BUILD_RELEASE", "MAINTAINABILITY", "DX"}
OUTCOMES = {"MATERIAL_FINDINGS", "NO_MATERIAL_FINDINGS", "INSUFFICIENT_EVIDENCE"}
COVERAGE = {"PARTIAL", "SUBSTANTIAL", "COMPLETE"}
SCOPE = {"FULL_TREE", "SAMPLED", "DIFF_ONLY", "MIXED"}
GATE_STATUS = {"PASS", "WARN", "BLOCKED"}
GATE_KEYS = {"scope", "contract", "source_integrity", "evidence", "challenge", "assurance", "severity", "repair", "boundary"}
SEVERITIES = {"CRITICAL", "MAJOR", "MINOR"}
SEVERITY_RANK = {"MINOR": 1, "MAJOR": 2, "CRITICAL": 3}
STATES = {"OBSERVED_CODE", "OBSERVED_CONFIG", "OBSERVED_TEST", "OBSERVED_HISTORY", "OBSERVED_RUNTIME", "OBSERVED_LOG", "OBSERVED_METRIC", "NOT_FOUND", "INFERRED"}
EVIDENCE_STRENGTH = {"STRONG", "MODERATE", "WEAK"}
SCOPE_SENSITIVITY = {"LOW", "MEDIUM", "HIGH"}
ANCHORS = {"file", "symbol", "line_range", "config", "test", "commit", "runtime", "log", "metric", "absence"}
REACH = {"PROVEN", "PLAUSIBLE", "STATIC_ONLY", "UNKNOWN"}
CATEGORIES = {"architecture", "correctness", "data_integrity", "isolation", "security", "error_handling", "recovery", "testing", "dependencies", "supply_chain", "configuration", "migrations", "performance", "observability", "build_release", "maintainability", "dx", "documentation"}
DEFECT = {"BUG", "INVARIANT_GAP", "ARCHITECTURE_DEBT", "TEST_GAP", "SECURITY_RISK", "OPERABILITY_GAP", "PERFORMANCE_RISK", "SUPPLY_CHAIN_RISK", "BUILD_RELEASE_RISK", "DX_DEBT"}
FIX_SCOPE = {"LOCAL", "CROSS_MODULE", "DATA_MIGRATION", "ARCHITECTURAL", "OPERATIONAL", "DEPENDENCY", "BUILD_RELEASE"}
VERIFY = {"UNIT_TEST", "INTEGRATION_TEST", "PROPERTY_TEST", "FAULT_INJECTION", "CONCURRENCY_TEST", "LOAD_TEST", "STATIC_CHECK", "RUNTIME_REPRO", "MIGRATION_TEST", "ROLLBACK_TEST", "CONTRACT_TEST", "MANUAL_INSPECTION"}
INV_STATUS = {"VERIFIED", "PARTIAL", "UNVERIFIED", "BROKEN"}
LEDGER_STATUS = {"VERIFIED", "PARTIAL", "UNVERIFIED", "BROKEN", "NOT_APPLICABLE"}
REF_STATUS = {"PINNED", "MOVING", "UNKNOWN"}
SURFACE_TYPES = {"ENTRYPOINT", "TRUST_BOUNDARY", "STATE_MUTATION", "EXTERNAL_SIDE_EFFECT", "JOB", "MIGRATION", "PUBLIC_API", "PRIVILEGED_OPERATION", "BUILD_RELEASE"}
BLAST_CLASS = {"LOCAL", "SINGLE_USER", "SINGLE_TENANT", "MULTI_TENANT", "GLOBAL", "UNKNOWN"}
CONTAINMENT = {"CONTAINED", "PROPAGATES", "UNKNOWN"}
CONF = {"high", "medium", "low"}
FALSIFIER = {"SURVIVES", "UNRESOLVED", "DOWNGRADED", "WITHDRAWN"}
RESOLUTION = {"RESOLVED", "PARTIAL", "OPEN", "REGRESSED", "NOT_ASSESSABLE"}
RESOLUTION_VERIFICATION = {"PASSED", "PARTIAL", "FAILED", "NOT_RUN"}
RESOLUTION_CHANGE_BASIS = {"ARTIFACT_CHANGED", "SCOPE_CHANGED", "JUDGMENT_CORRECTED", "MIXED", "UNKNOWN"}
MATERIAL_CENTRALITY = {"CENTRAL", "SUPPORTING", "LOCAL"}
MATERIAL_CONSEQUENCE = {"HIGH", "MEDIUM", "LOW"}
MATERIAL_REVERSIBILITY = {"EASY", "MODERATE", "HARD", "UNKNOWN"}
SOURCE_KIND = {"REPOSITORY", "DIFF", "RUNTIME", "LOG", "METRIC", "DEPLOYMENT_CONFIG", "TEST_RESULT", "OTHER"}
SOURCE_ROLE = {"PRIMARY", "SUPPORTING", "CONTEXT"}
VERSION_STATE = {"PINNED", "MOVING", "UNKNOWN"}

TEST_STATUS = {"COVERED", "PARTIAL", "ABSENT", "UNKNOWN"}
CHANGE_RISK = {"LOW", "MEDIUM", "HIGH", "UNKNOWN"}

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
PERSONAL_ATTACK = re.compile(r"\b(?:developer|engineer|author|maintainer|you|team)\b.{0,40}\b(?:stupid|idiot|moron|lazy|incompetent|clueless|fraud)\b", re.I)


def _text(v: Any) -> bool:
    return isinstance(v, str) and bool(v.strip())


def _list(v: Any) -> bool:
    return isinstance(v, list)


def _slist(v: Any, nonempty: bool = False) -> bool:
    return isinstance(v, list) and (bool(v) or not nonempty) and all(_text(x) for x in v)


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


def _anchor(obj: Any, prefix: str, errors: list[str], source_ids: set[str]) -> str | None:
    if not isinstance(obj, dict):
        errors.append(f"{prefix} must be an object")
        return None
    at = obj.get("type")
    if at not in ANCHORS:
        errors.append(f"{prefix}.type is invalid")
        return at
    if at != "absence" and not _text(obj.get("path", obj.get("value"))):
        errors.append(f"{prefix} requires path or value")
    source_id = obj.get("source_id")
    if source_id not in source_ids:
        errors.append(f"{prefix}.source_id must reference source_manifest")
    return at



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



def _test_evidence_ledger(value: Any, invariant_ids: set[str], evidence_ids: set[str], errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append("test_evidence_ledger must be a list")
        return
    seen: set[str] = set()
    for i, row in enumerate(value):
        p = f"test_evidence_ledger[{i}]"
        if not isinstance(row, dict): errors.append(f"{p} must be an object"); continue
        ref=row.get("invariant_ref")
        if ref not in invariant_ids: errors.append(f"{p}.invariant_ref references unknown invariant")
        elif ref in seen: errors.append(f"{p}.invariant_ref must be unique")
        else: seen.add(ref)
        if row.get("status") not in TEST_STATUS: errors.append(f"{p}.status is invalid")
        if not _slist(row.get("test_refs")): errors.append(f"{p}.test_refs must be a string list")
        ev=row.get("evidence_refs")
        if not isinstance(ev,list) or not ev: errors.append(f"{p}.evidence_refs must be a non-empty list"); ev=[]
        for eid in ev:
            if eid not in evidence_ids: errors.append(f"{p}.evidence_refs contains unknown evidence id {eid!r}")
        if not _text(row.get("gap")): errors.append(f"{p}.gap is required; use 'none' when covered")
    missing=invariant_ids-seen
    if missing: errors.append(f"test_evidence_ledger missing invariants: {', '.join(sorted(missing))}")


def _change_risk_ledger(value: Any, invariant_ids: set[str], mode: Any, errors: list[str]) -> None:
    if mode != "DIFF":
        if value is not None and not isinstance(value, list): errors.append("change_risk_ledger must be a list when present")
        return
    if not isinstance(value,list) or not value:
        errors.append("DIFF mode requires non-empty change_risk_ledger")
        return
    for i,row in enumerate(value):
        p=f"change_risk_ledger[{i}]"
        if not isinstance(row,dict): errors.append(f"{p} must be an object"); continue
        if not _text(row.get("surface")): errors.append(f"{p}.surface is required")
        refs=row.get("invariant_refs")
        if not isinstance(refs,list): errors.append(f"{p}.invariant_refs must be a list"); refs=[]
        for ref in refs:
            if ref not in invariant_ids: errors.append(f"{p}.invariant_refs contains unknown invariant {ref!r}")
        if row.get("risk") not in CHANGE_RISK: errors.append(f"{p}.risk is invalid")
        if not _text(row.get("reason")): errors.append(f"{p}.reason is required")
        _verification(row.get("verification"), f"{p}.verification", errors)


def validate(report: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(report, dict):
        return ["report must be an object"]

    if report.get("schema") != SCHEMA:
        errors.append(f"schema must equal {SCHEMA}")
    for key in ("repository", "ref"):
        if not _text(report.get(key)):
            errors.append(f"{key} must be a non-empty string")
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
    if report.get("review_profile") not in PROFILES:
        errors.append("review_profile is invalid")

    if mode == "DIFF":
        comparison = report.get("comparison")
        if not isinstance(comparison, dict) or not _text(comparison.get("base_ref")) or not _text(comparison.get("head_ref")):
            errors.append("DIFF mode requires comparison.base_ref and comparison.head_ref")
        change = report.get("change_surface")
        if not isinstance(change, dict):
            errors.append("DIFF mode requires change_surface")
        else:
            for key in ("public_api", "schema_data", "migrations", "configuration", "dependencies", "rollout", "rollback", "build_release"):
                if not isinstance(change.get(key), list):
                    errors.append(f"change_surface.{key} must be a list")
    if mode == "RECHECK":
        comparison = report.get("comparison")
        if not isinstance(comparison, dict) or not _text(comparison.get("prior_report")) or not _text(comparison.get("current_ref")):
            errors.append("RECHECK mode requires comparison.prior_report and comparison.current_ref")

    contract = report.get("repo_contract")
    critical_paths: set[str] = set()
    if not isinstance(contract, dict):
        errors.append("repo_contract must be an object")
    else:
        for key in ("topology_summary", "runtime_evidence", "deployment_model"):
            if not _text(contract.get(key)):
                errors.append(f"repo_contract.{key} is required")
        if contract.get("ref_status") not in REF_STATUS:
            errors.append("repo_contract.ref_status is invalid")
        cp = contract.get("critical_paths")
        if not isinstance(cp, list):
            errors.append("repo_contract.critical_paths must be a list")
        else:
            critical_paths = {x for x in cp if _text(x)}
            if len(critical_paths) != len(cp):
                errors.append("repo_contract.critical_paths must contain non-empty strings")

    lenses = report.get("lenses")
    if not isinstance(lenses, list) or not lenses:
        errors.append("lenses must be a non-empty list")
    else:
        for lens in lenses:
            if lens not in LENSES:
                errors.append(f"invalid lens {lens!r}")

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
        for key in ("inspected_paths", "excluded_paths", "limitations"):
            if not isinstance(coverage.get(key), list):
                errors.append(f"coverage.{key} must be a list")
        if mode == "FORENSIC" and coverage.get("level") == "COMPLETE" and coverage.get("excluded_paths"):
            errors.append("FORENSIC COMPLETE coverage cannot declare excluded_paths")

    _quality_gates(report.get("quality_gates"), outcome, errors)
    gates = report.get("quality_gates") if isinstance(report.get("quality_gates"), dict) else {}
    if unresolved_conflicts and gates.get("evidence") == "PASS":
        errors.append("unresolved evidence_conflicts require quality_gates.evidence=WARN or BLOCKED")
    if assurance.get("mode") == "SECOND_PASS" and assurance.get("second_pass_status") == "UNAVAILABLE" and gates.get("assurance") == "PASS":
        errors.append("unavailable SECOND_PASS requires quality_gates.assurance=WARN or BLOCKED")


    model = report.get("system_model")
    if not isinstance(model, dict):
        errors.append("system_model must be an object")
    else:
        for key in ("actors", "entrypoints", "trust_boundaries", "state_stores", "external_dependencies", "background_jobs", "privileged_surfaces"):
            if not isinstance(model.get(key), list):
                errors.append(f"system_model.{key} must be a list")

    invariants = report.get("invariant_ledger")
    if not isinstance(invariants, list) or not invariants:
        errors.append("invariant_ledger must be a non-empty list")
        invariants = []
    invariant_ids: set[str] = set()
    for i, row in enumerate(invariants):
        p = f"invariant_ledger[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{p} must be an object")
            continue
        iid = row.get("id")
        if not _text(iid):
            errors.append(f"{p}.id is required")
        elif iid in invariant_ids:
            errors.append(f"{p}.id must be unique")
        else:
            invariant_ids.add(iid)
        for key in ("invariant", "scope"):
            if not _text(row.get(key)):
                errors.append(f"{p}.{key} is required")
        for key in ("enforcement", "test_evidence"):
            if not isinstance(row.get(key), list):
                errors.append(f"{p}.{key} must be a list")
        if row.get("status") not in INV_STATUS:
            errors.append(f"{p}.status is invalid")

    _test_evidence_ledger(report.get("test_evidence_ledger"), invariant_ids, set(evidence_rows), errors)
    _change_risk_ledger(report.get("change_risk_ledger"), invariant_ids, mode, errors)

    surfaces = report.get("critical_surface_ledger")
    if not isinstance(surfaces, list):
        errors.append("critical_surface_ledger must be a list")
        surfaces = []
    surface_ids: set[str] = set()
    for i, row in enumerate(surfaces):
        p = f"critical_surface_ledger[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{p} must be an object")
            continue
        sid = row.get("id")
        if not _text(sid):
            errors.append(f"{p}.id is required")
        elif sid in surface_ids:
            errors.append(f"{p}.id must be unique")
        else:
            surface_ids.add(sid)
        if row.get("type") not in SURFACE_TYPES:
            errors.append(f"{p}.type is invalid")
        for key in ("anchor", "trust_transition", "side_effect"):
            if not _text(row.get(key)):
                errors.append(f"{p}.{key} is required")

    transitions = report.get("state_transition_ledger")
    if not isinstance(transitions, list):
        errors.append("state_transition_ledger must be a list")
        transitions = []
    transition_ids: set[str] = set()
    for i, row in enumerate(transitions):
        p = f"state_transition_ledger[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{p} must be an object")
            continue
        tid = row.get("id")
        if not _text(tid):
            errors.append(f"{p}.id is required")
        elif tid in transition_ids:
            errors.append(f"{p}.id must be unique")
        else:
            transition_ids.add(tid)
        for key in ("journey", "transition", "guard", "side_effect", "recovery"):
            if not _text(row.get(key)):
                errors.append(f"{p}.{key} is required")
        if row.get("status") not in LEDGER_STATUS:
            errors.append(f"{p}.status is invalid")

    failure_domains = report.get("failure_domain_ledger")
    if not isinstance(failure_domains, list):
        errors.append("failure_domain_ledger must be a list")
        failure_domains = []
    fd_ids: set[str] = set()
    for i, row in enumerate(failure_domains):
        p = f"failure_domain_ledger[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{p} must be an object")
            continue
        fid = row.get("id")
        if not _text(fid):
            errors.append(f"{p}.id is required")
        elif fid in fd_ids:
            errors.append(f"{p}.id must be unique")
        else:
            fd_ids.add(fid)
        for key in ("component", "failure_mode", "containment", "recovery", "observability"):
            if not _text(row.get(key)):
                errors.append(f"{p}.{key} is required")
        if row.get("status") not in LEDGER_STATUS:
            errors.append(f"{p}.status is invalid")

    roots = report.get("root_causes", [])
    if not isinstance(roots, list):
        errors.append("root_causes must be a list")
        roots = []
    root_ids: set[str] = set()
    for i, row in enumerate(roots):
        p = f"root_causes[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{p} must be an object")
            continue
        rid = row.get("id")
        if not _text(rid):
            errors.append(f"{p}.id is required")
        elif rid in root_ids:
            errors.append(f"{p}.id must be unique")
        else:
            root_ids.add(rid)
        for key in ("label", "summary"):
            if not _text(row.get(key)):
                errors.append(f"{p}.{key} is required")
        refs = row.get("invariant_refs", [])
        if not isinstance(refs, list):
            errors.append(f"{p}.invariant_refs must be a list")
        else:
            for ref in refs:
                if ref not in invariant_ids:
                    errors.append(f"{p}.invariant_refs contains unknown invariant id {ref!r}")

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
        if finding.get("defect_class") not in DEFECT:
            errors.append(f"{p}.defect_class is invalid")
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
        if state == "NOT_FOUND":
            if at != "absence":
                errors.append(f"{p}: NOT_FOUND requires absence anchor")
            proof = finding.get("absence_proof")
            if not isinstance(proof, dict):
                errors.append(f"{p}.absence_proof is required for NOT_FOUND")
            else:
                if not _slist(proof.get("searched_scope"), True):
                    errors.append(f"{p}.absence_proof.searched_scope must be a non-empty string list")
                if not _slist(proof.get("queries_or_locations"), True):
                    errors.append(f"{p}.absence_proof.queries_or_locations must be a non-empty string list")
                if not _text(proof.get("sufficiency_basis")):
                    errors.append(f"{p}.absence_proof.sufficiency_basis is required")
        if state == "INFERRED" and not _text(finding.get("inference_basis")):
            errors.append(f"{p}.inference_basis is required for INFERRED")

        inv_refs = finding.get("invariant_refs")
        if not isinstance(inv_refs, list):
            errors.append(f"{p}.invariant_refs must be a list")
            inv_refs = []
        for ref in inv_refs:
            if ref not in invariant_ids:
                errors.append(f"{p}.invariant_refs contains unknown invariant id {ref!r}")
        surface_refs = finding.get("surface_refs", [])
        if not isinstance(surface_refs, list):
            errors.append(f"{p}.surface_refs must be a list")
            surface_refs = []
        for ref in surface_refs:
            if ref not in surface_ids:
                errors.append(f"{p}.surface_refs contains unknown critical surface id {ref!r}")
        critical_path = finding.get("critical_path_ref")
        if critical_path is not None and critical_path not in critical_paths:
            errors.append(f"{p}.critical_path_ref references unknown critical path")
        root_id = finding.get("root_cause_id")
        if root_id is not None and root_id not in root_ids:
            errors.append(f"{p}.root_cause_id references unknown root cause")

        materiality = _materiality(finding.get("materiality"), f"{p}.materiality", errors)
        for key_name in ("observation", "failure_mode", "engineering_risk", "blast_radius", "repair"):
            if not _text(finding.get(key_name)):
                errors.append(f"{p}.{key_name} is required")
        if finding.get("blast_radius_class") not in BLAST_CLASS:
            errors.append(f"{p}.blast_radius_class is invalid")
        if finding.get("failure_containment") not in CONTAINMENT:
            errors.append(f"{p}.failure_containment is invalid")
        reachability = finding.get("reachability")
        if reachability not in REACH:
            errors.append(f"{p}.reachability is invalid")
        execution_path = finding.get("execution_path")
        if not isinstance(execution_path, list):
            errors.append(f"{p}.execution_path must be a list")
            execution_path = []
        if finding.get("fix_scope") not in FIX_SCOPE:
            errors.append(f"{p}.fix_scope is invalid")
        _verification(finding.get("verification"), f"{p}.verification", errors)

        falsifier_obj = finding.get("falsifier_check")
        if severity in {"CRITICAL", "MAJOR"} or falsifier_obj is not None:
            result = _falsifier(falsifier_obj, f"{p}.falsifier_check", errors)
            if result == "WITHDRAWN":
                errors.append(f"{p}: withdrawn finding must not remain in findings")
            if result == "UNRESOLVED" and confidence == "high":
                errors.append(f"{p}: unresolved falsifier cannot have high confidence")
            if result == "DOWNGRADED":
                prior = finding.get("falsifier_check", {}).get("downgraded_from")
                if prior not in SEVERITY_RANK or severity not in SEVERITY_RANK or SEVERITY_RANK[prior] <= SEVERITY_RANK[severity]:
                    errors.append(f"{p}: DOWNGRADED requires falsifier_check.downgraded_from above final severity")

        if severity == "CRITICAL":
            if reachability not in {"PROVEN", "PLAUSIBLE"}:
                errors.append(f"{p}: CRITICAL requires PROVEN or PLAUSIBLE reachability")
            if not execution_path:
                errors.append(f"{p}: CRITICAL requires non-empty execution_path")
            if confidence == "low":
                errors.append(f"{p}: CRITICAL cannot have low confidence")
            if not inv_refs and critical_path is None and not surface_refs:
                errors.append(f"{p}: CRITICAL requires invariant_refs, critical_path_ref, or surface_refs")
            if finding.get("blast_radius_class") == "UNKNOWN":
                errors.append(f"{p}: CRITICAL cannot have UNKNOWN blast_radius_class")
            if strength == "WEAK":
                errors.append(f"{p}: CRITICAL cannot use WEAK evidence_strength")
            if scope_sensitivity == "HIGH":
                errors.append(f"{p}: CRITICAL cannot use HIGH scope_sensitivity")
            if materiality.get("centrality") != "CENTRAL":
                errors.append(f"{p}: CRITICAL requires materiality.centrality=CENTRAL")
            if materiality.get("consequence") != "HIGH":
                errors.append(f"{p}: CRITICAL requires materiality.consequence=HIGH")

        combined = " ".join(str(finding.get(k, "")) for k in ("observation", "failure_mode", "roast_line", "engineering_risk", "repair"))
        if PERSONAL_ATTACK.search(combined):
            errors.append(f"{p} contains a personal attack on a developer/engineer")

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
    if mode == "RECHECK" and "resolution_ledger" not in report:
        errors.append("RECHECK mode requires resolution_ledger")

    gaps = report.get("verification_gaps")
    if not isinstance(gaps, list):
        errors.append("verification_gaps must be a list")
    else:
        for i, gap in enumerate(gaps):
            p = f"verification_gaps[{i}]"
            if not isinstance(gap, dict):
                errors.append(f"{p} must be an object")
                continue
            for key in ("id", "question", "evidence_needed", "why_it_matters"):
                if not _text(gap.get(key)):
                    errors.append(f"{p}.{key} is required")

    if not isinstance(report.get("preserve"), list):
        errors.append("preserve must be a list")
    if not _text(report.get("core_fix")):
        errors.append("core_fix must be a non-empty string")
    return errors


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args in (['--help'], ['-h']):
        print("usage: validate_repo_roast.py report.json")
        return 0
    if len(args) != 1:
        print("usage: validate_repo_roast.py report.json", file=sys.stderr)
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
    print("OK: repo roast report v6")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
