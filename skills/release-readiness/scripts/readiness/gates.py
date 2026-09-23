"""Gate policy tables, evidence binding, and check/governance normalization."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from .manifest import (
    DEFAULT_CHECK_WEIGHTS,
    DOMAINS,
    EVIDENCE_LEVELS,
    EVIDENCE_RANK,
    FRESHNESS,
    GOVERNANCE_STATUSES,
    GOVERNANCE_SURFACES,
    IMMUTABLE_KEYS,
    ManifestError,
    SEVERITIES,
    STATUSES,
    _evidence_obj,
    _identity_value,
    _num,
    _parse_dt,
    _release_ids,
    _text,
)

GATE_DOMAINS = {
    "release_scope_acceptance": {"product"},
    "candidate_verification": {"qa"},
    "security_release": {"security"},
    "release_delivery": {"ops"},
    "recovery_strategy": {"ops"},
    "observability": {"ops"},
    "operator_docs": {"docs"},
    "consumer_docs": {"docs"},
    "support_path": {"support"},
    "billing_entitlements": {"billing"},
    "billing_state_transitions": {"billing"},
    "auth_access_control": {"security"},
    "migration_integrity": {"ops"},
    "sensitive_data_handling": {"security"},
    "api_compatibility": {"product", "qa"},
    "infra_resilience": {"ops"},
    "store_delivery": {"ops"},
    "incident_regression": {"qa", "ops"},
    "ai_safety_behavior": {"product", "security"},
}

GATES = (
    "release_scope_acceptance",
    "candidate_verification",
    "security_release",
    "release_delivery",
    "recovery_strategy",
    "observability",
    "operator_docs",
    "consumer_docs",
    "support_path",
    "billing_entitlements",
    "billing_state_transitions",
    "auth_access_control",
    "migration_integrity",
    "sensitive_data_handling",
    "api_compatibility",
    "infra_resilience",
    "store_delivery",
    "incident_regression",
    "ai_safety_behavior",
)

PROFILE_REQUIRED_GATES = {
    "saas_web": {
        "release_scope_acceptance", "candidate_verification", "security_release", "release_delivery",
        "recovery_strategy", "observability", "operator_docs", "support_path",
    },
    "api_service": {
        "release_scope_acceptance", "candidate_verification", "security_release", "release_delivery",
        "recovery_strategy", "observability", "operator_docs", "support_path",
    },
    "mobile_app": {
        "release_scope_acceptance", "candidate_verification", "security_release", "release_delivery",
        "recovery_strategy", "observability", "operator_docs", "support_path",
    },
    "desktop_app": {
        "release_scope_acceptance", "candidate_verification", "security_release", "release_delivery",
        "recovery_strategy", "observability", "operator_docs", "support_path",
    },
    "internal_tool": {
        "release_scope_acceptance", "candidate_verification", "security_release", "release_delivery",
        "recovery_strategy", "observability", "operator_docs", "support_path",
    },
    "oss_library": {
        "release_scope_acceptance", "candidate_verification", "security_release", "release_delivery",
        "consumer_docs", "support_path",
    },
    "generic": {
        "release_scope_acceptance", "candidate_verification", "security_release", "release_delivery",
        "recovery_strategy", "observability", "operator_docs", "support_path",
    },
}

CONDITIONAL_GATES = {
    "auth_change": {"auth_access_control"},
    "billing_change": {"billing_entitlements", "billing_state_transitions"},
    "schema_or_data_migration": {"migration_integrity", "recovery_strategy"},
    "sensitive_data_change": {"sensitive_data_handling"},
    "public_api_breaking_change": {"api_compatibility"},
    "major_infra_change": {"infra_resilience", "recovery_strategy", "observability"},
    "mobile_store_release": {"store_delivery"},
    "incident_recovery_release": {"incident_regression"},
    "high_impact_ai_change": {"ai_safety_behavior"},
}

# Floors follow the canonical bootstrapper; a manifest may strengthen, not lower them.
GATE_EVIDENCE_FLOORS = {gate: "verified" for gate in GATES}
GATE_EVIDENCE_FLOORS.update({gate: "supported" for gate in ("operator_docs", "consumer_docs", "support_path")})


def _evidence_time_issues(evidence: Dict[str, Any], as_of: datetime | None) -> List[str]:
    issues = []
    supplied = [evidence[k] for k in ("last_verified_at", "observed_at") if k in evidence]
    times = [_parse_dt(v) for v in supplied]
    if not times or any(t is None for t in times):
        issues.append("observation_time_missing_or_invalid")
    elif len(set(times)) != 1:
        issues.append("observation_times_conflict")
    elif as_of is None or times[0] > as_of:
        issues.append("observation_after_assessment")
    if "expires_at" in evidence:
        expiry = _parse_dt(evidence["expires_at"])
        if expiry is None:
            issues.append("expiry_invalid")
        elif as_of is None or expiry <= as_of:
            issues.append("evidence_expired")
        elif times and times[0] is not None and expiry <= times[0]:
            issues.append("expiry_before_observation")
    return issues


def _candidate_evidence_matches(ref: Any, release: Dict[str, Any]) -> bool:
    pinned = {k: _identity_value(k, release.get(k)) for k in IMMUTABLE_KEYS}
    pinned = {k: v for k, v in pinned.items() if v}
    if not pinned:
        return False
    if isinstance(ref, dict):
        allowed = set(IMMUTABLE_KEYS) | {"id", "tag", "deployment_id", "environment", "config_digest"}
        if not ref or set(ref) - allowed:
            return False
        if any(_identity_value(k, ref.get(k)) != v for k, v in pinned.items()):
            return False
        return all(_identity_value(k, v) and _identity_value(k, v) == _identity_value(k, release.get(k)) for k, v in ref.items())
    refs = ref if isinstance(ref, list) else [ref]
    # No prefix matching and no release-name/tag substitution for immutable identity.
    if not refs or any(not isinstance(v, str) or not v.strip() for v in refs):
        return False
    values = {v.strip() for v in refs}
    return set(pinned.values()) <= values and values <= _release_ids(release)


def _binding_evidence_issues(check: Dict[str, Any], release: Dict[str, Any]) -> List[str]:
    evidence = check.get("evidence") or {}
    issues = []
    if not _text(evidence.get("summary")):
        issues.append("evidence_summary_missing")
    issues.extend(_evidence_time_issues(evidence, _parse_dt(release.get("as_of"))))
    if check["required_evidence"] == "verified":
        if not _candidate_evidence_matches(evidence.get("candidate_ref"), release):
            issues.append("candidate_binding_missing_or_mismatched")
        if not _text(evidence.get("environment")) or evidence.get("environment") != release.get("environment"):
            issues.append("environment_missing_or_mismatched")
        if release.get("config_digest") and evidence.get("config_digest") != release["config_digest"]:
            issues.append("configuration_missing_or_mismatched")
    elif "environment" in evidence and evidence["environment"] != release.get("environment"):
        issues.append("environment_mismatched")
    return issues


def _candidate_matches(ref: Any, release_ids: set[str]) -> bool:
    """Exact legacy helper; verdict binding additionally checks immutable field identity."""
    refs = ref if isinstance(ref, list) else [ref]
    return bool(refs) and all(isinstance(v, str) and v.strip() in release_ids for v in refs)


def _required_gates(profile: str, scope: Dict[str, Any]) -> List[str]:
    required = set(PROFILE_REQUIRED_GATES[profile])
    if scope["commercial"] == "paid":
        required.add("billing_entitlements")
    for flag, gates in CONDITIONAL_GATES.items():
        if scope["risk_flags"].get(flag) == "yes":
            required |= set(gates)
    return sorted(required)


def _normalize_check(raw: Dict[str, Any], seen: set[str], release: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        raise ManifestError("each check must be an object")
    check_id = _text(raw.get("id"))
    if not check_id:
        raise ManifestError("each check requires a non-empty id")
    if check_id in seen:
        raise ManifestError(f"duplicate check id: {check_id}")
    seen.add(check_id)

    domain = str(raw.get("domain", "")).lower().strip()
    if domain not in DOMAINS:
        raise ManifestError(f"{check_id}: invalid domain {domain!r}")
    gate = str(raw.get("gate", "")).lower().strip()
    if gate and gate not in GATES:
        raise ManifestError(f"{check_id}: invalid gate {gate!r}")
    if gate and domain not in GATE_DOMAINS[gate]:
        allowed = ", ".join(sorted(GATE_DOMAINS[gate]))
        raise ManifestError(f"{check_id}: gate {gate!r} cannot be satisfied by domain {domain!r}; allowed: {allowed}")

    status = str(raw.get("status", "unknown")).lower().strip()
    if status not in STATUSES:
        raise ManifestError(f"{check_id}: invalid status {status!r}")
    severity = str(raw.get("severity", "major")).lower().strip()
    if severity not in SEVERITIES:
        raise ManifestError(f"{check_id}: invalid severity {severity!r}")
    binding = raw.get("binding", False)
    applicable = raw.get("applicable", True)
    if type(binding) is not bool or type(applicable) is not bool:
        raise ManifestError(f"{check_id}: binding and applicable must be booleans")
    if not applicable:
        status = "na"

    if status == "accepted_risk" and (binding or severity in ("blocker", "critical")):
        raise ManifestError(f"{check_id}: accepted_risk is forbidden for binding/blocker/critical checks")

    evidence_level = str(raw.get("evidence_level", "missing")).lower().strip()
    if evidence_level not in EVIDENCE_LEVELS:
        raise ManifestError(f"{check_id}: invalid evidence_level {evidence_level!r}")
    required_default = "verified" if binding else "supported"
    required_evidence = str(raw.get("required_evidence", required_default)).lower().strip()
    if required_evidence not in EVIDENCE_LEVELS:
        raise ManifestError(f"{check_id}: invalid required_evidence {required_evidence!r}")
    requested_evidence = required_evidence
    if binding:
        floor = GATE_EVIDENCE_FLOORS.get(gate, "verified")
        required_evidence = max((required_evidence, floor), key=EVIDENCE_RANK.get)
    freshness = str(raw.get("freshness", "unknown")).lower().strip()
    if freshness not in FRESHNESS:
        raise ManifestError(f"{check_id}: invalid freshness {freshness!r}")

    weight = _num(raw.get("weight", DEFAULT_CHECK_WEIGHTS[severity]), f"{check_id}.weight")
    if weight <= 0:
        raise ManifestError(f"{check_id}.weight must be > 0")
    na_reason = _text(raw.get("na_reason"))
    if status == "na" and not na_reason:
        raise ManifestError(f"{check_id}: N/A requires na_reason")

    normalized = dict(raw)
    normalized.update({
        "id": check_id,
        "domain": domain,
        "gate": gate,
        "status": status,
        "severity": severity,
        "binding": binding,
        "applicable": status != "na",
        "evidence_level": evidence_level,
        "required_evidence": required_evidence,
        "requested_required_evidence": requested_evidence,
        "freshness": freshness,
        "weight": weight,
        "evidence": _evidence_obj(raw.get("evidence")),
    })
    normalized["evidence_issues"] = _binding_evidence_issues(normalized, release) if binding or status in ("pass", "pass_with_controls", "accepted_risk") else []
    normalized["effective_status"] = _effective_status(normalized, release)
    return normalized


def _control_valid(check: Dict[str, Any], as_of: datetime | None) -> bool:
    if not _text(check.get("control_owner")):
        return False
    if not _text(check.get("mitigation")):
        return False
    due = _parse_dt(check.get("control_due"))
    if due is None:
        return False
    if as_of and due <= as_of:
        return False
    return True


def _risk_acceptance_valid(check: Dict[str, Any], as_of: datetime | None) -> bool:
    ra = check.get("risk_acceptance")
    if not isinstance(ra, dict):
        return False
    for key in ("approved_by", "owner", "rationale", "mitigation", "expires_at"):
        if not _text(ra.get(key)):
            return False
    expiry = _parse_dt(ra.get("expires_at"))
    if expiry is None:
        return False
    return as_of is not None and expiry > as_of


def _binding_evidence_valid(check: Dict[str, Any], release: Dict[str, Any]) -> bool:
    return not _binding_evidence_issues(check, release)


def _effective_status(check: Dict[str, Any], release: Dict[str, Any]) -> str:
    status = check["status"]
    if status == "na":
        return "na"
    if status == "unknown":
        return "unknown"
    if status == "fail":
        return "unknown" if check["evidence_level"] == "missing" else "fail"

    as_of = _parse_dt(release.get("as_of"))
    if status == "pass_with_controls" and not _control_valid(check, as_of):
        return "unknown"
    if status == "accepted_risk" and not _risk_acceptance_valid(check, as_of):
        return "unknown"

    if EVIDENCE_RANK[check["evidence_level"]] < EVIDENCE_RANK[check["required_evidence"]]:
        return "unknown"
    if check["freshness"] != "current":
        return "unknown"
    if status in ("pass", "pass_with_controls", "accepted_risk") and not _binding_evidence_valid(check, release):
        return "unknown"
    if status == "accepted_risk" and not _text((check.get("evidence") or {}).get("summary")):
        return "unknown"
    return status


def _normalize_governance_gate(raw: Dict[str, Any], as_of: datetime | None, release: Dict[str, Any] | None = None) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        raise ManifestError("each governance gate must be an object")
    surface = str(raw.get("surface", "")).lower().strip()
    if surface not in GOVERNANCE_SURFACES:
        raise ManifestError(f"invalid governance gate surface: {surface!r}")
    status = str(raw.get("status", "counsel_required")).lower().strip()
    if status not in GOVERNANCE_STATUSES:
        raise ManifestError(f"{surface}: invalid governance status {status!r}")
    evidence = _evidence_obj(raw.get("evidence"))
    effective = status
    if status == "not_required" and not _text(raw.get("rationale")):
        effective = "counsel_required"
    if status in ("clear", "clear_with_controls"):
        if not _text(evidence.get("summary")) or _evidence_time_issues(evidence, as_of):
            effective = "counsel_required"
        if release is not None:
            if "environment" in evidence and evidence["environment"] != release.get("environment"):
                effective = "counsel_required"
            if "candidate_ref" in evidence and not _candidate_evidence_matches(evidence["candidate_ref"], release):
                effective = "counsel_required"
    if status == "clear_with_controls":
        temp = {
            "control_owner": raw.get("control_owner"),
            "mitigation": raw.get("control"),
            "control_due": raw.get("control_due"),
        }
        if not _control_valid(temp, as_of):
            effective = "counsel_required"
    out = dict(raw)
    out.update({"surface": surface, "status": status, "effective_status": effective, "evidence": evidence})
    return out

