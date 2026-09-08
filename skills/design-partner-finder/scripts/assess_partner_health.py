#!/usr/bin/env python3
"""Assess an active design partner without conflating learning and revenue.

The output supports periodic partner reviews through activation, repair, pause,
exit review, or handoff to a normal commercial motion.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

WEIGHTS = {
    "workflow_usage": 20.0,
    "learning_yield": 20.0,
    "user_champion_engagement": 15.0,
    "implementation_progress": 15.0,
    "feedback_quality": 10.0,
    "transferability": 10.0,
    "value_signal": 10.0,
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


def assess(payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("ratings") or {}
    missing = [k for k in WEIGHTS if k not in raw]
    if missing:
        raise ValueError("missing ratings: " + ", ".join(missing))
    ratings = {k: _rating(raw[k], k) for k in WEIGHTS}
    bespoke_pressure = _rating(payload.get("bespoke_pressure", 0), "bespoke_pressure")
    support_burden = _rating(payload.get("support_burden", 0), "support_burden")
    blocker_persistence = _rating(payload.get("blocker_persistence", 0), "blocker_persistence")
    willingness_to_buy = _rating(payload.get("willingness_to_buy", 0), "willingness_to_buy")
    product_ready = _strict_bool(payload.get("product_ready_for_conversion"), "product_ready_for_conversion", False)
    timing_capacity_blocker = _strict_bool(payload.get("timing_capacity_blocker"), "timing_capacity_blocker", False)

    contributions = {k: round((ratings[k] / 5.0) * w, 3) for k, w in WEIGHTS.items()}
    base_score = sum(contributions.values())
    risk_penalty = 2.0 * bespoke_pressure + 1.5 * support_burden + 1.5 * blocker_persistence
    score = round(max(0.0, base_score - risk_penalty), 2)

    reasons: list[str] = []
    if ratings["workflow_usage"] <= 1:
        reasons.append("low_real_workflow_usage")
    if ratings["learning_yield"] <= 1:
        reasons.append("low_learning_yield")
    if ratings["user_champion_engagement"] <= 1:
        reasons.append("low_user_champion_engagement")
    if bespoke_pressure >= 4:
        reasons.append("high_bespoke_pressure")
    if support_burden >= 4:
        reasons.append("high_support_burden")
    if blocker_persistence >= 4:
        reasons.append("persistent_blocker")

    severe_misfit = (
        (ratings["workflow_usage"] <= 1 and ratings["learning_yield"] <= 1)
        or (ratings["learning_yield"] <= 1 and bespoke_pressure >= 4)
        or ratings["transferability"] <= 1
    )

    if severe_misfit:
        status = "EXIT_REVIEW"
    elif timing_capacity_blocker or blocker_persistence >= 4:
        status = "PAUSE"
    elif product_ready and ratings["value_signal"] >= 4 and willingness_to_buy >= 3 and ratings["workflow_usage"] >= 3:
        status = "CONVERSION_CANDIDATE"
    elif score >= 75 and bespoke_pressure < 4 and support_burden < 4:
        status = "CONTINUE"
    elif score >= 50:
        status = "REPAIR"
    else:
        status = "EXIT_REVIEW"

    action = {
        "CONTINUE": "DEFINE_NEXT_LEARNING_QUESTIONS",
        "REPAIR": "FIX_HIGHEST_LEVERAGE_ENGAGEMENT_OR_IMPLEMENTATION_GAP",
        "PAUSE": "STOP_CONSUMING_ACTIVE_CAPACITY_AND_SET_RECHECK_TRIGGER",
        "EXIT_REVIEW": "REVIEW_EXIT_AND_CAPTURE_LEARNINGS",
        "CONVERSION_CANDIDATE": "HAND_OFF_TO_NORMAL_COMMERCIAL_QUALIFICATION",
    }[status]

    return {
        "partner": payload.get("partner") or payload.get("candidate"),
        "health_score": score,
        "base_score": round(base_score, 2),
        "risk_penalty": round(risk_penalty, 2),
        "status": status,
        "recommended_action": action,
        "ratings": ratings,
        "risk_inputs": {
            "bespoke_pressure": bespoke_pressure,
            "support_burden": support_burden,
            "blocker_persistence": blocker_persistence,
            "timing_capacity_blocker": timing_capacity_blocker,
        },
        "commercial_signal": {
            "product_ready_for_conversion": product_ready,
            "willingness_to_buy": willingness_to_buy,
        },
        "reasons": reasons,
        "interpretation": "Learning quality, usage, and transferability are evaluated separately from willingness to buy.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Input JSON file; omit to read stdin")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    try:
        if args.input:
            payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
        else:
            payload = json.load(sys.stdin)
        result = assess(payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
