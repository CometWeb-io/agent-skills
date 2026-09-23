"""Evidence admissibility and claim scoring."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

from .constants import (
    CLAIM_LANES,
    CLAIM_TYPES,
    CURRENT_ADMISSIBLE,
    FRESHNESS,
    DIRECTIONS,
    DIRECTNESS,
    LANE_MULTIPLIERS,
    MATERIALITIES,
    SCOPE_MATCH,
    SOURCE_BASE,
    VERIFICATION_SOURCES,
)
from .util import (
    clamp,
    freshness_value,
    normalized,
    normalized_lower,
    normalized_upper,
    require_choice,
    default_claim_type,
)


def evidence_row_strength(row: Dict[str, Any], lane: str, current_sensitive: bool) -> Tuple[float, bool, str | None, Dict[str, Any]]:
    source_type = normalized_lower(row.get("source_type", ""))
    if source_type not in SOURCE_BASE:
        raise ValueError(f"unknown source_type: {source_type or '<missing>'}")
    if source_type not in LANE_MULTIPLIERS.get(lane, {}):
        lane_multiplier = 0.45
    else:
        lane_multiplier = LANE_MULTIPLIERS[lane][source_type]

    directness = require_choice(row.get("directness", "supporting"), "directness", set(DIRECTNESS), case="lower")
    scope = require_choice(row.get("scope_match", "partial"), "scope_match", set(SCOPE_MATCH), case="lower")
    direction = require_choice(row.get("direction", "support"), "direction", DIRECTIONS, case="lower")
    freshness = freshness_value(row.get("freshness", "UNKNOWN"))

    admissible = True
    reason = None
    if freshness == "SUPERSEDED":
        admissible = False
        reason = "superseded"
    elif current_sensitive and freshness not in CURRENT_ADMISSIBLE:
        admissible = False
        reason = f"current_sensitive_claim_rejects_{freshness.lower()}"

    strength = SOURCE_BASE[source_type] * lane_multiplier * DIRECTNESS[directness] * FRESHNESS[freshness] * SCOPE_MATCH[scope]
    strength = clamp(strength, 0.0, 0.99)

    clean = {
        "source_type": source_type,
        "directness": directness,
        "scope_match": scope,
        "direction": direction,
        "freshness": freshness,
    }
    return strength, admissible, reason, clean


def combine_independent(strengths: Iterable[float]) -> float:
    product = 1.0
    for strength in strengths:
        product *= 1.0 - clamp(float(strength), 0.0, 0.99)
    return clamp(1.0 - product, 0.0, 0.99)


def absence_protocol_complete(check: Any) -> bool:
    if not isinstance(check, dict):
        return False
    if normalized_upper(check.get("status", "")) != "ABSENCE_VERIFIED":
        return False
    if check.get("inventory_complete") is not True:
        return False
    scopes = check.get("scopes_checked")
    if not isinstance(scopes, list) or not scopes:
        return False
    for key in ("dynamic_registration_checked", "generated_or_config_driven_paths_checked"):
        value = check.get(key)
        if value not in (True, "NOT_APPLICABLE"):
            return False
    return True


def evidence_report(claim: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(claim, dict):
        raise ValueError("claim must be an object")
    lane = require_choice(claim.get("claim_lane", "implementation"), "claim_lane", CLAIM_LANES, case="lower")
    claim_type = require_choice(claim.get("claim_type", default_claim_type(lane)), "claim_type", CLAIM_TYPES, case="lower")
    materiality = require_choice(claim.get("materiality", "medium"), "materiality", MATERIALITIES, case="lower")
    current_sensitive = bool(claim.get("current_sensitive", False)) or claim_type == "external_current"
    evidence = claim.get("evidence", [])
    if not isinstance(evidence, list):
        raise ValueError("evidence must be a list")

    support_groups: Dict[str, float] = {}
    contradiction_groups: Dict[str, float] = {}
    verification_sources: set[str] = set()
    direct_support_seen = False
    non_inference_support_seen = False
    admissible_count = 0
    inadmissible_count = 0
    inadmissible_reasons: List[str] = []
    warnings: List[str] = []

    for index, row in enumerate(evidence):
        if not isinstance(row, dict):
            raise ValueError(f"evidence[{index}] must be an object")
        strength, admissible, reason, clean = evidence_row_strength(row, lane, current_sensitive)
        if not admissible:
            inadmissible_count += 1
            if reason:
                inadmissible_reasons.append(reason)
            continue
        if strength <= 0:
            continue
        admissible_count += 1
        source_type = clean["source_type"]
        direction = clean["direction"]
        key = normalized(row.get("independence_key") or "")
        if not key:
            key = f"unknown_independence:{source_type}"
            warnings.append(f"evidence[{index}] missing independence_key; grouped conservatively as {key}")
        if direction == "contradict":
            contradiction_groups[key] = max(contradiction_groups.get(key, 0.0), strength)
        else:
            support_groups[key] = max(support_groups.get(key, 0.0), strength)
            if clean["directness"] == "direct":
                direct_support_seen = True
            if source_type != "inference":
                non_inference_support_seen = True
            if source_type in VERIFICATION_SOURCES[claim_type] and clean["directness"] == "direct":
                verification_sources.add(source_type)

    support_strength = combine_independent(support_groups.values())
    contradiction_strength = combine_independent(contradiction_groups.values())

    if claim_type == "absence":
        complete_absence = absence_protocol_complete(claim.get("absence_check"))
        if not complete_absence:
            warnings.append("absence claim lacks a complete ABSENCE_VERIFIED protocol")
    else:
        complete_absence = None

    confidence = support_strength * (1.0 - 0.62 * contradiction_strength)
    status = "SUPPORTED"

    if not support_groups:
        confidence = 0.0
        status = "STALE_EVIDENCE" if inadmissible_count else "UNSUPPORTED"
    elif contradiction_strength >= 0.52:
        confidence = min(confidence, 0.49)
        status = "CONTESTED"
    elif not non_inference_support_seen:
        confidence = min(confidence, 0.44)
        status = "HYPOTHESIS"
    elif claim_type == "absence" and not complete_absence:
        confidence = min(confidence, 0.44)
        status = "INSUFFICIENT_VERIFICATION"
    elif not verification_sources:
        cap = 0.68 if claim_type in {"behavior", "release", "outcome", "operational", "external_current"} else 0.82
        confidence = min(confidence, cap)
        if claim_type in {"behavior", "release", "outcome", "operational", "external_current"}:
            status = "INSUFFICIENT_VERIFICATION"
    elif not direct_support_seen:
        confidence = min(confidence, 0.82)

    verification_requirements_met = bool(verification_sources)
    if claim_type == "absence":
        verification_requirements_met = bool(verification_sources) and bool(complete_absence)

    if confidence >= 0.85 and status == "SUPPORTED" and verification_requirements_met:
        band = "VERIFIED"
    elif confidence >= 0.70 and status == "SUPPORTED":
        band = "STRONG"
    elif confidence >= 0.50:
        band = "MODERATE"
    elif confidence >= 0.30:
        band = "WEAK"
    else:
        band = "HYPOTHESIS"

    return {
        "claim_id": claim.get("claim_id"),
        "claim_lane": lane,
        "claim_type": claim_type,
        "materiality": materiality,
        "current_sensitive": current_sensitive,
        "status": status,
        "heuristic_confidence": round(confidence, 3),
        "confidence_band": band,
        "support_strength": round(support_strength, 3),
        "contradiction_strength": round(contradiction_strength, 3),
        "verification_requirements_met": verification_requirements_met,
        "verification_sources": sorted(verification_sources),
        "independent_support_groups": len(support_groups),
        "independent_contradiction_groups": len(contradiction_groups),
        "admissible_evidence_count": admissible_count,
        "inadmissible_evidence_count": inadmissible_count,
        "inadmissible_reasons": sorted(set(inadmissible_reasons)),
        "absence_protocol_complete": complete_absence,
        "warnings": sorted(set(warnings)),
        "note": "Heuristic confidence is a deterministic decision aid, not a calibrated probability.",
    }

