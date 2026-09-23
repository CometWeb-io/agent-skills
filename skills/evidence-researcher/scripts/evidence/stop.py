"""Stop-decision helper."""
from __future__ import annotations

from typing import Any, Dict

from .audit import audit
from .constants import VERSION


def stop_decision(ledger: Dict[str, Any], no_novelty_rounds: int, expected_information_gain: float, research_cost: float) -> Dict[str, Any]:
    result = audit(ledger)
    if result["research_status"] != "READY":
        return {
            "stop": False,
            "reason": f"research gate is {result['research_status']}",
            "research_status": result["research_status"],
            "kernel_version": VERSION,
        }
    saturation = int(no_novelty_rounds) >= 2
    voi_exhausted = float(expected_information_gain) <= float(research_cost)
    if saturation or voi_exhausted:
        return {
            "stop": True,
            "reason": "evidence gate is ready and marginal research value is exhausted",
            "saturation": saturation,
            "voi_exhausted": voi_exhausted,
            "kernel_version": VERSION,
        }
    return {
        "stop": False,
        "reason": "evidence gate is ready but another bounded research round may still add value",
        "saturation": saturation,
        "voi_exhausted": voi_exhausted,
        "kernel_version": VERSION,
    }

