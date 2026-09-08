#!/usr/bin/env python3
"""Deterministic validation helpers for repo-to-roadmap v2.

The kernel never discovers roadmap work and never replaces project judgment. It
validates evidence admissibility, applies bounded priority/gate rules, checks
coverage and dependency graphs, creates immutable snapshot hashes, computes
baseline/delta invalidation, and validates the machine-readable roadmap payload.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from collections import defaultdict, deque
from typing import Any, Dict, Iterable, List, Tuple

SCHEMA_VERSION = "2.0"

SOURCE_BASE = {
    "inventory": 0.94,
    "test": 0.95,
    "ci": 0.94,
    "runtime": 0.96,
    "analytics": 0.94,
    "incident": 0.92,
    "code": 0.90,
    "config": 0.88,
    "migration": 0.88,
    "deployment": 0.94,
    "release": 0.94,
    "external_primary": 0.95,
    "vendor_official": 0.94,
    "approved_decision": 0.94,
    "user_requirement": 0.92,
    "product_context": 0.86,
    "customer_research": 0.86,
    "support": 0.80,
    "experiment": 0.88,
    "pr": 0.74,
    "commit": 0.70,
    "issue": 0.66,
    "documentation": 0.60,
    "external_secondary": 0.60,
    "inference": 0.22,
}

LANE_MULTIPLIERS = {
    "implementation": {
        "inventory": 1.00,
        "test": 1.00,
        "ci": 0.98,
        "runtime": 1.00,
        "code": 1.00,
        "config": 1.00,
        "migration": 1.00,
        "deployment": 0.95,
        "release": 0.90,
        "pr": 0.82,
        "commit": 0.80,
        "issue": 0.62,
        "documentation": 0.62,
        "user_requirement": 0.38,
        "product_context": 0.40,
        "analytics": 0.55,
        "incident": 0.65,
        "inference": 0.45,
    },
    "intent": {
        "user_requirement": 1.00,
        "approved_decision": 1.00,
        "product_context": 1.00,
        "documentation": 0.90,
        "issue": 0.76,
        "pr": 0.62,
        "code": 0.40,
        "analytics": 0.40,
        "inference": 0.45,
    },
    "outcome": {
        "analytics": 1.00,
        "runtime": 0.92,
        "customer_research": 1.00,
        "support": 0.92,
        "incident": 0.95,
        "experiment": 1.00,
        "issue": 0.62,
        "code": 0.30,
        "test": 0.38,
        "documentation": 0.48,
        "inference": 0.42,
    },
    "operational": {
        "ci": 1.00,
        "runtime": 1.00,
        "incident": 1.00,
        "deployment": 1.00,
        "release": 0.95,
        "config": 0.92,
        "test": 0.78,
        "code": 0.78,
        "issue": 0.64,
        "documentation": 0.58,
        "inference": 0.40,
    },
    "external": {
        "external_primary": 1.00,
        "vendor_official": 1.00,
        "external_secondary": 0.78,
        "documentation": 0.55,
        "inference": 0.35,
    },
}

DIRECTNESS = {"direct": 1.00, "supporting": 0.76, "inferred": 0.42}
FRESHNESS = {
    "CURRENT": 1.00,
    "NEAR_EXPIRY": 0.90,
    "NOT_TIME_SENSITIVE": 1.00,
    "STALE": 0.30,
    "SUPERSEDED": 0.00,
    "UNKNOWN": 0.45,
}
CURRENT_ADMISSIBLE = {"CURRENT", "NEAR_EXPIRY"}
SCOPE_MATCH = {"exact": 1.00, "partial": 0.72, "weak": 0.42}
DIRECTIONS = {"support", "contradict"}
CLAIM_LANES = set(LANE_MULTIPLIERS)
CLAIM_TYPES = {
    "presence",
    "behavior",
    "release",
    "outcome",
    "intent",
    "operational",
    "external_current",
    "absence",
}
MATERIALITIES = {"low", "medium", "high", "critical"}

VERIFICATION_SOURCES = {
    "presence": {"inventory", "code", "config", "migration", "test", "ci", "runtime"},
    "behavior": {"test", "ci", "runtime", "experiment"},
    "release": {"deployment", "release", "runtime", "ci"},
    "outcome": {"analytics", "runtime", "customer_research", "support", "incident", "experiment"},
    "intent": {"user_requirement", "approved_decision", "product_context", "documentation"},
    "operational": {"ci", "runtime", "incident", "deployment", "release"},
    "external_current": {"external_primary", "vendor_official"},
    "absence": {"inventory", "code", "config"},
}

COVERAGE_FACTORS = {
    "COMPLETE": 1.00,
    "PARTIAL": 0.72,
    "SAMPLED": 0.42,
    "UNAVAILABLE": 0.00,
    "NOT_APPLICABLE": None,
}

EFFORT_FACTORS = {"XS": 1.00, "S": 1.35, "M": 1.90, "L": 2.70, "XL": 3.80}
EFFORT_ORDER = ["XS", "S", "M", "L", "XL"]
VALID_LANES = {"BLOCKER", "VERIFY_NOW", "NOW", "NEXT", "LATER", "PARK", "VALIDATE"}
LANE_ORDER = {"BLOCKER": 0, "VERIFY_NOW": 1, "NOW": 2, "VALIDATE": 3, "NEXT": 4, "LATER": 5, "PARK": 6}
ITEM_KINDS = {"BUILD", "FIX", "HARDEN", "VERIFY", "VALIDATE", "INSTRUMENT", "MIGRATE", "RETIRE", "DOCUMENT", "DECIDE"}
GATE_TYPES = {"release", "security", "privacy", "data_integrity", "legal", "core_flow"}
GATE_STATUSES = {"NOT_REQUIRED", "UNVERIFIED", "CLEAR", "CLEAR_WITH_CONTROLS", "BLOCK"}
CAPABILITY_STATES = {
    "VERIFIED_WORKING",
    "IMPLEMENTED_UNVERIFIED",
    "PARTIAL",
    "STUBBED",
    "BROKEN",
    "MISSING",
    "UNKNOWN",
    "NOT_APPLICABLE",
}
TARGET_PROFILES = {"PROTOTYPE", "INTERNAL_BETA", "PUBLIC_BETA", "CLIENT_READY", "PAID_PRODUCTION", "SCALE_READY", "CUSTOM"}
TARGET_APPLICABILITY = {"APPLIES", "NOT_APPLICABLE", "UNKNOWN"}


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def require_score(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field} must be numeric")
    if not 0 <= number <= 5:
        raise ValueError(f"{field} must be between 0 and 5")
    return number


def require_probability_like(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field} must be numeric")
    if not 0 <= number <= 1:
        raise ValueError(f"{field} must be between 0 and 1")
    return number


def normalized(value: Any) -> str:
    return str(value).strip()


def normalized_lower(value: Any) -> str:
    return normalized(value).lower()


def normalized_upper(value: Any) -> str:
    return normalized(value).upper()


def require_choice(value: Any, field: str, choices: set[str], case: str = "lower") -> str:
    if case == "upper":
        clean = normalized_upper(value)
    else:
        clean = normalized_lower(value)
    if clean not in choices:
        allowed = ", ".join(sorted(choices))
        raise ValueError(f"{field} must be one of: {allowed}")
    return clean


def default_claim_type(lane: str) -> str:
    return {
        "implementation": "presence",
        "intent": "intent",
        "outcome": "outcome",
        "operational": "operational",
        "external": "external_current",
    }[lane]


def freshness_value(value: Any) -> str:
    raw = normalized(value or "UNKNOWN")
    aliases = {
        "current": "CURRENT",
        "recent": "CURRENT",
        "near_expiry": "NEAR_EXPIRY",
        "near-expiry": "NEAR_EXPIRY",
        "not_time_sensitive": "NOT_TIME_SENSITIVE",
        "not-time-sensitive": "NOT_TIME_SENSITIVE",
        "dated": "STALE",
        "stale": "STALE",
        "superseded": "SUPERSEDED",
        "unknown": "UNKNOWN",
    }
    clean = aliases.get(raw.lower(), raw.upper())
    if clean not in FRESHNESS:
        raise ValueError(f"freshness must be one of: {', '.join(sorted(FRESHNESS))}")
    return clean


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


def priority_inputs(item: Dict[str, Any]) -> Tuple[Dict[str, float], float, float, str]:
    fields = {
        "impact": require_score(item.get("impact", 0), "impact"),
        "urgency": require_score(item.get("urgency", 0), "urgency"),
        "risk_reduction": require_score(item.get("risk_reduction", 0), "risk_reduction"),
        "strategic_alignment": require_score(item.get("strategic_alignment", 0), "strategic_alignment"),
        "enablement": require_score(item.get("enablement", 0), "enablement"),
        "reach": require_score(item.get("reach", 0), "reach"),
    }
    uncertainty = require_score(item.get("uncertainty", 2.5), "uncertainty")
    confidence = require_probability_like(item.get("evidence_confidence", 0.5), "evidence_confidence")
    effort = normalized_upper(item.get("effort", "M"))
    if effort not in EFFORT_FACTORS:
        raise ValueError("effort must be one of XS, S, M, L, XL")
    return fields, uncertainty, confidence, effort


def priority_report(item: Dict[str, Any]) -> Dict[str, Any]:
    fields, uncertainty, confidence, effort = priority_inputs(item)
    kind = normalized_upper(item.get("kind", "BUILD"))
    if kind not in ITEM_KINDS:
        raise ValueError(f"kind must be one of: {', '.join(sorted(ITEM_KINDS))}")

    weighted_parts = {
        "impact": 0.24 * fields["impact"],
        "urgency": 0.16 * fields["urgency"],
        "risk_reduction": 0.16 * fields["risk_reduction"],
        "strategic_alignment": 0.16 * fields["strategic_alignment"],
        "enablement": 0.18 * fields["enablement"],
        "reach": 0.10 * fields["reach"],
    }
    value = sum(weighted_parts.values())
    evidence_factor = 0.30 + 0.70 * confidence
    uncertainty_factor = 1.0 - 0.055 * uncertainty
    raw_score = 20.0 * value * evidence_factor * uncertainty_factor / EFFORT_FACTORS[effort]
    score = round(clamp(raw_score, 0.0, 100.0), 1)

    gate_raw = item.get("mandatory_gate")
    gate = normalized_lower(gate_raw) if gate_raw not in (None, "", "none") else None
    if gate is not None and gate not in GATE_TYPES:
        raise ValueError(f"mandatory_gate must be one of: {', '.join(sorted(GATE_TYPES))}")
    gate_status = normalized_upper(item.get("gate_status", "UNVERIFIED" if gate else "NOT_REQUIRED"))
    if gate_status not in GATE_STATUSES:
        raise ValueError(f"gate_status must be one of: {', '.join(sorted(GATE_STATUSES))}")
    severity = normalized_lower(item.get("severity", "medium"))
    if severity not in MATERIALITIES:
        raise ValueError("severity must be low, medium, high, or critical")

    target_blocker = bool(item.get("target_blocker", False))
    lane_reason = "heuristic_score"

    if gate and gate_status == "BLOCK":
        lane = "BLOCKER"
        lane_reason = f"binding_{gate}_gate_block"
    elif gate and gate_status == "UNVERIFIED":
        lane = "VERIFY_NOW"
        lane_reason = f"binding_{gate}_gate_unverified"
    elif target_blocker and confidence >= 0.70:
        lane = "BLOCKER"
        lane_reason = "strongly_evidenced_target_blocker"
    elif target_blocker and confidence < 0.70:
        lane = "VERIFY_NOW"
        lane_reason = "suspected_target_blocker_needs_verification"
    elif kind == "VALIDATE" and confidence < 0.60:
        lane = "VALIDATE"
        lane_reason = "outcome_or_problem_validation_needed"
    elif kind == "VERIFY" and confidence < 0.60 and score >= 25:
        lane = "VERIFY_NOW"
        lane_reason = "material_technical_truth_needs_verification"
    elif confidence < 0.45 and score >= 35:
        lane = "VALIDATE"
        lane_reason = "priority_sensitive_to_weak_evidence"
    elif score >= 60:
        lane = "NOW"
    elif score >= 40:
        lane = "NEXT"
    elif score >= 20:
        lane = "LATER"
    else:
        lane = "PARK"

    drivers = sorted(weighted_parts.items(), key=lambda row: (-row[1], row[0]))
    return {
        "id": item.get("id"),
        "priority_score": score,
        "lane": lane,
        "lane_reason": lane_reason,
        "value_score_0_5": round(value, 2),
        "evidence_confidence": round(confidence, 3),
        "effort": effort,
        "kind": kind,
        "mandatory_gate": gate,
        "gate_status": gate_status,
        "severity": severity,
        "target_blocker": target_blocker,
        "top_score_drivers": [name for name, _ in drivers[:3]],
        "note": "Use score only as a tie-breaker inside a lane. Gates, target blockers, and hard dependencies outrank it.",
    }


def sensitivity_report(item: Dict[str, Any]) -> Dict[str, Any]:
    base = priority_report(item)
    scenarios: List[Tuple[str, Dict[str, Any]]] = []
    score_fields = ["impact", "urgency", "risk_reduction", "strategic_alignment", "enablement", "reach", "uncertainty"]

    for field in score_fields:
        base_value = require_score(item.get(field, 2.5 if field == "uncertainty" else 0), field)
        for delta in (-1, 1):
            variant = copy.deepcopy(item)
            variant[field] = clamp(base_value + delta, 0.0, 5.0)
            scenarios.append((f"{field}:{delta:+d}", variant))

    confidence = require_probability_like(item.get("evidence_confidence", 0.5), "evidence_confidence")
    for delta in (-0.15, 0.15):
        variant = copy.deepcopy(item)
        variant["evidence_confidence"] = clamp(confidence + delta, 0.0, 1.0)
        scenarios.append((f"evidence_confidence:{delta:+.2f}", variant))

    effort = normalized_upper(item.get("effort", "M"))
    if effort not in EFFORT_FACTORS:
        raise ValueError("invalid effort")
    effort_index = EFFORT_ORDER.index(effort)
    for index in (effort_index - 1, effort_index + 1):
        if 0 <= index < len(EFFORT_ORDER):
            variant = copy.deepcopy(item)
            variant["effort"] = EFFORT_ORDER[index]
            scenarios.append((f"effort:{EFFORT_ORDER[index]}", variant))

    lane_changes: List[Dict[str, Any]] = []
    lanes = {base["lane"]}
    for label, variant in scenarios:
        report = priority_report(variant)
        lanes.add(report["lane"])
        if report["lane"] != base["lane"]:
            lane_changes.append({"scenario": label, "lane": report["lane"], "score": report["priority_score"]})

    if len(lanes) == 1:
        stability = "STABLE"
    else:
        base_rank = LANE_ORDER.get(base["lane"], 99)
        max_distance = max(abs(LANE_ORDER.get(lane, 99) - base_rank) for lane in lanes)
        stability = "SENSITIVE" if max_distance <= 1 and len(lanes) <= 2 else "FRAGILE"

    return {
        "id": item.get("id"),
        "base_lane": base["lane"],
        "base_score": base["priority_score"],
        "stability": stability,
        "lanes_seen": sorted(lanes, key=lambda lane: LANE_ORDER.get(lane, 99)),
        "lane_flip_scenarios": lane_changes,
        "note": "Sensitivity perturbs heuristic inputs. It does not test unknown strategic alternatives or hidden dependencies.",
    }


def graph_report(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    ids = [normalized(item.get("id")) for item in items if item.get("id") is not None]
    duplicate_ids = sorted({item_id for item_id in ids if ids.count(item_id) > 1})
    id_set = set(ids)
    deps: Dict[str, List[str]] = {}
    missing: Dict[str, List[str]] = {}

    for item in items:
        if item.get("id") is None:
            continue
        item_id = normalized(item["id"])
        raw_deps = item.get("depends_on", []) or []
        if not isinstance(raw_deps, list):
            raise ValueError(f"depends_on for {item_id} must be a list")
        parsed = [normalized(dep) for dep in raw_deps]
        deps[item_id] = [dep for dep in parsed if dep in id_set]
        absent = [dep for dep in parsed if dep not in id_set]
        if absent:
            missing[item_id] = sorted(set(absent))

    indegree = {item_id: 0 for item_id in id_set}
    outgoing: Dict[str, List[str]] = defaultdict(list)
    for item_id, item_deps in deps.items():
        for dep in item_deps:
            outgoing[dep].append(item_id)
            indegree[item_id] += 1

    queue = deque(sorted([item_id for item_id, degree in indegree.items() if degree == 0]))
    order: List[str] = []
    wave_index: Dict[str, int] = {item_id: 0 for item_id in queue}
    longest_chain: Dict[str, List[str]] = {item_id: [item_id] for item_id in queue}

    while queue:
        node = queue.popleft()
        order.append(node)
        for child in sorted(outgoing[node]):
            candidate_chain = longest_chain.get(node, [node]) + [child]
            if len(candidate_chain) > len(longest_chain.get(child, [])):
                longest_chain[child] = candidate_chain
            wave_index[child] = max(wave_index.get(child, 0), wave_index.get(node, 0) + 1)
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)

    cycle_nodes = sorted([item_id for item_id, degree in indegree.items() if degree > 0])
    waves: Dict[int, List[str]] = defaultdict(list)
    if not cycle_nodes:
        for node in order:
            waves[wave_index.get(node, 0)].append(node)

    transitive_unblocks: Dict[str, int] = {}
    for node in id_set:
        seen: set[str] = set()
        stack = list(outgoing[node])
        while stack:
            child = stack.pop()
            if child in seen:
                continue
            seen.add(child)
            stack.extend(outgoing[child])
        transitive_unblocks[node] = len(seen)

    leverage = sorted(
        ({"id": node, "direct_unblocks": len(outgoing[node]), "transitive_unblocks": transitive_unblocks[node]} for node in id_set),
        key=lambda row: (-row["transitive_unblocks"], -row["direct_unblocks"], row["id"]),
    )
    critical_chain = max(longest_chain.values(), key=lambda chain: (len(chain), chain)) if longest_chain and not cycle_nodes else []

    return {
        "duplicate_ids": duplicate_ids,
        "missing_dependencies": missing,
        "cycle_nodes": cycle_nodes,
        "topological_order": order if not cycle_nodes else [],
        "waves": [{"wave": index, "items": waves[index]} for index in sorted(waves)] if not cycle_nodes else [],
        "dependency_leverage": leverage[:10],
        "critical_chain_by_hard_dependency_count": critical_chain,
        "valid": not duplicate_ids and not missing and not cycle_nodes,
        "note": "Critical chain is structural only; it is not a calendar critical path unless duration/capacity evidence exists.",
    }


def coverage_report(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(rows, list):
        raise ValueError("coverage must be a list")
    numerator = 0.0
    denominator = 0.0
    incomplete_mandatory: List[str] = []
    sampled: List[str] = []
    unavailable: List[str] = []
    errors: List[str] = []
    names: List[str] = []

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"coverage[{index}] must be an object")
        name = normalized(row.get("name", f"domain-{index}"))
        names.append(name)
        status = normalized_upper(row.get("status", "UNAVAILABLE"))
        if status not in COVERAGE_FACTORS:
            raise ValueError(f"invalid coverage status for {name}: {status}")
        factor = COVERAGE_FACTORS[status]
        if status == "NOT_APPLICABLE":
            if not normalized(row.get("not_applicable_reason", "")):
                errors.append(f"{name}: NOT_APPLICABLE requires not_applicable_reason")
            continue
        try:
            weight = clamp(float(row.get("weight", 1.0)), 0.0, 10.0)
        except (TypeError, ValueError):
            raise ValueError(f"coverage weight for {name} must be numeric")
        denominator += weight
        numerator += weight * float(factor)
        if row.get("mandatory") and status != "COMPLETE":
            incomplete_mandatory.append(name)
        if status == "SAMPLED":
            sampled.append(name)
        if status == "UNAVAILABLE":
            unavailable.append(name)

    duplicate_names = sorted({name for name in names if names.count(name) > 1})
    if duplicate_names:
        errors.append(f"duplicate coverage domains: {duplicate_names}")

    score = numerator / denominator if denominator else 0.0
    if score >= 0.90:
        grade = "A"
    elif score >= 0.80:
        grade = "B"
    elif score >= 0.65:
        grade = "C"
    elif score >= 0.50:
        grade = "D"
    else:
        grade = "E"

    if errors:
        scope_claim = "COVERAGE_INVALID"
    elif score >= 0.88 and not incomplete_mandatory:
        scope_claim = "WHOLE_PROJECT_SCOPE_DEFENSIBLE"
    elif score >= 0.65:
        scope_claim = "WHOLE_PROJECT_SCOPE_QUALIFIED"
    else:
        scope_claim = "WHOLE_PROJECT_SCOPE_NOT_DEFENSIBLE"

    return {
        "coverage_score": round(score, 3),
        "coverage_grade": grade,
        "scope_claim": scope_claim,
        "incomplete_mandatory_domains": sorted(set(incomplete_mandatory)),
        "sampled_domains": sorted(set(sampled)),
        "unavailable_domains": sorted(set(unavailable)),
        "errors": errors,
        "note": "Coverage grade is a disclosure aid. Whole-project scope never implies every source file was read unless exhaustive file accounting proves it.",
    }


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def snapshot_core(payload: Dict[str, Any]) -> Dict[str, Any]:
    core = copy.deepcopy(payload)
    for key in ("snapshot_hash", "snapshot_hash_short", "validation"):
        core.pop(key, None)
    return core


def snapshot_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("roadmap payload must be an object")
    core = snapshot_core(payload)
    encoded = stable_json(core).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    return {
        "schema_version": payload.get("schema_version", SCHEMA_VERSION),
        "snapshot_hash": f"sha256:{digest}",
        "snapshot_hash_short": digest[:16],
        "canonical_bytes": len(encoded),
    }


def by_id(rows: Any, field: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    if not isinstance(rows, list):
        return result
    for row in rows:
        if not isinstance(row, dict) or row.get(field) in (None, ""):
            continue
        result[normalized(row[field])] = row
    return result


def changed_ids(before_rows: Any, after_rows: Any, field: str) -> Tuple[List[str], List[str], List[str]]:
    before = by_id(before_rows, field)
    after = by_id(after_rows, field)
    all_ids = sorted(set(before) | set(after))
    changed = [item_id for item_id in all_ids if stable_json(before.get(item_id)) != stable_json(after.get(item_id))]
    removed = sorted(set(before) - set(after))
    added = sorted(set(after) - set(before))
    return changed, added, removed


def delta_report(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(before, dict) or not isinstance(after, dict):
        raise ValueError("before and after must be objects")

    changed_claims, added_claims, removed_claims = changed_ids(before.get("claims", []), after.get("claims", []), "claim_id")
    changed_capabilities, added_capabilities, removed_capabilities = changed_ids(before.get("capabilities", []), after.get("capabilities", []), "capability_id")
    changed_items, added_items, removed_items = changed_ids(before.get("items", []), after.get("items", []), "id")

    target_changed = stable_json(before.get("target_contract", {})) != stable_json(after.get("target_contract", {}))
    coverage_changed = stable_json(before.get("coverage", [])) != stable_json(after.get("coverage", []))
    assessment_scope_changed = stable_json(before.get("assessment", {}).get("repos", [])) != stable_json(after.get("assessment", {}).get("repos", []))

    after_items = by_id(after.get("items", []), "id")
    after_capabilities = by_id(after.get("capabilities", []), "capability_id")
    revalidate: set[str] = set(changed_items)
    changed_claim_set = set(changed_claims)
    changed_cap_set = set(changed_capabilities)

    # A capability becomes suspect when any binding claim it references changed,
    # even when the capability row itself has not yet been updated.
    affected_capabilities = set(changed_cap_set)
    for cap_id, capability in after_capabilities.items():
        refs = {normalized(ref) for ref in (capability.get("claim_refs") or [])}
        if refs & changed_claim_set:
            affected_capabilities.add(cap_id)

    for item_id, item in after_items.items():
        refs = {normalized(ref) for ref in (item.get("problem_claim_refs") or [])}
        cap_refs = {normalized(ref) for ref in (item.get("capability_refs") or [])}
        if refs & changed_claim_set or cap_refs & affected_capabilities:
            revalidate.add(item_id)

    if target_changed or assessment_scope_changed:
        revalidate.update(after_items)

    outgoing: Dict[str, List[str]] = defaultdict(list)
    for item_id, item in after_items.items():
        for dep in item.get("depends_on", []) or []:
            dep_id = normalized(dep)
            if dep_id in after_items:
                outgoing[dep_id].append(item_id)

    queue = deque(sorted(revalidate))
    while queue:
        node = queue.popleft()
        for child in outgoing[node]:
            if child not in revalidate:
                revalidate.add(child)
                queue.append(child)

    source_fingerprints_before = sorted(
        normalized(row.get("fingerprint"))
        for claim in before.get("claims", []) if isinstance(claim, dict)
        for row in claim.get("evidence", []) if isinstance(row, dict) and row.get("fingerprint")
    )
    source_fingerprints_after = sorted(
        normalized(row.get("fingerprint"))
        for claim in after.get("claims", []) if isinstance(claim, dict)
        for row in claim.get("evidence", []) if isinstance(row, dict) and row.get("fingerprint")
    )
    fingerprints_changed = source_fingerprints_before != source_fingerprints_after

    validity = "REVALIDATE" if (revalidate or target_changed or coverage_changed or assessment_scope_changed or fingerprints_changed) else "VALID"

    return {
        "before_snapshot": snapshot_report(before)["snapshot_hash"],
        "after_snapshot": snapshot_report(after)["snapshot_hash"],
        "target_contract_changed": target_changed,
        "assessment_scope_changed": assessment_scope_changed,
        "coverage_changed": coverage_changed,
        "source_fingerprints_changed": fingerprints_changed,
        "changed_claim_ids": changed_claims,
        "added_claim_ids": added_claims,
        "removed_claim_ids": removed_claims,
        "changed_capability_ids": changed_capabilities,
        "affected_capability_ids": sorted(affected_capabilities),
        "added_capability_ids": added_capabilities,
        "removed_capability_ids": removed_capabilities,
        "changed_item_ids": changed_items,
        "added_item_ids": added_items,
        "removed_item_ids": removed_items,
        "revalidate_item_ids": sorted(revalidate),
        "roadmap_validity": validity,
        "note": "Revalidation propagates through hard item dependencies. It does not infer hidden runtime coupling that was never modeled.",
    }


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


def validate_roadmap(payload: Dict[str, Any]) -> Dict[str, Any]:
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

    target_errors, target_warnings, target_ids = validate_target_contract(payload.get("target_contract", {}))
    errors.extend(target_errors)
    warnings.extend(target_warnings)
    target_requirements = by_id(payload.get("target_contract", {}).get("requirements", []), "id")

    coverage = coverage_report(payload.get("coverage", []))
    errors.extend(coverage.get("errors", []))
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

    graph = graph_report(items)
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
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "coverage": coverage,
        "claim_reports": claim_reports,
        "graph": graph,
        "snapshot": snapshot,
    }


def parse_json_arg(value: str) -> Any:
    if value.startswith("@"):
        with open(value[1:], "r", encoding="utf-8") as handle:
            return json.load(handle)
    return json.loads(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Repo-to-roadmap v2 deterministic kernel")
    sub = parser.add_subparsers(dest="command", required=True)

    p_evidence = sub.add_parser("evidence", help="Validate/score evidence for one claim")
    p_evidence.add_argument("--claim-json", required=True, help="JSON object or @file.json")

    p_priority = sub.add_parser("priority", help="Apply gate/target blocker rules and score one roadmap candidate")
    p_priority.add_argument("--item-json", required=True, help="JSON object or @file.json")

    p_sensitivity = sub.add_parser("sensitivity", help="Perturb heuristic priority inputs and report lane stability")
    p_sensitivity.add_argument("--item-json", required=True, help="JSON object or @file.json")

    p_graph = sub.add_parser("graph", help="Validate hard dependencies and compute waves/leverage")
    p_graph.add_argument("--items-json", required=True, help="JSON array or @file.json")

    p_coverage = sub.add_parser("coverage", help="Validate and score analysis coverage")
    p_coverage.add_argument("--coverage-json", required=True, help="JSON array or @file.json")

    p_validate = sub.add_parser("validate", help="Validate complete roadmap payload")
    p_validate.add_argument("--roadmap-json", required=True, help="JSON object or @file.json")

    p_snapshot = sub.add_parser("snapshot", help="Create canonical immutable snapshot hash")
    p_snapshot.add_argument("--roadmap-json", required=True, help="JSON object or @file.json")

    p_delta = sub.add_parser("delta", help="Compare two roadmap snapshots and compute revalidation set")
    p_delta.add_argument("--before-json", required=True, help="JSON object or @file.json")
    p_delta.add_argument("--after-json", required=True, help="JSON object or @file.json")

    args = parser.parse_args()
    try:
        if args.command == "evidence":
            result = evidence_report(parse_json_arg(args.claim_json))
        elif args.command == "priority":
            result = priority_report(parse_json_arg(args.item_json))
        elif args.command == "sensitivity":
            result = sensitivity_report(parse_json_arg(args.item_json))
        elif args.command == "graph":
            payload = parse_json_arg(args.items_json)
            if not isinstance(payload, list):
                raise ValueError("items must be a JSON array")
            result = graph_report(payload)
        elif args.command == "coverage":
            payload = parse_json_arg(args.coverage_json)
            if not isinstance(payload, list):
                raise ValueError("coverage must be a JSON array")
            result = coverage_report(payload)
        elif args.command == "validate":
            result = validate_roadmap(parse_json_arg(args.roadmap_json))
        elif args.command == "snapshot":
            result = snapshot_report(parse_json_arg(args.roadmap_json))
        elif args.command == "delta":
            result = delta_report(parse_json_arg(args.before_json), parse_json_arg(args.after_json))
        else:
            raise ValueError("unknown command")
    except (ValueError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 2

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
