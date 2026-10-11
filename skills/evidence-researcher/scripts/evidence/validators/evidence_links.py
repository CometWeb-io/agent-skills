"""Evidence edge and search-link validators."""
from __future__ import annotations

from typing import Any, Dict

from ..constants import (
    ADMISSION_STATUSES,
    DIRECTIONS,
    FALSIFIER_PURPOSES,
    FIT_LEVELS,
    KNOWLEDGE_BASES,
    MEASUREMENT_LEVELS,
    SEARCH_LANES,
    SEARCH_PURPOSES,
)
from ..util import _member, _parse_dt
from .context import LedgerValidationState


def validate(ledger: Dict[str, Any], state: LedgerValidationState) -> None:
    errors = state.errors
    warnings = state.warnings
    claim_ids = state.claim_ids
    source_ids = state.source_ids
    evidence = state.evidence
    searches = state.searches
    claims = state.claims
    contract = state.contract

    accepted_support_by_claim: Dict[str, list] = {}
    accepted_contradict_by_claim: Dict[str, list] = {}
    for i, edge in enumerate(evidence):
        if not isinstance(edge, dict):
            continue
        eid = edge.get("evidence_id") or f"evidence[{i}]"
        cid = edge.get("claim_id")
        sid = edge.get("source_id")
        if not _member(cid, claim_ids):
            errors.append(f"{eid} references unknown claim_id {cid}")
        if not _member(sid, source_ids):
            errors.append(f"{eid} references unknown source_id {sid}")
        if not _member(edge.get("direction"), DIRECTIONS):
            errors.append(f"{eid}.direction is invalid")
        if not _member(edge.get("admission"), ADMISSION_STATUSES):
            errors.append(f"{eid}.admission is invalid")
        if not _member(edge.get("authority_fit"), FIT_LEVELS):
            errors.append(f"{eid}.authority_fit is invalid")
        if not _member(edge.get("directness"), FIT_LEVELS):
            errors.append(f"{eid}.directness is invalid")
        if not _member(edge.get("scope_fit"), FIT_LEVELS):
            errors.append(f"{eid}.scope_fit is invalid")
        if not _member(edge.get("measurement_quality"), MEASUREMENT_LEVELS):
            errors.append(f"{eid}.measurement_quality is invalid")
        if "basis" in edge and not _member(edge["basis"], KNOWLEDGE_BASES):
            errors.append(f"{eid}.basis is invalid")
        if edge.get("direction") == "CONTEXT" and edge.get("admission") == "ACCEPTED":
            errors.append(f"{eid} is CONTEXT but marked ACCEPTED; use CONTEXT_ONLY")
        if edge.get("admission") == "CONTEXT_ONLY" and edge.get("direction") != "CONTEXT":
            warnings.append(f"{eid} is CONTEXT_ONLY but direction is not CONTEXT")
        if edge.get("admission") == "ACCEPTED" and not edge.get("locator"):
            warnings.append(f"{eid} is ACCEPTED without a pinpoint locator")
        if edge.get("admission") == "ACCEPTED" and _member(edge.get("direction"), {"SUPPORT", "CONTRADICT"}):
            if edge.get("authority_fit") == "unknown" or edge.get("directness") == "unknown":
                warnings.append(f"{eid} accepted without explicit authority/directness assessment")
        if edge.get("admission") == "ACCEPTED" and _member(cid, claim_ids):
            if edge.get("direction") == "SUPPORT":
                accepted_support_by_claim.setdefault(str(cid), []).append(edge)
            elif edge.get("direction") == "CONTRADICT":
                accepted_contradict_by_claim.setdefault(str(cid), []).append(edge)

    state.accepted_support_by_claim = accepted_support_by_claim
    state.accepted_contradict_by_claim = accepted_contradict_by_claim

    completed_falsifier_claims: set[str] = set()
    for i, search in enumerate(searches):
        if not isinstance(search, dict):
            continue
        sid = search.get("search_id") or f"searches[{i}]"
        cid = search.get("claim_id")
        if not _member(cid, claim_ids):
            errors.append(f"{sid} references unknown claim_id {cid}")
        if not _member(search.get("purpose"), SEARCH_PURPOSES):
            errors.append(f"{sid}.purpose is invalid")
        if not _member(search.get("source_lane"), SEARCH_LANES):
            errors.append(f"{sid}.source_lane is invalid")
        if not isinstance(search.get("completed"), bool):
            errors.append(f"{sid}.completed must be boolean")
        result_ids = search.get("result_source_ids", [])
        if not isinstance(result_ids, list):
            errors.append(f"{sid}.result_source_ids must be a list")
            result_ids = []
        for source_id in result_ids:
            if not _member(source_id, source_ids):
                errors.append(f"{sid} references unknown result source_id {source_id}")
        if search.get("purpose") == "ABSENCE_TEST":
            basis = search.get("absence_basis")
            if not isinstance(basis, dict) or not basis.get("expected_location") or not basis.get("detection_logic") or not basis.get("coverage_limitations"):
                errors.append(f"{sid} ABSENCE_TEST requires expected_location, detection_logic, and coverage_limitations")
        if _member(contract.get("privacy_lane"), {"PRIVATE", "USER_SUPPLIED"}) and search.get("source_lane") == "PUBLIC":
            if search.get("sanitized_for_external") is not True:
                errors.append(f"{sid} public search from a non-public research lane must set sanitized_for_external=true")
        if search.get("completed") is True and _member(search.get("purpose"), FALSIFIER_PURPOSES) and _member(cid, claim_ids):
            done_at = _parse_dt(search.get("completed_at"))
            as_of = _parse_dt(contract.get("as_of"))
            if not isinstance(search.get("query_summary"), str) or not search["query_summary"].strip() or done_at is None or as_of is None or done_at > as_of:
                errors.append(f"{sid} completed falsifier requires query_summary and admissible completed_at")
                continue
            completed_falsifier_claims.add(str(cid))

    state.completed_falsifier_claims = completed_falsifier_claims

    for claim in claims:
        if not isinstance(claim, dict):
            continue
        cid = str(claim.get("claim_id") or "")
        if _member(claim.get("materiality"), {"critical", "material"}):
            if claim.get("contradiction_tested") and cid not in completed_falsifier_claims:
                errors.append(f"{cid} says contradiction_tested=true without a completed falsifier search record")
            if not claim.get("contradiction_tested"):
                warnings.append(f"{cid} has no contradiction search coverage")
        if claim.get("epistemic_kind") == "FACT" and claim.get("status") == "VERIFIED" and _member(claim.get("materiality"), {"critical", "material"}):
            if not accepted_support_by_claim.get(cid):
                errors.append(f"{cid} is VERIFIED without ACCEPTED SUPPORT evidence")
