from __future__ import annotations

from typing import Any

from .constants import GATE_STATUSES, VERDICTS
from .util import _boolean, _strings, _unit_interval

def gate_verdict(proposed_verdict: str, confidence: float, required_confidence_value: float,
                 reversible_experiment_available: bool, critical_gap: str | None = None,
                 gate_statuses: dict[str, str] | None = None, controls_implemented: bool = False,
                 freshness_status: str = "CLEAR", human_approval_required: bool = False,
                 human_approved: bool = False, required_gatekeepers: list[str] | None = None) -> str:
    """Apply declared constraints, not factual verification or execution authorization.

    A supplied BLOCK remains NO-GO even when other evidence needs refresh. That
    preserves the constraint; it does not authenticate its basis. Unknown inputs
    never become confidence zero, approval, implemented controls, or a clear gate.
    """
    conf = _unit_interval(confidence, "confidence")
    required = _unit_interval(required_confidence_value, "required_confidence")
    experiment = _boolean(reversible_experiment_available, "reversible_experiment_available")
    _boolean(controls_implemented, "controls_implemented")
    _boolean(human_approval_required, "human_approval_required")
    _boolean(human_approved, "human_approved")
    if critical_gap is not None and (not isinstance(critical_gap, str) or not critical_gap.strip()):
        raise ValueError("critical_gap must be null or nonempty text")
    if gate_statuses is not None and not isinstance(gate_statuses, dict):
        raise ValueError("gate_statuses must be an object")
    statuses = {}
    for name, status in (gate_statuses or {}).items():
        if not isinstance(name, str) or not name.strip() or not isinstance(status, str):
            raise ValueError("invalid gate name or status")
        statuses[name] = status.strip().upper()
    needed = _strings(required_gatekeepers if required_gatekeepers is not None else [], "required_gatekeepers")
    verdict = proposed_verdict.strip().upper() if isinstance(proposed_verdict, str) else "DEFER"
    if "BLOCK" in statuses.values():
        return "NO-GO"
    if verdict not in VERDICTS or any(v not in GATE_STATUSES for v in statuses.values()):
        return "DEFER"
    if any(name not in statuses or statuses[name] == "NOT_REQUIRED" for name in needed):
        return "DEFER"
    if "COUNSEL_REQUIRED" in statuses.values():
        return "DEFER"
    if not isinstance(freshness_status, str) or freshness_status.strip().upper() != "CLEAR":
        return "DEFER"
    if human_approval_required and not human_approved:
        return "DEFER"
    # A trial is not permission to skip safeguards required for the assessed scope.
    if "CLEAR_WITH_CONTROLS" in statuses.values() and not controls_implemented:
        return "DEFER"
    if verdict in {"GO", "NO-GO"} and (critical_gap or conf < required):
        return "TEST" if experiment else "DEFER"
    return verdict

def build_human_handoff_packet(kind: str, decision: dict[str, Any], issue: dict[str, Any]) -> dict[str, Any]:
    kind = str(kind or "expert").lower()
    packet_type = {"legal": "COUNSEL_PACKET", "security": "SECURITY_REVIEW_PACKET", "finance": "FINANCE_APPROVAL_PACKET", "medical": "DOMAIN_EXPERT_PACKET"}.get(kind, "DOMAIN_EXPERT_PACKET")
    return {
        "packet_type": packet_type,
        "decision": decision.get("question") or decision.get("decision") or "",
        "decision_key": decision.get("decision_key"),
        "jurisdictions": decision.get("jurisdictions") or [],
        "known_facts": decision.get("known_facts") or [],
        "exact_question": issue.get("question") or issue.get("exact_question") or "",
        "material_uncertainty": issue.get("material_uncertainty") or issue.get("uncertainty") or "",
        "primary_sources": issue.get("primary_sources") or [],
        "alternative_interpretations": issue.get("alternative_interpretations") or [],
        "business_consequence": issue.get("business_consequence") or "",
        "deadline": issue.get("deadline") or "",
        "decision_change_condition": issue.get("decision_change_condition") or "",
        "return_evidence_class": "HUMAN_EXPERT_EVIDENCE",
        "scope_is_bounded": True,
    }


def tool_authority_assessment(action: dict[str, Any]) -> dict[str, Any]:
    flags = {
        "write": bool(action.get("write", False)),
        "external_side_effect": bool(action.get("external_side_effect", False)),
        "financial": bool(action.get("financial", False)),
        "public": bool(action.get("public", False)),
        "destructive": bool(action.get("destructive", False)),
        "credential_sensitive": bool(action.get("credential_sensitive", False)),
        "sensitive_data": bool(action.get("sensitive_data", False)),
        "irreversible": bool(action.get("irreversible", False)),
    }
    score = 0
    if flags["write"]:
        score = max(score, 1)
    if flags["external_side_effect"] or flags["public"]:
        score = max(score, 2)
    if flags["financial"] or flags["destructive"] or flags["credential_sensitive"] or flags["sensitive_data"]:
        score = max(score, 3)
    if flags["irreversible"] and (flags["financial"] or flags["destructive"] or flags["public"] or flags["sensitive_data"]):
        score = 4
    klass = f"T{score}"
    return {
        "authority_class": klass,
        "approval_required": score >= 2,
        "explicit_human_approval_required": score >= 3,
        "execute_automatically": score <= 1,
        "flags": flags,
        "rule": "higher tool authority requires stronger approval; evidence gathering must not silently escalate into side effects",
    }
