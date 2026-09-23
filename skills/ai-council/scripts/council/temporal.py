from __future__ import annotations

from datetime import datetime
from typing import Any

from .constants import FRESHNESS_POLICIES, SOURCE_AUTHORITY_REGISTRY, TEMPORAL_STATUSES
from .util import _aware_time, _boolean, _rows

def source_authority_for_claim(claim_type: str) -> dict[str, Any]:
    key = str(claim_type or "general_web").strip().lower()
    if key not in SOURCE_AUTHORITY_REGISTRY:
        key = "general_web"
    row = dict(SOURCE_AUTHORITY_REGISTRY[key])
    row["claim_type"] = key
    row["policy"] = dict(FRESHNESS_POLICIES[row["freshness_policy"]])
    return row


def _hours_between(older: datetime, newer: datetime) -> float:
    if older.tzinfo is not None and newer.tzinfo is None:
        newer = newer.replace(tzinfo=older.tzinfo)
    if older.tzinfo is None and newer.tzinfo is not None:
        older = older.replace(tzinfo=newer.tzinfo)
    return max(0.0, (newer - older).total_seconds() / 3600.0)


def evaluate_temporal_truth(row: dict[str, Any], as_of: str) -> dict[str, Any]:
    now = _aware_time(as_of, "as_of")
    if not isinstance(row, dict):
        raise ValueError("temporal row must be an object")
    claim_type = row.get("claim_type", row.get("freshness_policy", "general_web"))
    known_policy = isinstance(claim_type, str) and claim_type.lower() in FRESHNESS_POLICIES
    claim_type = claim_type.lower() if isinstance(claim_type, str) else "unknown"
    policy = FRESHNESS_POLICIES.get(claim_type, {})
    material = row.get("material", True)
    status, reason, age_hours = "CURRENT", "within freshness policy", None
    parsed = {}
    fields = ("published_at", "effective_from", "effective_to", "expires_at",
              "last_verified_at", "verified_at", "observed_at")
    try:
        for name in ("material", "draft", "verified_for_decision", "system_of_record_verified"):
            if name in row:
                _boolean(row[name], name)
        if not known_policy:
            raise ValueError("unregistered freshness policy")
        for name in fields:
            parsed[name] = _aware_time(row[name], name) if row.get(name) is not None else None
        checks = [parsed[n] for n in ("last_verified_at", "verified_at", "observed_at") if parsed[n] is not None]
        if checks and any(t != checks[0] for t in checks):
            raise ValueError("conflicting verification timestamps")
        verified = checks[0] if checks else None
        if verified and verified > now:
            raise ValueError("verification is after as_of")
        if parsed["published_at"] and parsed["published_at"] > now:
            raise ValueError("publication is after as_of")
        if parsed["effective_from"] and parsed["effective_to"] and parsed["effective_to"] <= parsed["effective_from"]:
            raise ValueError("invalid effective interval")
        if parsed["expires_at"] and verified and parsed["expires_at"] < verified:
            raise ValueError("verification expiry predates verification")
        if row.get("draft", False):
            status, reason = "DRAFT", "source or rule is marked draft"
        elif row.get("superseded_by"):
            status, reason = "SUPERSEDED", "a superseding source/version is known"
        elif parsed["effective_from"] and now < parsed["effective_from"]:
            status, reason = "NOT_YET_EFFECTIVE", "effective_from is in the future"
        elif parsed["effective_to"] and now >= parsed["effective_to"]:
            status, reason = "SUPERSEDED", "effective_to has passed"
        elif parsed["expires_at"] and now >= parsed["expires_at"]:
            status, reason = "STALE", "explicit verification expiry reached"
        elif policy.get("versioned_static"):
            if not isinstance(row.get("source_version"), str) or not row["source_version"].strip():
                status, reason = "UNKNOWN", "versioned static source has no source_version"
        elif verified is None:
            status, reason = "UNKNOWN", "no last_verified_at/observed_at"
        else:
            age_hours = (now - verified).total_seconds() / 3600.0
            if policy.get("requires_system_of_record") and material and not row.get("system_of_record_verified", False):
                status, reason = "STALE", "material internal metric is not verified against system of record"
            elif policy.get("requires_live_verification") and material and not row.get("verified_for_decision", False):
                status, reason = "STALE", "material claim requires live verification for this decision"
            elif policy.get("max_age_hours") is not None and age_hours >= policy["max_age_hours"]:
                status, reason = "STALE", "verification age reaches freshness limit"
            elif policy.get("max_age_hours") is not None and age_hours > policy["max_age_hours"] * policy["near_expiry_ratio"]:
                status, reason = "NEAR_EXPIRY", "verification is near freshness limit"
    except ValueError as exc:
        status, reason = "UNKNOWN", str(exc)
        # Bad materiality is unresolved, not an opt-out from the freshness gate.
        if type(material) is not bool:
            material = True
    return {
        "claim_id": row.get("claim_id") or row.get("evidence_id") or row.get("id"),
        "claim_type": claim_type, "status": status,
        "admissible": status in {"CURRENT", "NEAR_EXPIRY"}, "material": material,
        "reason": reason, "published_at": row.get("published_at"),
        "effective_from": row.get("effective_from"), "effective_to": row.get("effective_to"),
        "expires_at": row.get("expires_at"),
        "last_verified_at": row.get("last_verified_at") or row.get("verified_at") or row.get("observed_at"),
        "age_hours": round(age_hours, 3) if age_hours is not None else None,
        "max_age_hours": policy.get("max_age_hours"),
        "requires_live_verification": bool(policy.get("requires_live_verification", False)),
        "requires_system_of_record": bool(policy.get("requires_system_of_record", False)),
        "superseded_by": row.get("superseded_by"),
        "evidence_authentication": "not_performed",
    }


def freshness_gate(rows: list[dict[str, Any]], as_of: str) -> dict[str, Any]:
    _aware_time(as_of, "as_of")
    evaluated = [evaluate_temporal_truth(row, as_of) for row in _rows(rows, "evidence")]
    blockers = [r for r in evaluated if r["material"] and not r["admissible"]]
    warnings = [r for r in evaluated if r["status"] == "NEAR_EXPIRY"]
    material_ages = [r["age_hours"] for r in evaluated if r["material"] and r["age_hours"] is not None]
    counts = {status: sum(1 for r in evaluated if r["status"] == status) for status in sorted(TEMPORAL_STATUSES)}
    return {
        "as_of": as_of,
        "status": "REFRESH_REQUIRED" if blockers or not evaluated else "CLEAR",
        "decision_ready": bool(evaluated) and not blockers,
        "coverage_assessed": False,
        "reason": "no evidence rows supplied" if not evaluated else "supplied rows evaluated",
        "material_blocker_count": len(blockers),
        "near_expiry_count": len(warnings),
        "oldest_material_evidence_hours": round(max(material_ages), 3) if material_ages else None,
        "counts": counts,
        "blockers": blockers,
        "warnings": warnings,
        "evaluated": evaluated,
    }
