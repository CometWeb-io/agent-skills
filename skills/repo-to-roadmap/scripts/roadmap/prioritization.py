"""Priority scoring and sensitivity analysis."""
from __future__ import annotations

import copy
from typing import Any, Dict, List, Tuple

from .constants import (
    EFFORT_FACTORS,
    EFFORT_ORDER,
    GATE_STATUSES,
    GATE_TYPES,
    ITEM_KINDS,
    LANE_ORDER,
    MATERIALITIES,
)
from .util import (
    clamp,
    normalized_lower,
    normalized_upper,
    require_probability_like,
    require_score,
)


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

