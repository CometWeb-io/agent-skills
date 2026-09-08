#!/usr/bin/env python3
"""Deterministic helpers for the customer-ops skill.

The kernel provides conservative operational fallbacks and safety/readiness checks.
It intentionally does not implement vendor-specific SLA policy engines, statistical churn
prediction, semantic identity resolution, or legal/security determinations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import unicodedata
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

VERSION = "2.0.0"

PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
PRIORITY_BY_ORDER = {v: k for k, v in PRIORITY_ORDER.items()}

OPERATIONAL_RANK_WEIGHTS = {
    "impact": 0.32,
    "urgency": 0.28,
    "breadth": 0.15,
    "recurrence": 0.15,
    "workaround": 0.10,
}

RETENTION_DIMENSIONS = (
    "cancel_intent",
    "support_pain",
    "usage_decline",
    "billing_risk",
    "relationship_risk",
    "renewal_pressure",
    "competitive_pressure",
)

TERMINAL_COMMITMENT_STATES = {"FULFILLED", "RENEGOTIATED", "CANCELLED"}

CASE_TRANSITIONS = {
    "NEW": {"TRIAGED", "DUPLICATE", "MERGED", "CANCELLED"},
    "TRIAGED": {"OWNED", "IN_PROGRESS", "WAITING_CUSTOMER", "WAITING_INTERNAL", "ENGINEERING", "INCIDENT", "RESOLVED", "DUPLICATE", "MERGED", "CANCELLED"},
    "OWNED": {"IN_PROGRESS", "WAITING_CUSTOMER", "WAITING_INTERNAL", "ENGINEERING", "INCIDENT", "RESOLVED", "CANCELLED"},
    "IN_PROGRESS": {"WAITING_CUSTOMER", "WAITING_INTERNAL", "ENGINEERING", "INCIDENT", "RESOLVED", "NOT_REPRODUCED", "WONT_FIX", "CANCELLED"},
    "WAITING_CUSTOMER": {"IN_PROGRESS", "RESOLVED", "CANCELLED"},
    "WAITING_INTERNAL": {"IN_PROGRESS", "ENGINEERING", "INCIDENT", "RESOLVED", "CANCELLED"},
    "ENGINEERING": {"IN_PROGRESS", "WAITING_INTERNAL", "INCIDENT", "RESOLVED", "CANCELLED"},
    "INCIDENT": {"IN_PROGRESS", "RESOLVED", "CANCELLED"},
    "RESOLVED": {"VERIFIED", "IN_PROGRESS"},
    "VERIFIED": {"CLOSED", "IN_PROGRESS"},
    "CLOSED": {"IN_PROGRESS"},
    "NOT_REPRODUCED": {"IN_PROGRESS", "RESOLVED", "CLOSED"},
    "WONT_FIX": {"RESOLVED", "CLOSED", "IN_PROGRESS"},
    "DUPLICATE": {"TRIAGED"},
    "MERGED": {"TRIAGED"},
    "CANCELLED": {"TRIAGED"},
}

INCIDENT_TRANSITIONS = {
    "DETECTED": {"INVESTIGATING", "CLOSED"},
    "INVESTIGATING": {"IDENTIFIED", "MITIGATING", "RECOVERED", "CLOSED"},
    "IDENTIFIED": {"MITIGATING", "MONITORING", "RECOVERED"},
    "MITIGATING": {"IDENTIFIED", "MONITORING", "RECOVERED"},
    "MONITORING": {"MITIGATING", "RECOVERED"},
    "RECOVERED": {"VERIFIED", "MITIGATING"},
    "VERIFIED": {"CLOSED", "MITIGATING"},
    "CLOSED": {"INVESTIGATING"},
}

HANDOFF_TRANSITIONS = {
    "PROPOSED": {"ACCEPTED", "REJECTED", "REROUTED"},
    "ACCEPTED": {"IN_PROGRESS", "BLOCKED", "DONE", "REROUTED"},
    "IN_PROGRESS": {"BLOCKED", "DONE", "REROUTED"},
    "BLOCKED": {"IN_PROGRESS", "DONE", "REROUTED"},
    "REJECTED": {"REROUTED", "PROPOSED"},
    "REROUTED": {"PROPOSED", "ACCEPTED"},
    "DONE": {"IN_PROGRESS"},
}

COMMITMENT_TRANSITIONS = {
    "OPEN": {"DUE_SOON", "OVERDUE", "FULFILLED", "RENEGOTIATED", "CANCELLED"},
    "DUE_SOON": {"OPEN", "OVERDUE", "FULFILLED", "RENEGOTIATED", "CANCELLED"},
    "OVERDUE": {"FULFILLED", "RENEGOTIATED", "CANCELLED"},
    "FULFILLED": set(),
    "RENEGOTIATED": set(),
    "CANCELLED": set(),
}

EXPOSURE_TRANSITIONS = {
    "SUSPECTED": {"CONFIRMED", "RECOVERED"},
    "CONFIRMED": {"MITIGATED", "RECOVERED"},
    "MITIGATED": {"RECOVERED", "CONFIRMED"},
    "RECOVERED": {"VERIFIED", "CONFIRMED"},
    "VERIFIED": {"FOLLOWED_UP", "CONFIRMED"},
    "FOLLOWED_UP": {"CONFIRMED"},
}

CLUSTER_TRANSITIONS = {
    "CANDIDATE": {"CONFIRMED", "WATCHING", "RESOLVED"},
    "CONFIRMED": {"ACTIONED", "WATCHING", "RESOLVED"},
    "ACTIONED": {"MONITORING", "WATCHING", "RESOLVED"},
    "WATCHING": {"CONFIRMED", "ACTIONED", "RESOLVED"},
    "MONITORING": {"ACTIONED", "RESOLVED"},
    "RESOLVED": {"CONFIRMED"},
}

TRANSITION_MAPS = {
    "case": CASE_TRANSITIONS,
    "incident": INCIDENT_TRANSITIONS,
    "handoff": HANDOFF_TRANSITIONS,
    "commitment": COMMITMENT_TRANSITIONS,
    "exposure": EXPOSURE_TRANSITIONS,
    "cluster": CLUSTER_TRANSITIONS,
}


def _read_json(value: str) -> Dict[str, Any]:
    if value == "-":
        payload = sys.stdin.read()
    elif value.startswith("@"):
        with open(value[1:], "r", encoding="utf-8") as fh:
            payload = fh.read()
    else:
        payload = value
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("input JSON must be an object")
    return data


def _int_dimension(data: Mapping[str, Any], key: str, low: int, high: int, *, default: int | None = None) -> int:
    if key not in data:
        if default is not None:
            return default
        raise ValueError(f"missing required field: {key}")
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be numeric in range {low}..{high}")
    if not math.isfinite(float(value)) or int(value) != value:
        raise ValueError(f"{key} must be an integer in range {low}..{high}")
    out = int(value)
    if out < low or out > high:
        raise ValueError(f"{key} must be in range {low}..{high}")
    return out


def _bool(data: Mapping[str, Any], key: str, default: bool = False) -> bool:
    value = data.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be boolean")
    return value


def _parse_dt(value: Any, key: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty ISO 8601 datetime string")
    raw = value.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"{key} must be ISO 8601") from exc
    if dt.tzinfo is None:
        raise ValueError(f"{key} must include a timezone offset")
    return dt


def _nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _norm_text(value: Any) -> str:
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value)).casefold().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s.:/@+\->]", "", text, flags=re.UNICODE)
    return text


def _weighted_rank(dimensions: Mapping[str, int], weights: Mapping[str, float], max_value: int) -> float:
    score = 0.0
    for key, weight in weights.items():
        score += (dimensions[key] / max_value) * weight * 100.0
    return round(score, 1)


def _raise_priority(priority: str, steps: int = 1, *, max_priority: str = "P1") -> str:
    current = PRIORITY_ORDER[priority]
    floor = PRIORITY_ORDER[max_priority]
    return PRIORITY_BY_ORDER[max(floor, current - max(0, steps))]


def priority_assess(data: Dict[str, Any]) -> Dict[str, Any]:
    impact = _int_dimension(data, "impact", 0, 4)
    urgency = _int_dimension(data, "urgency", 0, 4)
    breadth = _int_dimension(data, "breadth", 0, 4)
    recurrence = _int_dimension(data, "recurrence", 0, 4)
    workaround = _int_dimension(data, "workaround", 0, 4)
    customer_risk = _int_dimension(data, "customer_risk", 0, 4, default=0)
    strategic_value = _int_dimension(data, "strategic_value", 0, 4, default=0)
    contractual_deadline = _bool(data, "contractual_deadline", False)
    executive_escalation = _bool(data, "executive_escalation", False)

    if impact == 4 and urgency == 4 and workaround >= 3 and (breadth >= 3 or recurrence == 4):
        priority = "P0"
        base_priority = "P0"
        reasons = ["critical_active_harm_with_systemic_scope_or_recurrence_and_no_viable_workaround"]
    elif impact == 4 or (impact >= 3 and urgency >= 3):
        priority = "P1"
        base_priority = "P1"
        reasons = ["critical_or_major_time_sensitive_customer_impact"]
    elif impact >= 2 or urgency >= 2:
        priority = "P2"
        base_priority = "P2"
        reasons = ["material_normal_operational_work"]
    else:
        priority = "P3"
        base_priority = "P3"
        reasons = ["low_operational_urgency_or_impact"]

    modifier_reasons: List[str] = []
    if priority != "P0":
        if breadth >= 3:
            modifier_reasons.append("multi_account_or_broad_scope")
        if recurrence >= 3:
            modifier_reasons.append("repeated_cross_account_or_systemic_pattern")
        if workaround >= 3 and impact >= 2:
            modifier_reasons.append("weak_or_no_viable_workaround")
        if modifier_reasons:
            raised = _raise_priority(priority, 1, max_priority="P1")
            if raised != priority:
                priority = raised
                reasons.append("raised_one_band_for_operational_modifier")

    if executive_escalation or customer_risk >= 4:
        account_escalation = "EXECUTIVE"
        escalation_reasons = ["explicit_executive_or_critical_relationship_risk"]
    elif customer_risk >= 3 or strategic_value >= 3 or contractual_deadline:
        account_escalation = "EXPEDITED"
        escalation_reasons = []
        if customer_risk >= 3:
            escalation_reasons.append("high_relationship_or_retention_risk")
        if strategic_value >= 3:
            escalation_reasons.append("sourced_strategic_account_context")
        if contractual_deadline:
            escalation_reasons.append("contractual_deadline")
    else:
        account_escalation = "STANDARD"
        escalation_reasons = ["no_material_account_escalation_signal"]

    gate_reasons: List[str] = []
    gate_keys = {
        "security_signal": "security",
        "privacy_signal": "privacy",
        "security_privacy_signal": "security_or_privacy",
        "data_loss_signal": "data_loss",
        "legal_signal": "legal",
        "fraud_signal": "fraud",
        "material_financial_harm_signal": "material_financial_harm",
    }
    for key, label in gate_keys.items():
        if _bool(data, key, False):
            gate_reasons.append(label)

    incident_candidate = (
        (impact >= 3 and breadth >= 3)
        or (impact == 4 and urgency >= 3)
        or (recurrence == 4 and impact >= 2)
    )

    rank_dims = {
        "impact": impact,
        "urgency": urgency,
        "breadth": breadth,
        "recurrence": recurrence,
        "workaround": workaround,
    }
    rank_score = _weighted_rank(rank_dims, OPERATIONAL_RANK_WEIGHTS, 4)

    return {
        "kernel_version": VERSION,
        "method": "customer_ops_priority_fallback_v2",
        "operational_priority": priority,
        "base_priority": base_priority,
        "rank_score": rank_score,
        "rank_score_note": "Tie-break aid within comparable priority bands; not the priority definition or business value.",
        "operational_dimensions": rank_dims,
        "priority_reasons": reasons + modifier_reasons,
        "account_escalation": account_escalation,
        "account_escalation_reasons": escalation_reasons,
        "account_dimensions": {
            "customer_risk": customer_risk,
            "strategic_value": strategic_value,
            "contractual_deadline": contractual_deadline,
            "executive_escalation": executive_escalation,
        },
        "incident_candidate": incident_candidate,
        "specialist_gate_required": bool(gate_reasons),
        "specialist_gates": sorted(set(gate_reasons)),
        "note": "Use documented company priority/escalation policy when available. Strategic account value does not redefine incident severity.",
    }


def _retention_evidence_grade(data: Mapping[str, Any], any_signal: bool) -> str:
    if _bool(data, "evidence_conflicted", False):
        return "CONFLICTED"
    direct = _int_dimension(data, "direct_evidence_count", 0, 100, default=0)
    independent = _int_dimension(data, "independent_source_count", 0, 100, default=0)
    current = _bool(data, "evidence_current", True)
    if not any_signal and direct == 0 and independent == 0:
        return "UNKNOWN"
    if not current:
        return "LOW"
    if direct >= 1 and independent >= 2:
        return "HIGH"
    if direct >= 1 or independent >= 2:
        return "MEDIUM"
    return "LOW"


def churn_risk(data: Dict[str, Any]) -> Dict[str, Any]:
    dims = {key: _int_dimension(data, key, 0, 3) for key in RETENTION_DIMENSIONS}
    cancel = dims["cancel_intent"]
    support = dims["support_pain"]
    usage = dims["usage_decline"]
    billing = dims["billing_risk"]
    relationship = dims["relationship_risk"]
    renewal = dims["renewal_pressure"]
    competitive = dims["competitive_pressure"]

    material_count = sum(1 for value in dims.values() if value >= 2)
    severe_count = sum(1 for value in dims.values() if value >= 3)
    reasons: List[str] = []

    if cancel == 3 and max(support, competitive, renewal, relationship) >= 2:
        level = "CRITICAL"
        reasons.append("explicit_exit_intent_plus_material_pressure")
    elif cancel == 3:
        level = "HIGH"
        reasons.append("explicit_exit_intent")
    elif support == 3 and relationship >= 2:
        level = "HIGH"
        reasons.append("severe_unresolved_support_pain_plus_relationship_risk")
    elif usage == 3 and renewal >= 2:
        level = "HIGH"
        reasons.append("key_usage_collapse_near_decision_window")
    elif billing == 3:
        level = "HIGH"
        reasons.append("material_repeated_billing_risk")
    elif competitive == 3 and max(renewal, relationship) >= 2:
        level = "HIGH"
        reasons.append("active_migration_or_switch_with_decision_pressure")
    elif material_count >= 3 and severe_count >= 1:
        level = "HIGH"
        reasons.append("multiple_material_leading_indicators_with_severe_driver")
    elif cancel == 2 or material_count >= 2 or severe_count >= 1:
        level = "MEDIUM"
        reasons.append("material_but_not_decisive_retention_indicators")
    else:
        level = "LOW"
        reasons.append("no_material_combination_or_only_weak_signal")

    if cancel >= 3:
        expressed = "EXPLICIT"
    elif cancel == 2:
        expressed = "CONSIDERING"
    else:
        expressed = "NONE"

    if cancel == 3 or renewal == 3:
        time_pressure = "IMMEDIATE"
    elif cancel == 2 or renewal == 2 or competitive == 3:
        time_pressure = "HIGH"
    elif renewal == 1 or competitive == 2:
        time_pressure = "MEDIUM"
    else:
        time_pressure = "LOW"

    strongest = sorted(
        ({"driver": key, "level": value} for key, value in dims.items() if value > 0),
        key=lambda row: (-row["level"], row["driver"]),
    )[:5]

    any_signal = any(value > 0 for value in dims.values())
    evidence_grade = _retention_evidence_grade(data, any_signal)

    return {
        "kernel_version": VERSION,
        "method": "customer_ops_retention_risk_heuristic_v2",
        "risk_level": level,
        "expressed_exit_intent": expressed,
        "time_pressure": time_pressure,
        "evidence_grade": evidence_grade,
        "dimensions": dims,
        "strongest_drivers": strongest,
        "reasons": reasons,
        "disclaimer": "Ordinal operational risk heuristic, not churn probability or a validated ML prediction.",
    }


def incident_severity(data: Dict[str, Any]) -> Dict[str, Any]:
    impact = _int_dimension(data, "impact", 0, 4)
    breadth = _int_dimension(data, "breadth", 0, 4)
    workaround = _int_dimension(data, "workaround", 0, 4)
    critical_function = _bool(data, "critical_function", False)
    confirmed_data_loss = _bool(data, "confirmed_data_loss", False)
    confirmed_security_incident = _bool(data, "confirmed_security_incident", False)
    confirmed_privacy_incident = _bool(data, "confirmed_privacy_incident", False)
    legal_signal = _bool(data, "legal_signal", False)
    material_financial_harm = _bool(data, "material_financial_harm", False)

    gates: List[str] = []
    if confirmed_security_incident:
        gates.append("security")
    if confirmed_privacy_incident:
        gates.append("privacy")
    if confirmed_data_loss:
        gates.append("data_loss")
    if legal_signal:
        gates.append("legal")
    if material_financial_harm:
        gates.append("material_financial_harm")

    reasons: List[str] = []
    if impact == 4 and workaround >= 3 and (breadth >= 3 or critical_function or confirmed_data_loss):
        severity = "SEV1"
        reasons.append("critical_customer_impact_with_no_viable_workaround")
    elif confirmed_data_loss and impact >= 3:
        severity = "SEV1"
        reasons.append("material_confirmed_data_loss")
    elif impact >= 3 and (breadth >= 2 or critical_function):
        severity = "SEV2"
        reasons.append("major_core_customer_impact")
    elif impact >= 2 and breadth >= 3:
        severity = "SEV2"
        reasons.append("material_multi_customer_impact")
    elif impact >= 1 and (breadth >= 1 or critical_function):
        severity = "SEV3"
        reasons.append("limited_but_coordinated_customer_impact")
    else:
        severity = "NOT_INCIDENT"
        reasons.append("insufficient_customer_impact_for_incident_fallback")

    return {
        "kernel_version": VERSION,
        "method": "customer_ops_customer_impact_severity_v2",
        "customer_impact_severity": severity,
        "declaration_recommended": severity != "NOT_INCIDENT",
        "inputs": {
            "impact": impact,
            "breadth": breadth,
            "workaround": workaround,
            "critical_function": critical_function,
            "confirmed_data_loss": confirmed_data_loss,
        },
        "reasons": reasons,
        "specialist_gate_required": bool(gates),
        "specialist_gates": sorted(set(gates)),
        "note": "Use the organization's incident severity policy when available. Security/privacy/legal gates are separate from generic customer-impact severity.",
    }


def deadline_status(data: Dict[str, Any]) -> Dict[str, Any]:
    native_raw = data.get("native_status")
    native = str(native_raw).strip().casefold() if native_raw is not None else ""
    paused = _bool(data, "paused", False)

    native_map = {
        "paused": "PAUSED",
        "hit": "MET",
        "met": "MET",
        "fulfilled": "MET",
        "completed": "MET",
        "missed": "BREACHED",
        "breached": "BREACHED",
        "overdue": "BREACHED",
        "fixed": "FIXED",
    }
    if native in native_map:
        return {
            "kernel_version": VERSION,
            "method": "customer_ops_authoritative_deadline_v2",
            "status": native_map[native],
            "native_status_raw": native_raw,
            "source": "native_status",
            "note": "Native/provider status supplied by caller; kernel did not reconstruct provider SLA semantics.",
        }
    if paused:
        return {
            "kernel_version": VERSION,
            "method": "customer_ops_authoritative_deadline_v2",
            "status": "PAUSED",
            "native_status_raw": native_raw,
            "source": "paused_flag",
            "note": "Pause state supplied by caller; kernel did not reconstruct provider SLA semantics.",
        }

    now_raw = data.get("now")
    if not _nonempty(now_raw):
        return {
            "kernel_version": VERSION,
            "method": "customer_ops_authoritative_deadline_v2",
            "status": "UNKNOWN",
            "reason": "now is required when native terminal/paused status is not supplied",
        }
    try:
        now = _parse_dt(now_raw, "now")
    except ValueError as exc:
        return {"kernel_version": VERSION, "method": "customer_ops_authoritative_deadline_v2", "status": "UNKNOWN", "reason": str(exc)}

    due_raw = data.get("due_at")
    if _nonempty(due_raw):
        try:
            due = _parse_dt(due_raw, "due_at")
            warning_minutes = float(data.get("warning_minutes", 0))
        except (TypeError, ValueError) as exc:
            return {"kernel_version": VERSION, "method": "customer_ops_authoritative_deadline_v2", "status": "UNKNOWN", "reason": str(exc)}
        if not math.isfinite(warning_minutes) or warning_minutes < 0:
            return {"kernel_version": VERSION, "method": "customer_ops_authoritative_deadline_v2", "status": "UNKNOWN", "reason": "warning_minutes must be >= 0"}
        remaining = (due - now).total_seconds() / 60.0
        if remaining <= 0:
            status = "BREACHED"
        elif warning_minutes > 0 and remaining <= warning_minutes:
            status = "AT_RISK"
        else:
            status = "OK"
        return {
            "kernel_version": VERSION,
            "method": "customer_ops_authoritative_deadline_v2",
            "status": status,
            "due_at": due.isoformat(),
            "now": now.isoformat(),
            "remaining_minutes": round(remaining, 1),
            "warning_minutes": round(warning_minutes, 1),
            "source": "authoritative_due_at",
            "note": "Assumes due_at already reflects the applicable provider/policy clock semantics.",
        }

    # Explicit continuous-clock fallback. This is deliberately opt-in.
    if str(data.get("clock_mode") or "").strip().casefold() == "continuous":
        try:
            start = _parse_dt(data.get("start_at"), "start_at")
            target = float(data.get("target_minutes"))
            pause = float(data.get("pause_minutes", 0))
            warning_minutes = float(data.get("warning_minutes", 0))
        except (TypeError, ValueError) as exc:
            return {"kernel_version": VERSION, "method": "customer_ops_authoritative_deadline_v2", "status": "UNKNOWN", "reason": str(exc)}
        if not math.isfinite(target) or target <= 0:
            return {"kernel_version": VERSION, "method": "customer_ops_authoritative_deadline_v2", "status": "UNKNOWN", "reason": "target_minutes must be > 0"}
        if not math.isfinite(pause) or pause < 0:
            return {"kernel_version": VERSION, "method": "customer_ops_authoritative_deadline_v2", "status": "UNKNOWN", "reason": "pause_minutes must be >= 0"}
        if not math.isfinite(warning_minutes) or warning_minutes < 0:
            return {"kernel_version": VERSION, "method": "customer_ops_authoritative_deadline_v2", "status": "UNKNOWN", "reason": "warning_minutes must be >= 0"}
        if now < start:
            return {"kernel_version": VERSION, "method": "customer_ops_authoritative_deadline_v2", "status": "UNKNOWN", "reason": "now precedes start_at"}
        elapsed = max(0.0, (now - start).total_seconds() / 60.0 - pause)
        remaining = target - elapsed
        if remaining <= 0:
            status = "BREACHED"
        elif warning_minutes > 0 and remaining <= warning_minutes:
            status = "AT_RISK"
        else:
            status = "OK"
        return {
            "kernel_version": VERSION,
            "method": "customer_ops_authoritative_deadline_v2",
            "status": status,
            "elapsed_minutes": round(elapsed, 1),
            "remaining_minutes": round(remaining, 1),
            "target_minutes": round(target, 1),
            "source": "explicit_continuous_clock_fallback",
            "warning_minutes": round(warning_minutes, 1),
            "note": "Continuous-clock fallback explicitly requested; do not use for provider SLA when office-hours/pause/reopen semantics are unknown.",
        }

    return {
        "kernel_version": VERSION,
        "method": "customer_ops_authoritative_deadline_v2",
        "status": "UNKNOWN",
        "native_status_raw": native_raw,
        "reason": "authoritative native status or due_at required; start_at + target_minutes alone is insufficient for provider SLA",
    }


def dedupe_key(data: Dict[str, Any]) -> Dict[str, Any]:
    fields = ["symptom", "component", "environment", "trigger", "error_signature"]
    normalized = {key: _norm_text(data.get(key, "")) for key in fields}
    if not any(normalized.values()):
        raise ValueError("at least one dedupe field must be non-empty")
    canonical = "|".join(f"{key}={normalized[key]}" for key in fields)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
    return {
        "kernel_version": VERSION,
        "method": "customer_ops_dedupe_candidate_key_v2",
        "dedupe_key": f"cop-{digest}",
        "normalized": normalized,
        "decision": "CANDIDATE_ONLY",
        "note": "Stable fingerprint only. Semantic duplicate and identity review are still required.",
    }


def _token_jaccard(a: str, b: str) -> float:
    aa = {t for t in re.split(r"\W+", _norm_text(a)) if t}
    bb = {t for t in re.split(r"\W+", _norm_text(b)) if t}
    if not aa and not bb:
        return 1.0
    if not aa or not bb:
        return 0.0
    return len(aa & bb) / len(aa | bb)


def dedupe_pair(data: Dict[str, Any]) -> Dict[str, Any]:
    left = data.get("left")
    right = data.get("right")
    if not isinstance(left, dict) or not isinstance(right, dict):
        raise ValueError("left and right must be objects")

    weights = {
        "symptom": 0.35,
        "component": 0.20,
        "environment": 0.10,
        "trigger": 0.20,
        "error_signature": 0.15,
    }
    sims: Dict[str, float] = {}
    for field in weights:
        lv = _norm_text(left.get(field, ""))
        rv = _norm_text(right.get(field, ""))
        if field in {"symptom", "trigger"}:
            sim = _token_jaccard(lv, rv)
        else:
            if not lv and not rv:
                sim = 1.0
            elif lv and rv and lv == rv:
                sim = 1.0
            else:
                sim = 0.0
        sims[field] = round(sim, 4)

    score = sum(weights[field] * sims[field] for field in weights)
    # Different non-empty error signatures are material negative evidence.
    lerr = _norm_text(left.get("error_signature", ""))
    rerr = _norm_text(right.get("error_signature", ""))
    if lerr and rerr and lerr != rerr:
        score *= 0.75
    score = round(score, 4)

    if score >= 0.85:
        decision = "LIKELY_SAME_CANDIDATE"
    elif score >= 0.60:
        decision = "REVIEW"
    else:
        decision = "DISTINCT_CANDIDATE"

    return {
        "kernel_version": VERSION,
        "method": "customer_ops_dedupe_pair_v2",
        "similarity": score,
        "field_similarity": sims,
        "decision": decision,
        "note": "Candidate review only. Never auto-merge customer identities or problems from this score.",
    }


def commitment_status(data: Dict[str, Any]) -> Dict[str, Any]:
    current_state = str(data.get("state") or "OPEN").strip().upper()
    if current_state in TERMINAL_COMMITMENT_STATES:
        return {
            "kernel_version": VERSION,
            "method": "customer_ops_commitment_status_v2",
            "status": current_state,
            "note": "Terminal state supplied by source; verify the source-backed transition.",
        }

    due_raw = data.get("due_at") or data.get("checkpoint_at")
    if not _nonempty(due_raw):
        return {
            "kernel_version": VERSION,
            "method": "customer_ops_commitment_status_v2",
            "status": "OPEN",
            "reason": "no explicit due/checkpoint; do not invent overdue state",
        }

    try:
        due = _parse_dt(due_raw, "due_at")
        now = _parse_dt(data.get("now"), "now")
        warning_minutes = float(data.get("warning_minutes", 240))
    except (TypeError, ValueError) as exc:
        return {"kernel_version": VERSION, "method": "customer_ops_commitment_status_v2", "status": "UNKNOWN", "reason": str(exc)}
    if warning_minutes < 0 or not math.isfinite(warning_minutes):
        return {"kernel_version": VERSION, "method": "customer_ops_commitment_status_v2", "status": "UNKNOWN", "reason": "warning_minutes must be >= 0"}

    remaining = (due - now).total_seconds() / 60.0
    if remaining < 0:
        status = "OVERDUE"
    elif remaining <= warning_minutes:
        status = "DUE_SOON"
    else:
        status = "OPEN"

    return {
        "kernel_version": VERSION,
        "method": "customer_ops_commitment_status_v2",
        "status": status,
        "due_at": due.isoformat(),
        "now": now.isoformat(),
        "remaining_minutes": round(remaining, 1),
        "warning_minutes": round(warning_minutes, 1),
    }


def transition_check(data: Dict[str, Any]) -> Dict[str, Any]:
    entity = str(data.get("entity") or "").strip().casefold()
    from_state = str(data.get("from_state") or "").strip().upper()
    to_state = str(data.get("to_state") or "").strip().upper()
    if entity not in TRANSITION_MAPS:
        raise ValueError(f"entity must be one of: {', '.join(sorted(TRANSITION_MAPS))}")
    mapping = TRANSITION_MAPS[entity]
    if from_state not in mapping:
        return {
            "kernel_version": VERSION,
            "method": "customer_ops_transition_v2",
            "allowed": False,
            "entity": entity,
            "from_state": from_state,
            "to_state": to_state,
            "reason": "unknown from_state",
        }
    allowed = to_state in mapping[from_state]
    return {
        "kernel_version": VERSION,
        "method": "customer_ops_transition_v2",
        "allowed": allowed,
        "entity": entity,
        "from_state": from_state,
        "to_state": to_state,
        "allowed_next_states": sorted(mapping[from_state]),
        "reason": "allowed transition" if allowed else "transition is not in the default state machine",
        "note": "Organization-specific workflow may override the fallback state machine.",
    }


def _missing_fields(data: Mapping[str, Any], fields: Sequence[str]) -> List[str]:
    return [field for field in fields if not _nonempty(data.get(field))]


def case_gate(data: Dict[str, Any]) -> Dict[str, Any]:
    stage = str(data.get("stage") or "").strip().upper()
    if not stage:
        raise ValueError("stage is required")

    missing: List[str] = []
    warnings: List[str] = []
    blockers: List[str] = []

    if stage == "TRIAGED":
        missing = _missing_fields(data, ["source_id", "case_type", "customer_symptom", "owner_class", "next_action"])
        if str(data.get("owner_class") or "").strip().casefold() == "unknown":
            warnings.append("use explicit unassigned rather than unknown owner when no owner exists")

    elif stage == "GITHUB_READY":
        missing = _missing_fields(
            data,
            [
                "customer_symptom",
                "expected_behavior",
                "actual_behavior",
                "reproduction_state",
                "verification_criteria",
                "dedupe_search_status",
                "privacy_preflight_status",
            ],
        )
        dedupe = str(data.get("dedupe_search_status") or "").strip().casefold()
        if dedupe not in {"done", "unavailable"} and _nonempty(dedupe):
            warnings.append("dedupe_search_status should be done or unavailable")
        if dedupe == "unavailable":
            warnings.append("duplicate search unavailable; creation may duplicate existing work")
        repo = str(data.get("repo_conventions_status") or "").strip().casefold()
        if repo in {"unavailable", "partial", "unknown", ""}:
            warnings.append("repository conventions not fully verified")
        repro = str(data.get("reproduction_state") or "").strip().casefold()
        if repro in {"reported-only", "not-reproduced", "unknown"}:
            warnings.append("reproduction incomplete; preserve evidence gap in issue")
        privacy = str(data.get("privacy_preflight_status") or "").strip().casefold()
        if privacy == "blocked" or _bool(data, "known_secret_or_restricted_data", False):
            blockers.append("unsafe customer/secrets publication state")

    elif stage == "RESOLVED":
        missing = _missing_fields(data, ["resolution_summary"])
        if not (_nonempty(data.get("remedy_ref")) or _bool(data, "customer_answered", False)):
            missing.append("remedy_ref_or_customer_answered")

    elif stage == "VERIFIED":
        missing = _missing_fields(data, ["verification_method", "verification_evidence", "verified_at"])
        if data.get("verification_passed") is not True:
            blockers.append("verification_passed must be true")

    elif stage == "CLOSED":
        verified = data.get("verified") is True
        allow_unverified = _bool(data, "allow_unverified_close", False)
        exception_reason = _nonempty(data.get("unverified_close_reason"))
        if not verified and not (allow_unverified and exception_reason):
            blockers.append("case must be verified or have explicit approved unverified-close reason")
        follow = str(data.get("customer_followup_status") or "").strip().casefold()
        if follow not in {"sent", "confirmed", "waived", "not_required"}:
            blockers.append("customer_followup_status must be sent, confirmed, waived, or not_required")
        open_commitments = _int_dimension(data, "open_commitments_count", 0, 100000, default=0)
        if open_commitments > 0 and not _nonempty(data.get("open_commitments_exception_reason")):
            blockers.append("open customer commitments remain")
        if _int_dimension(data, "open_critical_handoffs_count", 0, 100000, default=0) > 0:
            warnings.append("critical handoffs remain open; verify they do not block customer closure")

    elif stage == "CUSTOMER_SEND":
        missing = _missing_fields(data, ["message"])
        if data.get("recipient_resolved") is not True:
            blockers.append("recipient_resolved must be true")
        if data.get("facts_current") is not True:
            blockers.append("material facts must be current/verified")
        if data.get("write_authorized") is not True:
            blockers.append("explicit write/send authority missing")
        privacy = str(data.get("privacy_preflight_status") or "").strip().casefold()
        if privacy == "blocked":
            blockers.append("privacy preflight blocked message")
        if data.get("canonical_incident_comms_conflict") is True:
            blockers.append("message conflicts with canonical incident communication")

    else:
        raise ValueError("stage must be one of TRIAGED, GITHUB_READY, RESOLVED, VERIFIED, CLOSED, CUSTOMER_SEND")

    missing = sorted(set(missing))
    blockers = sorted(set(blockers))
    warnings = sorted(set(warnings))
    if missing:
        blockers.append("missing required fields: " + ", ".join(missing))

    if blockers:
        status = "BLOCK"
    elif warnings:
        status = "WARN"
    else:
        status = "PASS"

    return {
        "kernel_version": VERSION,
        "method": "customer_ops_case_gate_v2",
        "stage": stage,
        "status": status,
        "missing_fields": missing,
        "blockers": blockers,
        "warnings": warnings,
    }


# Conservative best-effort patterns. These are intentionally not comprehensive DLP.
PRIVACY_PATTERNS: Sequence[Tuple[str, re.Pattern[str], str]] = (
    (
        "email",
        re.compile(r"(?<![\w.+-])([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})(?![\w.-])", re.IGNORECASE),
        "<REDACTED_EMAIL>",
    ),
    (
        "bearer_token",
        re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+\-/=]{12,}"),
        "Bearer <REDACTED_TOKEN>",
    ),
    (
        "jwt",
        re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
        "<REDACTED_JWT>",
    ),
    (
        "aws_access_key",
        re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
        "<REDACTED_AWS_ACCESS_KEY>",
    ),
    (
        "secret_assignment",
        re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|secret|password)\b\s*[:=]\s*['\"]?[^\s'\"&,;]{8,}"),
        "<REDACTED_SECRET_ASSIGNMENT>",
    ),
    (
        "credential_query_param",
        re.compile(r"(?i)([?&](?:access_token|token|api_key|apikey|auth|key)=)[^&#\s]+"),
        r"\1<REDACTED>",
    ),
    (
        "cookie_header",
        re.compile(r"(?im)^Cookie:\s*.+$"),
        "Cookie: <REDACTED>",
    ),
)


def privacy_scan(data: Dict[str, Any]) -> Dict[str, Any]:
    text = data.get("text")
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    redacted = text
    findings: List[Dict[str, Any]] = []
    for kind, pattern, replacement in PRIVACY_PATTERNS:
        matches = list(pattern.finditer(redacted))
        if matches:
            findings.append({"type": kind, "count": len(matches)})
            redacted = pattern.sub(replacement, redacted)
    return {
        "kernel_version": VERSION,
        "method": "customer_ops_privacy_preflight_v2",
        "status": "FINDINGS" if findings else "NO_OBVIOUS_FINDINGS",
        "findings": findings,
        "redacted_text": redacted,
        "note": "Best-effort pattern preflight only. It cannot prove the absence of PII, confidential customer data, or secrets; contextual review remains required.",
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Customer Ops deterministic kernel v2")
    parser.add_argument("--version", action="version", version=VERSION)
    sub = parser.add_subparsers(dest="command", required=True)

    commands = (
        "priority-assess",
        "score-case",  # compatibility alias
        "churn-risk",
        "incident-severity",
        "deadline-status",
        "sla-status",  # compatibility alias with safer semantics
        "dedupe-key",
        "dedupe-pair",
        "case-gate",
        "commitment-status",
        "transition",
        "privacy-scan",
    )
    for command in commands:
        p = sub.add_parser(command)
        p.add_argument("--json", required=True, help="JSON object, @file.json, or - for stdin")

    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        data = _read_json(args.json)
        if args.command in {"priority-assess", "score-case"}:
            result = priority_assess(data)
        elif args.command == "churn-risk":
            result = churn_risk(data)
        elif args.command == "incident-severity":
            result = incident_severity(data)
        elif args.command in {"deadline-status", "sla-status"}:
            result = deadline_status(data)
        elif args.command == "dedupe-key":
            result = dedupe_key(data)
        elif args.command == "dedupe-pair":
            result = dedupe_pair(data)
        elif args.command == "case-gate":
            result = case_gate(data)
        elif args.command == "commitment-status":
            result = commitment_status(data)
        elif args.command == "transition":
            result = transition_check(data)
        elif args.command == "privacy-scan":
            result = privacy_scan(data)
        else:  # pragma: no cover
            raise ValueError(f"unknown command: {args.command}")
    except ValueError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
