#!/usr/bin/env python3
"""Deterministic helpers for Product Operator v2.

Commands:
  rank       Rank evidence-backed candidate actions.
  reconcile  Detect product-state drift and evidence problems.
  sequence   Order candidate actions by dependencies after ranking.
  readiness  Calculate whether prioritization is READY/PROVISIONAL/BLOCKED.
  snapshot   Create an immutable comparable snapshot with hashes.
  delta      Compare two reports/snapshots and surface material movement.
  validate   Validate an operator-report.json sidecar.

The kernel never retrieves data and never performs external writes. It checks
consistency; it does not invent product judgment.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone
from typing import Any

PROTOCOL_VERSION = "2.0"
ALLOWED_MODES = {"PULSE", "STANDARD", "DEEP", "DELTA", "RELEASE"}
COVERAGE_VALUES = {"verified", "partial", "unavailable", "not-required"}
FRESHNESS_VALUES = {"CURRENT", "NEAR_EXPIRY", "STALE", "SUPERSEDED", "UNKNOWN", "NOT_REQUIRED"}
READINESS_VALUES = {"READY", "PROVISIONAL", "BLOCKED"}
PRIORITY_TIERS = {"BLOCKER", "VERIFY_NOW", "NOW", "NEXT", "LATER", "STOP"}
TIER_ORDER = {"BLOCKER": 0, "VERIFY_NOW": 1, "NOW": 2, "NEXT": 3, "LATER": 4, "STOP": 5}
STAGES = ("intent", "planned", "implemented", "verified", "shipped", "outcome")

STAGE_AUTHORITIES = {
    "intent": {"user", "product_context", "product_marketing", "prd", "strategy", "notion_product"},
    "planned": {"notion", "linear", "roadmap", "milestone", "planning", "release_plan"},
    "implemented": {"github", "github_code", "git", "git_pr", "git_commit", "repository"},
    "verified": {"ci", "test", "qa", "audit", "acceptance", "browser", "web_app_auditor"},
    "shipped": {"release", "deploy", "deployment", "environment", "github_release", "hosting"},
    "outcome": {"analytics", "customer", "revenue", "support", "crm", "billing", "experiment"},
}


def load_json_arg(value: str) -> Any:
    if value.startswith("@"):
        with open(value[1:], "r", encoding="utf-8") as handle:
            return json.load(handle)
    if os.path.isfile(value):
        with open(value, "r", encoding="utf-8") as handle:
            return json.load(handle)
    return json.loads(value)


def clamp(value: Any, low: float, high: float, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(number):
        return default
    return min(high, max(low, number))


def boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def norm(value: Any) -> str:
    return str(value or "").strip().upper().replace(" ", "_")


def parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def evidence_freshness(ev: dict[str, Any], as_of: str | None = None) -> str:
    explicit = norm(ev.get("freshness_status") or ev.get("temporal_status"))
    if explicit in FRESHNESS_VALUES:
        return explicit
    if boolish(ev.get("not_required")):
        return "NOT_REQUIRED"
    observed = parse_time(ev.get("observed_at") or ev.get("verified_at"))
    max_age = ev.get("max_age_days")
    as_of_dt = parse_time(as_of)
    if observed is not None and max_age is not None and as_of_dt is not None:
        age_days = max(0.0, (as_of_dt - observed).total_seconds() / 86400.0)
        ttl = clamp(max_age, 0, 36500, 0)
        if ttl <= 0:
            return "UNKNOWN"
        if age_days > ttl:
            return "STALE"
        if age_days >= ttl * 0.8:
            return "NEAR_EXPIRY"
        return "CURRENT"
    return "UNKNOWN"


def evidence_authority_ok(ev: dict[str, Any], stage: str) -> bool:
    authority = str(ev.get("authority") or ev.get("source") or "").strip().lower()
    if not authority:
        return False
    allowed = STAGE_AUTHORITIES.get(stage, set())
    return authority in allowed


def rank_candidate(row: dict[str, Any]) -> dict[str, Any]:
    impact = clamp(row.get("impact"), 0, 5, 0)
    goal_alignment = clamp(row.get("goal_alignment"), 0, 5, 0)
    urgency = clamp(row.get("urgency"), 0, 5, 0)
    dependency = clamp(row.get("dependency_leverage"), 0, 5, 0)
    risk = clamp(row.get("risk_reduction"), 0, 5, 0)
    learning = clamp(row.get("learning_value"), 0, 5, 0)
    effort = clamp(row.get("effort"), 0.5, 5, 1)
    confidence = clamp(row.get("confidence"), 0, 1, 0)
    evidence = clamp(row.get("evidence_strength"), 0, 1, 0)

    base = (
        2.0 * impact
        + 1.5 * goal_alignment
        + 1.25 * dependency
        + 1.0 * urgency
        + 1.0 * risk
        + 1.0 * learning
    )
    quality = math.sqrt(confidence * evidence)
    effort_penalty = 1 + 0.35 * max(0.0, effort - 1)
    score = base * quality / effort_penalty if effort_penalty else 0.0

    stop = boolish(row.get("stop"))
    blocker = boolish(row.get("blocker"))
    trust_critical = boolish(row.get("trust_critical"))
    verify_first = boolish(row.get("verify_first"))

    if stop:
        tier = "STOP"
    elif blocker or trust_critical:
        if verify_first or min(confidence, evidence) < 0.5:
            tier = "VERIFY_NOW"
        else:
            tier = "BLOCKER"
    elif verify_first and max(impact, dependency, risk, learning, goal_alignment) >= 4:
        tier = "VERIFY_NOW"
    elif score >= 12 and max(impact, goal_alignment, dependency, risk, learning) >= 4:
        tier = "NOW"
    elif dependency >= 4 and urgency >= 3 and quality >= 0.60:
        tier = "NOW"
    elif score >= 7 and max(impact, goal_alignment, dependency, risk, urgency, learning) >= 3:
        tier = "NEXT"
    else:
        tier = "LATER"

    result = dict(row)
    result.update(
        {
            "priority_tier": tier,
            "priority_score": round(score, 4),
            "score_breakdown": {
                "base": round(base, 4),
                "quality": round(quality, 4),
                "effort_penalty": round(effort_penalty, 4),
            },
        }
    )
    return result


def rank_candidates(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ranked = [rank_candidate(row) for row in rows]
    ranked.sort(key=lambda r: (TIER_ORDER.get(r["priority_tier"], 9), -r["priority_score"], str(r.get("id", ""))))
    groups: dict[str, list[dict[str, Any]]] = {k: [] for k in TIER_ORDER}
    for row in ranked:
        groups[row["priority_tier"]].append(row)
    return {"ranked": ranked, "groups": groups}


def state_value(item: dict[str, Any], key: str) -> str:
    states = item.get("states") or {}
    return norm(states.get(key, item.get(key, "UNKNOWN")))


def stage_evidence(item: dict[str, Any], stage: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for ev in item.get("evidence") or []:
        if not isinstance(ev, dict):
            continue
        ev_stage = str(ev.get("stage") or "").strip().lower()
        if ev_stage == stage.lower():
            out.append(ev)
    return out


def reconcile_item(item: dict[str, Any], as_of: str | None = None) -> list[dict[str, Any]]:
    item_id = str(item.get("id") or item.get("name") or "unknown")
    planned = state_value(item, "planned")
    implemented = state_value(item, "implemented")
    verified = state_value(item, "verified")
    shipped = state_value(item, "shipped")
    outcome = state_value(item, "outcome")
    issues: list[dict[str, Any]] = []

    def add(code: str, severity: str, message: str, stage: str | None = None) -> None:
        row = {"item_id": item_id, "code": code, "severity": severity, "message": message}
        if stage:
            row["stage"] = stage
        issues.append(row)

    if planned == "DONE" and implemented not in {"PRESENT", "DONE"}:
        add("PLAN_AHEAD_OF_CODE", "high", "Planning says Done but implementation is not proven present.")
    if implemented in {"PRESENT", "DONE"} and planned in {"ABSENT", "UNKNOWN"}:
        add("CODE_AHEAD_OF_PLAN", "medium", "Implementation exists but planning state is absent or unknown.")
    if implemented in {"PRESENT", "DONE"} and verified not in {"PASS", "PRESENT", "DONE"}:
        severity = "high" if verified == "FAIL" else "medium"
        add("CODE_AHEAD_OF_VERIFICATION", severity, "Implementation exists without complete verification.")
    if verified in {"PASS", "PRESENT", "DONE"} and shipped not in {"PRESENT", "DONE"}:
        add("VERIFIED_NOT_SHIPPED", "medium", "Verification is complete but ship/deploy evidence is absent.")
    if boolish(item.get("outcome_required")) and shipped in {"PRESENT", "DONE"} and outcome in {"UNKNOWN", "ABSENT"}:
        add("SHIP_WITHOUT_OUTCOME_EVIDENCE", "medium", "The item is shipped but decision-relevant outcome evidence is missing.")
    if shipped in {"PRESENT", "DONE"} and implemented not in {"PRESENT", "DONE"}:
        add("STATUS_CONTRADICTION", "critical", "Shipped state conflicts with missing implementation evidence.")
    if outcome in {"POSITIVE", "NEGATIVE", "MIXED", "PRESENT"} and shipped not in {"PRESENT", "DONE"}:
        add("STATUS_CONTRADICTION", "high", "Outcome evidence exists while shipped state is not proven.")

    if boolish(item.get("stale_plan")):
        add("STALE_PLAN", "medium", "Planning state is stale relative to newer material evidence.")
    if boolish(item.get("orphaned_wip")):
        add("ORPHANED_WIP", "medium", "Work in progress lacks a current goal/owner/dependency/progress signal.")
    if boolish(item.get("context_drift")):
        add("CONTEXT_DRIFT", "high", "Material product-context sources disagree.")
    if boolish(item.get("context_to_plan_drift")):
        add("CONTEXT_TO_PLAN_DRIFT", "high", "Active planning does not reflect the current product goal/context.")

    positive_states = {
        "intent": {"PRESENT", "DONE"},
        "planned": {"TODO", "IN_PROGRESS", "DONE", "PRESENT"},
        "implemented": {"PRESENT", "DONE"},
        "verified": {"PASS", "PRESENT", "DONE", "PARTIAL"},
        "shipped": {"PRESENT", "DONE"},
        "outcome": {"POSITIVE", "NEGATIVE", "MIXED", "PRESENT"},
    }
    for stage in STAGES:
        if state_value(item, stage) not in positive_states[stage]:
            continue
        evidence = stage_evidence(item, stage)
        if not evidence:
            severity = "high" if stage in {"implemented", "verified", "shipped"} else "medium"
            add(f"{stage.upper()}_EVIDENCE_MISSING", severity, f"{stage.title()} is positive without stage-specific evidence.", stage)
            continue
        if not any(evidence_authority_ok(ev, stage) for ev in evidence):
            severity = "high" if stage in {"implemented", "shipped"} else "medium"
            add(f"{stage.upper()}_EVIDENCE_WRONG_AUTHORITY", severity, f"{stage.title()} evidence is not from an authoritative lane.", stage)
        for ev in evidence:
            freshness = evidence_freshness(ev, as_of)
            if boolish(ev.get("required_current")) and freshness in {"STALE", "SUPERSEDED", "UNKNOWN"}:
                add("CURRENT_EVIDENCE_NOT_ADMISSIBLE", "high", f"Current evidence for {stage} is {freshness}.", stage)
            elif freshness == "STALE":
                add("STALE_EVIDENCE", "medium", f"Evidence for {stage} is stale.", stage)

    return issues


def reconcile_items(items: list[dict[str, Any]], as_of: str | None = None) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    for item in items:
        issues.extend(reconcile_item(item, as_of=as_of))
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    issues.sort(key=lambda x: (severity_order.get(x["severity"], 9), x["code"], x["item_id"]))
    counts: dict[str, int] = {}
    for issue in issues:
        counts[issue["code"]] = counts.get(issue["code"], 0) + 1
    return {"issues": issues, "counts": counts, "issue_count": len(issues)}


def sequence_candidates(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ranked_rows = rank_candidates(rows)["ranked"]
    by_id = {str(row.get("id")): row for row in ranked_rows if str(row.get("id") or "").strip()}
    missing_dependencies: list[dict[str, str]] = []
    indegree: dict[str, int] = {key: 0 for key in by_id}
    outgoing: dict[str, list[str]] = {key: [] for key in by_id}

    for key, row in by_id.items():
        deps = [str(x) for x in (row.get("depends_on") or []) if str(x).strip()]
        for dep in deps:
            if dep not in by_id:
                missing_dependencies.append({"action_id": key, "missing_dependency": dep})
                continue
            indegree[key] += 1
            outgoing[dep].append(key)

    ready = [key for key, degree in indegree.items() if degree == 0]
    ready.sort(key=lambda key: (TIER_ORDER.get(by_id[key]["priority_tier"], 9), -by_id[key]["priority_score"], key))
    order: list[str] = []
    while ready:
        current = ready.pop(0)
        order.append(current)
        for nxt in sorted(outgoing[current]):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                ready.append(nxt)
        ready.sort(key=lambda key: (TIER_ORDER.get(by_id[key]["priority_tier"], 9), -by_id[key]["priority_score"], key))

    cycles = sorted([key for key, degree in indegree.items() if degree > 0])
    blocked: dict[str, list[str]] = {}
    position = {action_id: idx for idx, action_id in enumerate(order)}
    for key, row in by_id.items():
        deps = [str(x) for x in (row.get("depends_on") or []) if str(x).strip()]
        if key in position:
            unresolved = [dep for dep in deps if dep in by_id and (dep not in position or position[dep] >= position[key])]
        else:
            unresolved = [dep for dep in deps if dep in by_id]
        if unresolved:
            blocked[key] = sorted(set(unresolved))

    return {
        "execution_order": [by_id[key] for key in order],
        "cycle_action_ids": cycles,
        "missing_dependencies": missing_dependencies,
        "blocked_by": blocked,
        "is_acyclic": not cycles,
    }


def readiness_report(payload: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    coverage = payload.get("coverage") or {}
    goal_known = boolish(payload.get("goal_known", True))
    critical_gap = boolish(payload.get("critical_gap_open"))
    unresolved_gate = boolish(payload.get("unresolved_gate"))
    material_current_evidence_block = boolish(payload.get("material_current_evidence_block"))

    if not goal_known:
        reasons.append("goal_unknown")
    if critical_gap:
        reasons.append("critical_gap_open")
    if unresolved_gate:
        reasons.append("unresolved_gate")
    if material_current_evidence_block:
        reasons.append("material_current_evidence_block")

    if reasons:
        return {"status": "BLOCKED", "reasons": reasons}

    degraded = []
    for key in ("github", "notion", "product_context"):
        value = str(coverage.get(key) or "unavailable").lower()
        if value in {"partial", "unavailable"}:
            degraded.append(f"coverage_{key}_{value}")
    if boolish(payload.get("material_unknowns_open")):
        degraded.append("material_unknowns_open")

    if boolish(payload.get("outcome_required")):
        outcome_value = str(coverage.get("outcome_data") or "unavailable").lower()
        if outcome_value in {"partial", "unavailable"}:
            degraded.append(f"coverage_outcome_data_{outcome_value}")

    if degraded:
        return {"status": "PROVISIONAL", "reasons": sorted(set(degraded))}
    return {"status": "READY", "reasons": []}


VOLATILE_FINGERPRINT_KEYS = {
    "as_of", "observed_at", "verified_at", "checked_at", "last_checked_at",
    "timestamp", "updated_at", "created_at",
}


def strip_volatile(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): strip_volatile(val)
            for key, val in sorted(value.items(), key=lambda x: str(x[0]))
            if str(key) not in VOLATILE_FINGERPRINT_KEYS
        }
    if isinstance(value, list):
        return [strip_volatile(item) for item in value]
    return value


def stable_state_payload(report: dict[str, Any]) -> dict[str, Any]:
    return strip_volatile({
        "target": report.get("target"),
        "goal": report.get("goal"),
        "horizon": report.get("horizon"),
        "state_items": report.get("state_items") or [],
        "blockers": report.get("blockers") or [],
        "drift": report.get("drift") or [],
    })


def snapshot_report(report: dict[str, Any]) -> dict[str, Any]:
    base = copy.deepcopy(report)
    base.pop("snapshot", None)
    state_fingerprint = sha256_json(stable_state_payload(base))
    snapshot_hash = sha256_json(base)
    return {
        "snapshot_version": PROTOCOL_VERSION,
        "as_of": base.get("as_of"),
        "target": base.get("target"),
        "snapshot_hash": snapshot_hash,
        "state_fingerprint": state_fingerprint,
        "report": base,
    }


def action_tier_map(report: dict[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for field, tier in (
        ("blockers", "BLOCKER"),
        ("verify_now", "VERIFY_NOW"),
        ("now", "NOW"),
        ("next", "NEXT"),
        ("later", "LATER"),
        ("stop", "STOP"),
    ):
        for action in report.get(field) or []:
            if isinstance(action, dict) and str(action.get("id") or "").strip():
                mapping[str(action["id"])] = tier
    return mapping


def item_map(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("id")): item
        for item in (report.get("state_items") or [])
        if isinstance(item, dict) and str(item.get("id") or "").strip()
    }


def delta_reports(old_payload: dict[str, Any], new_payload: dict[str, Any]) -> dict[str, Any]:
    old_report = old_payload.get("report") if isinstance(old_payload.get("report"), dict) else old_payload
    new_report = new_payload.get("report") if isinstance(new_payload.get("report"), dict) else new_payload

    old_items = item_map(old_report)
    new_items = item_map(new_report)
    transitions: list[dict[str, Any]] = []
    for item_id in sorted(set(old_items) | set(new_items)):
        if item_id not in old_items:
            transitions.append({"item_id": item_id, "kind": "NEW_ITEM"})
            continue
        if item_id not in new_items:
            transitions.append({"item_id": item_id, "kind": "REMOVED_ITEM"})
            continue
        for stage in STAGES:
            before = state_value(old_items[item_id], stage)
            after = state_value(new_items[item_id], stage)
            if before != after:
                transitions.append({"item_id": item_id, "kind": "STAGE_CHANGE", "stage": stage, "before": before, "after": after})

    old_tiers = action_tier_map(old_report)
    new_tiers = action_tier_map(new_report)
    priority_changes: list[dict[str, Any]] = []
    for action_id in sorted(set(old_tiers) | set(new_tiers)):
        before = old_tiers.get(action_id)
        after = new_tiers.get(action_id)
        if before != after:
            priority_changes.append({"action_id": action_id, "before": before, "after": after})

    old_state_fingerprint = sha256_json(stable_state_payload(old_report))
    new_state_fingerprint = sha256_json(stable_state_payload(new_report))
    thrash = []
    if old_state_fingerprint == new_state_fingerprint and priority_changes:
        thrash = [dict(change, code="PRIORITY_THRASH") for change in priority_changes]

    old_recon = reconcile_items(old_report.get("state_items") or [], as_of=old_report.get("as_of"))
    new_recon = reconcile_items(new_report.get("state_items") or [], as_of=new_report.get("as_of"))
    old_issue_keys = {(x["item_id"], x["code"]) for x in old_recon["issues"]}
    new_issue_keys = {(x["item_id"], x["code"]) for x in new_recon["issues"]}

    def entry_key(value: Any) -> str:
        if isinstance(value, dict):
            return str(value.get("id") or value.get("code") or value.get("title") or value.get("condition") or canonical_json(strip_volatile(value)))
        return str(value)

    old_blockers = {entry_key(x) for x in (old_report.get("blockers") or [])}
    new_blockers = {entry_key(x) for x in (new_report.get("blockers") or [])}

    return {
        "from_as_of": old_report.get("as_of"),
        "to_as_of": new_report.get("as_of"),
        "state_fingerprint_changed": old_state_fingerprint != new_state_fingerprint,
        "state_transitions": transitions,
        "priority_changes": priority_changes,
        "new_blockers": sorted(new_blockers - old_blockers),
        "resolved_blockers": sorted(old_blockers - new_blockers),
        "new_issues": [{"item_id": i, "code": c} for i, c in sorted(new_issue_keys - old_issue_keys)],
        "resolved_issues": [{"item_id": i, "code": c} for i, c in sorted(old_issue_keys - new_issue_keys)],
        "priority_thrash": thrash,
    }


def validate_evidence(ev: Any, path: str, errors: list[str], warnings: list[str], as_of: str | None = None) -> None:
    if not isinstance(ev, dict):
        errors.append(f"{path} must be an object")
        return
    for key in ("source", "locator", "claim", "claim_type"):
        if not str(ev.get(key) or "").strip():
            errors.append(f"{path}.{key} is required")
    freshness = evidence_freshness(ev, as_of)
    if freshness == "UNKNOWN" and boolish(ev.get("required_current")):
        errors.append(f"{path} requires current evidence but freshness is UNKNOWN")
    if freshness in {"STALE", "SUPERSEDED"} and boolish(ev.get("required_current")):
        errors.append(f"{path} requires current evidence but freshness is {freshness}")
    elif freshness == "NEAR_EXPIRY":
        warnings.append(f"{path} evidence is NEAR_EXPIRY")


def validate_action(action: Any, path: str, errors: list[str], warnings: list[str], as_of: str | None = None, require_why: bool = True) -> None:
    if not isinstance(action, dict):
        errors.append(f"{path} must be an object")
        return
    for key in ("id", "action", "done_when"):
        if not str(action.get(key) or "").strip():
            errors.append(f"{path}.{key} is required")
    if require_why and not str(action.get("why_now") or "").strip():
        errors.append(f"{path}.why_now is required")
    confidence = action.get("confidence")
    if confidence is None or clamp(confidence, 0, 1, -1) < 0:
        errors.append(f"{path}.confidence must be between 0 and 1")
    evidence = action.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append(f"{path}.evidence must be a non-empty list")
    else:
        for idx, ev in enumerate(evidence):
            validate_evidence(ev, f"{path}.evidence[{idx}]", errors, warnings, as_of=as_of)
    deps = action.get("depends_on")
    if deps is not None and not isinstance(deps, list):
        errors.append(f"{path}.depends_on must be a list")


def validate_report(report: Any) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(report, dict):
        return {"status": "FAIL", "errors": ["report must be a JSON object"], "warnings": []}

    for key in ("protocol_version", "as_of", "mode", "target", "goal", "horizon", "decision"):
        if not str(report.get(key) or "").strip():
            errors.append(f"{key} is required")

    if str(report.get("protocol_version") or "") != PROTOCOL_VERSION:
        errors.append(f"protocol_version must be {PROTOCOL_VERSION}")

    if parse_time(report.get("as_of")) is None:
        errors.append("as_of must be an ISO-8601 timestamp with timezone")

    mode = norm(report.get("mode"))
    if mode and mode not in ALLOWED_MODES:
        errors.append(f"mode must be one of {sorted(ALLOWED_MODES)}")

    coverage = report.get("coverage")
    if not isinstance(coverage, dict):
        errors.append("coverage must be an object")
    else:
        for key in ("github", "notion", "product_context", "outcome_data"):
            value = str(coverage.get(key) or "").lower()
            if value not in COVERAGE_VALUES:
                errors.append(f"coverage.{key} must be one of {sorted(COVERAGE_VALUES)}")

    readiness = report.get("readiness")
    if not isinstance(readiness, dict):
        errors.append("readiness must be an object")
    else:
        status = norm(readiness.get("status"))
        if status not in READINESS_VALUES:
            errors.append(f"readiness.status must be one of {sorted(READINESS_VALUES)}")
        if not isinstance(readiness.get("reasons") or [], list):
            errors.append("readiness.reasons must be a list")

    fields = {"blockers": None, "verify_now": 3, "now": 3, "next": 5, "later": None, "stop": None, "watch": None}
    for key, cap in fields.items():
        value = report.get(key) or []
        if not isinstance(value, list):
            errors.append(f"{key} must be a list")
            continue
        if cap is not None and len(value) > cap:
            if key in {"now", "verify_now"} and all(isinstance(x, dict) and boolish(x.get("critical_blocker")) for x in value[cap:]):
                pass
            else:
                errors.append(f"{key.upper()} may contain at most {cap} actions")
        if key in {"verify_now", "now", "next"}:
            for idx, action in enumerate(value):
                validate_action(action, f"{key}[{idx}]", errors, warnings, as_of=report.get("as_of"), require_why=True)

    for key in ("drift", "delegations", "unknowns"):
        if key in report and not isinstance(report[key], list):
            errors.append(f"{key} must be a list")

    if len(report.get("unknowns") or []) > 3:
        errors.append("unknowns may contain at most 3 material gaps")

    mutations = str(report.get("mutations") or "read-only").lower()
    if mutations not in {"read-only", "none"}:
        errors.append("Product Operator v2 must report mutations as read-only/none")

    state_items = report.get("state_items") or []
    if not isinstance(state_items, list):
        errors.append("state_items must be a list")
        state_items = []
    else:
        reconciliation = reconcile_items(state_items, as_of=report.get("as_of"))
        critical = [i for i in reconciliation["issues"] if i["severity"] == "critical"]
        inadmissible = [i for i in reconciliation["issues"] if i["code"] == "CURRENT_EVIDENCE_NOT_ADMISSIBLE"]
        if critical and not report.get("blockers") and not report.get("drift"):
            warnings.append("state_items contain critical contradictions but blockers/drift are empty")
        if inadmissible and norm((report.get("readiness") or {}).get("status")) == "READY":
            errors.append("readiness cannot be READY while required current evidence is inadmissible")

    if not report.get("now") and not report.get("verify_now") and not report.get("blockers"):
        warnings.append("report has no NOW/VERIFY_NOW action and no blocker; ensure this is intentional")

    status = "FAIL" if errors else "WARN" if warnings else "PASS"
    return {"status": status, "errors": errors, "warnings": warnings}


def main() -> int:
    parser = argparse.ArgumentParser(description="Product Operator deterministic kernel v2")
    sub = parser.add_subparsers(dest="command", required=True)

    rank_p = sub.add_parser("rank", help="Rank candidate actions")
    rank_p.add_argument("--candidates-json", required=True)

    reconcile_p = sub.add_parser("reconcile", help="Detect product-state drift")
    reconcile_p.add_argument("--items-json", required=True)
    reconcile_p.add_argument("--as-of")

    sequence_p = sub.add_parser("sequence", help="Order ranked actions by dependencies")
    sequence_p.add_argument("--candidates-json", required=True)

    readiness_p = sub.add_parser("readiness", help="Calculate decision readiness")
    readiness_p.add_argument("--input-json", required=True)

    snapshot_p = sub.add_parser("snapshot", help="Create immutable comparable snapshot")
    snapshot_p.add_argument("--report-json", required=True)

    delta_p = sub.add_parser("delta", help="Compare previous and current report/snapshot")
    delta_p.add_argument("--old-json", required=True)
    delta_p.add_argument("--new-json", required=True)

    validate_p = sub.add_parser("validate", help="Validate operator-report.json")
    validate_p.add_argument("--report-json", required=True)

    args = parser.parse_args()
    try:
        if args.command == "rank":
            payload = load_json_arg(args.candidates_json)
            rows = payload.get("candidates") if isinstance(payload, dict) else payload
            if not isinstance(rows, list):
                raise ValueError("candidates JSON must be a list or an object with candidates[]")
            result = rank_candidates(rows)
        elif args.command == "reconcile":
            payload = load_json_arg(args.items_json)
            rows = payload.get("items") if isinstance(payload, dict) else payload
            if not isinstance(rows, list):
                raise ValueError("items JSON must be a list or an object with items[]")
            result = reconcile_items(rows, as_of=args.as_of)
        elif args.command == "sequence":
            payload = load_json_arg(args.candidates_json)
            rows = payload.get("candidates") if isinstance(payload, dict) else payload
            if not isinstance(rows, list):
                raise ValueError("candidates JSON must be a list or an object with candidates[]")
            result = sequence_candidates(rows)
        elif args.command == "readiness":
            payload = load_json_arg(args.input_json)
            if not isinstance(payload, dict):
                raise ValueError("readiness input must be an object")
            result = readiness_report(payload)
        elif args.command == "snapshot":
            payload = load_json_arg(args.report_json)
            if not isinstance(payload, dict):
                raise ValueError("report JSON must be an object")
            result = snapshot_report(payload)
        elif args.command == "delta":
            old_payload = load_json_arg(args.old_json)
            new_payload = load_json_arg(args.new_json)
            if not isinstance(old_payload, dict) or not isinstance(new_payload, dict):
                raise ValueError("delta inputs must be objects")
            result = delta_reports(old_payload, new_payload)
        else:
            payload = load_json_arg(args.report_json)
            result = validate_report(payload)
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            return 1 if result["status"] == "FAIL" else 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
