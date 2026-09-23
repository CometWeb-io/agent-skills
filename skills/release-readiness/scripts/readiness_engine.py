#!/usr/bin/env python3
"""Deterministic release-readiness gate engine v2.

The engine intentionally separates:
- scope completeness,
- required-gate completeness,
- evidence admissibility,
- governance gates,
- weighted readiness,
- release verdict.

A high score can never override a binding failure, a missing required gate,
or an unresolved governance blocker.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

MANIFEST_VERSION = 2
ENGINE_VERSION = "2.1.0"

DOMAINS = ("product", "qa", "security", "ops", "docs", "billing", "support")
PROFILES = ("saas_web", "api_service", "mobile_app", "desktop_app", "internal_tool", "oss_library", "generic")
MODES = ("fast", "standard", "deep")
STATUSES = ("pass", "pass_with_controls", "accepted_risk", "fail", "unknown", "na")
SEVERITIES = ("blocker", "critical", "major", "minor")
EVIDENCE_LEVELS = ("missing", "claimed", "supported", "verified")
FRESHNESS = ("current", "stale", "mismatched", "unknown")
TRI = ("yes", "no", "unknown")
AUDIENCES = ("external", "internal", "library_consumers", "unknown")
COMMERCIAL = ("paid", "free", "not_applicable", "unknown")

GOVERNANCE_SURFACES = ("legal", "privacy", "financial_risk", "responsible_ai", "reputation", "platform_policy")
GOVERNANCE_STATUSES = ("not_required", "clear", "clear_with_controls", "counsel_required", "block")

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

SCOPE_FLAG_KEYS = (
    "first_production_release",
    "auth_change",
    "billing_change",
    "schema_or_data_migration",
    "sensitive_data_change",
    "public_api_breaking_change",
    "major_infra_change",
    "mobile_store_release",
    "incident_recovery_release",
    "high_impact_ai_change",
    "legal_or_regulatory_change",
)

HIGH_RISK_FLAGS = {
    "first_production_release",
    "auth_change",
    "billing_change",
    "schema_or_data_migration",
    "sensitive_data_change",
    "high_impact_ai_change",
    "legal_or_regulatory_change",
}
ELEVATED_RISK_FLAGS = {
    "public_api_breaking_change",
    "major_infra_change",
    "mobile_store_release",
    "incident_recovery_release",
}

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

FLAG_GOVERNANCE_SURFACES = {
    "sensitive_data_change": {"privacy"},
    "mobile_store_release": {"platform_policy"},
    "high_impact_ai_change": {"responsible_ai"},
    "legal_or_regulatory_change": {"legal"},
}

DEFAULT_DOMAIN_WEIGHTS = {
    "product": 15.0,
    "qa": 20.0,
    "security": 20.0,
    "ops": 20.0,
    "docs": 10.0,
    "billing": 8.0,
    "support": 7.0,
}
DEFAULT_CHECK_WEIGHTS = {"blocker": 8.0, "critical": 5.0, "major": 3.0, "minor": 1.0}
STATUS_CREDIT = {"pass": 1.0, "pass_with_controls": 0.75, "accepted_risk": 0.50, "fail": 0.0, "unknown": 0.0}
EVIDENCE_RANK = {name: idx for idx, name in enumerate(EVIDENCE_LEVELS)}
MODE_RANK = {"fast": 1, "standard": 2, "deep": 3}
RISK_MODE_FLOOR = {"R1": "fast", "R2": "standard", "R3": "deep"}
RISK_THRESHOLD_FLOORS = {
    "R1": {"go_score": 88.0, "conditional_score": 78.0, "min_coverage": 90.0},
    "R2": {"go_score": 92.0, "conditional_score": 84.0, "min_coverage": 95.0},
    "R3": {"go_score": 95.0, "conditional_score": 90.0, "min_coverage": 98.0},
}


class ManifestError(ValueError):
    pass



# Floors follow the canonical bootstrapper; a manifest may strengthen, not lower them.
GATE_EVIDENCE_FLOORS = {gate: "verified" for gate in GATES}
GATE_EVIDENCE_FLOORS.update({gate: "supported" for gate in ("operator_docs", "consumer_docs", "support_path")})
IMMUTABLE_KEYS = ("commit_sha", "artifact_id", "image_digest", "build_number")
MAX_INPUT_BYTES = 4 * 1024 * 1024


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _identity_value(key: str, value: Any) -> str:
    if key == "build_number" and type(value) is int and value >= 0:
        return str(value)
    value = _text(value)
    if not value or len(value) > 512 or value.casefold() in {"none", "null", "unknown", "n/a"}:
        return ""
    if key == "commit_sha" and not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", value):
        return ""
    if key == "image_digest" and not re.fullmatch(r"(?:sha256:[0-9a-f]{64}|sha512:[0-9a-f]{128})", value):
        return ""
    return value


def _validate_json(value: Any, depth: int = 0, budget: List[int] | None = None) -> None:
    if budget is None:
        budget = [100000]
    budget[0] -= 1
    if depth > 64 or budget[0] < 0:
        raise ManifestError("manifest complexity exceeds limit")
    if value is None or type(value) in (str, bool):
        return
    if type(value) is int:
        if value.bit_length() > 8192:
            raise ManifestError("integer exceeds rendering budget")
        return
    if type(value) is float and math.isfinite(value):
        return
    if isinstance(value, dict):
        if any(not isinstance(k, str) for k in value):
            raise ManifestError("JSON keys must be strings")
        for item in value.values():
            _validate_json(item, depth + 1, budget)
        return
    if isinstance(value, list):
        for item in value:
            _validate_json(item, depth + 1, budget)
        return
    raise ManifestError("manifest contains a non-JSON or non-finite value")


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ManifestError("duplicate JSON key")
        result[key] = value
    return result


def _invalid_constant(value):
    raise ManifestError("non-finite JSON constant")


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


def _contract_check(check: Dict[str, Any]) -> Dict[str, Any]:
    return {k: check.get(k) for k in ("id", "gate", "domain", "title", "severity", "binding", "applicable", "required_evidence", "weight")}


def _contract_hash(profile, scope, checks, domain_weights, thresholds, mode) -> str:
    return _snapshot_hash({"profile": profile, "scope": scope, "mode": mode,
                           "checks": sorted((_contract_check(c) for c in checks), key=lambda c: c["id"]),
                           "domain_weights": domain_weights, "thresholds": thresholds})


def _num(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ManifestError(f"{name} must be numeric")
    try:
        number = float(value)
    except OverflowError as exc:
        raise ManifestError(f"{name} exceeds numeric range") from exc
    if not math.isfinite(number):
        raise ManifestError(f"{name} must be finite")
    return number


def _pct(value: Any, name: str) -> float:
    number = _num(value, name)
    if number < 0 or number > 100:
        raise ManifestError(f"{name} must be between 0 and 100")
    return number


def _parse_dt(value: Any) -> datetime | None:
    value = _text(value)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})", value):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except (ValueError, OverflowError):
        return None


def _release_identity_gaps(release: Dict[str, Any]) -> List[str]:
    gaps = [k for k in ("id", "environment", "as_of") if not _identity_value(k, release.get(k))]
    if _parse_dt(release.get("as_of")) is None:
        gaps.append("as_of_invalid")
    elif _parse_dt(release["as_of"]) > datetime.now(timezone.utc):
        gaps.append("as_of_in_future")
    if not any(_identity_value(k, release.get(k)) for k in IMMUTABLE_KEYS):
        gaps.append("artifact_identity")
    for k in IMMUTABLE_KEYS:
        if k in release and not _identity_value(k, release[k]):
            gaps.append(k + "_invalid")
    if "config_digest" in release and not _identity_value("config_digest", release["config_digest"]):
        gaps.append("config_digest_invalid")
    return sorted(set(gaps))


def _release_ids(release: Dict[str, Any]) -> set[str]:
    keys = (*IMMUTABLE_KEYS, "id", "tag", "deployment_id")
    return {v for k in keys if (v := _identity_value(k, release.get(k)))}


def _candidate_matches(ref: Any, release_ids: set[str]) -> bool:
    """Exact legacy helper; verdict binding additionally checks immutable field identity."""
    refs = ref if isinstance(ref, list) else [ref]
    return bool(refs) and all(isinstance(v, str) and v.strip() in release_ids for v in refs)


def _evidence_obj(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, str) and raw.strip():
        return {"summary": raw.strip()}
    return {}


def _normalize_scope(raw: Any, profile: str) -> Tuple[Dict[str, Any], List[str], str, set[str]]:
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ManifestError("scope must be an object")
    audience = str(raw.get("audience", "unknown")).lower().strip()
    if audience not in AUDIENCES:
        raise ManifestError(f"scope.audience invalid: {audience!r}")
    commercial = str(raw.get("commercial", "unknown")).lower().strip()
    if commercial not in COMMERCIAL:
        raise ManifestError(f"scope.commercial invalid: {commercial!r}")

    raw_flags = raw.get("risk_flags", {})
    if not isinstance(raw_flags, dict):
        raise ManifestError("scope.risk_flags must be an object")
    if set(raw_flags) - set(SCOPE_FLAG_KEYS):
        raise ManifestError("unknown risk flag; check spelling")
    flags: Dict[str, str] = {}
    gaps: List[str] = []
    for key in SCOPE_FLAG_KEYS:
        value = str(raw_flags.get(key, "unknown")).lower().strip()
        if value not in TRI:
            raise ManifestError(f"scope.risk_flags.{key} invalid: {value!r}")
        flags[key] = value
        if value == "unknown":
            gaps.append(f"risk_flag:{key}")

    if audience == "unknown":
        gaps.append("audience")
    if commercial == "unknown":
        gaps.append("commercial")
    if raw.get("risk_assessment_complete") is not True:
        gaps.append("risk_assessment_complete")

    explicit_surfaces = raw.get("governance_surfaces", [])
    if not isinstance(explicit_surfaces, list):
        raise ManifestError("scope.governance_surfaces must be an array")
    surfaces: set[str] = set()
    for surface in explicit_surfaces:
        s = str(surface).lower().strip()
        if s not in GOVERNANCE_SURFACES:
            raise ManifestError(f"invalid governance surface: {s!r}")
        surfaces.add(s)
    for flag, derived in FLAG_GOVERNANCE_SURFACES.items():
        if flags.get(flag) == "yes":
            surfaces |= set(derived)

    yes_flags = {k for k, v in flags.items() if v == "yes"}
    if yes_flags & HIGH_RISK_FLAGS:
        risk_tier = "R3"
    elif yes_flags & ELEVATED_RISK_FLAGS:
        risk_tier = "R2"
    else:
        risk_tier = "R1"

    normalized = {
        "audience": audience,
        "commercial": commercial,
        "risk_flags": flags,
        "governance_surfaces": sorted(surfaces),
        "risk_assessment_complete": raw.get("risk_assessment_complete") is True,
        "notes": str(raw.get("notes", ""))[:1000],
    }
    return normalized, gaps, risk_tier, surfaces


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


def _domain_weights(raw: Any) -> Dict[str, float]:
    weights = dict(DEFAULT_DOMAIN_WEIGHTS)
    if raw is None:
        return weights
    if not isinstance(raw, dict):
        raise ManifestError("domain_weights must be an object")
    for domain, value in raw.items():
        if domain not in DOMAINS:
            raise ManifestError(f"invalid domain weight key: {domain}")
        number = _num(value, f"domain_weights.{domain}")
        if number < 0:
            raise ManifestError(f"domain_weights.{domain} must be >= 0")
        weights[domain] = number
    if not any(v > 0 for v in weights.values()):
        raise ManifestError("domain_weights must contain positive total weight")
    return weights


def _thresholds(raw: Any, risk_tier: str) -> Dict[str, float]:
    raw = {} if raw is None else raw
    if not isinstance(raw, dict):
        raise ManifestError("thresholds must be an object")
    floor = RISK_THRESHOLD_FLOORS[risk_tier]
    supplied_go = _pct(raw.get("go_score", floor["go_score"]), "thresholds.go_score")
    supplied_cond = _pct(raw.get("conditional_score", floor["conditional_score"]), "thresholds.conditional_score")
    supplied_cov = _pct(raw.get("min_coverage", floor["min_coverage"]), "thresholds.min_coverage")
    result = {
        "go_score": max(floor["go_score"], supplied_go),
        "conditional_score": max(floor["conditional_score"], supplied_cond),
        "min_coverage": max(floor["min_coverage"], supplied_cov),
    }
    if result["conditional_score"] > result["go_score"]:
        raise ManifestError("conditional_score cannot exceed go_score")
    return result


def _summarize_domain(checks: Iterable[Dict[str, Any]]) -> Tuple[float, float, int]:
    applicable = [c for c in checks if c["effective_status"] != "na"]
    if not applicable:
        return 0.0, 0.0, 0
    scale = max(c["weight"] for c in applicable)
    weights = [c["weight"] / scale for c in applicable]
    total = math.fsum(weights)
    earned = math.fsum(w * STATUS_CREDIT[c["effective_status"]] for c, w in zip(applicable, weights, strict=True))
    known = math.fsum(w for c, w in zip(applicable, weights, strict=True) if c["effective_status"] != "unknown")
    return (100.0 * (earned / total), 100.0 * (known / total), len(applicable))


def _snapshot_hash(manifest: Dict[str, Any]) -> str:
    canonical = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _revalidation_triggers(scope: Dict[str, Any]) -> List[str]:
    triggers = [
        "release candidate artifact, commit, tag, or build changes",
        "target environment or material production configuration changes",
        "a binding test, scan, deployment check, or runtime verification becomes invalid or expires",
        "a new blocker/critical/major finding appears in assessed scope",
        "a compensating control or accepted-risk approval expires",
        "a related incident occurs during rollout or immediately after release",
    ]
    if scope["commercial"] == "paid" or scope["risk_flags"].get("billing_change") == "yes":
        triggers.append("billing provider configuration, price/plan mapping, webhook behavior, or entitlement logic changes")
    if scope["risk_flags"].get("schema_or_data_migration") == "yes":
        triggers.append("migration plan, migration artifact, schema, backfill data set, or recovery procedure changes")
    if scope["risk_flags"].get("mobile_store_release") == "yes":
        triggers.append("store submission artifact, signing/provisioning state, or applicable platform policy changes")
    if scope.get("governance_surfaces"):
        triggers.append("material evidence underlying a governance gate changes or is superseded")
    return triggers


def _slim_check(c: Dict[str, Any]) -> Dict[str, Any]:
    evidence = c.get("evidence") or {}
    return {
        "id": c["id"],
        "gate": c.get("gate", ""),
        "domain": c["domain"],
        "title": c.get("title", ""),
        "severity": c["severity"],
        "status": c["status"],
        "effective_status": c["effective_status"],
        "evidence_level": c["evidence_level"],
        "freshness": c["freshness"],
        "evidence": evidence,
        "owner": c.get("owner", ""),
        "mitigation": c.get("mitigation", ""),
        "control_owner": c.get("control_owner", ""),
        "control_due": c.get("control_due", ""),
        "risk_acceptance": c.get("risk_acceptance"),
        "evidence_issues": c.get("evidence_issues", []),
    }


def evaluate(manifest: Dict[str, Any], *, expected_contract_hash: str | None = None) -> Dict[str, Any]:
    if not isinstance(manifest, dict):
        raise ManifestError("manifest must be a JSON object")
    _validate_json(manifest)
    if expected_contract_hash is not None and not re.fullmatch(r"[0-9a-f]{64}", expected_contract_hash):
        raise ManifestError("expected_contract_hash must be a SHA-256")
    if type(manifest.get("manifest_version")) is not int or manifest.get("manifest_version") != MANIFEST_VERSION:
        raise ManifestError(f"manifest_version must be {MANIFEST_VERSION}")

    profile = str(manifest.get("profile", "generic")).lower().strip()
    if profile not in PROFILES:
        raise ManifestError(f"invalid profile: {profile!r}")
    mode = str(manifest.get("mode", "standard")).lower().strip()
    if mode not in MODES:
        raise ManifestError(f"invalid mode: {mode!r}")

    release = manifest.get("release", {})
    if not isinstance(release, dict):
        raise ManifestError("release must be an object")
    identity_gaps = _release_identity_gaps(release)
    scope, scope_gaps, risk_tier, governance_surfaces = _normalize_scope(manifest.get("scope"), profile)
    mode_floor = RISK_MODE_FLOOR[risk_tier]
    mode_gap = MODE_RANK[mode] < MODE_RANK[mode_floor]

    raw_checks = manifest.get("checks")
    if not isinstance(raw_checks, list) or not raw_checks:
        raise ManifestError("checks must be a non-empty array")
    seen: set[str] = set()
    checks = [_normalize_check(raw, seen, release) for raw in raw_checks]

    required_gates = _required_gates(profile, scope)
    gate_members: Dict[str, List[Dict[str, Any]]] = {g: [] for g in GATES}
    for check in checks:
        if check.get("gate"):
            gate_members[check["gate"]].append(check)
    missing_required_gates: List[str] = []
    for gate in required_gates:
        members = [c for c in gate_members.get(gate, []) if c["effective_status"] != "na"]
        if not members or not any(c["binding"] for c in members):
            missing_required_gates.append(gate)

    as_of = _parse_dt(release.get("as_of"))
    raw_governance = manifest.get("governance_gates", [])
    if not isinstance(raw_governance, list):
        raise ManifestError("governance_gates must be an array")
    governance = [_normalize_governance_gate(row, as_of, release) for row in raw_governance]
    seen_surfaces: set[str] = set()
    for gate in governance:
        if gate["surface"] in seen_surfaces:
            raise ManifestError(f"duplicate governance gate: {gate['surface']}")
        seen_surfaces.add(gate["surface"])
    governance_by_surface = {g["surface"]: g for g in governance}
    missing_governance_gates = sorted(governance_surfaces - set(governance_by_surface))
    # Any explicitly recorded BLOCK/COUNSEL_REQUIRED/controlled gate is material by construction.
    # Required surfaces additionally reject NOT_REQUIRED as an invalid way to satisfy a routed gate.
    governance_blocks = [g for g in governance if g["effective_status"] == "block"]
    governance_unknowns = [
        g for g in governance
        if g["effective_status"] == "counsel_required"
        or (g["surface"] in governance_surfaces and g["effective_status"] == "not_required")
    ]
    governance_controls = [g for g in governance if g["effective_status"] == "clear_with_controls"]

    domain_weights = _domain_weights(manifest.get("domain_weights"))
    thresholds = _thresholds(manifest.get("thresholds"), risk_tier)
    by_domain: Dict[str, List[Dict[str, Any]]] = {domain: [] for domain in DOMAINS}
    for check in checks:
        by_domain[check["domain"]].append(check)

    contract_hash = _contract_hash(profile, scope, checks, domain_weights, thresholds, mode)
    contract_mismatch = expected_contract_hash is not None and expected_contract_hash != contract_hash
    domain_results: Dict[str, Dict[str, Any]] = {}
    unrounded_domains = {}
    active_domains: List[str] = []
    for domain in DOMAINS:
        score, coverage, count = _summarize_domain(by_domain[domain])
        if count:
            unrounded_domains[domain] = (score, coverage)
            active_domains.append(domain)
            domain_results[domain] = {"score": round(score, 1), "coverage": round(coverage, 1), "applicable_checks": count}
        else:
            domain_results[domain] = {"score": None, "coverage": None, "applicable_checks": 0}

    scale = max((domain_weights[d] for d in active_domains), default=0)
    if scale <= 0:
        raise ManifestError("applicable domains have zero total domain weight")
    weights = {d: domain_weights[d] / scale for d in active_domains}
    total = math.fsum(weights.values())
    overall_score = math.fsum(unrounded_domains[d][0] * weights[d] for d in active_domains) / total
    overall_coverage = math.fsum(unrounded_domains[d][1] * weights[d] for d in active_domains) / total

    binding_failures = [c for c in checks if c["binding"] and c["effective_status"] == "fail"]
    binding_unknowns = [c for c in checks if c["binding"] and c["effective_status"] == "unknown"]
    blocking_failures = [
        c for c in checks
        if c["effective_status"] == "fail" and (c["binding"] or c["severity"] in ("blocker", "critical", "major"))
    ]
    minor_failures = [c for c in checks if c["effective_status"] == "fail" and c["severity"] == "minor"]
    controlled = [c for c in checks if c["effective_status"] == "pass_with_controls"]
    accepted_risks = [c for c in checks if c["effective_status"] == "accepted_risk"]
    downgraded_unknowns = [
        c for c in checks if c["effective_status"] == "unknown" and c["status"] in ("pass", "pass_with_controls", "accepted_risk", "fail")
    ]

    material_unknowns = [c for c in checks if c["effective_status"] == "unknown" and c["severity"] in ("blocker", "critical", "major")]
    score = round(overall_score, 1)
    coverage = round(overall_coverage, 1)
    reasons: List[str] = []

    if blocking_failures or governance_blocks:
        verdict = "NO_GO"
        if blocking_failures:
            reasons.append("unresolved blocking failure")
        if governance_blocks:
            reasons.append("governance gate blocks release")
    elif contract_mismatch:
        verdict = "DEFER"
        reasons.append("assessment requirements differ from the independently pinned contract")
    elif identity_gaps:
        verdict = "DEFER"
        reasons.append("release identity incomplete")
    elif scope_gaps:
        verdict = "DEFER"
        reasons.append("release scope/risk assessment incomplete")
    elif mode_gap:
        verdict = "DEFER"
        reasons.append(f"{risk_tier} release requires at least {mode_floor} mode")
    elif missing_required_gates:
        verdict = "DEFER"
        reasons.append("required gate set is incomplete")
    elif binding_unknowns:
        verdict = "DEFER"
        reasons.append("binding gate lacks admissible evidence")
    elif missing_governance_gates or governance_unknowns:
        verdict = "DEFER"
        reasons.append("required governance gate unresolved")
    elif material_unknowns:
        verdict = "DEFER"
        reasons.append("material finding remains unverified")
    elif overall_coverage < thresholds["min_coverage"]:
        verdict = "DEFER"
        reasons.append("evidence coverage below risk-tier threshold")
    elif overall_score < thresholds["conditional_score"]:
        verdict = "NO_GO"
        reasons.append("readiness score below conditional threshold")
    elif controlled or accepted_risks or governance_controls or minor_failures or overall_score < thresholds["go_score"]:
        verdict = "GO_WITH_CONTROLS"
        reasons.append("non-blocking residual risk or readiness debt remains")
    else:
        verdict = "GO"
        reasons.append("scope, required gates, governance gates, evidence and thresholds satisfied")

    result = {
        "engine_version": ENGINE_VERSION,
        "contract_hash": contract_hash,
        "contract_mismatch": contract_mismatch,
        "assessment_basis": "declared_manifest",
        "evidence_authentication": "not_performed",
        "deployment_authorization": "not_provided",
        "gating_metrics": {"readiness_score": overall_score, "evidence_coverage": overall_coverage},
        "material_unknowns": [_slim_check(c) for c in material_unknowns],
        "check_states": {c["id"]: c["effective_status"] for c in checks},
        "manifest_version": MANIFEST_VERSION,
        "verdict": verdict,
        "reason": "; ".join(reasons),
        "profile": profile,
        "mode": mode,
        "risk_tier": risk_tier,
        "required_mode_floor": mode_floor,
        "release": release,
        "scope": scope,
        "readiness_score": score,
        "evidence_coverage": coverage,
        "thresholds": thresholds,
        "release_identity_gaps": identity_gaps,
        "scope_gaps": scope_gaps,
        "required_gates": required_gates,
        "missing_required_gates": missing_required_gates,
        "required_governance_surfaces": sorted(governance_surfaces),
        "missing_governance_gates": missing_governance_gates,
        "governance_gates": governance,
        "governance_blocks": governance_blocks,
        "governance_unknowns": governance_unknowns,
        "governance_controls": governance_controls,
        "domain_results": domain_results,
        "binding_failures": [_slim_check(c) for c in binding_failures],
        "binding_unknowns": [_slim_check(c) for c in binding_unknowns],
        "blocking_failures": [_slim_check(c) for c in blocking_failures],
        "minor_failures": [_slim_check(c) for c in minor_failures],
        "controlled_risks": [_slim_check(c) for c in controlled],
        "accepted_risks": [_slim_check(c) for c in accepted_risks],
        "evidence_downgrades": [_slim_check(c) for c in downgraded_unknowns],
        "checks_evaluated": len(checks),
        "snapshot_hash": _snapshot_hash(manifest),
        "revalidation_triggers": _revalidation_triggers(scope),
    }
    result["decision_validity"] = "VALID" if verdict == "GO" else ("WATCH" if verdict == "GO_WITH_CONTROLS" else "NOT_VALID_TO_SHIP")
    return result


def compare(current_manifest: Dict[str, Any], previous_manifest: Dict[str, Any], *, expected_contract_hash: str | None = None) -> Dict[str, Any]:
    previous = evaluate(previous_manifest)
    current = evaluate(current_manifest, expected_contract_hash=expected_contract_hash or previous["contract_hash"])
    def ids(rows):
        return {r["id"] for r in rows}
    cur_block, prev_block = ids(current["blocking_failures"]), ids(previous["blocking_failures"])
    cur_unknown, prev_unknown = ids(current["binding_unknowns"]), ids(previous["binding_unknowns"])
    prev_checks = {c["id"]: c for c in previous_manifest["checks"]}
    cur_checks = {c["id"]: c for c in current_manifest["checks"]}
    changed, weakened = [], set()
    contract_keys = ("gate", "domain", "title", "binding", "severity", "required_evidence", "applicable", "weight")
    for cid in sorted(prev_checks.keys() | cur_checks.keys()):
        a, b = prev_checks.get(cid), cur_checks.get(cid)
        if a is None or b is None:
            changed.append({"id": cid, "change": "added" if a is None else "removed"})
            continue
        keys = (*contract_keys, "status", "evidence_level", "freshness", "evidence")
        diffs = {k: {"from": a.get(k), "to": b.get(k)} for k in keys if a.get(k) != b.get(k)}
        if diffs:
            changed.append({"id": cid, "change": "modified", "fields": diffs})
        if any(k in diffs for k in contract_keys):
            weakened.add(cid)
    removed = prev_checks.keys() - cur_checks.keys()
    # A disappearance or downgrade is not a verified resolution.
    passing = {cid for cid, state in current["check_states"].items() if state in ("pass", "pass_with_controls")} - weakened
    resolved_blocks = prev_block & passing
    resolved_unknowns = prev_unknown & passing
    previous_release, current_release = previous["release"], current["release"]
    environment_changed = previous_release.get("environment") != current_release.get("environment")
    config_changed = previous_release.get("config_digest") != current_release.get("config_digest")
    if environment_changed or config_changed:
        # Evidence from a different deployment context is not closure of this context.
        resolved_blocks, resolved_unknowns = set(), set()
    requirements_changed = previous["contract_hash"] != current["contract_hash"]
    comparable = not (environment_changed or config_changed or requirements_changed)
    current_time, previous_time = _parse_dt(current_release.get("as_of")), _parse_dt(previous_release.get("as_of"))
    if current_time is None or previous_time is None or current_time < previous_time:
        raise ManifestError("delta chronology is invalid")
    identity_keys = (*IMMUTABLE_KEYS, "id", "tag", "deployment_id")
    prev_missing = set(previous["missing_required_gates"])
    cur_required = set(current["required_gates"])
    provided_gates = (prev_missing - set(current["missing_required_gates"])) & cur_required
    resolved_gates = {gate for gate in provided_gates
                      if all(current["check_states"][c["id"]] in ("pass", "pass_with_controls")
                             for c in current_manifest["checks"] if c.get("gate") == gate and c.get("binding") is True)}
    return {
        "previous_verdict": previous["verdict"], "current_verdict": current["verdict"],
        "verdict_changed": previous["verdict"] != current["verdict"],
        "candidate_changed": any(previous_release.get(k) != current_release.get(k) for k in identity_keys),
        "environment_changed": environment_changed, "configuration_changed": config_changed,
        "requirements_changed": requirements_changed, "scores_comparable": comparable,
        "contract_mismatch": current["contract_mismatch"],
        "score_delta": round(current["gating_metrics"]["readiness_score"] - previous["gating_metrics"]["readiness_score"], 1) if comparable else None,
        "coverage_delta": round(current["gating_metrics"]["evidence_coverage"] - previous["gating_metrics"]["evidence_coverage"], 1) if comparable else None,
        "new_blockers": sorted(cur_block - prev_block), "resolved_blockers": sorted(resolved_blocks),
        "removed_blockers": sorted(prev_block & removed),
        "blockers_no_longer_proven_resolved": sorted(prev_block - cur_block - resolved_blocks),
        "new_binding_unknowns": sorted(cur_unknown - prev_unknown), "resolved_binding_unknowns": sorted(resolved_unknowns),
        "removed_binding_unknowns": sorted(prev_unknown & removed),
        "changed_check_requirements": sorted(weakened),
        "new_missing_required_gates": sorted(set(current["missing_required_gates"]) - set(previous["missing_required_gates"])),
        "resolved_missing_required_gates": sorted(resolved_gates),
        "provided_required_gates": sorted(provided_gates),
        "no_longer_required_gates": sorted(set(previous["required_gates"]) - cur_required),
        "changed_checks": changed,
        "previous_snapshot_hash": previous["snapshot_hash"], "current_snapshot_hash": current["snapshot_hash"],
    }


def write_output(path: Path, text: str, inputs: Iterable[Path] = ()) -> None:
    """Create a result without overwriting source manifests or existing different results."""
    if path.resolve() in {p.resolve() for p in inputs}:
        raise ManifestError("output must not replace an input manifest")
    if path.exists() and path.is_symlink():
        raise ManifestError("output itself must not be a symlink")
    blob = (text + "\n").encode("utf-8")
    if path.exists():
        if path.is_file() and path.stat().st_size == len(blob) and path.read_bytes() == blob:
            return
        raise ManifestError("output already exists with different contents")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".readiness-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(blob)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    except OSError as exc:
        raise ManifestError("could not create immutable output") from exc
    finally:
        Path(temporary).unlink(missing_ok=True)


def _load(path: Path) -> Dict[str, Any]:
    try:
        with path.open("rb") as handle:
            blob = handle.read(MAX_INPUT_BYTES + 1)
        if len(blob) > MAX_INPUT_BYTES:
            raise ManifestError("input exceeds size limit")
        data = json.loads(blob, object_pairs_hook=_unique_pairs, parse_constant=_invalid_constant)
        _validate_json(data)
        if not isinstance(data, dict):
            raise ManifestError("input must be a JSON object")
        return data
    except (OSError, UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ManifestError("cannot read valid input JSON") from exc


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate a release-readiness v2 manifest")
    parser.add_argument("--input", required=True, type=Path, help="Path to readiness manifest JSON")
    parser.add_argument("--previous", type=Path, help="Optional previous manifest for delta analysis")
    parser.add_argument("--expected-contract-hash", help="Independent SHA-256 of frozen assessment requirements")
    parser.add_argument("--output", type=Path, help="Optional path for result JSON")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parser.add_argument("--validate-only", action="store_true", help="Validate/evaluate but emit only validation summary")
    parser.add_argument("--ci-policy", choices=("none", "strict", "controlled"), default="none",
                        help="strict: only GO exits 0; controlled: GO and GO_WITH_CONTROLS exit 0")
    args = parser.parse_args(argv)

    try:
        manifest = _load(args.input)
        previous = _load(args.previous) if args.previous else None
        pinned = args.expected_contract_hash
        if previous is not None and pinned is None:
            pinned = evaluate(previous)["contract_hash"]
        result = evaluate(manifest, expected_contract_hash=pinned)
        if previous is not None:
            result["delta"] = compare(manifest, previous, expected_contract_hash=pinned)
        if args.validate_only:
            result = {
                "valid": True,
                "verdict": result["verdict"],
                "snapshot_hash": result["snapshot_hash"],
                "contract_hash": result["contract_hash"],
                "contract_mismatch": result["contract_mismatch"],
                "missing_required_gates": result["missing_required_gates"],
                "scope_gaps": result["scope_gaps"],
            }
    except ManifestError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2

    text = json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True, allow_nan=False)
    try:
        if args.output:
            write_output(args.output, text, [args.input] + ([args.previous] if args.previous else []))
    except (ManifestError, OSError):
        print(json.dumps({"error": "output could not be safely written"}), file=sys.stderr)
        return 2
    print(text)

    if args.ci_policy == "strict":
        return 0 if result.get("verdict") == "GO" else 1
    if args.ci_policy == "controlled":
        return 0 if result.get("verdict") in ("GO", "GO_WITH_CONTROLS") else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
