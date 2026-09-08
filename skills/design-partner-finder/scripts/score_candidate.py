#!/usr/bin/env python3
"""Deterministic two-stage design-partner scoring.

Use --stage research for desk-research Discovery Fit and --stage live only after
there is direct company/user evidence. The score is a transparent prioritization
heuristic, not a probability that the company will partner or buy.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

RESEARCH_WEIGHTS = {
    "problem_evidence": 25.0,
    "representativeness": 20.0,
    "urgency": 15.0,
    "learning_value": 15.0,
    "implementation_plausibility": 10.0,
    "stakeholder_path": 5.0,
    "credibility": 5.0,
    "commercial_optionality": 3.0,
    "reference_network_value": 2.0,
}

LIVE_WEIGHTS = {
    "problem_confirmed": 15.0,
    "urgency_confirmed": 10.0,
    "user_champion_access": 15.0,
    "implementation_readiness": 15.0,
    "feedback_commitment": 15.0,
    "decision_procurement_feasibility": 10.0,
    "mutual_value_alignment": 10.0,
    "pilot_measurability": 5.0,
    "transferability": 5.0,
}

ENGAGEMENT_MODES = {
    "RESEARCH_PARTNER",
    "DESIGN_PARTNER",
    "BETA_PARTNER",
    "PAID_PILOT",
    "LIGHTHOUSE",
}


def _rating(value: Any, name: str) -> float:
    try:
        x = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric in 0..5") from exc
    if math.isnan(x) or math.isinf(x) or not 0 <= x <= 5:
        raise ValueError(f"{name} must be numeric in 0..5")
    return x


def _strict_bool(value: Any, name: str, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    raise ValueError(f"{name} must be boolean")


def _optional_bool(value: Any, name: str) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    raise ValueError(f"{name} must be boolean or null")


def _engagement_mode(payload: dict[str, Any]) -> str:
    mode = str(payload.get("engagement_mode") or "DESIGN_PARTNER").upper()
    if mode not in ENGAGEMENT_MODES:
        raise ValueError("engagement_mode must be one of: " + ", ".join(sorted(ENGAGEMENT_MODES)))
    return mode


def _score_dimensions(ratings_raw: dict[str, Any], weights: dict[str, float]) -> tuple[dict[str, float], dict[str, float], float]:
    missing = [key for key in weights if key not in ratings_raw]
    if missing:
        raise ValueError("missing ratings: " + ", ".join(missing))
    ratings = {key: _rating(ratings_raw[key], key) for key in weights}
    contributions = {
        key: round((ratings[key] / 5.0) * weight, 3)
        for key, weight in weights.items()
    }
    return ratings, contributions, round(sum(contributions.values()), 2)


def _confidence_map(payload: dict[str, Any], weights: dict[str, float]) -> dict[str, float]:
    raw = payload.get("dimension_confidence") or {}
    if not isinstance(raw, dict):
        raise ValueError("dimension_confidence must be an object when provided")
    out: dict[str, float] = {}
    for key in weights:
        if key in raw:
            out[key] = _rating(raw[key], f"dimension_confidence.{key}")
    return out


def _normalized(contributions: dict[str, float], keys: list[str], weights: dict[str, float]) -> float:
    denom = sum(weights[k] for k in keys)
    if denom <= 0:
        return 0.0
    return round(sum(contributions[k] for k in keys) / denom * 100.0, 2)


def _weakest(ratings: dict[str, float], keys: list[str]) -> dict[str, Any]:
    key = min(keys, key=lambda k: (ratings[k], k))
    return {"dimension": key, "rating": ratings[key]}


def _top_contributors(contributions: dict[str, float], n: int = 3) -> list[dict[str, Any]]:
    return [
        {"dimension": k, "points": v}
        for k, v in sorted(contributions.items(), key=lambda kv: (-kv[1], kv[0]))[:n]
    ]


def _apply_cap(state: dict[str, Any], limit: float, reason: str) -> None:
    if state["score"] > limit:
        state["score"] = limit
    state["caps"].append({"limit": limit, "reason": reason})


def score_research(payload: dict[str, Any]) -> dict[str, Any]:
    ratings, contributions, base_score = _score_dimensions(payload.get("ratings") or {}, RESEARCH_WEIGHTS)
    confidence_map = _confidence_map(payload, RESEARCH_WEIGHTS)
    evidence_confidence = _rating(payload.get("evidence_confidence", 0), "evidence_confidence")
    contradiction_risk = _rating(payload.get("contradiction_risk", 0), "contradiction_risk")
    customization_risk = _rating(payload.get("customization_risk", 0), "customization_risk")
    conflict_risk = _rating(payload.get("conflict_risk", 0), "conflict_risk")
    contact_path = _strict_bool(payload.get("professional_contact_path"), "professional_contact_path", False)
    exploration_mode = _strict_bool(payload.get("exploration_mode"), "exploration_mode", False)

    state: dict[str, Any] = {"score": base_score, "caps": [], "hard_reasons": [], "hold_reasons": []}

    if ratings["problem_evidence"] < 2:
        state["hard_reasons"].append("problem_evidence_below_2")
    if ratings["representativeness"] < 2 and not exploration_mode:
        state["hard_reasons"].append("representativeness_below_2")
    if state["hard_reasons"]:
        _apply_cap(state, 49.0, "hard_reject_rule")

    if evidence_confidence <= 1:
        _apply_cap(state, 49.0, "evidence_confidence_at_or_below_1")
        state["hold_reasons"].append("insufficient_evidence_confidence")
    if ratings["credibility"] <= 1:
        _apply_cap(state, 49.0, "credibility_at_or_below_1")
        state["hold_reasons"].append("material_credibility_unresolved")
    if contradiction_risk >= 4:
        state["hold_reasons"].append("material_contradiction_risk")
    if conflict_risk >= 4:
        state["hold_reasons"].append("material_conflict_risk")
    if customization_risk >= 4:
        _apply_cap(state, 64.0, "customization_risk_at_or_above_4")
    if ratings["implementation_plausibility"] <= 1:
        _apply_cap(state, 64.0, "implementation_plausibility_at_or_below_1")

    final_score = round(float(state["score"]), 2)
    if state["hard_reasons"]:
        status = "REJECT"
    elif state["hold_reasons"]:
        status = "HOLD_VERIFY"
    else:
        priority_gate = all(
            [
                final_score >= 80,
                ratings["problem_evidence"] >= 3,
                ratings["representativeness"] >= 3 or exploration_mode,
                ratings["urgency"] >= 3,
                ratings["learning_value"] >= 3,
                ratings["implementation_plausibility"] >= 2,
                evidence_confidence >= 3,
                contact_path,
            ]
        )
        if priority_gate:
            status = "PRIORITY_DISCOVERY"
        elif final_score >= 65:
            status = "DISCOVERY"
        elif final_score >= 50:
            status = "WATCHLIST"
        else:
            status = "REJECT"

    action = {
        "PRIORITY_DISCOVERY": "CONTACT_FOR_DISCOVERY",
        "DISCOVERY": "VALIDATE_HIGHEST_VALUE_GAP",
        "WATCHLIST": "MONITOR_OR_RESEARCH_IF_CHEAP",
        "HOLD_VERIFY": "RESOLVE_EVIDENCE_OR_CONFLICT",
        "REJECT": "DO_NOT_PURSUE",
    }[status]

    low_confidence = [
        {"dimension": k, "confidence": v}
        for k, v in sorted(confidence_map.items())
        if v <= 2
    ]

    return {
        "candidate": payload.get("candidate"),
        "stage": "research",
        "engagement_mode": _engagement_mode(payload),
        "base_score": base_score,
        "score": final_score,
        "status": status,
        "recommended_action": action,
        "sub_scores": {
            "learning_fit": _normalized(contributions, ["problem_evidence", "representativeness", "learning_value"], RESEARCH_WEIGHTS),
            "activation_plausibility": _normalized(contributions, ["urgency", "implementation_plausibility", "stakeholder_path"], RESEARCH_WEIGHTS),
            "strategic_confidence": _normalized(contributions, ["credibility", "commercial_optionality", "reference_network_value"], RESEARCH_WEIGHTS),
        },
        "ratings": ratings,
        "dimension_contributions": contributions,
        "dimension_confidence": confidence_map,
        "low_confidence_dimensions": low_confidence,
        "top_contributors": _top_contributors(contributions),
        "weakest_core_dimension": _weakest(ratings, ["problem_evidence", "representativeness", "urgency", "learning_value", "implementation_plausibility"]),
        "gates": {
            "evidence_confidence": evidence_confidence,
            "contradiction_risk": contradiction_risk,
            "customization_risk": customization_risk,
            "conflict_risk": conflict_risk,
            "professional_contact_path": contact_path,
            "exploration_mode": exploration_mode,
        },
        "caps_applied": state["caps"],
        "hard_reasons": state["hard_reasons"],
        "hold_reasons": state["hold_reasons"],
        "interpretation": "Research-stage prioritization only; this does not confirm interest, commitment, or partner readiness.",
    }


def score_live(payload: dict[str, Any]) -> dict[str, Any]:
    ratings, contributions, base_score = _score_dimensions(payload.get("ratings") or {}, LIVE_WEIGHTS)
    confidence_map = _confidence_map(payload, LIVE_WEIGHTS)
    mode = _engagement_mode(payload)
    direct_evidence = _strict_bool(payload.get("live_evidence_confirmed"), "live_evidence_confirmed", False)
    security_privacy_blocker = _strict_bool(payload.get("security_privacy_blocker"), "security_privacy_blocker", False)
    legal_contract_blocker = _strict_bool(payload.get("legal_contract_blocker"), "legal_contract_blocker", False)
    customization_risk = _rating(payload.get("customization_risk", 0), "customization_risk")
    conflict_risk = _rating(payload.get("conflict_risk", 0), "conflict_risk")
    commercial_commitment = _rating(payload.get("commercial_commitment", 0), "commercial_commitment")
    reference_permission = _optional_bool(payload.get("reference_permission"), "reference_permission")

    state: dict[str, Any] = {"score": base_score, "caps": [], "hard_reasons": [], "hold_reasons": [], "alignment_reasons": []}

    if ratings["problem_confirmed"] < 2:
        state["hard_reasons"].append("problem_not_confirmed")
    if state["hard_reasons"]:
        _apply_cap(state, 49.0, "hard_reject_rule")

    if not direct_evidence:
        state["hold_reasons"].append("live_evidence_not_confirmed")
    if security_privacy_blocker:
        state["hold_reasons"].append("security_privacy_blocker")
    if legal_contract_blocker:
        state["hold_reasons"].append("legal_contract_blocker")
    if conflict_risk >= 4:
        state["hold_reasons"].append("material_conflict_risk")

    if ratings["user_champion_access"] < 2:
        state["alignment_reasons"].append("insufficient_user_champion_access")
    if ratings["feedback_commitment"] < 2:
        state["alignment_reasons"].append("insufficient_feedback_commitment")
    if ratings["implementation_readiness"] < 2:
        state["alignment_reasons"].append("implementation_not_ready")
    if customization_risk >= 4:
        _apply_cap(state, 64.0, "customization_risk_at_or_above_4")
        state["alignment_reasons"].append("high_customization_risk")
    if ratings["transferability"] < 2:
        _apply_cap(state, 64.0, "transferability_below_2")
        state["alignment_reasons"].append("low_transferability")
    if mode == "PAID_PILOT" and commercial_commitment < 2:
        state["alignment_reasons"].append("paid_pilot_commercial_commitment_insufficient")
    if mode == "LIGHTHOUSE" and reference_permission is not True:
        state["alignment_reasons"].append("lighthouse_reference_permission_unconfirmed")

    final_score = round(float(state["score"]), 2)
    if state["hard_reasons"]:
        status = "REJECT"
    elif state["hold_reasons"]:
        status = "HOLD_VERIFY"
    else:
        ready_gate = all(
            [
                final_score >= 80,
                ratings["problem_confirmed"] >= 3,
                ratings["urgency_confirmed"] >= 3,
                ratings["user_champion_access"] >= 3,
                ratings["implementation_readiness"] >= 3,
                ratings["feedback_commitment"] >= 3,
                ratings["mutual_value_alignment"] >= 3,
                ratings["transferability"] >= 3,
                not state["alignment_reasons"],
            ]
        )
        if ready_gate:
            status = "PARTNER_READY"
        elif final_score >= 65:
            status = "ALIGNMENT_REQUIRED"
        elif final_score >= 50:
            status = "PAUSE"
        else:
            status = "REJECT"

    action = {
        "PARTNER_READY": "ACTIVATE_WITH_CHARTER",
        "ALIGNMENT_REQUIRED": "RESOLVE_COMMITMENT_OR_IMPLEMENTATION_GAPS",
        "PAUSE": "DEFER_AND_RECHECK_TRIGGER",
        "HOLD_VERIFY": "RESOLVE_BLOCKER",
        "REJECT": "DO_NOT_ACTIVATE",
    }[status]

    low_confidence = [
        {"dimension": k, "confidence": v}
        for k, v in sorted(confidence_map.items())
        if v <= 2
    ]

    return {
        "candidate": payload.get("candidate"),
        "stage": "live",
        "engagement_mode": mode,
        "base_score": base_score,
        "score": final_score,
        "status": status,
        "recommended_action": action,
        "sub_scores": {
            "learning_fit": _normalized(contributions, ["problem_confirmed", "pilot_measurability", "transferability"], LIVE_WEIGHTS),
            "activation_readiness": _normalized(contributions, ["urgency_confirmed", "user_champion_access", "implementation_readiness", "feedback_commitment", "decision_procurement_feasibility"], LIVE_WEIGHTS),
            "mutual_alignment": _normalized(contributions, ["mutual_value_alignment"], LIVE_WEIGHTS),
        },
        "ratings": ratings,
        "dimension_contributions": contributions,
        "dimension_confidence": confidence_map,
        "low_confidence_dimensions": low_confidence,
        "top_contributors": _top_contributors(contributions),
        "weakest_core_dimension": _weakest(ratings, ["problem_confirmed", "user_champion_access", "implementation_readiness", "feedback_commitment", "mutual_value_alignment", "transferability"]),
        "gates": {
            "live_evidence_confirmed": direct_evidence,
            "security_privacy_blocker": security_privacy_blocker,
            "legal_contract_blocker": legal_contract_blocker,
            "customization_risk": customization_risk,
            "conflict_risk": conflict_risk,
            "commercial_commitment": commercial_commitment,
            "reference_permission": reference_permission,
        },
        "caps_applied": state["caps"],
        "hard_reasons": state["hard_reasons"],
        "hold_reasons": state["hold_reasons"],
        "alignment_reasons": state["alignment_reasons"],
        "interpretation": "Live readiness requires direct evidence; use the engagement-mode gates before activation.",
    }


def score(payload: dict[str, Any], stage: str) -> dict[str, Any]:
    stage = stage.lower()
    if stage == "research":
        return score_research(payload)
    if stage == "live":
        return score_live(payload)
    raise ValueError("stage must be research or live")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Input JSON file; omit to read stdin")
    parser.add_argument("--stage", choices=("research", "live"), help="Override payload stage")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = parser.parse_args()

    try:
        if args.input:
            payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
        else:
            payload = json.load(sys.stdin)
        stage = args.stage or str(payload.get("stage") or "research")
        result = score(payload, stage)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
