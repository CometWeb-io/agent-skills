"""Temporal freshness evaluation for sources."""
from __future__ import annotations

import math
from datetime import timedelta
from typing import Any, Dict, Optional

from .constants import DEFAULT_TTL_DAYS, LIVE_VERIFICATION_TYPES, POLICY_VERSION
from .util import _parse_dt


def temporal_status(
    source: Dict[str, Any], as_of_text: str, claim_type: Optional[str] = None,
    *, research_id: Optional[str] = None, research_started_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Evaluate supplied dates, not source truth or authenticity of inspection.

    Positive cache TTLs are ceilings even for live-verification classes. A zero
    cache window requires explicit current-run binding and a bounded run interval.
    """
    def result(status, reason, **extra):
        return {"temporal_status": status, "reason": reason,
                "policy_version": POLICY_VERSION, **extra}

    as_of = _parse_dt(as_of_text)
    if as_of is None or not isinstance(source, dict):
        return result("UNKNOWN", "source must be an object and as_of must be a timezone-aware timestamp")
    ctype = claim_type or source.get("claim_type") or "current_fact"
    if not isinstance(ctype, str):
        return result("UNKNOWN", "invalid claim_type")
    for field in ("requires_live_verification", "verified_for_research"):
        if field in source and type(source[field]) is not bool:
            return result("UNKNOWN", f"{field} must be boolean")
    state = source.get("source_state", "final")
    if not isinstance(state, str) or state.strip().casefold() not in {"final", "draft", "superseded", "withdrawn"}:
        return result("UNKNOWN", "invalid source_state")
    state = state.strip().casefold()
    if source.get("superseded_by_source_id") or source.get("superseded_by") or state in {"superseded", "withdrawn"}:
        return result("SUPERSEDED", "source is superseded or withdrawn")
    if state == "draft":
        return result("DRAFT", "source_state is draft")

    parsed = {}
    for field in ("published_at", "effective_from", "effective_to", "last_verified_at", "expires_at"):
        value = source.get(field)
        parsed[field] = _parse_dt(value)
        if value is not None and parsed[field] is None:
            return result("UNKNOWN", f"invalid {field}")
    published, start, end, observed, expires = (parsed[f] for f in
        ("published_at", "effective_from", "effective_to", "last_verified_at", "expires_at"))
    if start and end and end <= start:
        return result("UNKNOWN", "effective interval is empty or reversed")
    if published and published > as_of:
        return result("UNKNOWN", "published_at is after as_of")
    if observed and observed > as_of:
        return result("UNKNOWN", "last_verified_at is after as_of")
    if published and observed and published > observed:
        return result("UNKNOWN", "verification predates the published artifact")
    if start and start > as_of:
        return result("NOT_YET_EFFECTIVE", "effective_from is after as_of")
    if end and end <= as_of:
        return result("STALE", "effective interval has ended")
    if expires and expires <= as_of:
        return result("STALE", "verification has expired")

    requires_live = source.get("requires_live_verification") is True or ctype in LIVE_VERIFICATION_TYPES
    if requires_live and source.get("verified_for_research") is not True:
        return result("UNKNOWN", "live verification required but not explicitly recorded", requires_live_verification=True)
    if observed is None:
        return result("UNKNOWN", "last_verified_at is required")

    default = DEFAULT_TTL_DAYS.get(ctype)
    explicit = source.get("freshness_ttl_days")
    if explicit is not None:
        if type(explicit) not in (int, float) or not math.isfinite(explicit) or not 0 <= explicit <= 36500:
            return result("UNKNOWN", "invalid freshness_ttl_days")
    ttl = default if explicit is None else min(default, explicit) if default is not None else explicit
    if ttl is None:
        return result("UNKNOWN", "unregistered claim type needs an explicit freshness policy")

    bound_run = source.get("verified_research_id")
    if bound_run is not None:
        if not isinstance(bound_run, str) or not bound_run.strip() or not research_id or bound_run != research_id:
            return result("UNKNOWN", "verification belongs to an unconfirmed or different research run")
    run_start = _parse_dt(research_started_at)
    if research_started_at is not None and (run_start is None or run_start > as_of):
        return result("UNKNOWN", "invalid research start")
    if bound_run is not None and run_start is not None and observed < run_start:
        return result("UNKNOWN", "verification predates this research run")
    if ttl == 0:
        if source.get("verified_for_research") is not True or not bound_run or run_start is None or observed < run_start:
            return result("UNKNOWN", "zero-cache evidence needs verified_research_id and research_contract.started_at")
        return result("CURRENT", "verified within the explicitly identified research run; not reusable cache",
                      requires_live_verification=requires_live, verification_run_bound=True)
    try:
        expiry = observed + timedelta(days=ttl)
        near = observed + timedelta(days=ttl * 0.8)
    except (OverflowError, ValueError):
        return result("UNKNOWN", "freshness window exceeds timestamp range")
    if as_of >= expiry:
        return result("STALE", "verification age exceeds freshness policy", computed_expires_at=expiry.isoformat())
    status = "NEAR_EXPIRY" if as_of >= near else "CURRENT"
    return result(status, "verification is within freshness policy", computed_expires_at=expiry.isoformat(),
                  requires_live_verification=requires_live, verification_run_bound=bool(bound_run))

